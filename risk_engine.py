"""
STREAM — Risk Engine (shared logic for app.py and agent tools).

Extracts ML model loading, feature engineering, rule-based scoring,
and prediction logic so both the FastAPI app and the AI agent can use them.
"""

import os
import json
import numpy as np
import pandas as pd
import joblib

from db import fetch_one

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

MODEL_DIR = "trained_model"

NUMERIC_FEATURES = [
    "tender/value/amount",
    "tender/numberOfTenderers",
    "tender/tenderPeriod/durationInDays",
]
CATEGORICAL_FEATURES = [
    "tender/procurementMethod",
    "tenderclassification/description",
    "buyer/name",
]

FLAG_WEIGHTS = {
    "flag_single_bidder": 25,
    "flag_zero_bidders": 20,
    "flag_short_window": 15,
    "flag_non_open": 10,
    "flag_high_value": 10,
    "flag_buyer_concentration": 10,
    "flag_round_amount": 5,
}

FLAG_EXPLANATIONS = {
    "flag_single_bidder": "Only 1 bidder submitted (possible bid-rigging)",
    "flag_zero_bidders": "No bidders recorded (may be pre-awarded)",
    "flag_short_window": "Very short tender window ({duration_days} days)",
    "flag_non_open": "Non-open procurement method: {procurement_method}",
    "flag_high_value": "Contract value above 95th percentile for this category",
    "flag_buyer_concentration": "This buyer dominates >70% of contracts in this category",
    "flag_round_amount": "Contract amount is suspiciously round (possible fixed pricing)",
}


# ─────────────────────────────────────────────
# MODEL LOADING
# ─────────────────────────────────────────────

def load_model_artifacts():
    """Load the trained model and supporting objects."""
    try:
        model = joblib.load(os.path.join(MODEL_DIR, "model.joblib"))
        scaler = joblib.load(os.path.join(MODEL_DIR, "scaler.joblib"))
        label_encoders = joblib.load(os.path.join(MODEL_DIR, "label_encoders.joblib"))
        feature_cols = joblib.load(os.path.join(MODEL_DIR, "feature_cols.joblib"))
        with open(os.path.join(MODEL_DIR, "training_report.json"), "r") as f:
            report = json.load(f)
        print("   ✅ ML model loaded from trained_model/")
        return {
            "model": model,
            "scaler": scaler,
            "label_encoders": label_encoders,
            "feature_cols": feature_cols,
            "report": report,
        }
    except FileNotFoundError:
        print("   ⚠️  ML model not found — /predict endpoints disabled")
        return None


# ─────────────────────────────────────────────
# FEATURE ENGINEERING
# ─────────────────────────────────────────────

def engineer_df(df: pd.DataFrame, artifacts: dict) -> pd.DataFrame:
    """Apply feature engineering to a DataFrame for ML prediction."""
    for col in NUMERIC_FEATURES:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["amount"] = df.get("tender/value/amount", pd.Series([0] * len(df))).fillna(0)
    df["num_tenderers"] = df.get("tender/numberOfTenderers", pd.Series([0] * len(df))).fillna(0)
    df["duration_days"] = df.get("tender/tenderPeriod/durationInDays", pd.Series([0] * len(df))).fillna(0)
    df["log_amount"] = np.log1p(df["amount"])
    df["is_round_amount"] = (df["amount"] % 100000 == 0).astype(int)

    buyer_avg = df.groupby("buyer/name")["amount"].transform("mean")
    df["amount_vs_buyer_avg"] = df["amount"] / (buyer_avg + 1)

    le_map = artifacts["label_encoders"]
    for col in CATEGORICAL_FEATURES:
        le = le_map[col]
        col_enc = col + "_enc"
        df[col_enc] = df[col].astype(str).apply(
            lambda x, _le=le: _le.transform([x])[0] if x in _le.classes_ else -1
        )
    return df


def predict_df(df: pd.DataFrame, artifacts: dict) -> pd.DataFrame:
    """Run ML predictions on an engineered DataFrame."""
    model = artifacts["model"]
    scaler = artifacts["scaler"]
    feature_cols = artifacts["feature_cols"]

    X = df[feature_cols].fillna(0).values
    X_scaled = scaler.transform(X)

    df["predicted_suspicious"] = model.predict(X_scaled)
    df["suspicion_probability"] = model.predict_proba(X_scaled)[:, 1].round(4)
    df["predicted_risk_tier"] = pd.cut(
        df["suspicion_probability"],
        bins=[0, 0.3, 0.6, 1.0],
        labels=["Low", "Medium", "High"],
        include_lowest=True,
    )
    return df


# ─────────────────────────────────────────────
# RULE-BASED FLAGS
# ─────────────────────────────────────────────

def compute_rule_flags(amount, num_tenderers, duration_days, procurement_method, category, buyer_name):
    """
    Compute rule-based flags for a single tender, matching ml_model.py logic.
    Returns: (flags_dict, risk_score, risk_tier, explanation_string)
    """
    flags = {}
    flags["flag_single_bidder"] = 1 if num_tenderers == 1 else 0
    flags["flag_zero_bidders"] = 1 if num_tenderers == 0 else 0
    flags["flag_short_window"] = 1 if duration_days < 7 else 0
    flags["flag_non_open"] = 1 if procurement_method.lower() not in ("open tender", "open") else 0
    flags["flag_round_amount"] = 1 if amount % 100000 == 0 else 0

    # High value: compare against DB percentile
    p95 = fetch_one(
        "SELECT percentile_cont(0.95) WITHIN GROUP (ORDER BY amount) AS p95 "
        "FROM procurement_tender WHERE category = %s",
        (category,),
    )
    p95_val = float(p95["p95"]) if p95 and p95["p95"] else 1e12
    flags["flag_high_value"] = 1 if amount > p95_val else 0

    # Buyer concentration
    buyer_share = fetch_one(
        """
        SELECT COALESCE(
            COUNT(*) FILTER (WHERE buyer_name = %s)::float /
            NULLIF(COUNT(*) FILTER (WHERE category = %s), 0), 0
        ) AS share
        FROM procurement_tender WHERE category = %s
        """,
        (buyer_name, category, category),
    )
    flags["flag_buyer_concentration"] = 1 if buyer_share and float(buyer_share["share"]) > 0.7 else 0

    # Compute risk score (matching ml_model.py weights)
    max_weight = sum(FLAG_WEIGHTS.values())
    weighted_sum = sum(flags[k] * FLAG_WEIGHTS[k] for k in FLAG_WEIGHTS)
    risk_score = round((weighted_sum / max_weight) * 85, 2)  # 85% from rules

    if risk_score >= 60:
        risk_tier = "🔴 High"
    elif risk_score >= 30:
        risk_tier = "🟡 Medium"
    else:
        risk_tier = "🟢 Low"

    # Build explanation
    explanations = []
    if flags["flag_single_bidder"]:
        explanations.append(FLAG_EXPLANATIONS["flag_single_bidder"])
    if flags["flag_zero_bidders"]:
        explanations.append(FLAG_EXPLANATIONS["flag_zero_bidders"])
    if flags["flag_short_window"]:
        explanations.append(FLAG_EXPLANATIONS["flag_short_window"].format(duration_days=duration_days))
    if flags["flag_non_open"]:
        explanations.append(FLAG_EXPLANATIONS["flag_non_open"].format(procurement_method=procurement_method))
    if flags["flag_high_value"]:
        explanations.append(FLAG_EXPLANATIONS["flag_high_value"])
    if flags["flag_buyer_concentration"]:
        explanations.append(FLAG_EXPLANATIONS["flag_buyer_concentration"])
    if flags["flag_round_amount"]:
        explanations.append(FLAG_EXPLANATIONS["flag_round_amount"])

    return flags, risk_score, risk_tier, "; ".join(explanations)


def explain_flags_detailed(flags: dict, risk_score: float, risk_tier: str,
                           amount=None, duration_days=None, procurement_method=None) -> str:
    """
    Return a detailed human-readable breakdown of how the risk score was computed.
    Used by the agent's risk_explainer tool.
    """
    max_weight = sum(FLAG_WEIGHTS.values())
    lines = [f"Risk Score: {risk_score}/100 — Tier: {risk_tier}", ""]
    lines.append("Flag Breakdown:")
    lines.append(f"{'Flag':<30} {'Fired':<8} {'Weight':<8} {'Contribution':<12}")
    lines.append("-" * 60)

    for flag_name, weight in FLAG_WEIGHTS.items():
        fired = flags.get(flag_name, 0)
        contribution = fired * weight
        status = "YES ⚠️" if fired else "no"
        lines.append(f"{flag_name:<30} {status:<8} {weight:<8} {contribution:<12}")

    weighted_sum = sum(flags.get(k, 0) * v for k, v in FLAG_WEIGHTS.items())
    lines.append("-" * 60)
    lines.append(f"Weighted Sum: {weighted_sum}/{max_weight}")
    lines.append(f"Score Calculation: ({weighted_sum}/{max_weight}) × 85 = {round((weighted_sum / max_weight) * 85, 2)}")

    return "\n".join(lines)

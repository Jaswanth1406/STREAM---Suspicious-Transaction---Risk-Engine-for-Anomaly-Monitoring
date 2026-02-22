"""
STREAM Anti-Corruption Engine — FastAPI Backend  v3.0 (Neon DB)
All data served from Neon PostgreSQL. New tenders run through the ML pipeline.

Run:  uvicorn app:app --reload
Docs: http://localhost:8000/docs
"""

import os
import io
import json
import math
import uuid
import threading
import traceback
import numpy as np
import pandas as pd
import joblib
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from db import fetch_all, fetch_one, execute, execute_returning, pool

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

# ─────────────────────────────────────────────
# LOAD ML MODEL (still from disk — model artifacts are local)
# ─────────────────────────────────────────────

def load_model_artifacts():
    """Load the trained model and supporting objects."""
    try:
        model          = joblib.load(os.path.join(MODEL_DIR, "model.joblib"))
        scaler         = joblib.load(os.path.join(MODEL_DIR, "scaler.joblib"))
        label_encoders = joblib.load(os.path.join(MODEL_DIR, "label_encoders.joblib"))
        feature_cols   = joblib.load(os.path.join(MODEL_DIR, "feature_cols.joblib"))
        with open(os.path.join(MODEL_DIR, "training_report.json"), "r") as f:
            report = json.load(f)
        print("   ✅ ML model loaded from trained_model/")
        return {
            "model": model, "scaler": scaler,
            "label_encoders": label_encoders,
            "feature_cols": feature_cols, "report": report,
        }
    except FileNotFoundError:
        print("   ⚠️  ML model not found — /predict endpoints disabled")
        return None


artifacts = load_model_artifacts()


# ─────────────────────────────────────────────
# FASTAPI APP
# ─────────────────────────────────────────────

app = FastAPI(
    title="STREAM Anti-Corruption Engine",
    description="Procurement Fraud Detection API — All data from Neon PostgreSQL.",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# PYDANTIC MODELS
# ─────────────────────────────────────────────

class TenderInput(BaseModel):
    ocid: Optional[str] = Field(None, description="Open Contracting ID")
    tender_id: Optional[str] = Field(None, alias="tender/id")
    tender_title: Optional[str] = Field(None, alias="tender/title")
    buyer_name: str = Field(..., alias="buyer/name")
    tender_value_amount: float = Field(..., alias="tender/value/amount")
    tender_numberOfTenderers: int = Field(..., alias="tender/numberOfTenderers")
    tender_tenderPeriod_durationInDays: int = Field(..., alias="tender/tenderPeriod/durationInDays")
    tender_procurementMethod: str = Field(..., alias="tender/procurementMethod")
    tenderclassification_description: str = Field(..., alias="tenderclassification/description")
    model_config = {"populate_by_name": True}


class PredictionResult(BaseModel):
    ocid: Optional[str] = None
    tender_id: Optional[str] = None
    predicted_suspicious: int
    suspicion_probability: float
    risk_tier: str
    input_summary: dict


class BatchSummary(BaseModel):
    total_records: int
    suspicious_count: int
    suspicious_pct: float
    risk_distribution: dict
    timestamp: str


class TenderSubmission(BaseModel):
    """New tender submission by user."""
    tender_id: Optional[str] = None
    tender_title: Optional[str] = None
    buyer_name: str
    amount: float
    num_tenderers: int
    duration_days: int
    procurement_method: str
    category: str


# ─────────────────────────────────────────────
# ML FEATURE ENGINEERING
# ─────────────────────────────────────────────

def engineer_df(df: pd.DataFrame) -> pd.DataFrame:
    """Apply feature engineering to a DataFrame for ML prediction."""
    for col in NUMERIC_FEATURES:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["amount"]        = df.get("tender/value/amount", pd.Series([0]*len(df))).fillna(0)
    df["num_tenderers"] = df.get("tender/numberOfTenderers", pd.Series([0]*len(df))).fillna(0)
    df["duration_days"] = df.get("tender/tenderPeriod/durationInDays", pd.Series([0]*len(df))).fillna(0)
    df["log_amount"]      = np.log1p(df["amount"])
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


def predict_df(df: pd.DataFrame) -> pd.DataFrame:
    """Run ML predictions on an engineered DataFrame."""
    model        = artifacts["model"]
    scaler       = artifacts["scaler"]
    feature_cols = artifacts["feature_cols"]

    X = df[feature_cols].fillna(0).values
    X_scaled = scaler.transform(X)

    df["predicted_suspicious"]  = model.predict(X_scaled)
    df["suspicion_probability"] = model.predict_proba(X_scaled)[:, 1].round(4)
    df["predicted_risk_tier"]   = pd.cut(
        df["suspicion_probability"],
        bins=[0, 0.3, 0.6, 1.0],
        labels=["Low", "Medium", "High"],
        include_lowest=True,
    )
    return df


# ─────────────────────────────────────────────
# RULE-BASED FLAGS (for new tender submissions)
# ─────────────────────────────────────────────

def compute_rule_flags(amount, num_tenderers, duration_days, procurement_method, category, buyer_name):
    """Compute rule-based flags for a single tender, matching ml_model.py logic."""
    flags = {}
    flags["flag_single_bidder"]      = 1 if num_tenderers == 1 else 0
    flags["flag_zero_bidders"]       = 1 if num_tenderers == 0 else 0
    flags["flag_short_window"]       = 1 if duration_days < 7 else 0
    flags["flag_non_open"]           = 1 if procurement_method.lower() not in ("open tender", "open") else 0
    flags["flag_round_amount"]       = 1 if amount % 100000 == 0 else 0

    # High value: compare against DB percentile
    p95 = fetch_one(
        "SELECT percentile_cont(0.95) WITHIN GROUP (ORDER BY amount) AS p95 "
        "FROM procurement_tender WHERE category = %s",
        (category,),
    )
    p95_val = float(p95["p95"]) if p95 and p95["p95"] else 1e12
    flags["flag_high_value"] = 1 if amount > p95_val else 0

    # Buyer concentration
    buyer_share = fetch_one("""
        SELECT COALESCE(
            COUNT(*) FILTER (WHERE buyer_name = %s)::float /
            NULLIF(COUNT(*) FILTER (WHERE category = %s), 0), 0
        ) AS share
        FROM procurement_tender WHERE category = %s
    """, (buyer_name, category, category))
    flags["flag_buyer_concentration"] = 1 if buyer_share and float(buyer_share["share"]) > 0.7 else 0

    # Compute risk score (matching ml_model.py weights)
    weights = {
        "flag_single_bidder": 25, "flag_zero_bidders": 20,
        "flag_short_window": 15, "flag_non_open": 10,
        "flag_high_value": 10, "flag_buyer_concentration": 10,
        "flag_round_amount": 5,
    }
    max_weight = sum(weights.values())
    weighted_sum = sum(flags[k] * weights[k] for k in weights)
    risk_score = round((weighted_sum / max_weight) * 85, 2)  # 85% from rules

    if risk_score >= 60:
        risk_tier = "🔴 High"
    elif risk_score >= 30:
        risk_tier = "🟡 Medium"
    else:
        risk_tier = "🟢 Low"

    # Build explanation
    explanations = []
    if flags["flag_single_bidder"]: explanations.append("Only 1 bidder submitted (possible bid-rigging)")
    if flags["flag_zero_bidders"]:  explanations.append("No bidders recorded (may be pre-awarded)")
    if flags["flag_short_window"]:  explanations.append(f"Very short tender window ({duration_days} days)")
    if flags["flag_non_open"]:      explanations.append(f"Non-open procurement method: {procurement_method}")
    if flags["flag_high_value"]:    explanations.append("Contract value above 95th percentile for this category")
    if flags["flag_buyer_concentration"]: explanations.append("This buyer dominates >70% of contracts in this category")
    if flags["flag_round_amount"]:  explanations.append("Contract amount is suspiciously round (possible fixed pricing)")

    return flags, risk_score, risk_tier, "; ".join(explanations)


# ─────────────────────────────────────────────
# HELPER: safe value conversion
# ─────────────────────────────────────────────

def safe_val(v):
    """Convert non-JSON-serializable types."""
    if v is None:
        return None
    if isinstance(v, (list, tuple)):
        return [safe_val(x) for x in v]
    if isinstance(v, dict):
        return {k: safe_val(val) for k, val in v.items()}
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        if math.isnan(v) or math.isinf(v):
            return None
        return float(v)
    if isinstance(v, (pd.Timestamp, datetime)):
        return v.isoformat()
    if isinstance(v, np.ndarray):
        return v.tolist()
    try:
        if pd.isna(v):
            return None
    except (ValueError, TypeError):
        pass
    return v


def row_safe(row: dict) -> dict:
    """Make a DB row JSON-safe."""
    return {k: safe_val(v) for k, v in row.items()}


# ═══════════════════════════════════════════════
#  HEALTH & MODEL ENDPOINTS
# ═══════════════════════════════════════════════

@app.get("/", tags=["Health"])
def root():
    counts = fetch_one("""
        SELECT
            (SELECT COUNT(*) FROM procurement_tender)  AS tenders,
            (SELECT COUNT(*) FROM company)             AS companies,
            (SELECT COUNT(*) FROM vendor_profile)      AS vendors,
            (SELECT COUNT(*) FROM bond_flow)            AS bond_flows
    """)
    return {
        "status": "running",
        "service": "STREAM Anti-Corruption Engine",
        "version": "3.0.0",
        "database": "Neon PostgreSQL",
        "model_loaded": artifacts is not None,
        "data_loaded": {
            "procurement_tenders": counts["tenders"],
            "companies": counts["companies"],
            "vendor_profiles": counts["vendors"],
            "bond_flows": counts["bond_flows"],
        },
    }


@app.get("/model/info", tags=["Model"])
def model_info():
    if not artifacts:
        raise HTTPException(status_code=503, detail="Model not loaded.")
    return {
        "model": artifacts["report"]["model"],
        "roc_auc": artifacts["report"]["roc_auc"],
        "accuracy": artifacts["report"]["accuracy"],
        "f1_score": artifacts["report"]["f1_score"],
        "threshold": artifacts["report"]["threshold"],
        "trained_at": artifacts["report"]["trained_at"],
        "features": artifacts["report"]["features"],
    }


# ═══════════════════════════════════════════════
#  DASHBOARD KPIs
# ═══════════════════════════════════════════════

@app.get("/dashboard/kpis", tags=["Dashboard"])
def dashboard_kpis():
    """Top-bar KPIs for the frontend dashboard — all from Neon."""
    kpis = fetch_one("""
        SELECT
            -- Tender flags
            COUNT(*) FILTER (WHERE risk_score >= 20)                              AS active_tender_flags,
            COALESCE(SUM(amount) FILTER (WHERE risk_score >= 20), 0)              AS at_risk_value,
            COUNT(*)                                                               AS total_tenders,
            COUNT(*) FILTER (WHERE risk_tier LIKE '%%High%%')                     AS high_risk_tenders,
            COUNT(*) FILTER (WHERE risk_tier LIKE '%%Medium%%')                   AS medium_risk_tenders,
            COUNT(*) FILTER (WHERE risk_tier LIKE '%%Low%%')                      AS low_risk_tenders,
            COALESCE(SUM(flag_single_bidder), 0)                                  AS bid_rigging_count,
            COALESCE(SUM(flag_zero_bidders), 0)                                   AS zero_bidder_count,
            COALESCE(SUM(flag_short_window), 0)                                   AS short_window_count,
            COALESCE(SUM(ml_anomaly_flag), 0)                                     AS ml_anomaly_count
        FROM procurement_tender
    """)

    company_kpis = fetch_one("""
        SELECT
            COUNT(*) FILTER (WHERE shell_risk_score >= 30) AS shell_networks,
            COUNT(*)                                        AS total_companies
        FROM company
    """)

    vendor_count = fetch_one("SELECT COUNT(*) AS cnt FROM vendor_profile")

    bond_kpis = fetch_one("""
        SELECT
            COALESCE(SUM(total_value), 0)  AS total_bond_value,
            COUNT(DISTINCT purchaser_name)  AS unique_purchasers,
            COUNT(DISTINCT party_name)      AS unique_parties
        FROM bond_flow
    """)

    precision_rate = 0.0
    if artifacts and "report" in artifacts:
        precision_rate = artifacts["report"].get("accuracy", 0.0) * 100

    at_risk = float(kpis["at_risk_value"] or 0)

    return {
        "active_flags": int(kpis["active_tender_flags"]) + int(company_kpis["shell_networks"]),
        "at_risk_value": at_risk,
        "at_risk_value_cr": round(at_risk / 1e7, 1),
        "vendors_tracked": int(vendor_count["cnt"]),
        "precision_rate": round(precision_rate, 1),
        "bid_rigging_detected": int(kpis["bid_rigging_count"]),
        "shell_networks_mapped": int(company_kpis["shell_networks"]),
        "political_connections": int(bond_kpis["unique_purchasers"]),
        "false_positive_control": round(precision_rate, 1),
        "total_tenders": int(kpis["total_tenders"]),
        "high_risk_tenders": int(kpis["high_risk_tenders"]),
        "medium_risk_tenders": int(kpis["medium_risk_tenders"]),
        "low_risk_tenders": int(kpis["low_risk_tenders"]),
        "total_companies": int(company_kpis["total_companies"]),
        "total_bond_value_cr": round(float(bond_kpis["total_bond_value"] or 0) / 1e7, 1),
        "unique_bond_purchasers": int(bond_kpis["unique_purchasers"]),
        "political_parties_linked": int(bond_kpis["unique_parties"]),
    }


# ═══════════════════════════════════════════════
#  FRAUD ALERTS
# ═══════════════════════════════════════════════

@app.get("/alerts", tags=["Alerts"])
def get_alerts(
    alert_type: Optional[str] = Query(None, description="Filter: bid_rigging | shell_network | political | all"),
    risk_tier: Optional[str] = Query(None, description="Filter: High | Medium | Low"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by tender/company name"),
    sort_by: str = Query("risk_score", description="Sort field"),
    sort_order: str = Query("desc", description="asc | desc"),
):
    """Paginated fraud alerts — combines tender, company, and bond alerts."""
    alerts = []

    # ── Tender-level alerts ────────────────────
    if alert_type in (None, "all", "bid_rigging"):
        where_clauses = ["risk_score >= 15"]
        params = []

        if risk_tier:
            where_clauses.append("risk_tier ILIKE %s")
            params.append(f"%{risk_tier}%")

        if search:
            where_clauses.append(
                "(tender_id ILIKE %s OR buyer_name ILIKE %s OR tender_title ILIKE %s OR category ILIKE %s)"
            )
            s = f"%{search}%"
            params.extend([s, s, s, s])

        where_sql = " AND ".join(where_clauses)
        tender_rows = fetch_all(
            f"SELECT * FROM procurement_tender WHERE {where_sql} ORDER BY risk_score DESC LIMIT 500",
            tuple(params),
        )

        for row in tender_rows:
            flags_triggered = []
            if row.get("flag_single_bidder"): flags_triggered.append("Single Bidder")
            if row.get("flag_zero_bidders"):  flags_triggered.append("Zero Bidders")
            if row.get("flag_short_window"):  flags_triggered.append("Short Window")
            if row.get("flag_non_open"):      flags_triggered.append("Non-Open")
            if row.get("flag_high_value"):    flags_triggered.append("High Value")
            if row.get("flag_round_amount"):  flags_triggered.append("Round Amount")
            if row.get("ml_anomaly_flag"):    flags_triggered.append("ML Anomaly")

            sub_type = "bid_rigging"
            if row.get("flag_single_bidder"): sub_type = "bid_rigging"
            elif row.get("flag_short_window"): sub_type = "short_window"
            elif row.get("flag_high_value"): sub_type = "high_value"

            amount = float(row.get("amount") or 0)
            risk_score = float(row.get("risk_score") or 0)
            tier = str(row.get("risk_tier", "Low")).replace("🟢 ", "").replace("🟡 ", "").replace("🔴 ", "")

            # Use ML confidence if available, otherwise fallback to risk_score
            confidence = float(row.get("suspicion_probability") or 0)
            if confidence == 0:
                confidence = min(risk_score / 100, 0.99)

            alerts.append({
                "alert_id": row.get("ocid", ""),
                "alert_type": "bid_rigging",
                "sub_type": sub_type,
                "risk_score": risk_score,
                "confidence": round(confidence, 4),
                "risk_tier": tier,
                "title": f"{', '.join(flags_triggered[:3])} — {(row.get('tender_title') or 'Untitled')[:80]}",
                "tender_id": row.get("tender_id", ""),
                "buyer_name": row.get("buyer_name", ""),
                "category": row.get("category", ""),
                "procurement_method": row.get("procurement_method", ""),
                "amount": amount,
                "amount_cr": round(amount / 1e7, 2),
                "num_tenderers": row.get("num_tenderers", 0),
                "duration_days": row.get("duration_days", 0),
                "flags_triggered": flags_triggered,
                "explanation": row.get("risk_explanation", ""),
                "evidence_strength": risk_score,
                "is_user_submitted": row.get("is_user_submitted", False),
            })

    # ── Company-level alerts (shell network) ──
    if alert_type in (None, "all", "shell_network"):
        company_where = ["shell_risk_score >= 25"]
        company_params = []
        if search:
            company_where.append("(company_name ILIKE %s OR cin ILIKE %s)")
            company_params.extend([f"%{search}%", f"%{search}%"])

        company_rows = fetch_all(
            f"SELECT * FROM company WHERE {' AND '.join(company_where)} "
            "ORDER BY shell_risk_score DESC LIMIT 200",
            tuple(company_params),
        )

        for row in company_rows:
            score = float(row.get("shell_risk_score") or 0)
            tier_val = "High" if score >= 50 else "Medium"
            if risk_tier and tier_val.lower() != risk_tier.lower():
                continue

            flags_triggered = []
            if row.get("address_cluster_flag"): flags_triggered.append("Address Cluster")
            if row.get("low_capital_flag"):     flags_triggered.append("Low Capital")
            if row.get("young_company_flag"):   flags_triggered.append("Young Company")
            if row.get("inactive_flag"):        flags_triggered.append("Inactive")
            if row.get("high_auth_paid_ratio"): flags_triggered.append("High Auth/Paid Ratio")
            if row.get("opc_flag"):             flags_triggered.append("One Person Company")

            alerts.append({
                "alert_id": row.get("cin", ""),
                "alert_type": "shell_network",
                "sub_type": "shell_company",
                "risk_score": score,
                "confidence": min(score / 100, 0.99),
                "risk_tier": tier_val,
                "title": f"Shell Risk — {row.get('company_name', 'Unknown')}",
                "cin": row.get("cin", ""),
                "company_name": row.get("company_name", ""),
                "company_status": row.get("company_status", ""),
                "state": row.get("state_code", ""),
                "address_cluster_size": row.get("address_cluster_size", 0),
                "flags_triggered": flags_triggered,
                "explanation": row.get("explanation", ""),
                "evidence_strength": score,
            })

    # ── Political connection alerts ───────────
    if alert_type in (None, "all", "political"):
        bond_rows = fetch_all("""
            SELECT purchaser_name,
                   SUM(total_value) AS total_value,
                   SUM(total_bonds) AS total_bonds,
                   ARRAY_AGG(DISTINCT party_name) AS parties
            FROM bond_flow
            GROUP BY purchaser_name
            ORDER BY SUM(total_value) DESC
            LIMIT 200
        """)

        for row in bond_rows:
            value = float(row.get("total_value") or 0)
            value_cr = round(value / 1e7, 2)
            score = min(value_cr * 2, 100)
            tier_val = "High" if value_cr >= 50 else ("Medium" if value_cr >= 10 else "Low")
            if risk_tier and tier_val.lower() != risk_tier.lower():
                continue
            if search and search.lower() not in str(row.get("purchaser_name", "")).lower():
                continue

            parties = row.get("parties", []) or []
            alerts.append({
                "alert_id": f"BOND_{str(row['purchaser_name'])[:50]}",
                "alert_type": "political",
                "sub_type": "electoral_bond",
                "risk_score": score,
                "confidence": min(value_cr / 100, 0.99),
                "risk_tier": tier_val,
                "title": f"Electoral Bond — {row['purchaser_name']}",
                "purchaser_name": row["purchaser_name"],
                "total_bond_value": value,
                "total_bond_value_cr": value_cr,
                "total_bonds": int(row.get("total_bonds") or 0),
                "parties_funded": parties,
                "flags_triggered": ["Electoral Bond Purchaser"],
                "explanation": f"Purchased {row.get('total_bonds')} bonds worth ₹{value_cr}Cr to {len(parties)} parties",
                "evidence_strength": score,
            })

    # ── Sort ──
    valid_sort_fields = {"risk_score", "amount", "confidence", "evidence_strength", "num_tenderers", "duration_days"}
    if sort_by not in valid_sort_fields:
        sort_by = "risk_score"
    reverse = sort_order == "desc"
    alerts.sort(key=lambda a: a.get(sort_by, 0) or 0, reverse=reverse)

    # ── Paginate ──
    total = len(alerts)
    start = (page - 1) * page_size
    page_alerts = alerts[start:start + page_size]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if total > 0 else 0,
        "alerts": page_alerts,
    }


# ═══════════════════════════════════════════════
#  VENDOR PROFILE
# ═══════════════════════════════════════════════

@app.get("/vendor/{entity_id}", tags=["Vendor"])
def get_vendor_profile(entity_id: str):
    """Full vendor profile with risk breakdown — from Neon."""
    row = fetch_one(
        "SELECT * FROM vendor_profile WHERE entity_id = %s OR cin = %s",
        (entity_id, entity_id),
    )
    if not row:
        # Try case-insensitive
        row = fetch_one(
            "SELECT * FROM vendor_profile WHERE LOWER(entity_id) = LOWER(%s) OR LOWER(cin) = LOWER(%s)",
            (entity_id, entity_id),
        )
    if not row:
        raise HTTPException(status_code=404, detail=f"Vendor '{entity_id}' not found")

    return {
        "entity_id": row["entity_id"],
        "cin": row.get("cin"),
        "company_name": row["company_name"],
        "company_status": row.get("company_status"),
        "state": row.get("state"),
        "composite_risk_score": float(row.get("composite_risk_score") or 0),
        "risk_tier": row.get("risk_tier", "LOW"),
        "sub_scores": {
            "bid_pattern": float(row.get("bid_pattern_score") or 0),
            "shell_risk": float(row.get("shell_risk_sub_score") or 0),
            "political": float(row.get("political_score") or 0),
            "financials": float(row.get("financials_score") or 0),
        },
        "bid_stats": row.get("bid_stats") or {},
        "political_info": row.get("political_info") or {},
        "connections": row.get("connections") or [],
        "shell_explanation": row.get("shell_explanation"),
        "requires_human_review": row.get("requires_human_review", False),
    }


@app.get("/vendor/search/{query}", tags=["Vendor"])
def search_vendors(query: str, limit: int = Query(20, ge=1, le=100)):
    """Search vendors by name or CIN — from Neon."""
    results = fetch_all(
        """SELECT entity_id, cin, company_name, composite_risk_score, risk_tier,
                  bid_pattern_score, shell_risk_sub_score, political_score, financials_score
           FROM vendor_profile
           WHERE company_name ILIKE %s OR cin ILIKE %s OR entity_id ILIKE %s
           ORDER BY composite_risk_score DESC
           LIMIT %s""",
        (f"%{query}%", f"%{query}%", f"%{query}%", limit),
    )

    return {
        "total": len(results),
        "results": [
            {
                "entity_id": r["entity_id"],
                "company_name": r["company_name"],
                "cin": r.get("cin"),
                "composite_risk_score": float(r.get("composite_risk_score") or 0),
                "risk_tier": r.get("risk_tier", "LOW"),
                "sub_scores": {
                    "bid_pattern": float(r.get("bid_pattern_score") or 0),
                    "shell_risk": float(r.get("shell_risk_sub_score") or 0),
                    "political": float(r.get("political_score") or 0),
                    "financials": float(r.get("financials_score") or 0),
                },
            }
            for r in results
        ],
    }


# ═══════════════════════════════════════════════
#  VENDOR CONNECTIONS
# ═══════════════════════════════════════════════

@app.get("/vendor/{entity_id}/connections", tags=["Vendor"])
def get_vendor_connections(entity_id: str):
    """Connections for a vendor — from Neon."""
    row = fetch_one(
        "SELECT entity_id, company_name, connections FROM vendor_profile "
        "WHERE entity_id = %s OR cin = %s OR LOWER(entity_id) = LOWER(%s)",
        (entity_id, entity_id, entity_id),
    )
    if not row:
        raise HTTPException(status_code=404, detail=f"Vendor '{entity_id}' not found")

    connections = row.get("connections") or []

    # Enrich with risk tiers
    for conn in connections:
        if conn.get("type") == "electoral_bond":
            conn["target_type"] = "POLITICAL_PARTY"
            value = conn.get("value", 0)
            conn["risk_tier"] = "HIGH" if value >= 1e9 else ("MEDIUM" if value >= 1e8 else "LOW")

    return {
        "entity_id": row["entity_id"],
        "company_name": row["company_name"],
        "total_connections": len(connections),
        "connections": connections,
    }


# ═══════════════════════════════════════════════
#  NETWORK GRAPH
# ═══════════════════════════════════════════════

@app.get("/network/graph", tags=["Network"])
def get_network_graph(
    min_risk_score: float = Query(20, description="Min composite risk to include"),
    include_parties: bool = Query(True, description="Include political party nodes"),
    max_nodes: int = Query(200, ge=10, le=2000),
):
    """Network graph for D3/Cytoscape — from Neon."""
    vendor_rows = fetch_all(
        """SELECT entity_id, company_name, composite_risk_score, risk_tier, connections
           FROM vendor_profile
           WHERE composite_risk_score >= %s
           ORDER BY composite_risk_score DESC
           LIMIT %s""",
        (min_risk_score, max_nodes),
    )

    nodes = []
    edges = []
    node_ids = set()

    for row in vendor_rows:
        eid = row["entity_id"]
        node = {
            "id": eid,
            "label": (row["company_name"] or "")[:40],
            "type": "company",
            "risk_score": float(row.get("composite_risk_score") or 0),
            "risk_tier": row.get("risk_tier", "LOW"),
        }
        nodes.append(node)
        node_ids.add(eid)

        for conn in (row.get("connections") or []):
            if conn.get("type") == "electoral_bond":
                target_id = f"PARTY_{conn['target'][:50]}"
                edges.append({
                    "source": eid,
                    "target": target_id,
                    "type": "electoral_bond",
                    "value": conn.get("value", 0),
                    "label": conn.get("label", ""),
                })
                if include_parties and target_id not in node_ids:
                    nodes.append({
                        "id": target_id,
                        "label": conn["target"][:40],
                        "type": "political_party",
                        "risk_score": 0,
                        "risk_tier": "PARTY",
                    })
                    node_ids.add(target_id)
            elif conn.get("type") == "shared_address":
                edges.append({
                    "source": eid,
                    "target": f"ADDR_{eid}",
                    "type": "shared_address",
                    "cluster_size": conn.get("cluster_size", 0),
                    "label": conn.get("label", ""),
                })

    return {
        "nodes": nodes,
        "edges": edges,
        "total_nodes": len(nodes),
        "total_edges": len(edges),
    }


# ═══════════════════════════════════════════════
#  BID ANALYSIS
# ═══════════════════════════════════════════════

@app.get("/bid-analysis", tags=["Bid Analysis"])
def get_bid_analysis(
    buyer_name: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    risk_tier: Optional[str] = Query(None),
    min_amount: Optional[float] = Query(None),
    max_amount: Optional[float] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Bid-level analysis — directly from Neon procurement_tender table."""
    where_parts = []
    params = []

    if buyer_name:
        where_parts.append("buyer_name ILIKE %s")
        params.append(f"%{buyer_name}%")
    if category:
        where_parts.append("category ILIKE %s")
        params.append(f"%{category}%")
    if risk_tier:
        where_parts.append("risk_tier ILIKE %s")
        params.append(f"%{risk_tier}%")
    if min_amount is not None:
        where_parts.append("amount >= %s")
        params.append(min_amount)
    if max_amount is not None:
        where_parts.append("amount <= %s")
        params.append(max_amount)

    where_sql = "WHERE " + " AND ".join(where_parts) if where_parts else ""

    # Count
    count_row = fetch_one(f"SELECT COUNT(*) AS cnt FROM procurement_tender {where_sql}", tuple(params))
    total = int(count_row["cnt"])

    # Paginated fetch
    offset = (page - 1) * page_size
    rows = fetch_all(
        f"""SELECT ocid, tender_id, tender_title, buyer_name, category,
                   procurement_method, amount, num_tenderers, duration_days,
                   flag_single_bidder, flag_zero_bidders, flag_short_window,
                   flag_non_open, flag_high_value, flag_buyer_concentration,
                   flag_round_amount, ml_anomaly_flag, anomaly_score,
                   risk_score, risk_tier, risk_explanation,
                   predicted_suspicious, suspicion_probability, predicted_risk_tier,
                   is_user_submitted
            FROM procurement_tender {where_sql}
            ORDER BY risk_score DESC
            LIMIT %s OFFSET %s""",
        tuple(params) + (page_size, offset),
    )

    tenders = []
    for r in rows:
        t = {k: (float(v) if isinstance(v, (int, float)) and k in ("amount", "anomaly_score", "risk_score", "suspicion_probability") else v)
             for k, v in r.items()}
        # Convert Decimal types
        for k in ("amount", "anomaly_score", "risk_score", "suspicion_probability"):
            if t.get(k) is not None:
                t[k] = float(t[k])
        tenders.append(t)

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if total > 0 else 0,
        "tenders": tenders,
    }


@app.get("/bid-analysis/summary", tags=["Bid Analysis"])
def bid_analysis_summary():
    """Summary statistics for the Bid Analysis tab — from Neon."""
    stats = fetch_one("""
        SELECT
            COUNT(*) AS total_tenders,
            COALESCE(SUM(amount), 0) AS total_amount,
            COALESCE(AVG(risk_score), 0) AS avg_risk,
            COALESCE(SUM(flag_single_bidder), 0) AS single_bidder,
            COALESCE(SUM(flag_zero_bidders), 0) AS zero_bidders,
            COALESCE(SUM(flag_short_window), 0) AS short_window,
            COALESCE(SUM(flag_non_open), 0) AS non_open,
            COALESCE(SUM(flag_high_value), 0) AS high_value,
            COALESCE(SUM(flag_buyer_concentration), 0) AS buyer_concentration,
            COALESCE(SUM(flag_round_amount), 0) AS round_amount,
            COALESCE(SUM(ml_anomaly_flag), 0) AS ml_anomaly
        FROM procurement_tender
    """)

    tier_counts = fetch_all(
        "SELECT risk_tier, COUNT(*) AS cnt FROM procurement_tender GROUP BY risk_tier"
    )
    risk_distribution = {r["risk_tier"]: int(r["cnt"]) for r in tier_counts}

    top_categories = fetch_all("""
        SELECT category AS "tenderclassification/description",
               COUNT(*) AS total,
               SUM(flag_single_bidder) AS flagged,
               AVG(risk_score) AS avg_risk,
               SUM(amount) AS total_value
        FROM procurement_tender
        GROUP BY category
        ORDER BY AVG(risk_score) DESC
        LIMIT 10
    """)

    top_buyers = fetch_all("""
        SELECT buyer_name AS "buyer/name",
               COUNT(*) AS total,
               SUM(flag_single_bidder) AS flagged,
               AVG(risk_score) AS avg_risk,
               SUM(amount) AS total_value
        FROM procurement_tender
        GROUP BY buyer_name
        ORDER BY AVG(risk_score) DESC
        LIMIT 10
    """)

    return {
        "total_tenders": int(stats["total_tenders"]),
        "risk_distribution": risk_distribution,
        "flag_counts": {
            "single_bidder": int(stats["single_bidder"]),
            "zero_bidders": int(stats["zero_bidders"]),
            "short_window": int(stats["short_window"]),
            "non_open": int(stats["non_open"]),
            "high_value": int(stats["high_value"]),
            "buyer_concentration": int(stats["buyer_concentration"]),
            "round_amount": int(stats["round_amount"]),
            "ml_anomaly": int(stats["ml_anomaly"]),
        },
        "top_categories": [row_safe(r) for r in top_categories],
        "top_buyers": [row_safe(r) for r in top_buyers],
        "amount_stats": {
            "total": float(stats["total_amount"]),
            "mean": float(stats["total_amount"]) / max(int(stats["total_tenders"]), 1),
        },
    }


# ═══════════════════════════════════════════════
#  RECENT ACTIVITY FEED
# ═══════════════════════════════════════════════

@app.get("/activity/recent", tags=["Activity"])
def get_recent_activity(limit: int = Query(50, ge=1, le=200)):
    """Recent activity feed — from Neon procurement_tender + bond_flow."""
    activities = []

    # Tender flag events (top by risk score)
    tender_events = fetch_all("""
        SELECT ocid, tender_id, tender_title, buyer_name, category,
               amount, risk_score, risk_tier,
               flag_single_bidder, flag_high_value, flag_short_window,
               is_user_submitted, created_at
        FROM procurement_tender
        WHERE risk_score >= 20
        ORDER BY risk_score DESC
        LIMIT %s
    """, (limit,))

    for row in tender_events:
        risk_tier = str(row.get("risk_tier", "")).replace("🟢 ", "").replace("🟡 ", "").replace("🔴 ", "")
        amount = float(row.get("amount") or 0)
        amount_cr = round(amount / 1e7, 1)

        if row.get("flag_single_bidder"):
            event_type, icon, title = "bid_rigging_flag", "alert", "Bid rigging flag raised"
        elif row.get("flag_high_value"):
            event_type, icon, title = "high_value_flag", "money", "High value contract flagged"
        elif row.get("flag_short_window"):
            event_type, icon, title = "short_window_flag", "clock", "Short tender window detected"
        else:
            event_type, icon, title = "risk_flag", "flag", "Risk flag raised"

        activities.append({
            "event_type": event_type,
            "icon": icon,
            "title": title,
            "subtitle": f"{row.get('tender_id', '')} · {row.get('category', '')}",
            "risk_tier": risk_tier,
            "risk_score": float(row.get("risk_score") or 0),
            "amount_cr": amount_cr,
            "entity_name": row.get("buyer_name", ""),
            "entity_id": row.get("ocid", ""),
            "is_user_submitted": row.get("is_user_submitted", False),
            "sort_key": float(row.get("risk_score") or 0),
        })

    # Bond purchase events
    bond_events = fetch_all("""
        SELECT purchaser_name, party_name, total_bonds, total_value, last_date
        FROM bond_flow
        ORDER BY total_value DESC
        LIMIT %s
    """, (limit,))

    for row in bond_events:
        value = float(row.get("total_value") or 0)
        value_cr = round(value / 1e7, 1)
        activities.append({
            "event_type": "electoral_bond",
            "icon": "bond",
            "title": "Electoral bond purchased",
            "subtitle": f"{row.get('last_date', '')} · ₹{value_cr}Cr donation",
            "risk_tier": "HIGH" if value_cr >= 50 else ("MEDIUM" if value_cr >= 10 else "LOW"),
            "risk_score": min(value_cr * 2, 100),
            "amount_cr": value_cr,
            "entity_name": row.get("purchaser_name", ""),
            "party_name": row.get("party_name", ""),
            "sort_key": value_cr,
        })

    activities.sort(key=lambda a: a.get("sort_key", 0), reverse=True)
    return {"total": len(activities), "activities": activities[:limit]}


# ═══════════════════════════════════════════════
#  STATISTICS / ANALYTICS
# ═══════════════════════════════════════════════

@app.get("/stats/risk-distribution", tags=["Statistics"])
def risk_distribution():
    """Risk score distribution across all tenders — from Neon."""
    rows = fetch_all("""
        SELECT
            width_bucket(risk_score, 0, 100, 20) AS bucket,
            COUNT(*) AS cnt,
            MIN(risk_score) AS bucket_min,
            MAX(risk_score) AS bucket_max
        FROM procurement_tender
        GROUP BY bucket
        ORDER BY bucket
    """)

    bins = [float(r["bucket_min"]) if r["bucket_min"] else i * 5 for i, r in enumerate(rows)]
    counts = [int(r["cnt"]) for r in rows]

    stats_row = fetch_one("""
        SELECT AVG(risk_score) AS mean, 
               PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY risk_score) AS median,
               STDDEV(risk_score) AS std
        FROM procurement_tender
    """)

    return {
        "bins": bins,
        "counts": counts,
        "mean": round(float(stats_row["mean"] or 0), 2),
        "median": round(float(stats_row["median"] or 0), 2),
        "std": round(float(stats_row["std"] or 0), 2),
    }


@app.get("/stats/top-risk-buyers", tags=["Statistics"])
def top_risk_buyers(limit: int = Query(20, ge=1, le=100)):
    """Top buyers by average risk score — from Neon."""
    rows = fetch_all("""
        SELECT buyer_name AS "buyer/name",
               COUNT(*) AS total_tenders,
               AVG(risk_score) AS avg_risk_score,
               MAX(risk_score) AS max_risk_score,
               SUM(amount) AS total_amount,
               SUM(flag_single_bidder) AS flagged_tenders
        FROM procurement_tender
        GROUP BY buyer_name
        HAVING COUNT(*) >= 3
        ORDER BY AVG(risk_score) DESC
        LIMIT %s
    """, (limit,))

    return {"buyers": [row_safe(r) for r in rows]}


@app.get("/stats/bond-summary", tags=["Statistics"])
def bond_summary():
    """Electoral bond flow summary — from Neon."""
    overview = fetch_one("""
        SELECT COALESCE(SUM(total_value), 0) AS total_value,
               COUNT(*) AS total_flows,
               COUNT(DISTINCT purchaser_name) AS unique_purchasers,
               COUNT(DISTINCT party_name) AS unique_parties
        FROM bond_flow
    """)

    party_rows = fetch_all("""
        SELECT party_name,
               SUM(total_value) AS total_value,
               SUM(total_bonds) AS total_bonds,
               COUNT(DISTINCT purchaser_name) AS unique_purchasers
        FROM bond_flow
        GROUP BY party_name
        ORDER BY SUM(total_value) DESC
    """)

    return {
        "total_flows": int(overview["total_flows"]),
        "total_value": float(overview["total_value"]),
        "total_value_cr": round(float(overview["total_value"]) / 1e7, 1),
        "unique_purchasers": int(overview["unique_purchasers"]),
        "unique_parties": int(overview["unique_parties"]),
        "party_breakdown": [row_safe(r) for r in party_rows],
    }


# ═══════════════════════════════════════════════
#  ML PREDICTION ENDPOINTS (live inference)
# ═══════════════════════════════════════════════

@app.post("/predict", response_model=PredictionResult, tags=["Predict"])
def predict_single(tender: TenderInput):
    """Predict if a single tender is suspicious (live ML inference)."""
    if not artifacts:
        raise HTTPException(status_code=503, detail="Model not loaded.")

    row = {
        "buyer/name": tender.buyer_name,
        "tender/value/amount": tender.tender_value_amount,
        "tender/numberOfTenderers": tender.tender_numberOfTenderers,
        "tender/tenderPeriod/durationInDays": tender.tender_tenderPeriod_durationInDays,
        "tender/procurementMethod": tender.tender_procurementMethod,
        "tenderclassification/description": tender.tenderclassification_description,
    }
    df = pd.DataFrame([row])
    df = engineer_df(df)
    df = predict_df(df)

    return PredictionResult(
        ocid=tender.ocid,
        tender_id=tender.tender_id,
        predicted_suspicious=int(df["predicted_suspicious"].iloc[0]),
        suspicion_probability=float(df["suspicion_probability"].iloc[0]),
        risk_tier=str(df["predicted_risk_tier"].iloc[0]),
        input_summary={
            "amount": tender.tender_value_amount,
            "num_tenderers": tender.tender_numberOfTenderers,
            "duration_days": tender.tender_tenderPeriod_durationInDays,
            "procurement_method": tender.tender_procurementMethod,
            "category": tender.tenderclassification_description,
            "buyer": tender.buyer_name,
        },
    )


@app.post("/predict/batch", tags=["Predict"])
async def predict_batch(file: UploadFile = File(...)):
    """Upload CSV → get predictions CSV back (live ML inference)."""
    if not artifacts:
        raise HTTPException(status_code=503, detail="Model not loaded.")
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files accepted.")

    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV parse error: {e}")

    required = [
        "buyer/name", "tender/value/amount", "tender/numberOfTenderers",
        "tender/tenderPeriod/durationInDays", "tender/procurementMethod",
        "tenderclassification/description",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing columns: {missing}")

    df = engineer_df(df)
    df = predict_df(df)

    output_cols = [
        "ocid", "tender/id", "tender/title", "buyer/name",
        "tenderclassification/description", "tender/procurementMethod",
        "amount", "num_tenderers", "duration_days",
        "predicted_suspicious", "suspicion_probability", "predicted_risk_tier",
    ]
    output_cols = [c for c in output_cols if c in df.columns]
    result = df[output_cols].sort_values("suspicion_probability", ascending=False)

    csv_buffer = io.StringIO()
    result.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    return StreamingResponse(
        io.BytesIO(csv_buffer.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=predictions_{file.filename}"},
    )


@app.post("/predict/batch/json", response_model=BatchSummary, tags=["Predict"])
async def predict_batch_json(file: UploadFile = File(...)):
    """Upload CSV → get JSON summary of predictions (live ML inference)."""
    if not artifacts:
        raise HTTPException(status_code=503, detail="Model not loaded.")
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files accepted.")

    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV parse error: {e}")

    required = [
        "buyer/name", "tender/value/amount", "tender/numberOfTenderers",
        "tender/tenderPeriod/durationInDays", "tender/procurementMethod",
        "tenderclassification/description",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing columns: {missing}")

    df = engineer_df(df)
    df = predict_df(df)

    n_sus = int(df["predicted_suspicious"].sum())
    risk_dist = df["predicted_risk_tier"].value_counts().to_dict()
    risk_dist = {str(k): int(v) for k, v in risk_dist.items()}

    return BatchSummary(
        total_records=len(df),
        suspicious_count=n_sus,
        suspicious_pct=round(100 * n_sus / len(df), 1),
        risk_distribution=risk_dist,
        timestamp=datetime.now().isoformat(),
    )


# ═══════════════════════════════════════════════
#  NEW TENDER SUBMISSION + PIPELINE
# ═══════════════════════════════════════════════

def _run_pipeline_for_tender(job_id: int, tender_data: dict):
    """Background worker: run rule-based + ML pipeline on a new tender, store results in Neon."""
    try:
        # Mark job as running
        execute(
            "UPDATE pipeline_job SET status = 'running', started_at = NOW() WHERE job_id = %s",
            (job_id,),
        )

        amount = tender_data["amount"]
        num_tenderers = tender_data["num_tenderers"]
        duration_days = tender_data["duration_days"]
        procurement_method = tender_data["procurement_method"]
        category = tender_data["category"]
        buyer_name = tender_data["buyer_name"]

        # Step 1: Rule-based flags
        flags, risk_score, risk_tier, explanation = compute_rule_flags(
            amount, num_tenderers, duration_days, procurement_method, category, buyer_name
        )

        # Step 2: ML prediction
        predicted_suspicious = 0
        suspicion_probability = 0.0
        predicted_risk_tier = "Low"

        if artifacts:
            row = {
                "buyer/name": buyer_name,
                "tender/value/amount": amount,
                "tender/numberOfTenderers": num_tenderers,
                "tender/tenderPeriod/durationInDays": duration_days,
                "tender/procurementMethod": procurement_method,
                "tenderclassification/description": category,
            }
            df = pd.DataFrame([row])
            df = engineer_df(df)
            df = predict_df(df)

            predicted_suspicious = int(df["predicted_suspicious"].iloc[0])
            suspicion_probability = float(df["suspicion_probability"].iloc[0])
            predicted_risk_tier = str(df["predicted_risk_tier"].iloc[0])

            # Update risk_score to blend rule-based + ML
            ml_boost = suspicion_probability * 15  # 15% weight from ML
            risk_score = min(round(risk_score + ml_boost, 2), 100)
            if risk_score >= 60:
                risk_tier = "🔴 High"
            elif risk_score >= 30:
                risk_tier = "🟡 Medium"

            if predicted_suspicious:
                explanation += "; ML model flagged this as suspicious"

        # Step 3: Generate OCID
        ocid = tender_data.get("ocid") or f"USER_{datetime.now().strftime('%Y%m%d%H%M%S')}_{job_id}"

        # Step 4: Insert into procurement_tender
        execute("""
            INSERT INTO procurement_tender (
                ocid, tender_id, tender_title, buyer_name, category,
                procurement_method, amount, num_tenderers, duration_days,
                flag_single_bidder, flag_zero_bidders, flag_short_window,
                flag_non_open, flag_high_value, flag_buyer_concentration,
                flag_round_amount, ml_anomaly_flag, anomaly_score,
                risk_score, risk_tier, risk_explanation,
                predicted_suspicious, suspicion_probability, predicted_risk_tier,
                source_file, is_user_submitted
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s
            )
        """, (
            ocid,
            tender_data.get("tender_id", ""),
            tender_data.get("tender_title", ""),
            buyer_name,
            category,
            procurement_method,
            amount,
            num_tenderers,
            duration_days,
            flags["flag_single_bidder"],
            flags["flag_zero_bidders"],
            flags["flag_short_window"],
            flags["flag_non_open"],
            flags["flag_high_value"],
            flags["flag_buyer_concentration"],
            flags["flag_round_amount"],
            0,  # ml_anomaly_flag (Isolation Forest not run for single tenders)
            0,  # anomaly_score
            risk_score,
            risk_tier,
            explanation,
            predicted_suspicious,
            suspicion_probability,
            predicted_risk_tier,
            "user_submitted",
            True,
        ))

        # Step 5: Update pipeline_job with results
        result = {
            "ocid": ocid,
            "risk_score": risk_score,
            "risk_tier": risk_tier,
            "predicted_suspicious": predicted_suspicious,
            "suspicion_probability": suspicion_probability,
            "predicted_risk_tier": predicted_risk_tier,
            "flags": flags,
            "explanation": explanation,
        }

        execute(
            "UPDATE pipeline_job SET status = 'completed', completed_at = NOW(), result_data = %s WHERE job_id = %s",
            (json.dumps(result), job_id),
        )

    except Exception as e:
        execute(
            "UPDATE pipeline_job SET status = 'failed', completed_at = NOW(), error_message = %s WHERE job_id = %s",
            (f"{type(e).__name__}: {str(e)}", job_id),
        )
        traceback.print_exc()


@app.post("/tender/submit", tags=["Submit"])
def submit_tender(tender: TenderSubmission, background_tasks: BackgroundTasks):
    """
    Submit a new tender for risk analysis. Runs through the full pipeline
    (rule-based flags + ML prediction) in the background and stores the result in Neon.
    Returns a job_id to poll for status.
    """
    tender_data = {
        "tender_id": tender.tender_id or "",
        "tender_title": tender.tender_title or "",
        "buyer_name": tender.buyer_name,
        "amount": tender.amount,
        "num_tenderers": tender.num_tenderers,
        "duration_days": tender.duration_days,
        "procurement_method": tender.procurement_method,
        "category": tender.category,
    }

    # Create pipeline job
    job = execute_returning(
        """INSERT INTO pipeline_job (job_type, status, input_data, created_at)
           VALUES ('single_tender', 'queued', %s, NOW())
           RETURNING job_id""",
        (json.dumps(tender_data),),
    )
    job_id = job["job_id"]

    # Launch background worker
    background_tasks.add_task(_run_pipeline_for_tender, job_id, tender_data)

    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Tender submitted for analysis. Poll /pipeline/status/{job_id} for results.",
    }


@app.post("/tender/submit/batch", tags=["Submit"])
async def submit_tender_batch(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """
    Upload a CSV of new tenders. Each row is queued as a separate pipeline job.
    Returns a list of job_ids.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files accepted.")

    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV parse error: {e}")

    # Map columns flexibly
    col_map = {
        "buyer/name": "buyer_name", "buyer_name": "buyer_name",
        "tender/value/amount": "amount", "amount": "amount",
        "tender/numberOfTenderers": "num_tenderers", "num_tenderers": "num_tenderers",
        "tender/tenderPeriod/durationInDays": "duration_days", "duration_days": "duration_days",
        "tender/procurementMethod": "procurement_method", "procurement_method": "procurement_method",
        "tenderclassification/description": "category", "category": "category",
        "tender/id": "tender_id", "tender_id": "tender_id",
        "tender/title": "tender_title", "tender_title": "tender_title",
    }

    required_fields = {"buyer_name", "amount", "num_tenderers", "duration_days", "procurement_method", "category"}
    mapped = {}
    for col in df.columns:
        if col in col_map:
            mapped[col_map[col]] = col

    missing = required_fields - set(mapped.keys())
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing columns (need {missing}). Found: {list(df.columns)}")

    job_ids = []
    for _, row in df.iterrows():
        tender_data = {
            "tender_id": str(row.get(mapped.get("tender_id", ""), "")),
            "tender_title": str(row.get(mapped.get("tender_title", ""), "")),
            "buyer_name": str(row[mapped["buyer_name"]]),
            "amount": float(row[mapped["amount"]]),
            "num_tenderers": int(row[mapped["num_tenderers"]]),
            "duration_days": int(row[mapped["duration_days"]]),
            "procurement_method": str(row[mapped["procurement_method"]]),
            "category": str(row[mapped["category"]]),
        }

        job = execute_returning(
            """INSERT INTO pipeline_job (job_type, status, input_data, created_at)
               VALUES ('batch_tender', 'queued', %s, NOW())
               RETURNING job_id""",
            (json.dumps(tender_data),),
        )
        job_id = job["job_id"]
        job_ids.append(job_id)

        background_tasks.add_task(_run_pipeline_for_tender, job_id, tender_data)

    return {
        "total_submitted": len(job_ids),
        "job_ids": job_ids,
        "message": f"{len(job_ids)} tenders queued for analysis. Poll /pipeline/status/{{job_id}} for each.",
    }


# ═══════════════════════════════════════════════
#  PIPELINE JOB STATUS
# ═══════════════════════════════════════════════

@app.get("/pipeline/status/{job_id}", tags=["Pipeline"])
def get_pipeline_status(job_id: int):
    """Check the status of a pipeline job (single or batch tender)."""
    row = fetch_one(
        "SELECT * FROM pipeline_job WHERE job_id = %s", (job_id,)
    )
    if not row:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    result = {
        "job_id": row["job_id"],
        "job_type": row["job_type"],
        "status": row["status"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "started_at": row["started_at"].isoformat() if row["started_at"] else None,
        "completed_at": row["completed_at"].isoformat() if row["completed_at"] else None,
        "input_data": row.get("input_data"),
    }

    if row["status"] == "completed":
        result["result"] = row.get("result_data")
    elif row["status"] == "failed":
        result["error"] = row.get("error_message")

    return result


@app.get("/pipeline/jobs", tags=["Pipeline"])
def list_pipeline_jobs(
    status: Optional[str] = Query(None, description="Filter: queued | running | completed | failed"),
    limit: int = Query(50, ge=1, le=200),
):
    """List recent pipeline jobs."""
    if status:
        rows = fetch_all(
            "SELECT job_id, job_type, status, created_at, completed_at FROM pipeline_job "
            "WHERE status = %s ORDER BY created_at DESC LIMIT %s",
            (status, limit),
        )
    else:
        rows = fetch_all(
            "SELECT job_id, job_type, status, created_at, completed_at FROM pipeline_job "
            "ORDER BY created_at DESC LIMIT %s",
            (limit,),
        )

    return {
        "total": len(rows),
        "jobs": [
            {
                "job_id": r["job_id"],
                "job_type": r["job_type"],
                "status": r["status"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                "completed_at": r["completed_at"].isoformat() if r["completed_at"] else None,
            }
            for r in rows
        ],
    }


# ═══════════════════════════════════════════════
#  LIFECYCLE
# ═══════════════════════════════════════════════

@app.on_event("shutdown")
def shutdown():
    """Close the connection pool on shutdown."""
    pool.close()

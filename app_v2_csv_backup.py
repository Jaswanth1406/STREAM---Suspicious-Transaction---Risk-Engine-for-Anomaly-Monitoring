"""
STREAM Anti-Corruption Engine — FastAPI Backend
Serves the trained ML model and all precomputed risk data for the frontend.

Run:  uvicorn app:app --reload
Docs: http://localhost:8000/docs
"""

import os
import sys
import io
import json
import math
import numpy as np
import pandas as pd
import joblib
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

MODEL_DIR = "trained_model"
OUTPUT_DIR = "outputs"
OUTPUT_DATASETS_DIR = "output_datasets"

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
# LOAD ALL DATA AT STARTUP
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

        return {
            "model": model,
            "scaler": scaler,
            "label_encoders": label_encoders,
            "feature_cols": feature_cols,
            "report": report,
        }
    except FileNotFoundError:
        return None


def load_dataframes():
    """Load all precomputed CSV/JSON data into memory for fast API responses."""
    data = {}

    # Procurement risk scores (rule-based)
    try:
        data["procurement"] = pd.read_csv(
            os.path.join(OUTPUT_DATASETS_DIR, "procurement_risk_scores.csv")
        )
    except FileNotFoundError:
        data["procurement"] = pd.DataFrame()

    # ML predictions (all years combined)
    try:
        pred_files = sorted([
            f for f in os.listdir(OUTPUT_DATASETS_DIR)
            if f.endswith("_predictions.csv")
        ])
        if pred_files:
            frames = [pd.read_csv(os.path.join(OUTPUT_DATASETS_DIR, f)) for f in pred_files]
            data["predictions"] = pd.concat(frames, ignore_index=True)
        else:
            data["predictions"] = pd.DataFrame()
    except FileNotFoundError:
        data["predictions"] = pd.DataFrame()

    # Company risk table
    try:
        data["companies"] = pd.read_csv(os.path.join(OUTPUT_DIR, "company_risk_table.csv"))
    except FileNotFoundError:
        data["companies"] = pd.DataFrame()

    # Vendor profiles
    try:
        with open(os.path.join(OUTPUT_DIR, "vendor_profiles.json"), "r") as f:
            data["vendor_profiles"] = json.load(f)
    except FileNotFoundError:
        data["vendor_profiles"] = {}

    # Vendor risk summary
    try:
        data["vendor_summary"] = pd.read_csv(os.path.join(OUTPUT_DIR, "vendor_risk_summary.csv"))
    except FileNotFoundError:
        data["vendor_summary"] = pd.DataFrame()

    # Political bond flows
    try:
        data["bond_flows"] = pd.read_csv(os.path.join(OUTPUT_DIR, "political_bond_flows.csv"))
    except FileNotFoundError:
        data["bond_flows"] = pd.DataFrame()

    # Entity matches
    try:
        data["entity_matches_p2c"] = pd.read_csv(
            os.path.join(OUTPUT_DIR, "entity_matches_purchaser_company.csv")
        )
    except FileNotFoundError:
        data["entity_matches_p2c"] = pd.DataFrame()

    try:
        data["entity_matches_b2c"] = pd.read_csv(
            os.path.join(OUTPUT_DIR, "entity_matches_buyer_company.csv")
        )
    except FileNotFoundError:
        data["entity_matches_b2c"] = pd.DataFrame()

    # Entity registry
    try:
        data["entity_registry"] = pd.read_csv(os.path.join(OUTPUT_DIR, "entity_registry.csv"))
    except FileNotFoundError:
        data["entity_registry"] = pd.DataFrame()

    return data


# ── Load everything once at startup ──
artifacts = load_model_artifacts()
app_data = load_dataframes()


# ─────────────────────────────────────────────
# FASTAPI APP
# ─────────────────────────────────────────────

app = FastAPI(
    title="STREAM Anti-Corruption Engine",
    description=(
        "Procurement Fraud Detection API — Dashboard KPIs, fraud alerts, "
        "vendor profiles, network graph, and ML predictions."
    ),
    version="2.0.0",
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


# ─────────────────────────────────────────────
# FEATURE ENGINEERING (for ML prediction)
# ─────────────────────────────────────────────

def engineer_df(df: pd.DataFrame) -> pd.DataFrame:
    """Apply feature engineering to a DataFrame."""
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
    """Run predictions on an engineered DataFrame."""
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


# ─── Helper: safe JSON conversion for numpy/pandas types ───

def safe_val(v):
    """Convert numpy/pandas types to native Python for JSON serialisation."""
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
    if isinstance(v, np.bool_):
        return bool(v)
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


def row_to_dict(row):
    """Convert a pandas row/dict to JSON-safe dict."""
    return {k: safe_val(v) for k, v in row.items()}


# ═══════════════════════════════════════════════
#  HEALTH & MODEL ENDPOINTS
# ═══════════════════════════════════════════════

@app.get("/", tags=["Health"])
def root():
    return {
        "status": "running",
        "service": "STREAM Anti-Corruption Engine",
        "version": "2.0.0",
        "model_loaded": artifacts is not None,
        "data_loaded": {
            "procurement_tenders": len(app_data.get("procurement", [])),
            "ml_predictions": len(app_data.get("predictions", [])),
            "companies": len(app_data.get("companies", [])),
            "vendor_profiles": len(app_data.get("vendor_profiles", {})),
            "bond_flows": len(app_data.get("bond_flows", [])),
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
    """
    Top-bar KPIs for the frontend dashboard.
    Maps to: Active Flags, At Risk Value, Vendors Tracked, Precision Rate.
    """
    proc = app_data.get("procurement", pd.DataFrame())
    companies = app_data.get("companies", pd.DataFrame())
    vendor_profiles = app_data.get("vendor_profiles", {})

    # Active flags: tenders with risk_score >= 20 + companies with shell_risk_score >= 30
    tender_flags = 0
    at_risk_value = 0
    if not proc.empty:
        flagged_tenders = proc[proc["risk_score"] >= 20]
        tender_flags = len(flagged_tenders)
        at_risk_value = float(flagged_tenders["amount"].sum())

    company_flags = 0
    if not companies.empty:
        company_flags = int((companies["shell_risk_score"] >= 30).sum())

    active_flags = tender_flags + company_flags

    # Vendors tracked
    vendors_tracked = len(vendor_profiles)

    # Precision rate from model report
    precision_rate = 0.0
    if artifacts and "report" in artifacts:
        precision_rate = artifacts["report"].get("accuracy", 0.0) * 100

    # Bid rigging count (single-bidder tenders)
    bid_rigging_count = 0
    if not proc.empty and "flag_single_bidder" in proc.columns:
        bid_rigging_count = int(proc["flag_single_bidder"].sum())

    # Shell networks mapped (companies with shell_risk_score >= 30)
    shell_networks = company_flags

    # Political connections found
    bond_flows = app_data.get("bond_flows", pd.DataFrame())
    political_connections = 0
    if not bond_flows.empty:
        political_connections = int(bond_flows["purchaser_name"].nunique())

    # False positive control (model precision)
    false_positive_control = precision_rate

    return {
        "active_flags": active_flags,
        "at_risk_value": at_risk_value,
        "at_risk_value_cr": round(at_risk_value / 1e7, 1),
        "vendors_tracked": vendors_tracked,
        "precision_rate": round(precision_rate, 1),
        "bid_rigging_detected": bid_rigging_count,
        "shell_networks_mapped": shell_networks,
        "political_connections": political_connections,
        "false_positive_control": round(false_positive_control, 1),
        "total_tenders": len(proc) if not proc.empty else 0,
        "total_companies": len(companies) if not companies.empty else 0,
    }


# ═══════════════════════════════════════════════
#  FRAUD ALERTS
# ═══════════════════════════════════════════════

@app.get("/alerts", tags=["Alerts"])
def get_alerts(
    alert_type: Optional[str] = Query(
        None, description="Filter: bid_rigging | shell_network | political | all"
    ),
    risk_tier: Optional[str] = Query(None, description="Filter: High | Medium | Low"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by tender/company name"),
    sort_by: str = Query("risk_score", description="Sort field"),
    sort_order: str = Query("desc", description="asc | desc"),
):
    """
    Paginated fraud alerts — powers the Fraud Alerts tab.
    Combines tender-level alerts and company-level alerts.
    """
    alerts = []

    proc = app_data.get("procurement", pd.DataFrame())
    companies = app_data.get("companies", pd.DataFrame())
    bond_flows = app_data.get("bond_flows", pd.DataFrame())

    # ── Tender-level alerts (bid rigging) ─────
    if not proc.empty and alert_type in (None, "all", "bid_rigging"):
        flagged = proc[proc["risk_score"] >= 15].copy()
        for _, row in flagged.iterrows():
            # Determine alert sub-type
            sub_type = "bid_rigging"
            if row.get("flag_single_bidder", 0) == 1:
                sub_type = "bid_rigging"
            elif row.get("flag_short_window", 0) == 1:
                sub_type = "short_window"
            elif row.get("flag_high_value", 0) == 1:
                sub_type = "high_value"

            # Build title from flags
            flags_triggered = []
            if row.get("flag_single_bidder", 0): flags_triggered.append("Single Bidder")
            if row.get("flag_zero_bidders", 0): flags_triggered.append("Zero Bidders")
            if row.get("flag_short_window", 0): flags_triggered.append("Short Window")
            if row.get("flag_non_open", 0): flags_triggered.append("Non-Open")
            if row.get("flag_high_value", 0): flags_triggered.append("High Value")
            if row.get("flag_round_amount", 0): flags_triggered.append("Round Amount")
            if row.get("ml_anomaly_flag", 0): flags_triggered.append("ML Anomaly")

            amount = safe_val(row.get("amount", 0))
            amount_cr = round(amount / 1e7, 2) if amount else 0

            alerts.append({
                "alert_id": safe_val(row.get("ocid", "")),
                "alert_type": "bid_rigging",
                "sub_type": sub_type,
                "risk_score": safe_val(row.get("risk_score", 0)),
                "confidence": min(safe_val(row.get("risk_score", 0)) / 100, 0.99),
                "risk_tier": safe_val(row.get("risk_tier", "Low")).replace("🟢 ", "").replace("🟡 ", "").replace("🔴 ", ""),
                "title": f"{', '.join(flags_triggered[:3])} — {safe_val(row.get('tender/title', 'Untitled'))[:80]}",
                "tender_id": safe_val(row.get("tender/id", "")),
                "buyer_name": safe_val(row.get("buyer/name", "")),
                "category": safe_val(row.get("tenderclassification/description", "")),
                "procurement_method": safe_val(row.get("tender/procurementMethod", "")),
                "amount": amount,
                "amount_cr": amount_cr,
                "num_tenderers": safe_val(row.get("num_tenderers", 0)),
                "duration_days": safe_val(row.get("duration_days", 0)),
                "flags_triggered": flags_triggered,
                "explanation": safe_val(row.get("risk_explanation", "")),
                "evidence_strength": safe_val(row.get("risk_score", 0)),
            })

    # ── Company-level alerts (shell network) ──
    if not companies.empty and alert_type in (None, "all", "shell_network"):
        shell_flagged = companies[companies["shell_risk_score"] >= 25].copy()
        for _, row in shell_flagged.iterrows():
            alerts.append({
                "alert_id": safe_val(row.get("CIN", "")),
                "alert_type": "shell_network",
                "sub_type": "shell_company",
                "risk_score": safe_val(row.get("shell_risk_score", 0)),
                "confidence": min(safe_val(row.get("shell_risk_score", 0)) / 100, 0.99),
                "risk_tier": "High" if row.get("shell_risk_score", 0) >= 50 else "Medium",
                "title": f"Shell Risk — {safe_val(row.get('CompanyName', 'Unknown'))}",
                "cin": safe_val(row.get("CIN", "")),
                "company_name": safe_val(row.get("CompanyName", "")),
                "company_status": safe_val(row.get("CompanyStatus", "")),
                "state": safe_val(row.get("CompanyStateCode", "")),
                "address_cluster_size": safe_val(row.get("address_cluster_size", 0)),
                "flags_triggered": [
                    f for f in [
                        "Address Cluster" if row.get("address_cluster_flag", 0) else None,
                        "Low Capital" if row.get("low_capital_flag", 0) else None,
                        "Young Company" if row.get("young_company_flag", 0) else None,
                        "Inactive" if row.get("inactive_flag", 0) else None,
                        "High Auth/Paid Ratio" if row.get("high_auth_paid_ratio", 0) else None,
                        "One Person Company" if row.get("opc_flag", 0) else None,
                    ] if f
                ],
                "explanation": safe_val(row.get("explanation", "")),
                "evidence_strength": safe_val(row.get("shell_risk_score", 0)),
            })

    # ── Political connection alerts ───────────
    if not bond_flows.empty and alert_type in (None, "all", "political"):
        top_purchasers = bond_flows.groupby("purchaser_name").agg(
            total_value=("total_value", "sum"),
            total_bonds=("total_bonds", "sum"),
            parties=("party_name", lambda x: list(x.unique())),
        ).reset_index().sort_values("total_value", ascending=False)

        for _, row in top_purchasers.head(200).iterrows():
            value = safe_val(row["total_value"])
            value_cr = round(value / 1e7, 2) if value else 0
            alerts.append({
                "alert_id": f"BOND_{safe_val(row['purchaser_name'])[:50]}",
                "alert_type": "political",
                "sub_type": "electoral_bond",
                "risk_score": min(value_cr * 2, 100),
                "confidence": min(value_cr / 100, 0.99),
                "risk_tier": "High" if value_cr >= 50 else ("Medium" if value_cr >= 10 else "Low"),
                "title": f"Electoral Bond — {safe_val(row['purchaser_name'])}",
                "purchaser_name": safe_val(row["purchaser_name"]),
                "total_bond_value": value,
                "total_bond_value_cr": value_cr,
                "total_bonds": safe_val(row["total_bonds"]),
                "parties_funded": safe_val(row["parties"]),
                "flags_triggered": ["Electoral Bond Purchaser"],
                "explanation": f"Purchased {safe_val(row['total_bonds'])} bonds worth ₹{value_cr}Cr to {len(row['parties'])} parties",
                "evidence_strength": min(value_cr * 2, 100),
            })

    # ── Apply filters ─────────────────────────
    if risk_tier:
        clean_tier = risk_tier.replace("🟢 ", "").replace("🟡 ", "").replace("🔴 ", "")
        alerts = [a for a in alerts if a.get("risk_tier", "").lower() == clean_tier.lower()]

    if search:
        search_lower = search.lower()
        alerts = [
            a for a in alerts
            if search_lower in str(a.get("title", "")).lower()
            or search_lower in str(a.get("buyer_name", "")).lower()
            or search_lower in str(a.get("company_name", "")).lower()
            or search_lower in str(a.get("purchaser_name", "")).lower()
            or search_lower in str(a.get("tender_id", "")).lower()
            or search_lower in str(a.get("cin", "")).lower()
        ]

    # ── Sort ──────────────────────────────────
    reverse = sort_order == "desc"
    alerts.sort(key=lambda a: a.get(sort_by, 0) or 0, reverse=reverse)

    # ── Paginate ──────────────────────────────
    total = len(alerts)
    start = (page - 1) * page_size
    end = start + page_size
    page_alerts = alerts[start:end]

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
    """
    Full vendor profile with risk breakdown — powers the Vendor Profile panel.
    entity_id can be a CIN or a BUYER_ prefixed ID.
    """
    profiles = app_data.get("vendor_profiles", {})

    # Direct lookup
    if entity_id in profiles:
        return profiles[entity_id]

    # Try case-insensitive search
    for pid, profile in profiles.items():
        if pid.lower() == entity_id.lower():
            return profile

    raise HTTPException(status_code=404, detail=f"Vendor '{entity_id}' not found")


@app.get("/vendor/search/{query}", tags=["Vendor"])
def search_vendors(
    query: str,
    limit: int = Query(20, ge=1, le=100),
):
    """
    Search vendors by name, CIN, or partial match.
    Used by the search bar in the frontend.
    """
    profiles = app_data.get("vendor_profiles", {})
    query_lower = query.lower()

    results = []
    for pid, profile in profiles.items():
        name = profile.get("company_name", "").lower()
        cin = str(profile.get("cin", "")).lower()
        if query_lower in name or query_lower in cin or query_lower in pid.lower():
            results.append({
                "entity_id": pid,
                "company_name": profile["company_name"],
                "cin": profile.get("cin"),
                "composite_risk_score": profile["composite_risk_score"],
                "risk_tier": profile["risk_tier"],
                "sub_scores": profile["sub_scores"],
            })

    results.sort(key=lambda r: (
        0 if query_lower == r["company_name"].lower() else 1,
        -r["composite_risk_score"]
    ))

    return {"total": len(results), "results": results[:limit]}


# ═══════════════════════════════════════════════
#  VENDOR CONNECTIONS
# ═══════════════════════════════════════════════

@app.get("/vendor/{entity_id}/connections", tags=["Vendor"])
def get_vendor_connections(entity_id: str):
    """
    Connections for a vendor — political, co-bidder, address cluster.
    Powers the Connections section in the Vendor Profile panel.
    """
    profiles = app_data.get("vendor_profiles", {})
    profile = profiles.get(entity_id)
    if not profile:
        for pid, p in profiles.items():
            if pid.lower() == entity_id.lower():
                profile = p
                break
        if not profile:
            raise HTTPException(status_code=404, detail=f"Vendor '{entity_id}' not found")

    connections = profile.get("connections", [])

    # Enrich political connections with risk tiers
    for conn in connections:
        if conn.get("type") == "electoral_bond":
            target = conn.get("target", "")
            conn["target_type"] = "POLITICAL_PARTY"
            value = conn.get("value", 0)
            if value >= 1e9:
                conn["risk_tier"] = "HIGH"
            elif value >= 1e8:
                conn["risk_tier"] = "MEDIUM"
            else:
                conn["risk_tier"] = "LOW"

    # Also find co-bidder connections from procurement data
    proc = app_data.get("procurement", pd.DataFrame())
    entity_b2c = app_data.get("entity_matches_b2c", pd.DataFrame())

    buyer_name = None
    if not entity_b2c.empty:
        matched = entity_b2c[entity_b2c["matched_cin"] == entity_id]
        if not matched.empty:
            buyer_name = matched.iloc[0]["buyer_name"]

    if buyer_name is None:
        buyer_name = profile.get("company_name", "")

    co_bidder_connections = []
    if not proc.empty and buyer_name:
        buyer_tenders = proc[proc["buyer/name"] == buyer_name]
        if not buyer_tenders.empty:
            for cat in buyer_tenders["tenderclassification/description"].unique():
                cat_tenders = proc[proc["tenderclassification/description"] == cat]
                other_buyers = cat_tenders[cat_tenders["buyer/name"] != buyer_name]["buyer/name"].unique()
                for other in other_buyers[:5]:
                    other_tender_count = len(cat_tenders[cat_tenders["buyer/name"] == other])
                    co_bidder_connections.append({
                        "type": "co_category_buyer",
                        "target": other,
                        "target_type": "PROCUREMENT_BUYER",
                        "shared_category": cat,
                        "tenders_in_category": other_tender_count,
                        "risk_tier": "LOW",
                        "label": f"Co-bidder · {other_tender_count} tenders",
                    })

    all_connections = connections + co_bidder_connections[:10]

    return {
        "entity_id": entity_id,
        "company_name": profile["company_name"],
        "total_connections": len(all_connections),
        "connections": all_connections,
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
    """
    Network graph data for the Network Graph tab.
    Returns nodes + edges as JSON for rendering with D3/Cytoscape.
    """
    profiles = app_data.get("vendor_profiles", {})
    bond_flows = app_data.get("bond_flows", pd.DataFrame())

    nodes = []
    edges = []
    node_ids = set()

    # ── Add high-risk vendor nodes ────────────
    sorted_profiles = sorted(
        profiles.items(),
        key=lambda x: x[1]["composite_risk_score"],
        reverse=True,
    )

    for pid, profile in sorted_profiles[:max_nodes]:
        if profile["composite_risk_score"] < min_risk_score:
            continue

        node = {
            "id": pid,
            "label": profile["company_name"][:40],
            "type": "company",
            "risk_score": profile["composite_risk_score"],
            "risk_tier": profile["risk_tier"],
            "sub_scores": profile["sub_scores"],
        }
        nodes.append(node)
        node_ids.add(pid)

        # Add connections as edges
        for conn in profile.get("connections", []):
            if conn.get("type") == "electoral_bond":
                target_id = f"PARTY_{conn['target'][:50]}"
                edges.append({
                    "source": pid,
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
                    "source": pid,
                    "target": f"ADDR_CLUSTER_{pid}",
                    "type": "shared_address",
                    "cluster_size": conn.get("cluster_size", 0),
                    "label": conn.get("label", ""),
                })

    # ── Add address cluster edges between companies ──
    companies = app_data.get("companies", pd.DataFrame())
    if not companies.empty:
        node_cins = [n["id"] for n in nodes if n.get("type") == "company"]
        if node_cins:
            node_companies = companies[companies["CIN"].isin(node_cins)]
            if "address_cluster_size" in node_companies.columns:
                addr_grouped = node_companies[node_companies["address_cluster_size"] >= 2]
                for state in addr_grouped["CompanyStateCode"].unique():
                    state_companies = addr_grouped[addr_grouped["CompanyStateCode"] == state]["CIN"].tolist()
                    for i in range(len(state_companies)):
                        for j in range(i+1, min(i+3, len(state_companies))):
                            edges.append({
                                "source": state_companies[i],
                                "target": state_companies[j],
                                "type": "address_cluster",
                                "label": f"Same state: {state}",
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
    """
    Bid-level analysis — powers the Bid Analysis tab.
    Returns individual tender data with risk flags and predictions.
    """
    proc = app_data.get("procurement", pd.DataFrame())
    predictions = app_data.get("predictions", pd.DataFrame())

    if proc.empty:
        return {"total": 0, "page": page, "page_size": page_size, "tenders": []}

    df = proc.copy()

    # Merge with ML predictions if available
    if not predictions.empty and "suspicion_probability" in predictions.columns:
        pred_cols = ["ocid", "predicted_suspicious", "suspicion_probability", "predicted_risk_tier"]
        pred_cols = [c for c in pred_cols if c in predictions.columns]
        df = df.merge(predictions[pred_cols], on="ocid", how="left", suffixes=("", "_ml"))

    # ── Filters ───────────────────────────────
    if buyer_name:
        df = df[df["buyer/name"].str.contains(buyer_name, case=False, na=False)]
    if category:
        df = df[df["tenderclassification/description"].str.contains(category, case=False, na=False)]
    if risk_tier:
        clean_tier = risk_tier.replace("🟢 ", "").replace("🟡 ", "").replace("🔴 ", "")
        df = df[df["risk_tier"].str.contains(clean_tier, case=False, na=False)]
    if min_amount is not None:
        df = df[df["amount"] >= min_amount]
    if max_amount is not None:
        df = df[df["amount"] <= max_amount]

    df = df.sort_values("risk_score", ascending=False)

    total = len(df)
    start = (page - 1) * page_size
    page_df = df.iloc[start:start + page_size]

    tenders = []
    for _, row in page_df.iterrows():
        tenders.append(row_to_dict(row))

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if total > 0 else 0,
        "tenders": tenders,
    }


@app.get("/bid-analysis/summary", tags=["Bid Analysis"])
def bid_analysis_summary():
    """Summary statistics for the Bid Analysis tab."""
    proc = app_data.get("procurement", pd.DataFrame())
    if proc.empty:
        return {}

    category_stats = proc.groupby("tenderclassification/description").agg(
        total=("ocid", "count"),
        flagged=("flag_single_bidder", "sum"),
        avg_risk=("risk_score", "mean"),
        total_value=("amount", "sum"),
    ).reset_index().sort_values("avg_risk", ascending=False)

    buyer_stats = proc.groupby("buyer/name").agg(
        total=("ocid", "count"),
        flagged=("flag_single_bidder", "sum"),
        avg_risk=("risk_score", "mean"),
        total_value=("amount", "sum"),
    ).reset_index().sort_values("avg_risk", ascending=False)

    return {
        "total_tenders": len(proc),
        "risk_distribution": proc["risk_tier"].value_counts().to_dict(),
        "flag_counts": {
            "single_bidder": int(proc["flag_single_bidder"].sum()),
            "zero_bidders": int(proc["flag_zero_bidders"].sum()),
            "short_window": int(proc["flag_short_window"].sum()),
            "non_open": int(proc["flag_non_open"].sum()),
            "high_value": int(proc["flag_high_value"].sum()),
            "buyer_concentration": int(proc["flag_buyer_concentration"].sum()),
            "round_amount": int(proc["flag_round_amount"].sum()),
            "ml_anomaly": int(proc["ml_anomaly_flag"].sum()),
        },
        "top_categories": [row_to_dict(r) for _, r in category_stats.head(10).iterrows()],
        "top_buyers": [row_to_dict(r) for _, r in buyer_stats.head(10).iterrows()],
        "amount_stats": {
            "total": float(proc["amount"].sum()),
            "mean": float(proc["amount"].mean()),
            "median": float(proc["amount"].median()),
            "max": float(proc["amount"].max()),
        },
    }


# ═══════════════════════════════════════════════
#  RECENT ACTIVITY FEED
# ═══════════════════════════════════════════════

@app.get("/activity/recent", tags=["Activity"])
def get_recent_activity(limit: int = Query(50, ge=1, le=200)):
    """
    Recent activity feed — combines procurement flags and bond events,
    sorted by risk/importance. Powers the Recent Activity section.
    """
    activities = []

    proc = app_data.get("procurement", pd.DataFrame())
    bond_flows = app_data.get("bond_flows", pd.DataFrame())

    # ── Tender flag events ────────────────────
    if not proc.empty:
        flagged = proc[proc["risk_score"] >= 20].copy()
        flagged = flagged.sort_values("risk_score", ascending=False).head(limit)

        for _, row in flagged.iterrows():
            risk_tier = str(row.get("risk_tier", "")).replace("🟢 ", "").replace("🟡 ", "").replace("🔴 ", "")

            if row.get("flag_single_bidder", 0):
                event_type = "bid_rigging_flag"
                icon = "alert"
                title = "Bid rigging flag raised"
            elif row.get("flag_high_value", 0):
                event_type = "high_value_flag"
                icon = "money"
                title = "High value contract flagged"
            elif row.get("flag_short_window", 0):
                event_type = "short_window_flag"
                icon = "clock"
                title = "Short tender window detected"
            else:
                event_type = "risk_flag"
                icon = "flag"
                title = "Risk flag raised"

            amount_cr = round(safe_val(row.get("amount", 0)) / 1e7, 1)

            activities.append({
                "event_type": event_type,
                "icon": icon,
                "title": title,
                "subtitle": f"{safe_val(row.get('tender/id', ''))} · {safe_val(row.get('tenderclassification/description', ''))}",
                "risk_tier": risk_tier,
                "risk_score": safe_val(row.get("risk_score", 0)),
                "amount_cr": amount_cr,
                "entity_name": safe_val(row.get("buyer/name", "")),
                "entity_id": safe_val(row.get("ocid", "")),
                "sort_key": safe_val(row.get("risk_score", 0)),
            })

    # ── Bond purchase events ──────────────────
    if not bond_flows.empty:
        top_flows = bond_flows.sort_values("total_value", ascending=False).head(limit)
        for _, row in top_flows.iterrows():
            value = safe_val(row.get("total_value", 0))
            value_cr = round(value / 1e7, 1) if value else 0
            activities.append({
                "event_type": "electoral_bond",
                "icon": "bond",
                "title": "Electoral bond purchased",
                "subtitle": f"{safe_val(row.get('last_date', ''))} · ₹{value_cr}Cr donation",
                "risk_tier": "HIGH" if value_cr >= 50 else ("MEDIUM" if value_cr >= 10 else "LOW"),
                "risk_score": min(value_cr * 2, 100),
                "amount_cr": value_cr,
                "entity_name": safe_val(row.get("purchaser_name", "")),
                "party_name": safe_val(row.get("party_name", "")),
                "sort_key": value_cr,
            })

    # ── Contract award events (from predictions) ──
    predictions = app_data.get("predictions", pd.DataFrame())
    if not predictions.empty:
        high_risk = predictions[predictions["predicted_suspicious"] == 1].copy()
        high_risk = high_risk.sort_values("suspicion_probability", ascending=False).head(limit)
        for _, row in high_risk.iterrows():
            amount = safe_val(row.get("amount", 0))
            amount_cr = round(amount / 1e7, 1) if amount else 0
            activities.append({
                "event_type": "contract_awarded",
                "icon": "contract",
                "title": f"Contract awarded ₹{amount_cr}Cr",
                "subtitle": f"{safe_val(row.get('tenderclassification/description', ''))} · {safe_val(row.get('tender/procurementMethod', ''))}",
                "risk_tier": str(row.get("predicted_risk_tier", "")).replace("🟢 ", "").replace("🟡 ", "").replace("🔴 ", ""),
                "risk_score": safe_val(row.get("suspicion_probability", 0)) * 100,
                "amount_cr": amount_cr,
                "entity_name": safe_val(row.get("buyer/name", "")),
                "entity_id": safe_val(row.get("ocid", "")),
                "sort_key": safe_val(row.get("suspicion_probability", 0)) * 100,
            })

    activities.sort(key=lambda a: a.get("sort_key", 0), reverse=True)

    return {
        "total": len(activities),
        "activities": activities[:limit],
    }


# ═══════════════════════════════════════════════
#  STATISTICS / ANALYTICS
# ═══════════════════════════════════════════════

@app.get("/stats/risk-distribution", tags=["Statistics"])
def risk_distribution():
    """Risk score distribution across all tenders."""
    proc = app_data.get("procurement", pd.DataFrame())
    if proc.empty:
        return {"bins": [], "counts": []}

    counts, bin_edges = np.histogram(proc["risk_score"], bins=20, range=(0, 100))
    return {
        "bins": [round(float(b), 1) for b in bin_edges[:-1]],
        "counts": [int(c) for c in counts],
        "mean": round(float(proc["risk_score"].mean()), 2),
        "median": round(float(proc["risk_score"].median()), 2),
        "std": round(float(proc["risk_score"].std()), 2),
    }


@app.get("/stats/top-risk-buyers", tags=["Statistics"])
def top_risk_buyers(limit: int = Query(20, ge=1, le=100)):
    """Top buyers by average risk score."""
    proc = app_data.get("procurement", pd.DataFrame())
    if proc.empty:
        return {"buyers": []}

    buyer_stats = proc.groupby("buyer/name").agg(
        total_tenders=("ocid", "count"),
        avg_risk_score=("risk_score", "mean"),
        max_risk_score=("risk_score", "max"),
        total_amount=("amount", "sum"),
        flagged_tenders=("flag_single_bidder", "sum"),
    ).reset_index().sort_values("avg_risk_score", ascending=False)

    return {
        "buyers": [row_to_dict(r) for _, r in buyer_stats.head(limit).iterrows()]
    }


@app.get("/stats/bond-summary", tags=["Statistics"])
def bond_summary():
    """Electoral bond flow summary statistics."""
    bond_flows = app_data.get("bond_flows", pd.DataFrame())
    if bond_flows.empty:
        return {"total_flows": 0}

    party_totals = bond_flows.groupby("party_name").agg(
        total_value=("total_value", "sum"),
        total_bonds=("total_bonds", "sum"),
        unique_purchasers=("purchaser_name", "nunique"),
    ).reset_index().sort_values("total_value", ascending=False)

    return {
        "total_flows": len(bond_flows),
        "total_value": float(bond_flows["total_value"].sum()),
        "total_value_cr": round(float(bond_flows["total_value"].sum()) / 1e7, 1),
        "unique_purchasers": int(bond_flows["purchaser_name"].nunique()),
        "unique_parties": int(bond_flows["party_name"].nunique()),
        "party_breakdown": [row_to_dict(r) for _, r in party_totals.iterrows()],
    }


# ═══════════════════════════════════════════════
#  ML PREDICTION ENDPOINTS (preserved from v1)
# ═══════════════════════════════════════════════

@app.post("/predict", response_model=PredictionResult, tags=["Predict"])
def predict_single(tender: TenderInput):
    """Predict if a single tender is suspicious."""
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
    """Upload CSV → get predictions CSV back."""
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
    """Upload CSV → get JSON summary of predictions."""
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

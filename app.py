"""
STREAM Anti-Corruption Engine — FastAPI Backend
Serves the trained ML model for procurement fraud detection.

Run:  uvicorn app:app --reload
Docs: http://localhost:8000/docs
"""

import os
import sys
import io
import json
import numpy as np
import pandas as pd
import joblib
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

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
# LOAD MODEL (once at startup)
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


artifacts = load_model_artifacts()

# ─────────────────────────────────────────────
# FASTAPI APP
# ─────────────────────────────────────────────

app = FastAPI(
    title="STREAM Anti-Corruption Engine",
    description="Procurement Fraud Detection API — Predict suspicious transactions using ML",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# REQUEST / RESPONSE MODELS
# ─────────────────────────────────────────────

class TenderInput(BaseModel):
    ocid: Optional[str] = Field(None, description="Open Contracting ID")
    tender_id: Optional[str] = Field(None, alias="tender/id", description="Tender ID")
    tender_title: Optional[str] = Field(None, alias="tender/title", description="Tender title")
    buyer_name: str = Field(..., alias="buyer/name", description="Procuring entity name")
    tender_value_amount: float = Field(..., alias="tender/value/amount", description="Contract value")
    tender_numberOfTenderers: int = Field(..., alias="tender/numberOfTenderers", description="Number of bidders")
    tender_tenderPeriod_durationInDays: int = Field(..., alias="tender/tenderPeriod/durationInDays", description="Tender window in days")
    tender_procurementMethod: str = Field(..., alias="tender/procurementMethod", description="e.g. Open Tender, Limited")
    tenderclassification_description: str = Field(..., alias="tenderclassification/description", description="Tender category")

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
# FEATURE ENGINEERING (shared logic)
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


# ─────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    """Health check."""
    return {
        "status": "running",
        "service": "STREAM Anti-Corruption Engine",
        "model_loaded": artifacts is not None,
    }


@app.get("/model/info", tags=["Model"])
def model_info():
    """Get info about the trained model."""
    if not artifacts:
        raise HTTPException(status_code=503, detail="Model not loaded. Run `python ml_model.py` first.")
    return {
        "model": artifacts["report"]["model"],
        "roc_auc": artifacts["report"]["roc_auc"],
        "accuracy": artifacts["report"]["accuracy"],
        "f1_score": artifacts["report"]["f1_score"],
        "threshold": artifacts["report"]["threshold"],
        "trained_at": artifacts["report"]["trained_at"],
        "features": artifacts["report"]["features"],
    }


@app.post("/predict", response_model=PredictionResult, tags=["Predict"])
def predict_single(tender: TenderInput):
    """Predict if a single tender is suspicious."""
    if not artifacts:
        raise HTTPException(status_code=503, detail="Model not loaded. Run `python ml_model.py` first.")

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
        }
    )


@app.post("/predict/batch", tags=["Predict"])
async def predict_batch(file: UploadFile = File(..., description="CSV file with procurement data")):
    """
    Upload a CSV file and get predictions for all tenders.
    Returns a CSV file with predictions appended.
    """
    if not artifacts:
        raise HTTPException(status_code=503, detail="Model not loaded. Run `python ml_model.py` first.")

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    # Read uploaded CSV
    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {e}")

    # Validate required columns
    required = ["buyer/name", "tender/value/amount", "tender/numberOfTenderers",
                 "tender/tenderPeriod/durationInDays", "tender/procurementMethod",
                 "tenderclassification/description"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required columns: {missing}")

    # Predict
    df = engineer_df(df)
    df = predict_df(df)

    # Select output columns
    output_cols = [
        "ocid", "tender/id", "tender/title", "buyer/name",
        "tenderclassification/description", "tender/procurementMethod",
        "amount", "num_tenderers", "duration_days",
        "predicted_suspicious", "suspicion_probability", "predicted_risk_tier",
    ]
    output_cols = [c for c in output_cols if c in df.columns]
    result = df[output_cols].sort_values("suspicion_probability", ascending=False)

    # Return as downloadable CSV
    csv_buffer = io.StringIO()
    result.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    return StreamingResponse(
        io.BytesIO(csv_buffer.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=predictions_{file.filename}"},
    )


@app.post("/predict/batch/json", response_model=BatchSummary, tags=["Predict"])
async def predict_batch_json(file: UploadFile = File(..., description="CSV file with procurement data")):
    """
    Upload a CSV file and get a JSON summary of predictions.
    """
    if not artifacts:
        raise HTTPException(status_code=503, detail="Model not loaded. Run `python ml_model.py` first.")

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {e}")

    required = ["buyer/name", "tender/value/amount", "tender/numberOfTenderers",
                 "tender/tenderPeriod/durationInDays", "tender/procurementMethod",
                 "tenderclassification/description"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required columns: {missing}")

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

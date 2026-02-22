"""
STREAM Anti-Corruption Engine
Supervised ML Pipeline — learns from rule-based risk labels
AIA-26 Hackathon - Anna University

Pipeline:
  1. Load rule-scored data  (procurement_risk_scores.csv)
  2. Create binary label    (is_suspicious: 1 if risk_score >= 20)
  3. Feature engineering     (from raw procurement CSV)
  4. SMOTE class balancing   (handle 95/5 imbalance)
  5. Train GradientBoosting  + RandomForest for comparison
  6. Evaluate & report       (classification report, ROC-AUC, confusion matrix)
  7. Save model artifacts    (trained_model/)
  8. predict_new_data()      (score any new CSV)
"""

import os
import sys
import json
import warnings
import numpy as np
import pandas as pd
import joblib
from datetime import datetime

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import (
    classification_report, confusion_matrix,
    roc_auc_score, accuracy_score, f1_score
)

warnings.filterwarnings("ignore")

# Fix Windows console encoding for emoji/unicode output
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

RISK_SCORES_CSV  = "output_datasets/procurement_risk_scores.csv"
RAW_DATA_CSV     = "datasets"
MODEL_DIR        = "trained_model"
RISK_THRESHOLD   = 20          # risk_score >= this  →  is_suspicious = 1
TEST_SIZE        = 0.20
RANDOM_STATE     = 42

# Features to use from raw data
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
# 1. CREATE LABELS
# ─────────────────────────────────────────────

def create_labels(risk_csv=RISK_SCORES_CSV, threshold=RISK_THRESHOLD):
    """Load the rule-based risk scores and create a binary label."""
    df_risk = pd.read_csv(risk_csv)
    df_risk["is_suspicious"] = (df_risk["risk_score"] >= threshold).astype(int)

    n_pos = df_risk["is_suspicious"].sum()
    n_neg = len(df_risk) - n_pos
    print(f"📊 Labels created  (threshold = {threshold})")
    print(f"   Suspicious (1):     {n_pos:>5}  ({100*n_pos/len(df_risk):.1f}%)")
    print(f"   Non-suspicious (0): {n_neg:>5}  ({100*n_neg/len(df_risk):.1f}%)")

    return df_risk[["ocid", "is_suspicious", "risk_score"]]


# ─────────────────────────────────────────────
# 2. FEATURE ENGINEERING
# ─────────────────────────────────────────────

def engineer_features(raw_csv=RAW_DATA_CSV):
    """Build feature matrix from raw procurement CSVs.
    
    If raw_csv points to a directory, all CSVs inside are loaded and combined.
    Otherwise, a single CSV file is loaded.
    """
    if os.path.isdir(raw_csv):
        csv_files = sorted([os.path.join(raw_csv, f) for f in os.listdir(raw_csv)
                            if f.endswith(".csv") and f.startswith("ocds_mapped_procurement_data")])
        df = pd.concat([pd.read_csv(f) for f in csv_files], ignore_index=True)
        print(f"🔧 Loaded {len(csv_files)} files → {len(df)} total rows")
    else:
        df = pd.read_csv(raw_csv)

    # ── Numeric features ──────────────────────
    for col in NUMERIC_FEATURES:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["amount"]          = df["tender/value/amount"].fillna(0)
    df["num_tenderers"]   = df["tender/numberOfTenderers"].fillna(0)
    df["duration_days"]   = df["tender/tenderPeriod/durationInDays"].fillna(0)

    # Derived numeric features
    df["log_amount"]      = np.log1p(df["amount"])
    df["is_round_amount"] = (df["amount"] % 100000 == 0).astype(int)

    buyer_avg = df.groupby("buyer/name")["amount"].transform("mean")
    df["amount_vs_buyer_avg"] = df["amount"] / (buyer_avg + 1)

    # ── Categorical features (label-encode) ───
    label_encoders = {}
    for col in CATEGORICAL_FEATURES:
        le = LabelEncoder()
        df[col + "_enc"] = le.fit_transform(df[col].astype(str))
        label_encoders[col] = le

    # ── Final feature list ────────────────────
    feature_cols = [
        "amount", "num_tenderers", "duration_days",
        "log_amount", "is_round_amount", "amount_vs_buyer_avg",
    ] + [col + "_enc" for col in CATEGORICAL_FEATURES]

    print(f"🔧 Engineered {len(feature_cols)} features from {len(df)} rows")
    return df, feature_cols, label_encoders


# ─────────────────────────────────────────────
# 3. MERGE & PREPARE TRAINING SET
# ─────────────────────────────────────────────

def prepare_dataset():
    """Merge labels with features and return X, y arrays."""
    labels = create_labels()
    df, feature_cols, label_encoders = engineer_features()

    # Merge on ocid
    df = df.merge(labels, on="ocid", how="inner")
    print(f"✅ Merged dataset: {len(df)} rows\n")

    X = df[feature_cols].fillna(0).values
    y = df["is_suspicious"].values

    return X, y, feature_cols, label_encoders, df


# ─────────────────────────────────────────────
# 4. TRAIN & EVALUATE
# ─────────────────────────────────────────────

def train_and_evaluate():
    """Full training pipeline with evaluation."""
    print("\n🚀 STREAM ML Pipeline — Supervised Training")
    print("=" * 55)

    X, y, feature_cols, label_encoders, df = prepare_dataset()

    # ── Scale features ────────────────────────
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # ── Train / Test split ────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y,
        test_size=TEST_SIZE,
        stratify=y,
        random_state=RANDOM_STATE,
    )

    print(f"📦 Train: {len(X_train)}  |  Test: {len(X_test)}")
    print(f"   Train positives: {y_train.sum()}  |  Test positives: {y_test.sum()}")

    # ── SMOTE oversampling (train set only) ───
    try:
        from imblearn.over_sampling import SMOTE
        smote = SMOTE(random_state=RANDOM_STATE)
        X_train_bal, y_train_bal = smote.fit_resample(X_train, y_train)
        print(f"⚖️  SMOTE applied → Train size: {len(X_train_bal)} (balanced)")
    except ImportError:
        print("⚠️  imbalanced-learn not installed — using class_weight='balanced' instead")
        X_train_bal, y_train_bal = X_train, y_train

    # ── Model 1: Gradient Boosting ────────────
    print("\n── Training Gradient Boosting ──")
    gb = GradientBoostingClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.1,
        subsample=0.8,
        random_state=RANDOM_STATE,
    )
    gb.fit(X_train_bal, y_train_bal)
    gb_pred  = gb.predict(X_test)
    gb_proba = gb.predict_proba(X_test)[:, 1]
    gb_auc   = roc_auc_score(y_test, gb_proba)
    print(f"   ROC-AUC: {gb_auc:.4f}")
    print(classification_report(y_test, gb_pred, target_names=["Non-Suspicious", "Suspicious"]))

    # ── Model 2: Random Forest ────────────────
    print("── Training Random Forest ──")
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=6,
        class_weight="balanced",
        random_state=RANDOM_STATE,
    )
    rf.fit(X_train_bal, y_train_bal)
    rf_pred  = rf.predict(X_test)
    rf_proba = rf.predict_proba(X_test)[:, 1]
    rf_auc   = roc_auc_score(y_test, rf_proba)
    print(f"   ROC-AUC: {rf_auc:.4f}")
    print(classification_report(y_test, rf_pred, target_names=["Non-Suspicious", "Suspicious"]))

    # ── Pick best model ───────────────────────
    if gb_auc >= rf_auc:
        best_model, best_name, best_auc = gb, "GradientBoosting", gb_auc
        best_pred, best_proba = gb_pred, gb_proba
    else:
        best_model, best_name, best_auc = rf, "RandomForest", rf_auc
        best_pred, best_proba = rf_pred, rf_proba

    print(f"\n🏆 Best model: {best_name}  (ROC-AUC = {best_auc:.4f})")

    # ── Cross-validation on best ──────────────
    cv_scores = cross_val_score(best_model, X_scaled, y, cv=5, scoring="roc_auc")
    print(f"📈 5-Fold CV ROC-AUC: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    # ── Feature importance ────────────────────
    importances = best_model.feature_importances_
    feat_imp = sorted(zip(feature_cols, importances), key=lambda x: x[1], reverse=True)
    print("\n📊 Feature Importance:")
    for fname, imp in feat_imp:
        bar = "█" * int(imp * 50)
        print(f"   {fname:30s}  {imp:.4f}  {bar}")

    # ── Confusion matrix ──────────────────────
    cm = confusion_matrix(y_test, best_pred)
    print(f"\n🔢 Confusion Matrix:")
    print(f"   {'':15s} Pred 0    Pred 1")
    print(f"   {'Actual 0':15s} {cm[0][0]:>6}    {cm[0][1]:>6}")
    print(f"   {'Actual 1':15s} {cm[1][0]:>6}    {cm[1][1]:>6}")

    # ── Save artifacts ────────────────────────
    save_model(best_model, scaler, label_encoders, feature_cols, best_name, best_auc, y_test, best_pred)

    return best_model, scaler, label_encoders, feature_cols


# ─────────────────────────────────────────────
# 5. SAVE MODEL
# ─────────────────────────────────────────────

def save_model(model, scaler, label_encoders, feature_cols, model_name, auc, y_true, y_pred):
    """Persist the trained model and supporting objects."""
    os.makedirs(MODEL_DIR, exist_ok=True)

    joblib.dump(model, os.path.join(MODEL_DIR, "model.joblib"))
    joblib.dump(scaler, os.path.join(MODEL_DIR, "scaler.joblib"))
    joblib.dump(label_encoders, os.path.join(MODEL_DIR, "label_encoders.joblib"))
    joblib.dump(feature_cols, os.path.join(MODEL_DIR, "feature_cols.joblib"))

    # Training report
    report = {
        "model": model_name,
        "roc_auc": round(auc, 4),
        "accuracy": round(accuracy_score(y_true, y_pred), 4),
        "f1_score": round(f1_score(y_true, y_pred), 4),
        "threshold": RISK_THRESHOLD,
        "trained_at": datetime.now().isoformat(),
        "features": feature_cols,
    }
    with open(os.path.join(MODEL_DIR, "training_report.json"), "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n💾 Model saved → {MODEL_DIR}/")
    print(f"   model.joblib, scaler.joblib, label_encoders.joblib, training_report.json")


# ─────────────────────────────────────────────
# 6. PREDICT NEW DATA
# ─────────────────────────────────────────────

def predict_new_data(filepath, output_csv="new_predictions.csv"):
    """
    Score a brand-new procurement CSV using the trained model.

    Args:
        filepath:   Path to a new raw procurement CSV (same schema as training data)
        output_csv: Where to save the predictions

    Returns:
        DataFrame with original data + predicted label + probability
    """
    print(f"\n🔮 Scoring new data: {filepath}")

    # Load saved artifacts
    model          = joblib.load(os.path.join(MODEL_DIR, "model.joblib"))
    scaler         = joblib.load(os.path.join(MODEL_DIR, "scaler.joblib"))
    label_encoders = joblib.load(os.path.join(MODEL_DIR, "label_encoders.joblib"))
    feature_cols   = joblib.load(os.path.join(MODEL_DIR, "feature_cols.joblib"))

    # Load new data
    df = pd.read_csv(filepath)
    original_len = len(df)

    # ── Apply same feature engineering ────────
    for col in NUMERIC_FEATURES:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["amount"]          = df["tender/value/amount"].fillna(0)
    df["num_tenderers"]   = df["tender/numberOfTenderers"].fillna(0)
    df["duration_days"]   = df["tender/tenderPeriod/durationInDays"].fillna(0)
    df["log_amount"]      = np.log1p(df["amount"])
    df["is_round_amount"] = (df["amount"] % 100000 == 0).astype(int)

    buyer_avg = df.groupby("buyer/name")["amount"].transform("mean")
    df["amount_vs_buyer_avg"] = df["amount"] / (buyer_avg + 1)

    # Label-encode categoricals (handle unseen labels gracefully)
    for col in CATEGORICAL_FEATURES:
        le = label_encoders[col]
        col_enc = col + "_enc"
        df[col_enc] = df[col].astype(str).apply(
            lambda x: le.transform([x])[0] if x in le.classes_ else -1
        )

    # ── Predict ───────────────────────────────
    X_new = df[feature_cols].fillna(0).values
    X_new_scaled = scaler.transform(X_new)

    df["predicted_suspicious"] = model.predict(X_new_scaled)
    df["suspicion_probability"] = model.predict_proba(X_new_scaled)[:, 1].round(4)

    # Risk tier from probability
    df["predicted_risk_tier"] = pd.cut(
        df["suspicion_probability"],
        bins=[0, 0.3, 0.6, 1.0],
        labels=["🟢 Low", "🟡 Medium", "🔴 High"],
        include_lowest=True,
    )

    # ── Summary ───────────────────────────────
    n_sus = df["predicted_suspicious"].sum()
    print(f"   Total records:    {original_len}")
    print(f"   Flagged suspicious: {n_sus}  ({100*n_sus/original_len:.1f}%)")
    print(f"\n   Predicted Risk Distribution:")
    print(f"   {df['predicted_risk_tier'].value_counts().to_string()}")

    # ── Save results ──────────────────────────
    output_cols = [
        "ocid", "tender/id", "tender/title", "buyer/name",
        "tenderclassification/description", "tender/procurementMethod",
        "amount", "num_tenderers", "duration_days",
        "predicted_suspicious", "suspicion_probability", "predicted_risk_tier",
    ]
    # Only include columns that exist
    output_cols = [c for c in output_cols if c in df.columns]
    result = df[output_cols].sort_values("suspicion_probability", ascending=False)
    result.to_csv(output_csv, index=False)
    print(f"\n✅ Predictions saved → {output_csv}")

    return result


# ─────────────────────────────────────────────
# 7. BATCH SCORE ALL DATASETS
# ─────────────────────────────────────────────

DATASETS_DIR = "datasets"
OUTPUT_DIR   = "output_datasets"

def batch_score_all_datasets(datasets_dir=DATASETS_DIR, output_dir=OUTPUT_DIR):
    """Score every CSV in the datasets/ folder and save results to output_datasets/."""
    os.makedirs(output_dir, exist_ok=True)

    csv_files = sorted([f for f in os.listdir(datasets_dir)
                         if f.endswith(".csv") and f.startswith("ocds_mapped_procurement_data")])
    if not csv_files:
        print(f"\n⚠️  No CSV files found in {datasets_dir}/")
        return

    print(f"\n{'='*60}")
    print(f"  STREAM — Batch Scoring {len(csv_files)} Datasets")
    print(f"{'='*60}")

    results_summary = []

    for i, fname in enumerate(csv_files, 1):
        input_path  = os.path.join(datasets_dir, fname)
        output_name = fname.replace(".csv", "_predictions.csv")
        output_path = os.path.join(output_dir, output_name)

        print(f"\n[{i}/{len(csv_files)}] Processing: {fname}")
        print("-" * 50)

        try:
            result = predict_new_data(input_path, output_path)
            n_total = len(result)
            n_sus   = int(result["predicted_suspicious"].sum())
            results_summary.append({
                "dataset": fname,
                "total": n_total,
                "suspicious": n_sus,
                "pct": round(100 * n_sus / n_total, 1),
                "status": "✅ Success"
            })
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results_summary.append({
                "dataset": fname,
                "total": 0, "suspicious": 0, "pct": 0,
                "status": f"❌ {e}"
            })

    # Final summary table
    print(f"\n\n{'='*60}")
    print(f"  BATCH SCORING SUMMARY")
    print(f"{'='*60}")
    print(f"{'Dataset':<55} {'Total':>6} {'Susp':>6} {'%':>6}  Status")
    print("-" * 90)
    for r in results_summary:
        print(f"{r['dataset']:<55} {r['total']:>6} {r['suspicious']:>6} {r['pct']:>5.1f}%  {r['status']}")

    ok = len([r for r in results_summary if "✅" in r["status"]])
    fail = len(results_summary) - ok
    print(f"\n📁 All outputs saved to: {output_dir}/")
    print(f"   {ok} succeeded, {fail} failed")

    return results_summary


# ─────────────────────────────────────────────
# 8. ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "predict":
        # Score a single file:  python ml_pipeline.py predict <data.csv> [output.csv]
        new_file = sys.argv[2] if len(sys.argv) > 2 else RAW_DATA_CSV
        output   = sys.argv[3] if len(sys.argv) > 3 else "new_predictions.csv"
        predict_new_data(new_file, output)
    else:
        # Default: train the model, then score ALL datasets in datasets/
        train_and_evaluate()
        batch_score_all_datasets()

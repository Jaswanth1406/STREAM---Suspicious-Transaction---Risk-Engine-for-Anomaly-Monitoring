"""
STREAM Anti-Corruption Engine
Procurement Fraud Risk Scoring Engine
AIA-26 Hackathon - Anna University
"""

import sys
import os
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Fix Windows console encoding for emoji/unicode output
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

filepath = "datasets/ocds_mapped_procurement_data_fiscal_year_2016_2017.csv"
# ─────────────────────────────────────────────
# 1. LOAD DATA
# ─────────────────────────────────────────────

def load_data(filepath):
    df = pd.read_csv(filepath)
    print(f"✅ Loaded {len(df)} tenders from {filepath}")
    return df


# ─────────────────────────────────────────────
# 2. FEATURE ENGINEERING
# ─────────────────────────────────────────────

def engineer_features(df):
    df = df.copy()

    # --- Parse dates ---
    df['date_published'] = pd.to_datetime(df['tender/datePublished'], errors='coerce')
    df['bid_opening_dt']  = pd.to_datetime(df['tender/bidOpening/date'], errors='coerce', dayfirst=True)

    # --- Amount: fill 0/NaN with median ---
    df['amount'] = pd.to_numeric(df['tender/value/amount'], errors='coerce')
    median_amount = df['amount'].median()
    df['amount'] = df['amount'].fillna(median_amount).replace(0, median_amount)

    # --- Number of bidders ---
    df['num_tenderers'] = pd.to_numeric(df['tender/numberOfTenderers'], errors='coerce').fillna(0)

    # --- Duration ---
    df['duration_days'] = pd.to_numeric(df['tender/tenderPeriod/durationInDays'], errors='coerce').fillna(0)

    # ── Per-buyer average amount for relative comparison ──
    buyer_avg = df.groupby('buyer/name')['amount'].transform('mean')
    df['amount_vs_buyer_avg'] = df['amount'] / (buyer_avg + 1)

    # ── Log-amount for anomaly detection ──
    df['log_amount'] = np.log1p(df['amount'])

    return df


# ─────────────────────────────────────────────
# 3. RULE-BASED RED FLAGS
# ─────────────────────────────────────────────

def compute_rule_flags(df):
    df = df.copy()

    # Flag 1 – Single bidder (strongest cartel/bid-rigging signal)
    df['flag_single_bidder'] = (df['num_tenderers'] == 1).astype(int)

    # Flag 2 – Zero bidders (tender may be pre-awarded)
    df['flag_zero_bidders'] = (df['num_tenderers'] == 0).astype(int)

    # Flag 3 – Very short tender window (< 7 days = rushed, limits competition)
    df['flag_short_window'] = (
        (df['duration_days'] > 0) & (df['duration_days'] < 7)
    ).astype(int)

    # Flag 4 – Non-open procurement method (limited/restricted = less competition)
    open_methods = ['Open Tender']
    df['flag_non_open'] = (~df['tender/procurementMethod'].isin(open_methods)).astype(int)

    # Flag 5 – Unusually high-value contract (> 95th percentile for category)
    p95 = df.groupby('tenderclassification/description')['amount'].transform(lambda x: x.quantile(0.95))
    df['flag_high_value'] = (df['amount'] > p95).astype(int)

    # Flag 6 – Repeat buyer dominating a single category (concentration risk)
    buyer_cat = df.groupby(['buyer/name', 'tenderclassification/description']).size().reset_index(name='count')
    total_cat  = df.groupby('tenderclassification/description').size().reset_index(name='total')
    buyer_cat  = buyer_cat.merge(total_cat, on='tenderclassification/description')
    buyer_cat['concentration'] = buyer_cat['count'] / buyer_cat['total']
    # flag if a buyer handles > 70% of a category
    high_conc = buyer_cat[buyer_cat['concentration'] > 0.7][['buyer/name', 'tenderclassification/description']]
    high_conc['flag_buyer_concentration'] = 1
    df = df.merge(high_conc, on=['buyer/name', 'tenderclassification/description'], how='left')
    df['flag_buyer_concentration'] = df['flag_buyer_concentration'].fillna(0).astype(int)

    # Flag 7 – Round-number amounts (psychological bid-fixing signal)
    df['flag_round_amount'] = (df['amount'] % 100000 == 0).astype(int)

    return df


# ─────────────────────────────────────────────
# 4. STATISTICAL ANOMALY DETECTION (ML)
# ─────────────────────────────────────────────

def run_anomaly_detection(df):
    df = df.copy()

    features = ['log_amount', 'num_tenderers', 'duration_days', 'amount_vs_buyer_avg']
    X = df[features].fillna(0)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    iso = IsolationForest(
        n_estimators=200,
        contamination=0.1,   # expect ~10% anomalies
        random_state=42
    )
    iso.fit(X_scaled)

    # anomaly_score: higher = more anomalous (0 to 1)
    raw_scores = iso.decision_function(X_scaled)   # negative = more anomalous
    df['anomaly_score'] = 1 - (raw_scores - raw_scores.min()) / (raw_scores.max() - raw_scores.min())
    df['ml_anomaly_flag'] = (iso.predict(X_scaled) == -1).astype(int)

    return df


# ─────────────────────────────────────────────
# 5. COMPOSITE RISK SCORE (0 – 100)
# ─────────────────────────────────────────────

FLAG_WEIGHTS = {
    'flag_single_bidder':      25,   # strongest signal
    'flag_zero_bidders':       20,
    'flag_short_window':       15,
    'flag_non_open':           10,
    'flag_high_value':         10,
    'flag_buyer_concentration':10,
    'flag_round_amount':        5,
    'ml_anomaly_flag':         15,   # ML contribution
}

def compute_risk_score(df):
    df = df.copy()
    rule_score = sum(df[flag] * weight for flag, weight in FLAG_WEIGHTS.items())

    # Normalise rule_score to 0-85, add anomaly_score * 15
    max_rule = sum(FLAG_WEIGHTS.values())
    df['risk_score'] = ((rule_score / max_rule) * 85) + (df['anomaly_score'] * 15)
    df['risk_score']  = df['risk_score'].clip(0, 100).round(2)

    # Risk tier
    df['risk_tier'] = pd.cut(
        df['risk_score'],
        bins=[0, 30, 60, 100],
        labels=['🟢 Low', '🟡 Medium', '🔴 High'],
        include_lowest=True
    )

    return df


# ─────────────────────────────────────────────
# 6. HUMAN-READABLE EXPLANATION PER TENDER
# ─────────────────────────────────────────────

def explain_risk(row):
    reasons = []
    if row['flag_single_bidder']:
        reasons.append("Only 1 bidder submitted (possible bid-rigging)")
    if row['flag_zero_bidders']:
        reasons.append("No bidders recorded (may be pre-awarded)")
    if row['flag_short_window']:
        reasons.append(f"Very short tender window ({int(row['duration_days'])} days)")
    if row['flag_non_open']:
        reasons.append(f"Non-open procurement method: {row['tender/procurementMethod']}")
    if row['flag_high_value']:
        reasons.append("Contract value above 95th percentile for this category")
    if row['flag_buyer_concentration']:
        reasons.append("This buyer dominates >70% of contracts in this category")
    if row['flag_round_amount']:
        reasons.append("Contract amount is suspiciously round (possible fixed pricing)")
    if row['ml_anomaly_flag']:
        reasons.append("ML model flagged this as a statistical outlier")
    return "; ".join(reasons) if reasons else "No specific flags triggered"


# ─────────────────────────────────────────────
# 7. FULL PIPELINE
# ─────────────────────────────────────────────

def run_pipeline(filepath):
    print("\n🚀 STREAM Anti-Corruption Risk Scoring Engine")
    print("=" * 55)

    df = load_data(filepath)
    df = engineer_features(df)
    df = compute_rule_flags(df)
    df = run_anomaly_detection(df)
    df = compute_risk_score(df)
    df['risk_explanation'] = df.apply(explain_risk, axis=1)

    # ── Summary ──
    print("\n📊 RISK TIER SUMMARY:")
    print(df['risk_tier'].value_counts().to_string())

    high_risk = df[df['risk_tier'] == '🔴 High']
    print(f"\n🔴 HIGH-RISK TENDERS: {len(high_risk)}")
    print(f"   → Single-bidder contracts : {df['flag_single_bidder'].sum()}")
    print(f"   → Zero-bidder contracts   : {df['flag_zero_bidders'].sum()}")
    print(f"   → Non-open procurement    : {df['flag_non_open'].sum()}")
    print(f"   → ML anomaly flagged      : {df['ml_anomaly_flag'].sum()}")

    # ── Top 10 highest risk ──
    print("\n🔍 TOP 10 HIGHEST-RISK TENDERS:")
    top10 = df.nlargest(10, 'risk_score')[
        ['tender/id', 'buyer/name', 'tenderclassification/description',
         'amount', 'num_tenderers', 'risk_score', 'risk_tier', 'risk_explanation']
    ]
    pd.set_option('display.max_colwidth', 60)
    print(top10.to_string(index=False))

    # ── Export results ──
    output_cols = [
        'ocid', 'tender/id', 'tender/title', 'buyer/name',
        'tenderclassification/description', 'tender/procurementMethod',
        'amount', 'num_tenderers', 'duration_days',
        'flag_single_bidder', 'flag_zero_bidders', 'flag_short_window',
        'flag_non_open', 'flag_high_value', 'flag_buyer_concentration',
        'flag_round_amount', 'ml_anomaly_flag', 'anomaly_score',
        'risk_score', 'risk_tier', 'risk_explanation'
    ]
    result = df[output_cols].sort_values('risk_score', ascending=False)
    out_path = 'output_datasets/procurement_risk_scores.csv'
    result.to_csv(out_path, index=False)
    print(f"\n✅ Full results saved → {out_path}")

    return result


# ─────────────────────────────────────────────
# 8. ENTRY POINT — FULL END-TO-END PIPELINE
# ─────────────────────────────────────────────
#
# Running `python ml_model.py` will:
#   1) Rule-score ALL CSVs in datasets/
#   2) Train the supervised ML model (ml_pipeline)
#   3) Predict on ALL datasets and save to output_datasets/

DATASETS_DIR = "datasets"
OUTPUT_DIR   = "output_datasets"

if __name__ == "__main__":
    import sys
    import os

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ── Step 1: Rule-based risk scoring on ALL datasets ──
    csv_files = sorted([
        f for f in os.listdir(DATASETS_DIR)
        if f.endswith(".csv") and f.startswith("ocds_mapped_procurement_data")
    ])
    print(f"\n{'='*60}")
    print(f"  STREAM — Processing {len(csv_files)} Datasets")
    print(f"{'='*60}")

    all_risk_scores = []
    for i, fname in enumerate(csv_files, 1):
        fpath = os.path.join(DATASETS_DIR, fname)
        print(f"\n[{i}/{len(csv_files)}] Rule-scoring: {fname}")
        print("-" * 50)

        result = run_pipeline(fpath)

        # Save individual risk scores
        out_name = fname.replace(".csv", "_risk_scores.csv")
        out_path = os.path.join(OUTPUT_DIR, out_name)
        result.to_csv(out_path, index=False)
        print(f"   💾 Saved → {out_path}")

        all_risk_scores.append(result)

    # Combine all risk scores into one file for ML training
    combined = pd.concat(all_risk_scores, ignore_index=True)
    combined_path = os.path.join(OUTPUT_DIR, "procurement_risk_scores.csv")
    combined.to_csv(combined_path, index=False)
    print(f"\n📦 Combined risk scores ({len(combined)} rows) → {combined_path}")

    # ── Step 2 & 3: Train ML model + batch predict ──
    print(f"\n{'='*60}")
    print(f"  STREAM — ML Pipeline: Train + Predict")
    print(f"{'='*60}")

    from ml_pipeline import train_and_evaluate, batch_score_all_datasets
    train_and_evaluate()
    batch_score_all_datasets()

    print(f"\n{'='*60}")
    print(f"  ✅ ALL DONE — Risk scores + ML predictions in {OUTPUT_DIR}/")
    print(f"{'='*60}")

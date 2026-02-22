# 🔍 STREAM — Suspicious Transaction Risk Engine for Anomaly Monitoring

> **Anti-Corruption Procurement Fraud Detection Engine**
> AIA-26 Hackathon — Anna University

STREAM is a two-stage ML pipeline that detects suspicious procurement transactions in government tender data. It combines **rule-based red flag detection** with a **supervised machine learning model** to identify potentially corrupt or fraudulent contracts.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     python ml_model.py                          │
├─────────────────────┬───────────────────────────────────────────┤
│                     │                                           │
│   STAGE 1           │   STAGE 2                                 │
│   Rule-Based        │   Supervised ML                           │
│   Risk Scoring      │   Classification                         │
│   (ml_model.py)     │   (ml_pipeline.py)                       │
│                     │                                           │
│   ┌─────────────┐   │   ┌──────────────┐   ┌────────────────┐  │
│   │ Load all     │   │   │ Create binary │   │ Train Gradient │  │
│   │ datasets/    │   │   │ labels from  │   │ Boosting +     │  │
│   │ CSV files    │   │   │ risk scores  │   │ Random Forest  │  │
│   └──────┬──────┘   │   └──────┬───────┘   └───────┬────────┘  │
│          │          │          │                    │           │
│   ┌──────▼──────┐   │   ┌──────▼───────┐   ┌───────▼────────┐  │
│   │ Feature     │   │   │ Feature      │   │ Pick best      │  │
│   │ Engineering │   │   │ Engineering  │   │ model by       │  │
│   │ + Rule Flags│   │   │ (all data)   │   │ ROC-AUC        │  │
│   └──────┬──────┘   │   └──────┬───────┘   └───────┬────────┘  │
│          │          │          │                    │           │
│   ┌──────▼──────┐   │   ┌──────▼───────┐   ┌───────▼────────┐  │
│   │ Isolation   │   │   │ Train/Test   │   │ Batch predict  │  │
│   │ Forest      │   │   │ Split +      │   │ ALL datasets   │  │
│   │ Anomaly Det.│   │   │ SMOTE        │   │ → output_      │  │
│   └──────┬──────┘   │   └──────────────┘   │   datasets/    │  │
│          │          │                      └────────────────┘  │
│   ┌──────▼──────┐   │                                          │
│   │ Composite   │   │                                          │
│   │ Risk Score  │   │                                          │
│   │ (0-100)     │   │                                          │
│   └─────────────┘   │                                          │
│                     │                                          │
└─────────────────────┴──────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
STREAM/
├── datasets/                    ← Drop your procurement CSVs here
│   ├── ocds_..._2016_2017.csv
│   ├── ocds_..._2017_2018.csv
│   ├── ocds_..._2018_2019.csv
│   ├── ocds_..._2019_2020.csv
│   └── ocds_..._2020_2021.csv
│
├── output_datasets/             ← All generated outputs
│   ├── *_risk_scores.csv        ← Rule-based risk scores per dataset
│   ├── *_predictions.csv        ← ML predictions per dataset
│   └── procurement_risk_scores.csv  ← Combined risk scores (ML training labels)
│
├── trained_model/               ← Saved ML model artifacts
│   ├── model.joblib             ← Trained classifier
│   ├── scaler.joblib            ← Feature scaler
│   ├── label_encoders.joblib    ← Categorical encoders
│   ├── feature_cols.joblib      ← Feature column list
│   └── training_report.json     ← Metrics summary
│
├── ml_model.py                  ← 🚀 Main entry point (run this)
├── ml_pipeline.py               ← Supervised ML training + prediction
└── README.md
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install pandas numpy scikit-learn joblib
```

Optional (for better class balancing):

```bash
pip install imbalanced-learn
```

### 2. Add Your Data

Place procurement CSV files in the `datasets/` folder. They should follow the [OCDS (Open Contracting Data Standard)](https://www.open-contracting.org/data-standard/) schema with these required columns:

| Column                               | Description                |
| ------------------------------------ | -------------------------- |
| `ocid`                               | Open Contracting ID        |
| `tender/id`                          | Tender identifier          |
| `tender/title`                       | Tender title               |
| `buyer/name`                         | Procuring entity           |
| `tender/value/amount`                | Contract value             |
| `tender/numberOfTenderers`           | Number of bidders          |
| `tender/tenderPeriod/durationInDays` | Tender window              |
| `tender/procurementMethod`           | Open Tender / Limited etc. |
| `tenderclassification/description`   | Category                   |
| `tender/bidOpening/date`             | Bid opening date           |
| `tender/datePublished`               | Publication date           |

### 3. Run the Full Pipeline

```bash
python ml_model.py
```

This single command does everything:

1. **Rule-scores** every CSV in `datasets/`
2. **Trains** the ML model on the combined labeled data
3. **Predicts** on all datasets
4. **Saves** everything to `output_datasets/`

---

## 🔬 How It Works

### Stage 1: Rule-Based Risk Scoring (`ml_model.py`)

Seven expert-defined red flags are computed for each tender, each with a weight reflecting its severity:

| Flag                   | Weight | What It Detects                                          |
| ---------------------- | ------ | -------------------------------------------------------- |
| 🔴 Single Bidder       | 25     | Only 1 bidder — possible bid-rigging                     |
| 🔴 Zero Bidders        | 20     | No bidders recorded — possibly pre-awarded               |
| 🟡 Short Window        | 15     | Tender period < 7 days — rushed, limits competition      |
| 🟡 Non-Open Method     | 10     | Limited/restricted procurement — less transparency       |
| 🟡 High Value          | 10     | Amount > 95th percentile for category — inflated pricing |
| 🟡 Buyer Concentration | 10     | Buyer handles > 70% of category — monopoly risk          |
| 🟢 Round Amount        | 5      | Contract divisible by ₹100,000 — possible fixed pricing  |
| 🤖 ML Anomaly          | 15     | Isolation Forest statistical outlier                     |

These flags produce a **composite risk score (0–100)** and a **risk tier**:

- 🟢 **Low** (0–30): No major flags
- 🟡 **Medium** (30–60): Multiple flags triggered
- 🔴 **High** (60–100): Strong indicators of corruption

### Stage 2: Supervised ML Classification (`ml_pipeline.py`)

The rule-based risk scores are used as **training labels** (`is_suspicious = 1` if `risk_score ≥ 20`) to train a supervised classifier:

1. **Feature Engineering** — 9 features: amount, log amount, tenderer count, duration, round amount flag, buyer-relative amount, procurement method, category, buyer (encoded)
2. **Class Balancing** — SMOTE oversampling (or `class_weight='balanced'` fallback)
3. **Two Models Trained** — GradientBoosting and RandomForest
4. **Best Model Selected** — By ROC-AUC score
5. **Batch Prediction** — All datasets scored with `predicted_suspicious` (0/1) and `suspicion_probability`

### Why Two Stages?

|            | Rule-Based (Stage 1)                  | ML Model (Stage 2)                                 |
| ---------- | ------------------------------------- | -------------------------------------------------- |
| **Pros**   | Interpretable, domain-expert designed | Generalizes to new data, captures complex patterns |
| **Cons**   | Fixed rules, can't learn new patterns | Needs labeled data to train                        |
| **Output** | `risk_score` (0–100) + explanations   | `predicted_suspicious` (0/1) + probability         |

The ML model learns from the rule-based labels, then can **score new procurement data instantly** without re-running the full rule engine.

---

## 📊 Model Performance (29,542 training records)

| Metric                     | Score  |
| -------------------------- | ------ |
| **ROC-AUC**                | 0.9939 |
| **Accuracy**               | 97%    |
| **Precision (Suspicious)** | 95%    |
| **Recall (Suspicious)**    | 90%    |
| **F1 (Suspicious)**        | 93%    |

### Top Features by Importance

| Rank | Feature                | Importance |
| ---- | ---------------------- | ---------- |
| 1    | `num_tenderers`        | 46.2%      |
| 2    | `amount_vs_buyer_avg`  | 17.4%      |
| 3    | `duration_days`        | 9.9%       |
| 4    | `log_amount`           | 7.3%       |
| 5    | `tenderclassification` | 7.3%       |

---

## 📋 Output Format

Each prediction CSV contains:

| Column                  | Description                       |
| ----------------------- | --------------------------------- |
| `ocid`                  | Contract ID                       |
| `tender/id`             | Tender ID                         |
| `tender/title`          | Description                       |
| `buyer/name`            | Procuring entity                  |
| `amount`                | Contract value                    |
| `num_tenderers`         | Number of bidders                 |
| `predicted_suspicious`  | **1** = suspicious, **0** = clean |
| `suspicion_probability` | Model confidence (0.0 – 1.0)      |
| `predicted_risk_tier`   | 🟢 Low / 🟡 Medium / 🔴 High      |

---

## 🔄 Adding New Data

1. Drop new procurement CSV files into `datasets/`
2. Run `python ml_model.py`
3. Find predictions in `output_datasets/`

To score a single file without retraining:

```bash
python ml_pipeline.py predict path/to/new_data.csv output.csv
```

---

## 🛠️ Tech Stack

- **Python 3.8+**
- **pandas / numpy** — Data processing
- **scikit-learn** — ML models (GradientBoosting, RandomForest, IsolationForest)
- **imbalanced-learn** _(optional)_ — SMOTE oversampling
- **joblib** — Model persistence

---

## 📜 License

Built for the AIA-26 Hackathon at Anna University.

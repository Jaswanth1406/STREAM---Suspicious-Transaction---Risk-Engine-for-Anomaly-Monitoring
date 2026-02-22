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
├── backend/                         ← Python ML + API
│   ├── datasets/                    ← Drop procurement CSVs here
│   │   ├── ocds_..._2016_2017.csv
│   │   ├── ocds_..._2017_2018.csv
│   │   └── ...
│   ├── output_datasets/             ← Generated outputs
│   │   ├── *_risk_scores.csv
│   │   ├── *_predictions.csv
│   │   └── procurement_risk_scores.csv
│   ├── trained_model/               ← Saved ML model artifacts
│   ├── ml_model.py                  ← 🚀 Main entry point
│   ├── ml_pipeline.py               ← ML training + prediction
│   ├── app.py                       ← FastAPI REST API
│   ├── create_auth_tables.py        ← DB migration script
│   └── .env                         ← Database + auth secrets
│
├── frontend/                        ← Next.js + Better Auth
│   ├── app/
│   │   ├── api/auth/[...all]/       ← Auth API route handler
│   │   ├── sign-in/                 ← Sign in page
│   │   ├── sign-up/                 ← Sign up page
│   │   └── dashboard/               ← Protected dashboard
│   ├── lib/
│   │   ├── auth.ts                  ← Better Auth server config
│   │   └── auth-client.ts           ← Better Auth React client
│   └── .env.local                   ← Frontend env vars
│
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start

### 1. Backend Setup

```bash
cd backend
pip install pandas numpy scikit-learn joblib fastapi uvicorn python-multipart psycopg2-binary python-dotenv
```

**Train the model + score all datasets:**

```bash
python ml_model.py
```

**Start the API server:**

```bash
uvicorn app:app --reload
# API docs → http://localhost:8000/docs
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
# App → http://localhost:3000
```

### 3. Add Your Data

Place procurement CSV files in `backend/datasets/`. They should follow the [OCDS](https://www.open-contracting.org/data-standard/) schema with these required columns:

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

---

## 🌐 API Endpoints

| Method | Endpoint              | Description                       |
| ------ | --------------------- | --------------------------------- |
| `GET`  | `/`                   | Health check                      |
| `GET`  | `/model/info`         | Model metrics (ROC-AUC, accuracy) |
| `POST` | `/predict`            | Score a single tender (JSON)      |
| `POST` | `/predict/batch`      | Upload CSV → get predictions CSV  |
| `POST` | `/predict/batch/json` | Upload CSV → get JSON summary     |

---

## 🔬 How It Works

### Stage 1: Rule-Based Risk Scoring (`ml_model.py`)

Seven expert-defined red flags are computed for each tender:

| Flag                   | Weight | What It Detects                             |
| ---------------------- | ------ | ------------------------------------------- |
| 🔴 Single Bidder       | 25     | Only 1 bidder — possible bid-rigging        |
| 🔴 Zero Bidders        | 20     | No bidders recorded — possibly pre-awarded  |
| 🟡 Short Window        | 15     | Tender period < 7 days — rushed             |
| 🟡 Non-Open Method     | 10     | Limited procurement — less transparency     |
| 🟡 High Value          | 10     | Amount > 95th percentile — inflated pricing |
| 🟡 Buyer Concentration | 10     | Buyer handles > 70% of category             |
| 🟢 Round Amount        | 5      | Divisible by ₹100,000 — fixed pricing       |
| 🤖 ML Anomaly          | 15     | Isolation Forest outlier                    |

Risk tiers: 🟢 Low (0–30) · 🟡 Medium (30–60) · 🔴 High (60–100)

### Stage 2: Supervised ML Classification (`ml_pipeline.py`)

The rule-based scores become **training labels** (`is_suspicious = 1` if `risk_score ≥ 20`):

1. **9 features** engineered from raw data
2. **GradientBoosting** + **RandomForest** trained
3. **Best model selected** by ROC-AUC
4. **Batch prediction** on all datasets

---

## 📊 Model Performance (29,542 records)

| Metric        | Score  |
| ------------- | ------ |
| **ROC-AUC**   | 0.9939 |
| **Accuracy**  | 97%    |
| **Precision** | 95%    |
| **Recall**    | 90%    |
| **F1**        | 93%    |

Top features: `num_tenderers` (46%), `amount_vs_buyer_avg` (17%), `duration_days` (10%)

---

## 🔐 Authentication

The frontend uses [Better Auth](https://better-auth.com) with:

- **Email/Password** sign-up and sign-in
- **Google OAuth** social sign-in
- **Neon PostgreSQL** session storage

---

## 🛠️ Tech Stack

| Layer           | Technologies                                                     |
| --------------- | ---------------------------------------------------------------- |
| **ML Pipeline** | Python, pandas, scikit-learn, Isolation Forest, GradientBoosting |
| **API**         | FastAPI, Uvicorn                                                 |
| **Frontend**    | Next.js 15, TypeScript, Tailwind CSS                             |
| **Auth**        | Better Auth (email/password + Google OAuth)                      |
| **Database**    | Neon PostgreSQL                                                  |

---

## 📜 License

Built for the AIA-26 Hackathon at Anna University.

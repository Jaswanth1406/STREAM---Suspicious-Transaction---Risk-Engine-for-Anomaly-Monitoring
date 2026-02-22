# 🔍 STREAM — Suspicious Transaction Risk Engine for Anomaly Monitoring

> **Anti-Corruption Procurement Fraud Detection Engine**  
> AIA-26 Hackathon — Anna University

STREAM is a two-stage ML pipeline that detects suspicious procurement transactions in government tender data. It combines **rule-based red flag detection** with a **supervised machine learning model** to identify potentially corrupt or fraudulent contracts, served through a **FastAPI backend** and a **Next.js frontend** with Better Auth authentication.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          STREAM Pipeline                             │
├──────────────────────┬───────────────────────────────────────────────┤
│                      │                                               │
│   STAGE 1            │   STAGE 2                                     │
│   Rule-Based         │   Supervised ML                               │
│   Risk Scoring       │   Classification                             │
│   (ml_model.py)      │   (ml_pipeline.py)                           │
│                      │                                               │
│   ┌──────────────┐   │   ┌──────────────┐   ┌─────────────────┐    │
│   │ Load all     │   │   │ Create binary │   │ Train Gradient  │    │
│   │ datasets/    │   │   │ labels from  │   │ Boosting +      │    │
│   │ CSV files    │   │   │ risk scores  │   │ Random Forest   │    │
│   └──────┬───────┘   │   └──────┬───────┘   └────────┬────────┘    │
│          │           │          │                     │             │
│   ┌──────▼───────┐   │   ┌──────▼───────┐   ┌────────▼────────┐    │
│   │ Feature      │   │   │ Feature      │   │ Pick best       │    │
│   │ Engineering  │   │   │ Engineering  │   │ model by        │    │
│   │ + Rule Flags │   │   │ (all data)   │   │ ROC-AUC         │    │
│   └──────┬───────┘   │   └──────┬───────┘   └────────┬────────┘    │
│          │           │          │                     │             │
│   ┌──────▼───────┐   │   ┌──────▼───────┐   ┌────────▼────────┐    │
│   │ Isolation    │   │   │ Train/Test   │   │ Batch predict   │    │
│   │ Forest       │   │   │ Split +      │   │ ALL datasets    │    │
│   │ Anomaly Det. │   │   │ SMOTE        │   │ → output_       │    │
│   └──────┬───────┘   │   └──────────────┘   │   datasets/     │    │
│          │           │                      └─────────────────┘    │
│   ┌──────▼───────┐   │                                             │
│   │ Composite    │   │                                             │
│   │ Risk Score   │   │                                             │
│   │ (0-100)      │   │                                             │
│   └──────────────┘   │                                             │
│                      │                                             │
└──────────────────────┴─────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌──────────────────┐          ┌──────────────────┐
│   FastAPI REST   │          │   Next.js        │
│   API (app.py)   │◄────────│   Frontend       │
│   Port 8000      │          │   Port 3000      │
└──────────────────┘          └──────────────────┘
                              │  Better Auth     │
                              │  (Google + Email) │
                              └──────────────────┘
```

---

## 📁 Project Structure

```
STREAM/
├── backend/                           ← Python ML + API Server
│   ├── datasets/                      ← Drop procurement CSVs here
│   │   ├── ocds_..._2016_2017.csv
│   │   ├── ocds_..._2017_2018.csv
│   │   ├── ocds_..._2018_2019.csv
│   │   ├── ocds_..._2019_2020.csv
│   │   └── ocds_..._2020_2021.csv
│   ├── output_datasets/               ← Generated outputs
│   │   ├── *_risk_scores.csv
│   │   ├── *_predictions.csv
│   │   └── procurement_risk_scores.csv
│   ├── trained_model/                 ← Saved ML model artifacts
│   │   ├── model.joblib
│   │   ├── scaler.joblib
│   │   ├── label_encoders.joblib
│   │   ├── feature_cols.joblib
│   │   └── training_report.json
│   ├── ml_model.py                    ← 🚀 Main ML entry point
│   ├── ml_pipeline.py                 ← ML training + prediction
│   ├── app.py                         ← FastAPI REST API
│   ├── create_auth_tables.py          ← DB migration script
│   └── .env                           ← Backend secrets
│
├── frontend/                          ← Next.js + Better Auth
│   ├── app/
│   │   ├── api/auth/[...all]/route.ts ← Auth API handler
│   │   ├── sign-in/page.tsx           ← Sign in page
│   │   ├── sign-up/page.tsx           ← Sign up page
│   │   └── dashboard/page.tsx         ← Protected dashboard
│   ├── lib/
│   │   ├── auth.ts                    ← Better Auth server config
│   │   └── auth-client.ts             ← Better Auth React client
│   └── .env.local                     ← Frontend secrets
│
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** with pip
- **Node.js 18+** with npm
- **Neon PostgreSQL** database (or any PostgreSQL)

### 1. Clone & Setup Backend

```bash
cd backend

# Install Python dependencies
pip install pandas numpy scikit-learn joblib fastapi uvicorn python-multipart psycopg2-binary python-dotenv imbalanced-learn

# Configure environment
cp .env.example .env   # Then fill in your DATABASE_URL

# Create auth tables in Neon
python create_auth_tables.py

# Train model + score all datasets
python ml_model.py

# Start API server
uvicorn app:app --reload
# → http://localhost:8000/docs
```

### 2. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local   # Then fill in your secrets

# Start dev server
npm run dev
# → http://localhost:3000
```

### 3. Environment Variables

**`backend/.env`**

```env
DATABASE_URL=postgresql://user:pass@host/dbname?sslmode=require
```

**`frontend/.env.local`**

```env
DATABASE_URL=postgresql://user:pass@host/dbname?sslmode=require
BETTER_AUTH_SECRET=your-32-char-secret
BETTER_AUTH_URL=http://localhost:3000
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🔐 Authentication

STREAM uses [Better Auth](https://better-auth.com) with:

| Method             | Description                     |
| ------------------ | ------------------------------- |
| **Email/Password** | Traditional sign-up and sign-in |
| **Google OAuth**   | One-click sign-in via Google    |

**Database tables:** `user`, `session`, `account`, `verification` — all stored in Neon PostgreSQL.

**Google OAuth Setup:**

1. Go to [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials)
2. Create an OAuth 2.0 Client ID
3. Set **Authorized JavaScript origins:** `http://localhost:3000`
4. Set **Authorized redirect URIs:** `http://localhost:3000/api/auth/callback/google`
5. Copy Client ID and Secret to `frontend/.env.local`

---

## 🌐 API Endpoints

| Method | Endpoint              | Description                                 |
| ------ | --------------------- | ------------------------------------------- |
| `GET`  | `/`                   | Health check                                |
| `GET`  | `/model/info`         | Model metrics (ROC-AUC, accuracy, features) |
| `POST` | `/predict`            | Score a single tender (JSON body)           |
| `POST` | `/predict/batch`      | Upload CSV → download predictions CSV       |
| `POST` | `/predict/batch/json` | Upload CSV → get JSON summary               |

**Example — score a single tender:**

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "tender/value/amount": 5000000,
    "tender/numberOfTenderers": 1,
    "tender/tenderPeriod/durationInDays": 3,
    "tender/procurementMethod": "Limited",
    "tenderclassification/description": "Civil Works",
    "buyer/name": "Public Works Department"
  }'
```

---

## 🔬 How It Works

### Stage 1: Rule-Based Risk Scoring (`ml_model.py`)

Seven expert-defined red flags are computed for each tender:

| Flag                   | Weight | What It Detects                                          |
| ---------------------- | ------ | -------------------------------------------------------- |
| 🔴 Single Bidder       | 25     | Only 1 bidder — possible bid-rigging                     |
| 🔴 Zero Bidders        | 20     | No bidders recorded — possibly pre-awarded               |
| 🟡 Short Window        | 15     | Tender period < 7 days — rushed, limits competition      |
| 🟡 Non-Open Method     | 10     | Limited/restricted procurement — less transparency       |
| 🟡 High Value          | 10     | Amount > 95th percentile for category — inflated pricing |
| 🟡 Buyer Concentration | 10     | Buyer handles > 70% of category — monopoly risk          |
| 🟢 Round Amount        | 5      | Divisible by ₹100,000 — possible fixed pricing           |
| 🤖 ML Anomaly          | 15     | Isolation Forest statistical outlier                     |

**Risk Tiers:** 🟢 Low (0–30) · 🟡 Medium (30–60) · 🔴 High (60–100)

### Stage 2: Supervised ML Classification (`ml_pipeline.py`)

Rule-based scores become **training labels** (`is_suspicious = 1` if `risk_score ≥ 20`):

1. **Feature Engineering** — 9 features from raw data
2. **Class Balancing** — SMOTE oversampling
3. **Two Models Trained** — GradientBoosting + RandomForest
4. **Best Model Selected** — By ROC-AUC score
5. **Batch Prediction** — All datasets scored and saved

### Why Two Stages?

|            | Rule-Based (Stage 1)                  | ML Model (Stage 2)                         |
| ---------- | ------------------------------------- | ------------------------------------------ |
| **Pros**   | Interpretable, domain-expert designed | Generalizes, captures complex patterns     |
| **Cons**   | Fixed rules, can't learn              | Needs labeled data to train                |
| **Output** | `risk_score` (0–100) + explanations   | `predicted_suspicious` (0/1) + probability |

---

## 📊 Model Performance (29,542 records)

| Metric                     | Score  |
| -------------------------- | ------ |
| **ROC-AUC**                | 0.9939 |
| **Accuracy**               | 97%    |
| **Precision (Suspicious)** | 95%    |
| **Recall (Suspicious)**    | 90%    |
| **F1 (Suspicious)**        | 93%    |

**Top Features:** `num_tenderers` (46.2%) · `amount_vs_buyer_avg` (17.4%) · `duration_days` (9.9%) · `log_amount` (7.3%)

---

## 📋 Output Format

Each prediction CSV in `output_datasets/` contains:

| Column                  | Description                       |
| ----------------------- | --------------------------------- |
| `ocid`                  | Contract ID                       |
| `tender/id`             | Tender ID                         |
| `tender/title`          | Description                       |
| `buyer/name`            | Procuring entity                  |
| `amount`                | Contract value                    |
| `num_tenderers`         | Number of bidders                 |
| `predicted_suspicious`  | **1** = suspicious, **0** = clean |
| `suspicion_probability` | Model confidence (0.0–1.0)        |
| `predicted_risk_tier`   | 🟢 Low / 🟡 Medium / 🔴 High      |

---

## 🔄 Adding New Data

1. Drop new OCDS-format CSV files into `backend/datasets/`
2. Run `python ml_model.py` from `backend/`
3. Find predictions in `backend/output_datasets/`

---

## 🛠️ Tech Stack

| Layer              | Technologies                                                     |
| ------------------ | ---------------------------------------------------------------- |
| **ML Pipeline**    | Python, pandas, scikit-learn, Isolation Forest, GradientBoosting |
| **Backend API**    | FastAPI, Uvicorn                                                 |
| **Frontend**       | Next.js 15, TypeScript, Tailwind CSS                             |
| **Authentication** | Better Auth (Email/Password + Google OAuth)                      |
| **Database**       | Neon PostgreSQL                                                  |

---

## 📜 License

Built for the AIA-26 Hackathon at Anna University.

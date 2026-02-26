# 🔍 STREAM — Suspicious Transaction Risk Engine for Anomaly Monitoring

> **AI-Powered Anti-Corruption Procurement Intelligence Platform**  

STREAM is a full-stack procurement fraud detection platform that analyzes Indian public contracting data to surface bid-rigging, shell company networks, cartel behavior, and politically connected vendors. It combines a **two-stage ML pipeline** (rule-based risk scoring + supervised classification) with an **interactive analytics dashboard**, network graph visualization, AI-powered chatbot, and vendor profiling — served through a **FastAPI backend** and a **Next.js frontend** with Better Auth authentication.

All flags are **probabilistic risk indicators** — STREAM emphasizes due process, human-in-the-loop review, and false positive control.

---

## ✨ Features at a Glance

| Category | Highlights |
|---|---|
| **ML Pipeline** | 7 rule-based red flags, Isolation Forest anomaly detection, GradientBoosting classification (97% accuracy, 0.994 ROC-AUC) |
| **Dashboard** | Real-time KPIs, fraud alert feed with search/filter/pagination, risk distribution charts |
| **Network Graph** | Interactive force-directed canvas graph with zoom, pan, edge-type filtering, node detail panels |
| **Bid Analysis** | Sortable/filterable tender table, risk-by-category bar chart, risk distribution donut chart |
| **Timeline** | Chronological event feed — electoral bonds, flags, contracts, ML predictions |
| **Vendor Profiles** | Deep-dive per-vendor pages with risk sub-scores, connections, tender history, CIN lookup |
| **AI Chatbot** | Floating widget + full-page assistant with preset fraud analysis queries |
| **Auth** | Email/password + Google OAuth via Better Auth, session-protected routes |
| **Responsive** | 3-column desktop layout, bottom nav + sidebar overlay on mobile |

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
│   │   ├── companies.csv              ← Vendor/company master data
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
│   │   ├── page.tsx                   ← Animated landing page
│   │   ├── layout.tsx                 ← Root layout (Syne + Space Mono fonts)
│   │   ├── globals.css                ← Theme variables, glassmorphism, orbs
│   │   ├── login/page.tsx             ← Sign-in (email + Google OAuth)
│   │   ├── signup/page.tsx            ← Sign-up (email + Google OAuth)
│   │   ├── api/auth/[...all]/         ← Better Auth API handler
│   │   └── dashboard/
│   │       ├── layout.tsx             ← 3-column dashboard shell
│   │       ├── page.tsx               ← Fraud alerts feed
│   │       ├── network/page.tsx       ← Network graph visualization
│   │       ├── bids/page.tsx          ← Bid analysis & charts
│   │       ├── timeline/page.tsx      ← Activity timeline
│   │       ├── chat/page.tsx          ← Full-page AI assistant
│   │       └── vendor/[cin]/          ← Vendor profile (dynamic route)
│   ├── components/
│   │   ├── Header.tsx                 ← KPI strip + live monitoring badge
│   │   ├── Sidebar.tsx                ← Detection module filters + data sources
│   │   ├── RightPanel.tsx             ← Vendor search + quick profile
│   │   ├── AlertCard.tsx              ← Fraud alert card with flags
│   │   ├── ChatBot.tsx                ← Floating chat widget
│   │   └── MobileNav.tsx              ← Bottom tab bar for mobile
│   ├── lib/
│   │   ├── api.ts                     ← API client (all backend calls)
│   │   ├── auth.ts                    ← Better Auth server config
│   │   ├── auth-client.ts             ← Better Auth React client
│   │   ├── store.ts                   ← Zustand global state
│   │   └── types.ts                   ← TypeScript interfaces
│   ├── middleware.ts                   ← Route protection
│   └── .env.local                     ← Frontend secrets
│
└── README.md
```

---

## 🖥️ Frontend Pages & Features

### Landing Page (`/`)

- **Animated hero** with parallax scrolling, floating particle effects, and concentric rotating rings
- **Live stats bar** — Active Flags, At-Risk Value (₹Cr), Vendors Tracked, False Positive Control rate
- **4 Detection Module cards** — Bid Rigging, Shell Company Networks, Political Connection Flags, Cartel Behavior
- **Dashboard preview** section with animated SVG mockups (dashboard, network graph, bid chart, timeline)
- **How It Works** — 3-step visual architecture: Public Ledger Analysis → Network Intelligence → Behavioral Anomaly Detection
- **Platform capabilities** grid (6 capabilities)
- **Data sources** section — OCDS Procurement Data, MCA Company Filings, Electoral Bond Disclosures, GeM Portal Records, Income Tax PAN Links
- **Due Process** section emphasizing probabilistic scoring and human-in-the-loop review
- **CTA** with sign-up / sign-in buttons

### Login & Sign Up (`/login`, `/signup`)

- Email/password forms with validation (min 8 chars, password confirmation)
- Google OAuth one-click sign-in/sign-up
- Animated hexagonal STREAM logo with rotating border
- Error handling with visual alerts
- Auto-redirect to `/dashboard` on success

### Dashboard Layout (`/dashboard/*`)

- **3-column responsive layout** — Sidebar (260px) · Center Content · Right Panel (320px)
- **Header** — STREAM logo, live KPI strip (Active Flags, At Risk Value, Vendors Tracked, Precision Rate), "LIVE MONITORING" badge, notification bell, chat toggle, user info, sign-out
- **Mobile** — Bottom tab bar (Alerts, Network, Bids, Timeline, Chat), overlay sidebar

### Fraud Alerts (`/dashboard`)

- **4 KPI cards** — Active Flags, At Risk Value, Vendors Tracked, False Positive Control
- **Due Process Notice** banner
- **Search bar** with keyboard shortcut (ESC to clear)
- **Alert cards** showing:
  - Color-coded risk score (0–100) and confidence percentage
  - Alert type badge and procurement category
  - Tender title with human-readable risk explanation
  - Metadata — amount, buyer, number of bidders, tender window duration
  - Active flags list
  - Evidence strength progress bar (0–100)
- **Alert type filtering** — Bid Rigging, Shell Networks, Political Links, High Value, Short Window
- **Risk level filtering** — High (60–100), Medium (30–59), Low (0–29)
- **Pagination** controls

### Network Graph (`/dashboard/network`)

- **Canvas-based interactive** force-directed graph with custom physics simulation (80 iterations)
- **Zoom controls** — In, out, reset
- **Edge-type filtering** — Dynamic filter buttons generated from data (co_bidder, electoral_bond, shared_address, shared_director, etc.)
- **Node hover** — Tooltip with risk score, glow highlight effect
- **Node selection** — Side panel showing: label, type, risk score, risk tier, connection count
- **Legend panel** — Node types with color coding, edge types with line styles
- **Pan & zoom** via mouse drag and scroll

### Bid Analysis (`/dashboard/bids`)

- **4 summary stat cards** — Total Tenders, Total Value (₹Cr), Avg Risk Score, High Risk count
- **Bar chart** — Average risk score by tender category (top 8 categories, color-coded by risk level)
- **Donut chart** — Risk distribution breakdown (High / Medium / Low)
- **Sortable table** with columns: Tender (title + ID), Buyer, Amount, Bidders, Duration, Risk Score, ML Prediction (SUS/CLEAN with probability %), Flags
- **Risk tier filter** buttons — High, Medium, Low
- **Sort options** — Risk score, Amount, Number of bidders
- **Pagination** controls

### Timeline (`/dashboard/timeline`)

- **Vertical timeline** with connecting line and staggered fade-in animations
- **Event type filters** — All, Electoral Bonds, Flags, Contracts, ML Predictions
- **Color-coded event cards** by type:
  - 🏦 `bond_purchased` / `electoral_bond` — Blue
  - 🚩 `flag_raised` — Red
  - 📄 `contract_awarded` — Yellow
  - 🤖 `prediction_made` — Green
- Each card shows: risk tier badge, risk score, title, subtitle, amount (₹Cr), entity name, party name

### AI Chat Assistant (`/dashboard/chat`)

- **Full-page chat interface** branded "STREAM Intelligence Assistant"
- **Active status indicator** — "Active · Analyzing 47 flags"
- **4 preset query buttons** — Top risky vendors, Bid rigging patterns, Shell company links, Electoral bond analysis
- **Rich responses** with Markdown-formatted analysis, vendor risk rankings, and pattern summaries
- **Typing indicator** with animated dots
- **Message bubbles** with user/assistant avatars and timestamps

### Floating Chat Widget (all dashboard pages)

- **Minimizable/closeable** bottom-right widget (380px wide)
- **Shared state** with full-page chat via Zustand store
- **Toggleable** from the header chat icon

### Vendor Profile (`/dashboard/vendor/[cin]`)

- **Dynamic route** by CIN (Corporate Identification Number)
- **Animated SVG risk ring** (0–100 score with color gradient)
- **Company header** — Name, CIN, registration date, status, industry
- **4 stat boxes** — Total Tenders, Total Value (₹Cr), Risk Tier, Flags Triggered
- **Risk sub-scores** with animated progress bars — Bid Pattern, Shell Risk, Political, Financials
- **Connections panel** — Lists linked entities with relationship type (political_bond, co_bidder, shared_address, shared_director), detail, and risk level
- **Recent tenders** panel — Tender list with title, ID, amount, risk score, date
- **Action buttons** — Flag for Review, View on MCA, Export Report

### Sidebar

- **Detection Modules** filter — Bid Rigging, Shell Networks, Political Links, High Value, Short Window (with live counts)
- **Risk Level** filter — High, Medium, Low (with counts and color dots)
- **Summary stats** — Total Tenders Analyzed, Bond Value (₹Cr), Parties Linked
- **Data Sources** status — Procurement (OCDS), Company Registry, Electoral Bonds, ML Pipeline — all with live indicators
- **Version footer** — STREAM v2.4, ML Pipeline v3.2

### Right Panel

- **Vendor search** — Debounced typeahead (300ms delay, min 2 chars)
- **Quick vendor profile** — Risk score ring, basic stats, risk sub-scores
- **Vendor connections** — Linked entities with type and risk
- **Action buttons** — Escalate, Annotate

---

## 🌐 API Endpoints

### Core ML Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check — service status, model loaded state |
| `GET` | `/model/info` | Trained model metadata (algorithm, ROC-AUC, accuracy, F1, features, timestamp) |
| `POST` | `/predict` | Single tender prediction — returns risk tier + suspicion probability |
| `POST` | `/predict/batch` | Upload CSV → download predictions CSV |
| `POST` | `/predict/batch/json` | Upload CSV → JSON summary (total, suspicious count/%, risk distribution) |

### Dashboard Data Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/dashboard/kpis` | KPI summary — active flags, at-risk value, vendors tracked, precision rate, risk breakdowns, bond value, political parties |
| `GET` | `/alerts` | Paginated fraud alerts with filtering (`alert_type`, `risk_tier`, `search`, `sort`) |
| `GET` | `/vendor/{id}` | Full vendor risk profile with sub-scores, connections, and recent tenders |
| `GET` | `/vendor/search/{query}` | Vendor search by name or CIN |
| `GET` | `/network/graph` | Network graph data — nodes + edges with types, colors, risk scores (`min_risk_score`, `limit_nodes` params) |
| `GET` | `/bid-analysis` | Paginated bid analysis with sorting/filtering |
| `GET` | `/bid-analysis/summary` | Bid summary stats — totals, risk distribution, top categories, top buyers, fiscal year breakdown |
| `GET` | `/activity/recent` | Activity timeline events with type filtering |
| `GET` | `/stats/risk-distribution` | Risk score histogram — bins, mean, median, std, p95, p99 |
| `GET` | `/stats/top-risk-buyers` | Top risk buyers with flag details |
| `GET` | `/stats/bond-summary` | Electoral bond summary per party |

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

## 🔐 Authentication

STREAM uses [Better Auth](https://better-auth.com) with:

| Method | Description |
|---|---|
| **Email/Password** | Traditional sign-up and sign-in with validation |
| **Google OAuth** | One-click sign-in via Google |

**Database tables** (Neon PostgreSQL):

| Table | Purpose |
|---|---|
| `user` | id, name, email, emailVerified, image, timestamps |
| `session` | id, expiresAt, token, ipAddress, userAgent, userId |
| `account` | id, accountId, providerId, userId, tokens, scope, password |
| `verification` | id, identifier, value, expiresAt |

**Route protection:** Middleware checks `better-auth.session_token` cookie on `/dashboard/*` routes.

**Google OAuth Setup:**

1. Go to [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials)
2. Create an OAuth 2.0 Client ID
3. Set **Authorized JavaScript origins:** `http://localhost:3000`
4. Set **Authorized redirect URIs:** `http://localhost:3000/api/auth/callback/google`
5. Copy Client ID and Secret to `frontend/.env.local`

---

## 🔬 How It Works

### Stage 1: Rule-Based Risk Scoring (`ml_model.py`)

Seven expert-defined red flags are computed for each tender:

| Flag | Weight | What It Detects |
|---|---|---|
| 🔴 Single Bidder | 25 | Only 1 bidder — possible bid-rigging |
| 🔴 Zero Bidders | 20 | No bidders recorded — possibly pre-awarded |
| 🟡 Short Window | 15 | Tender period < 7 days — rushed, limits competition |
| 🟡 Non-Open Method | 10 | Limited/restricted procurement — less transparency |
| 🟡 High Value | 10 | Amount > 95th percentile for category — inflated pricing |
| 🟡 Buyer Concentration | 10 | Buyer handles > 70% of category — monopoly risk |
| 🟢 Round Amount | 5 | Divisible by ₹100,000 — possible fixed pricing |
| 🤖 ML Anomaly | 15 | Isolation Forest statistical outlier |

**Composite Risk Score:** 0–100 scale (85% weighted rules + 15% Isolation Forest anomaly score)

**Risk Tiers:** 🟢 Low (0–30) · 🟡 Medium (30–60) · 🔴 High (60–100)

**Human-readable explanations** are auto-generated per tender describing which flags triggered and why.

### Stage 2: Supervised ML Classification (`ml_pipeline.py`)

Rule-based scores become **training labels** (`is_suspicious = 1` if `risk_score ≥ 20`):

1. **Feature Engineering** — 9 features from raw OCDS data
2. **Class Balancing** — SMOTE oversampling for minority class
3. **Two Models Trained** — GradientBoosting + RandomForest
4. **Best Model Selected** — By ROC-AUC score
5. **5-Fold Cross-Validation** — On selected model
6. **Batch Prediction** — All datasets scored and saved

### 9 ML Features

| Feature | Description |
|---|---|
| `amount` | Contract value |
| `num_tenderers` | Number of bidders |
| `duration_days` | Tender window duration |
| `log_amount` | Log-transformed contract amount |
| `is_round_amount` | Binary — divisible by ₹100K |
| `amount_vs_buyer_avg` | Amount relative to buyer's historical average |
| `tender/procurementMethod_enc` | Label-encoded procurement method |
| `tenderclassification/description_enc` | Label-encoded tender category |
| `buyer/name_enc` | Label-encoded buyer |

### Why Two Stages?

| | Rule-Based (Stage 1) | ML Model (Stage 2) |
|---|---|---|
| **Pros** | Interpretable, domain-expert designed | Generalizes, captures complex patterns |
| **Cons** | Fixed rules, can't learn | Needs labeled data to train |
| **Output** | `risk_score` (0–100) + explanations | `predicted_suspicious` (0/1) + probability |

---

## 📊 Model Performance (29,542 records)

| Metric | Score |
|---|---|
| **Algorithm** | GradientBoosting (selected over RandomForest) |
| **ROC-AUC** | 0.9939 |
| **Accuracy** | 96.85% |
| **Precision (Suspicious)** | 95% |
| **Recall (Suspicious)** | 90% |
| **F1 (Suspicious)** | 92.87% |

**Top Features by Importance:** `num_tenderers` (46.2%) · `amount_vs_buyer_avg` (17.4%) · `duration_days` (9.9%) · `log_amount` (7.3%)

---

## 📋 Output Format

Each prediction CSV in `output_datasets/` contains:

| Column | Description |
|---|---|
| `ocid` | Contract ID |
| `tender/id` | Tender ID |
| `tender/title` | Description |
| `buyer/name` | Procuring entity |
| `amount` | Contract value |
| `num_tenderers` | Number of bidders |
| `predicted_suspicious` | **1** = suspicious, **0** = clean |
| `suspicion_probability` | Model confidence (0.0–1.0) |
| `predicted_risk_tier` | 🟢 Low / 🟡 Medium / 🔴 High |

---

## 🗂️ Data Sources

| Source | Description |
|---|---|
| **OCDS Procurement Data** | 5 fiscal years (2016–2021) of Indian public tender data in Open Contracting Data Standard format |
| **MCA Company Filings** | `companies.csv` — vendor master data with CIN, registration dates, capital, industry |
| **Electoral Bond Disclosures** | Political donation links surfaced in network graph and timeline |
| **GeM Portal Records** | Government e-Marketplace procurement records |
| **Income Tax PAN Links** | Cross-referencing for vendor identity verification |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** with pip
- **Node.js 18+** with npm
- **Neon PostgreSQL** database (or any PostgreSQL)


### 1. Setup Frontend

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

### 2. Environment Variables

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

## 🔄 Adding New Data

1. Drop new OCDS-format CSV files into `backend/datasets/`
2. Run `python ml_model.py` from `backend/`
3. Find predictions in `backend/output_datasets/`

---

## 🛠️ Tech Stack

| Layer | Technologies |
|---|---|
| **ML Pipeline** | Python, pandas, NumPy, scikit-learn, Isolation Forest, GradientBoosting, SMOTE (imbalanced-learn) |
| **Backend API** | FastAPI, Uvicorn, joblib |
| **Frontend** | Next.js, React, TypeScript, Tailwind CSS |
| **Visualization** | Recharts (charts), Canvas API (network graph), D3 (force layout), Framer Motion (animations) |
| **State Management** | Zustand |
| **Icons** | Lucide React |
| **Authentication** | Better Auth (Email/Password + Google OAuth) |
| **Database** | Neon PostgreSQL |
| **Fonts** | Syne (display), Space Mono (monospace/data) |

---

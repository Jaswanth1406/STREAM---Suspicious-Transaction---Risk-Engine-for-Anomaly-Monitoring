# STREAM — Suspicious Transaction Risk Engine for Anomaly Monitoring

> Anti-Corruption Procurement Fraud Detection Platform
>
> AIA-26 Hackathon — Anna University

STREAM detects corruption in government procurement by combining **rule-based red flags**, a **supervised ML model**, **entity resolution** across procurement, electoral bonds, and company registries, and an **AI agent** for natural-language investigation — all backed by **Neon PostgreSQL**.

---

## Table of Contents

- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
  - [1. Clone & Virtual Environment](#1-clone--virtual-environment)
  - [2. Environment Variables](#2-environment-variables)
  - [3. Load Data into Neon](#3-load-data-into-neon)
  - [4. Train the ML Model](#4-train-the-ml-model)
  - [5. Start the Server](#5-start-the-server)
- [API Endpoints](#api-endpoints)
  - [Health & Model](#health--model)
  - [Dashboard](#dashboard)
  - [Fraud Alerts](#fraud-alerts)
  - [Vendor Profile](#vendor-profile)
  - [Network Graph](#network-graph)
  - [Bid Analysis](#bid-analysis)
  - [Activity Feed](#activity-feed)
  - [Statistics](#statistics)
  - [ML Predictions (Live)](#ml-predictions-live)
  - [Tender Submission & Pipeline](#tender-submission--pipeline)
  - [AI Agent](#ai-agent)
- [Risk Scoring Methodology](#risk-scoring-methodology)
- [ML Model Performance](#ml-model-performance)
- [Data Sources](#data-sources)
- [Tech Stack](#tech-stack)

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         STREAM Backend Pipeline                            │
│                                                                            │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌────────────┐  │
│  │ Data Ingestion│──▶│ Risk Scoring │──▶│ ML Training  │──▶│  Database  │  │
│  │              │   │ (7 rule flags│   │ Gradient     │   │  Neon      │  │
│  │ Procurement  │   │ + Isolation  │   │ Boosting     │   │  PostgreSQL│  │
│  │ Bonds        │   │   Forest)    │   │ ROC-AUC 0.99 │   │            │  │
│  │ Companies    │   └──────────────┘   └──────────────┘   └─────┬──────┘  │
│  └──────────────┘                                               │         │
│                                                                 │         │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐         │         │
│  │ Entity       │──▶│ Vendor       │──▶│ Populate     │─────────┘         │
│  │ Resolution   │   │ Profiling    │   │ Risk Alerts  │                   │
│  │ (fuzzy match)│   │ (sub-scores) │   │ (17K alerts) │                   │
│  └──────────────┘   └──────────────┘   └──────────────┘                   │
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    FastAPI Server (app.py)                           │   │
│  │  21 REST endpoints  ·  AI Agent (LangGraph)  ·  Background Pipeline │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
STREAM/
├── app.py                     # FastAPI server — 21 endpoints + AI agent
├── db.py                      # Neon PostgreSQL connection pool & helpers
├── risk_engine.py             # Rule-based flags, feature engineering, ML helpers
├── ml_model.py                # Entry point — trains the ML model
├── ml_pipeline.py             # ML training pipeline (model comparison, SMOTE)
├── company_risk_scorer.py     # Shell company risk scoring
├── vendor_risk_scorer.py      # Vendor profile builder (4 sub-scores)
├── entity_resolution.py       # Cross-domain entity matching (fuzzy)
├── requirements.txt           # Python dependencies
│
├── agent/                     # AI Auditor Agent (LangGraph + OpenAI)
│   ├── agent.py               #   ReAct agent — invoke() and astream_events()
│   ├── llm.py                 #   LLM config (AIPipe / OpenRouter)
│   ├── prompts.py             #   System prompt + few-shot SQL examples
│   └── tools/                 #   6 agent tools
│       ├── sql_query.py       #     NL → SQL (read-only, max 50 rows)
│       ├── risk_explainer.py  #     Explain a tender's risk flags
│       ├── vendor_lookup.py   #     Investigate vendor risk sub-scores
│       ├── ml_predict.py      #     Run ML prediction on a tender
│       ├── report_gen.py      #     Generate audit memo via LLM
│       └── network_analysis.py#     Explore entity connections & bonds
│
├── data_ingestion/            # Database loaders & migrations
│   ├── .env                   #   Database URL + API credentials
│   ├── load_all_to_neon.py    #   Load bonds + entities into Neon
│   ├── migrate_all_to_neon.py #   Migrate procurement/company/vendor data
│   ├── populate_risk_alerts.py#   Generate risk_alert + risk_explanation rows
│   ├── download.csv           #   Electoral bond purchase data
│   └── redemption.csv         #   Electoral bond redemption data
│
├── datasets/                  # Source procurement CSVs (OCDS format)
│   ├── ocds_..._2016_2017.csv
│   ├── ocds_..._2017_2018.csv
│   ├── ocds_..._2018_2019.csv
│   ├── ocds_..._2019_2020.csv
│   ├── ocds_..._2020_2021.csv
│   └── companies.csv          # MCA company registry (20K companies)
│
├── output_datasets/           # Generated risk scores & predictions
│   ├── *_risk_scores.csv      #   Rule-based risk scores per fiscal year
│   ├── *_predictions.csv      #   ML predictions per fiscal year
│   └── procurement_risk_scores.csv  # Combined scores (ML training labels)
│
├── trained_model/             # Saved ML model artifacts
│   ├── model.joblib           #   GradientBoosting classifier
│   ├── scaler.joblib          #   StandardScaler
│   ├── label_encoders.joblib  #   Categorical encoders
│   ├── feature_cols.joblib    #   Feature column list
│   └── training_report.json   #   Model metrics & metadata
│
└── outputs/                   # Entity resolution & vendor outputs
    ├── company_risk_table.csv
    ├── tender_risk_table.csv
    └── company_network.gpickle
```

---

## Prerequisites

- **Python 3.10+**
- **pip**
- A **Neon PostgreSQL** database ([neon.tech](https://neon.tech) — free tier works)

---

## Setup

### 1. Clone & Virtual Environment

```bash
cd STREAM---Suspicious-Transaction---Risk-Engine-for-Anomaly-Monitoring

python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

### 2. Environment Variables

STREAM reads configuration from **`data_ingestion/.env`** (primary location).  
`agent/llm.py` also checks a root-level **`.env`** as a fallback (with override).

Create `data_ingestion/.env` using the template below:

```env
# ── Database (required) ──────────────────────────────────────────────────────
# Neon PostgreSQL connection string — get this from your Neon project dashboard
# Format: postgresql://<user>:<password>@<host>/<dbname>?sslmode=require
NEON_DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require

# ── AI Agent / LLM (required only for /agent/* endpoints) ───────────────────
# AIPipe / OpenRouter-compatible bearer token
AIPIPE_TOKEN=your_api_key_here

# LLM API base URL — defaults to AIPipe's OpenRouter proxy if not set
AIPIPE_BASE_URL=https://aipipe.org/openrouter/v1

# Model identifier passed to the LLM API — change to any OpenRouter-supported model
AIPIPE_MODEL=openai/gpt-4.1-nano
```

**Variable reference:**

| Variable | Required | Default | Used By | Description |
|----------|----------|---------|---------|-------------|
| `NEON_DATABASE_URL` | **Yes** | — | `db.py`, all endpoints, data ingestion scripts | Neon PostgreSQL connection string with `sslmode=require` |
| `AIPIPE_TOKEN` | Agent only | — | `agent/llm.py` | Bearer token for AIPipe / OpenRouter LLM API |
| `AIPIPE_BASE_URL` | No | `https://aipipe.org/openrouter/v1` | `agent/llm.py` | LLM API base URL (OpenAI-compatible) |
| `AIPIPE_MODEL` | No | `openai/gpt-4.1-nano` | `agent/llm.py` | Model identifier string passed to the API |

**How variables are loaded:**

| File | Loads from |
|------|------------|
| `db.py` | `data_ingestion/.env` |
| `data_ingestion/load_all_to_neon.py` | `data_ingestion/.env` (via `load_dotenv()`) |
| `data_ingestion/migrate_all_to_neon.py` | `data_ingestion/.env` (via `load_dotenv()`) |
| `data_ingestion/populate_risk_alerts.py` | `data_ingestion/.env` (via `load_dotenv()`) |
| `agent/llm.py` | `data_ingestion/.env` first, then root `.env` (override) |

> **Missing `NEON_DATABASE_URL`** → app exits immediately with `SystemExit`.  
> **Missing `AIPIPE_TOKEN`** → app starts normally; `RuntimeError` raised only when an `/agent/*` endpoint is called.

### 3. Load Data into Neon

Run these in order:

```bash
# Step 1: Load electoral bonds, entities, relationship edges
cd data_ingestion
python load_all_to_neon.py

# Step 2: Migrate procurement tenders, companies, vendor profiles
python migrate_all_to_neon.py

# Step 3: Generate risk alerts and explanations
python populate_risk_alerts.py

cd ..
```

**Tables created:**

| Table | Rows | Content |
|-------|------|---------|
| `procurement_tender` | 29,542 | Tenders with 8 flags + risk scores |
| `company` | 20,249 | MCA company registry |
| `vendor_profile` | 20,333 | Vendor sub-scores + connections (JSONB) |
| `bond_flow` | 1,654 | Aggregated purchaser → party flows |
| `bond_master` | 20,551 | Bond lifecycle records |
| `bond_purchase_event` | 18,871 | Purchase records |
| `bond_redemption_event` | 20,416 | Redemption records |
| `entity` | 12,528 | Unique entities across all domains |
| `relationship_edge` | 1,654 | Bond purchaser → party edges |
| `risk_alert` | 17,221 | Generated fraud alerts |
| `risk_explanation` | 37,861 | Detailed per-flag explanations |
| `pipeline_job` | dynamic | User-submitted tender analysis jobs |

### 4. Train the ML Model

```bash
python ml_model.py
```

This runs the full pipeline:
1. Loads all procurement CSVs from `datasets/`
2. Applies 7 rule-based flags + Isolation Forest anomaly detection
3. Computes composite risk scores (0–100) for every tender
4. Trains GradientBoosting + RandomForest, selects best by ROC-AUC
5. Batch-scores all tenders with `predict_proba()`
6. Saves model artifacts to `trained_model/`

Output: `trained_model/model.joblib`, `scaler.joblib`, `label_encoders.joblib`, `training_report.json`

### 5. Start the Server

```bash
source .venv/bin/activate
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Verify it's running:

```bash
curl http://localhost:8000/
```

```json
{
  "status": "running",
  "service": "STREAM Anti-Corruption Engine",
  "version": "3.0.0",
  "database": "Neon PostgreSQL",
  "model_loaded": true,
  "data_loaded": {
    "procurement_tenders": 29542,
    "companies": 20249,
    "vendor_profiles": 20333,
    "bond_flows": 1654
  }
}
```

**API docs:** [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI) · [http://localhost:8000/redoc](http://localhost:8000/redoc) (ReDoc)

---

## API Endpoints

### Health & Model

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check — server status and data counts |
| `GET` | `/model/info` | ML model metrics (ROC-AUC, accuracy, F1, features) |

---

### Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/dashboard/kpis` | Top-bar KPI cards — active flags, at-risk value, vendor count, risk distribution, bond stats |

---

### Fraud Alerts

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/alerts` | Paginated fraud alerts (tender + company + bond alerts combined) |

**Query params:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `alert_type` | string | all | `bid_rigging`, `shell_network`, `political`, or `all` |
| `risk_tier` | string | — | `High`, `Medium`, `Low` |
| `search` | string | — | Free-text search across name, ID, category |
| `page` | int | 1 | Page number |
| `page_size` | int | 20 | Items per page (max 100) |
| `sort_by` | string | `risk_score` | `risk_score`, `amount`, `confidence` |
| `sort_order` | string | `desc` | `asc` or `desc` |

---

### Vendor Profile

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/vendor/{entity_id}` | Full vendor risk profile — sub-scores, connections, metadata |
| `GET` | `/vendor/search/{query}` | Search vendors by name or CIN (ILIKE match) |
| `GET` | `/vendor/{entity_id}/connections` | Vendor connections — political bonds, shared addresses |

**Vendor sub-scores:**

| Sub-Score | Weight | What It Measures |
|-----------|--------|------------------|
| `bid_pattern` | 35% | Anomaly scores across tenders |
| `shell_risk` | 25% | Low capital, dormant, shared addresses |
| `political` | 25% | Electoral bond donation volume |
| `financials` | 15% | Capital adequacy, compliance |

---

### Network Graph

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/network/graph` | D3.js/Cytoscape-ready graph (nodes + edges) |

**Query params:** `min_risk_score` (default 20), `include_parties` (default true), `max_nodes` (default 200)

---

### Bid Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/bid-analysis` | Paginated tender list with all flags and scores |
| `GET` | `/bid-analysis/summary` | Summary stats — flag counts, top categories, top buyers |

**Query params:** `buyer_name`, `category`, `risk_tier`, `min_amount`, `max_amount`, `page`, `page_size`

---

### Activity Feed

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/activity/recent` | Recent events — tender flags, bond purchases |

**Query params:** `limit` (default 50)

---

### Statistics

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/stats/risk-distribution` | Risk score histogram (bins + mean/median/std) |
| `GET` | `/stats/top-risk-buyers` | Top buyers ranked by avg risk score |
| `GET` | `/stats/bond-summary` | Bond flow summary — party-level breakdown |

---

### ML Predictions (Live)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/predict` | Score a single tender via live ML inference |
| `POST` | `/predict/batch` | Upload CSV → get predictions CSV back |
| `POST` | `/predict/batch/json` | Upload CSV → get JSON summary |

**`POST /predict` body:**

```json
{
  "buyer/name": "Tamil Nadu PWD",
  "tender/value/amount": 340000000,
  "tender/numberOfTenderers": 1,
  "tender/tenderPeriod/durationInDays": 3,
  "tender/procurementMethod": "Limited Tender",
  "tenderclassification/description": "Road Construction"
}
```

**Response:**

```json
{
  "predicted_suspicious": 1,
  "suspicion_probability": 0.94,
  "risk_tier": "High",
  "input_summary": { ... }
}
```

**Required CSV columns for batch endpoints:**

`buyer/name` · `tender/value/amount` · `tender/numberOfTenderers` · `tender/tenderPeriod/durationInDays` · `tender/procurementMethod` · `tenderclassification/description`

---

### Tender Submission & Pipeline

Submit new tenders for full analysis (rule flags + ML prediction), scored in the background and stored in Neon.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/tender/submit` | Submit single tender → background pipeline → returns `job_id` |
| `POST` | `/tender/submit/batch` | Upload CSV → each row queued as separate pipeline job |
| `GET` | `/pipeline/status/{job_id}` | Poll job status and get results |
| `GET` | `/pipeline/jobs` | List all pipeline jobs |

**`POST /tender/submit` body:**

```json
{
  "buyer_name": "Public Works Department",
  "amount": 50000000,
  "num_tenderers": 1,
  "duration_days": 5,
  "procurement_method": "Limited Tender",
  "category": "Construction/Civil Works"
}
```

**Response:**

```json
{
  "job_id": 1,
  "status": "queued",
  "message": "Tender submitted for analysis. Poll /pipeline/status/1 for results."
}
```

**Poll results (`GET /pipeline/status/1`):**

```json
{
  "job_id": 1,
  "status": "completed",
  "result": {
    "risk_score": 64.21,
    "risk_tier": "🔴 High",
    "predicted_suspicious": 1,
    "suspicion_probability": 1.0,
    "flags": {
      "flag_single_bidder": 1,
      "flag_short_window": 1,
      "flag_non_open": 1,
      "flag_round_amount": 1
    },
    "explanation": "Only 1 bidder submitted (possible bid-rigging); Very short tender window (5 days); Non-open procurement method: Limited Tender; Contract amount is suspiciously round"
  }
}
```

**Pipeline flow:**

```
POST /tender/submit
  → pipeline_job created (status: queued)
  → background worker starts
    → 7 rule-based flags computed
    → ML model.predict_proba()
    → blended score = 0.85 × rule + 0.15 × ML
    → INSERT into procurement_tender (is_user_submitted = true)
    → pipeline_job updated (status: completed, result JSONB)
  → User polls GET /pipeline/status/{job_id}
  → Full analysis returned
```

**Batch CSV:** Same columns as `/predict/batch`. Each row becomes a separate pipeline job. Response includes all `job_id`s.

---

### AI Agent

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/agent/chat` | Chat with the STREAM Auditor AI agent |
| `POST` | `/agent/chat/stream` | Streaming variant (Server-Sent Events) |

**`POST /agent/chat` body:**

```json
{
  "messages": [
    { "role": "user", "content": "Show me the top 5 riskiest tenders" }
  ]
}
```

**Response:**

```json
{
  "response": "Here are the top 5 riskiest tenders:\n\n| # | Tender ID | Buyer | Amount | Risk Score |\n...",
  "tool_calls": [
    { "tool": "query_database", "input": "top 5 tenders by risk score", "output": "..." }
  ]
}
```

**Agent tools:**

| Tool | What It Does |
|------|--------------|
| `query_database` | Converts natural language to SQL, runs read-only queries against Neon |
| `explain_tender_risk` | Breaks down a specific tender's risk flags and weights |
| `investigate_vendor` | Looks up vendor profile with sub-scores and connections |
| `predict_tender_risk` | Runs live ML prediction on hypothetical tender data |
| `generate_audit_report` | Generates a structured audit memo using LLM |
| `analyze_network` | Explores entity connections across bonds, co-bidders, shared addresses |

**Example prompts:**

- "Which buyers have the highest average risk score?"
- "Explain why tender 2019_PWBNH_12494_1 was flagged"
- "Investigate MEGHA ENGINEERING"
- "Generate an audit report for Road Construction tenders"
- "What are the political connections of FUTURE GAMING?"

---

## Risk Scoring Methodology

### Stage 1: Rule-Based Flags

Seven expert-defined heuristics, each weighted by severity:

| Flag | Weight | Trigger |
|------|--------|---------|
| Single Bidder | 25 | `num_tenderers == 1` — bid-rigging signal |
| Zero Bidders | 20 | `num_tenderers == 0` — pre-awarded contract |
| Short Window | 15 | `duration_days < 7` — rushed procurement |
| Non-Open Method | 10 | Method ≠ "Open Tender" — restricted competition |
| High Value | 10 | Amount > 95th percentile for category |
| Buyer Concentration | 10 | Buyer handles > 70% of category volume |
| Round Amount | 5 | Amount divisible by ₹100,000 |
| ML Anomaly (Isolation Forest) | 15 | Statistical outlier in [amount, tenderers, duration] |

### Stage 2: Composite Score

```
risk_score = (weighted_flag_sum / max_possible_weight) × 85 + anomaly_score × 15
```

| Tier | Score | Label |
|------|-------|-------|
| Low | 0–30 | 🟢 Low |
| Medium | 30–60 | 🟡 Medium |
| High | 60–100 | 🔴 High |

### Stage 3: Supervised ML

- **Model:** GradientBoostingClassifier (200 trees, depth 4, lr 0.1)
- **Label:** `is_suspicious = 1` if `risk_score ≥ 20`
- **Features:** 9 (numeric + label-encoded categoricals)
- **Output:** `predicted_suspicious` (0/1) + `suspicion_probability` (0.0–1.0)

---

## ML Model Performance

Trained on 29,542 procurement tenders across 5 fiscal years (2016–2021):

| Metric | Score |
|--------|-------|
| **ROC-AUC** | 0.9936 |
| **Accuracy** | 96.9% |
| **Precision** | 93% |
| **Recall** | 91% |
| **F1 Score** | 93% |
| **Cross-Validation** | 5-fold, ROC-AUC 0.984 ± 0.010 |

**Top features by importance:**

| Feature | Importance |
|---------|------------|
| `num_tenderers` | 60% |
| `amount_vs_buyer_avg` | 12% |
| `log_amount` | 8% |
| `duration_days` | 6% |
| `is_round_amount` | 4% |

---

## Data Sources

| Source | Records | Description |
|--------|---------|-------------|
| Government e-Procurement (OCDS) | 29,542 tenders | 5 fiscal years of Assam state procurement |
| Electoral Bond Disclosures | 18,871 purchases, 20,416 redemptions | ECI-released bond data |
| MCA Company Registry | 20,249 companies | Active/dormant companies with capital, address, industry |
| Entity Resolution | 12,528 entities | Fuzzy-matched across procurement, bonds, companies |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **API** | FastAPI + Uvicorn |
| **Database** | Neon PostgreSQL (psycopg 3 + connection pool) |
| **ML** | scikit-learn (GradientBoosting, IsolationForest), imbalanced-learn (SMOTE) |
| **AI Agent** | LangGraph + LangChain + OpenAI-compatible LLM |
| **Data** | pandas, numpy, networkx |
| **Config** | python-dotenv |

---

## Error Codes

| Code | Meaning |
|------|---------|
| `200` | Success |
| `400` | Bad request (missing/invalid params) |
| `404` | Not found (vendor, job, etc.) |
| `422` | Validation error |
| `500` | Internal server error |
| `503` | Model not loaded — run `python ml_model.py` first |

---

## Quick Reference

```bash
# Full setup from scratch
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Configure database
echo 'NEON_DATABASE_URL=postgresql://...' > data_ingestion/.env

# Load data
cd data_ingestion
python load_all_to_neon.py
python migrate_all_to_neon.py
python populate_risk_alerts.py
cd ..

# Train model
python ml_model.py

# Start server
uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# Test
curl http://localhost:8000/
curl http://localhost:8000/dashboard/kpis
curl http://localhost:8000/alerts?page_size=5
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"buyer/name":"Test","tender/value/amount":1000000,"tender/numberOfTenderers":1,"tender/tenderPeriod/durationInDays":3,"tender/procurementMethod":"Limited","tenderclassification/description":"IT"}'
```

---

## Endpoint Summary

| # | Method | Endpoint | Description |
|---|--------|----------|-------------|
| 1 | GET | `/` | Health check |
| 2 | GET | `/model/info` | Model metrics |
| 3 | GET | `/dashboard/kpis` | Dashboard KPIs |
| 4 | GET | `/alerts` | Paginated fraud alerts |
| 5 | GET | `/vendor/{id}` | Vendor risk profile |
| 6 | GET | `/vendor/search/{q}` | Search vendors |
| 7 | GET | `/vendor/{id}/connections` | Vendor connections |
| 8 | GET | `/network/graph` | Network graph |
| 9 | GET | `/bid-analysis` | Paginated bid analysis |
| 10 | GET | `/bid-analysis/summary` | Bid analysis summary |
| 11 | GET | `/activity/recent` | Activity feed |
| 12 | GET | `/stats/risk-distribution` | Risk histogram |
| 13 | GET | `/stats/top-risk-buyers` | Top risk buyers |
| 14 | GET | `/stats/bond-summary` | Bond summary |
| 15 | POST | `/predict` | Live ML prediction (single) |
| 16 | POST | `/predict/batch` | Batch prediction (CSV → CSV) |
| 17 | POST | `/predict/batch/json` | Batch prediction (CSV → JSON) |
| 18 | POST | `/tender/submit` | Submit tender → pipeline |
| 19 | POST | `/tender/submit/batch` | Batch submit (CSV) |
| 20 | GET | `/pipeline/status/{id}` | Poll job status |
| 21 | GET | `/pipeline/jobs` | List all jobs |
| 22 | POST | `/agent/chat` | AI agent chat |
| 23 | POST | `/agent/chat/stream` | AI agent chat (SSE stream) |

---

*STREAM — AIA-26 Hackathon · Anna University*

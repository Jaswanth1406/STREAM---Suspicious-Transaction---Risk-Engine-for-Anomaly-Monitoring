"""
STREAM — Migrate ALL data into Neon PostgreSQL
Creates new tables for procurement tenders, ML predictions, companies, and vendor profiles,
then bulk-loads all CSV/JSON data.

Usage:
    source .venv/bin/activate
    python data_ingestion/migrate_all_to_neon.py
"""

import os
import sys
import json
import csv
from pathlib import Path
import psycopg
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

load_dotenv(BASE_DIR / ".env")
DB_URL = os.environ.get("NEON_DATABASE_URL")
if not DB_URL:
    raise SystemExit("Missing NEON_DATABASE_URL")

# ─────────────────────────────────────────────
# DDL — New tables
# ─────────────────────────────────────────────

DDL_SQL = """
-- Procurement tenders with rule-based risk scores
CREATE TABLE IF NOT EXISTS procurement_tender (
    tender_pk       BIGSERIAL PRIMARY KEY,
    ocid            TEXT,
    tender_id       TEXT,
    tender_title    TEXT,
    buyer_name      TEXT NOT NULL,
    category        TEXT,
    procurement_method TEXT,
    amount          NUMERIC(20,2),
    num_tenderers   INTEGER,
    duration_days   INTEGER,

    -- Rule-based flags (0 or 1)
    flag_single_bidder    SMALLINT DEFAULT 0,
    flag_zero_bidders     SMALLINT DEFAULT 0,
    flag_short_window     SMALLINT DEFAULT 0,
    flag_non_open         SMALLINT DEFAULT 0,
    flag_high_value       SMALLINT DEFAULT 0,
    flag_buyer_concentration SMALLINT DEFAULT 0,
    flag_round_amount     SMALLINT DEFAULT 0,
    ml_anomaly_flag       SMALLINT DEFAULT 0,

    -- Risk scores
    anomaly_score   NUMERIC(10,6),
    risk_score      NUMERIC(8,4),
    risk_tier       TEXT,
    risk_explanation TEXT,

    -- ML predictions
    predicted_suspicious   SMALLINT,
    suspicion_probability  NUMERIC(8,6),
    predicted_risk_tier    TEXT,

    -- Metadata
    source_file     TEXT,
    created_at      TIMESTAMP DEFAULT NOW(),
    is_user_submitted BOOLEAN DEFAULT FALSE
);

-- Company risk table
CREATE TABLE IF NOT EXISTS company (
    company_pk      BIGSERIAL PRIMARY KEY,
    cin             TEXT UNIQUE,
    company_name    TEXT NOT NULL,
    company_status  TEXT,
    company_class   TEXT,
    paidup_capital  NUMERIC(20,2),
    authorized_capital NUMERIC(20,2),
    registered_address TEXT,
    state_code      TEXT,
    nic_code        TEXT,
    industry_classification TEXT,
    reg_date        TEXT,
    age_days        INTEGER,

    -- Risk flags
    address_cluster_size INTEGER DEFAULT 0,
    capital_percentile_rank NUMERIC(8,4),
    status_flag     SMALLINT DEFAULT 0,
    degree_centrality NUMERIC(10,6),
    address_cluster_flag SMALLINT DEFAULT 0,
    low_capital_flag SMALLINT DEFAULT 0,
    young_company_flag SMALLINT DEFAULT 0,
    inactive_flag   SMALLINT DEFAULT 0,
    high_auth_paid_ratio SMALLINT DEFAULT 0,
    opc_flag        SMALLINT DEFAULT 0,

    -- Shell risk
    shell_risk_score NUMERIC(8,4),
    explanation     TEXT,
    requires_human_review BOOLEAN DEFAULT FALSE,

    created_at      TIMESTAMP DEFAULT NOW()
);

-- Vendor profiles (composite risk)
CREATE TABLE IF NOT EXISTS vendor_profile (
    vendor_pk       BIGSERIAL PRIMARY KEY,
    entity_id       TEXT UNIQUE NOT NULL,
    cin             TEXT,
    company_name    TEXT NOT NULL,
    company_status  TEXT,
    state           TEXT,
    composite_risk_score NUMERIC(8,4),
    risk_tier       TEXT,

    -- Sub-scores
    bid_pattern_score    NUMERIC(8,4) DEFAULT 0,
    shell_risk_sub_score NUMERIC(8,4) DEFAULT 0,
    political_score      NUMERIC(8,4) DEFAULT 0,
    financials_score     NUMERIC(8,4) DEFAULT 0,

    -- Profile data (JSON for flexibility)
    bid_stats       JSONB DEFAULT '{}',
    political_info  JSONB DEFAULT '{}',
    connections     JSONB DEFAULT '[]',
    shell_explanation TEXT,
    requires_human_review BOOLEAN DEFAULT FALSE,

    created_at      TIMESTAMP DEFAULT NOW()
);

-- Political bond flows (aggregated)
CREATE TABLE IF NOT EXISTS bond_flow (
    flow_pk         BIGSERIAL PRIMARY KEY,
    purchaser_name  TEXT NOT NULL,
    party_name      TEXT NOT NULL,
    total_bonds     INTEGER,
    total_value     NUMERIC(20,2),
    first_date      TEXT,
    last_date       TEXT,
    UNIQUE (purchaser_name, party_name)
);

-- Job queue for background pipeline processing
CREATE TABLE IF NOT EXISTS pipeline_job (
    job_id          BIGSERIAL PRIMARY KEY,
    job_type        TEXT NOT NULL,        -- 'single' or 'batch'
    status          TEXT DEFAULT 'pending',  -- pending, processing, completed, failed
    input_data      JSONB NOT NULL,
    result_data     JSONB,
    error_message   TEXT,
    created_at      TIMESTAMP DEFAULT NOW(),
    started_at      TIMESTAMP,
    completed_at    TIMESTAMP
);
"""

INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_tender_ocid ON procurement_tender(ocid);
CREATE INDEX IF NOT EXISTS idx_tender_buyer ON procurement_tender(buyer_name);
CREATE INDEX IF NOT EXISTS idx_tender_category ON procurement_tender(category);
CREATE INDEX IF NOT EXISTS idx_tender_risk_score ON procurement_tender(risk_score DESC);
CREATE INDEX IF NOT EXISTS idx_tender_risk_tier ON procurement_tender(risk_tier);
CREATE INDEX IF NOT EXISTS idx_tender_amount ON procurement_tender(amount DESC);
CREATE INDEX IF NOT EXISTS idx_tender_created ON procurement_tender(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tender_user_submitted ON procurement_tender(is_user_submitted);

CREATE INDEX IF NOT EXISTS idx_company_name ON company(company_name);
CREATE INDEX IF NOT EXISTS idx_company_state ON company(state_code);
CREATE INDEX IF NOT EXISTS idx_company_shell_risk ON company(shell_risk_score DESC);

CREATE INDEX IF NOT EXISTS idx_vendor_name ON vendor_profile(company_name);
CREATE INDEX IF NOT EXISTS idx_vendor_risk ON vendor_profile(composite_risk_score DESC);
CREATE INDEX IF NOT EXISTS idx_vendor_cin ON vendor_profile(cin);

CREATE INDEX IF NOT EXISTS idx_bond_flow_purchaser ON bond_flow(purchaser_name);
CREATE INDEX IF NOT EXISTS idx_bond_flow_party ON bond_flow(party_name);
CREATE INDEX IF NOT EXISTS idx_bond_flow_value ON bond_flow(total_value DESC);

CREATE INDEX IF NOT EXISTS idx_job_status ON pipeline_job(status);
CREATE INDEX IF NOT EXISTS idx_job_created ON pipeline_job(created_at DESC);
"""

BATCH_SIZE = 500


def safe_float(v):
    try:
        if v is None or v == '' or v == 'nan':
            return None
        return float(v)
    except (ValueError, TypeError):
        return None


def safe_int(v):
    try:
        if v is None or v == '' or v == 'nan':
            return None
        return int(float(v))
    except (ValueError, TypeError):
        return None


def load_procurement_tenders(cur):
    """Load procurement risk scores + ML predictions into procurement_tender table."""
    risk_csv = PROJECT_DIR / "output_datasets" / "procurement_risk_scores.csv"
    if not risk_csv.exists():
        print("  ⚠️  procurement_risk_scores.csv not found, skipping")
        return 0

    # Read risk scores
    with open(risk_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Read ML predictions and index by ocid
    pred_map = {}
    pred_dir = PROJECT_DIR / "output_datasets"
    for pred_file in sorted(pred_dir.glob("*_predictions.csv")):
        with open(pred_file, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                ocid = row.get("ocid", "")
                if ocid:
                    pred_map[ocid] = row

    print(f"  📊 {len(rows)} tenders, {len(pred_map)} predictions")

    batch = []
    total = 0

    for row in rows:
        ocid = row.get("ocid", "")
        pred = pred_map.get(ocid, {})

        batch.append((
            ocid,
            row.get("tender/id"),
            row.get("tender/title"),
            row.get("buyer/name", ""),
            row.get("tenderclassification/description"),
            row.get("tender/procurementMethod"),
            safe_float(row.get("amount")),
            safe_int(row.get("num_tenderers")),
            safe_int(row.get("duration_days")),
            safe_int(row.get("flag_single_bidder")),
            safe_int(row.get("flag_zero_bidders")),
            safe_int(row.get("flag_short_window")),
            safe_int(row.get("flag_non_open")),
            safe_int(row.get("flag_high_value")),
            safe_int(row.get("flag_buyer_concentration")),
            safe_int(row.get("flag_round_amount")),
            safe_int(row.get("ml_anomaly_flag")),
            safe_float(row.get("anomaly_score")),
            safe_float(row.get("risk_score")),
            row.get("risk_tier"),
            row.get("risk_explanation"),
            safe_int(pred.get("predicted_suspicious")),
            safe_float(pred.get("suspicion_probability")),
            pred.get("predicted_risk_tier"),
            "bulk_migration",
            False,
        ))

        if len(batch) >= BATCH_SIZE:
            _insert_tender_batch(cur, batch)
            total += len(batch)
            batch = []

    if batch:
        _insert_tender_batch(cur, batch)
        total += len(batch)

    return total


def _insert_tender_batch(cur, batch):
    cur.executemany("""
        INSERT INTO procurement_tender (
            ocid, tender_id, tender_title, buyer_name, category,
            procurement_method, amount, num_tenderers, duration_days,
            flag_single_bidder, flag_zero_bidders, flag_short_window,
            flag_non_open, flag_high_value, flag_buyer_concentration,
            flag_round_amount, ml_anomaly_flag,
            anomaly_score, risk_score, risk_tier, risk_explanation,
            predicted_suspicious, suspicion_probability, predicted_risk_tier,
            source_file, is_user_submitted
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s
        )
    """, batch)


def load_companies(cur):
    """Load company risk table into company table."""
    csv_path = PROJECT_DIR / "outputs" / "company_risk_table.csv"
    if not csv_path.exists():
        print("  ⚠️  company_risk_table.csv not found, skipping")
        return 0

    with open(csv_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    batch = []
    total = 0

    for row in rows:
        batch.append((
            row.get("CIN"),
            row.get("CompanyName", ""),
            row.get("CompanyStatus"),
            row.get("CompanyClass"),
            safe_float(row.get("PaidupCapital")),
            safe_float(row.get("AuthorizedCapital")),
            row.get("Registered_Office_Address"),
            row.get("CompanyStateCode"),
            row.get("nic_code"),
            row.get("CompanyIndustrialClassification"),
            row.get("reg_date"),
            safe_int(row.get("age_days")),
            safe_int(row.get("address_cluster_size")),
            safe_float(row.get("capital_percentile_rank")),
            safe_int(row.get("status_flag")),
            safe_float(row.get("degree_centrality")),
            safe_int(row.get("address_cluster_flag")),
            safe_int(row.get("low_capital_flag")),
            safe_int(row.get("young_company_flag")),
            safe_int(row.get("inactive_flag")),
            safe_int(row.get("high_auth_paid_ratio")),
            safe_int(row.get("opc_flag")),
            safe_float(row.get("shell_risk_score")),
            row.get("explanation"),
            row.get("requires_human_review", "").lower() == "true",
        ))

        if len(batch) >= BATCH_SIZE:
            _insert_company_batch(cur, batch)
            total += len(batch)
            batch = []

    if batch:
        _insert_company_batch(cur, batch)
        total += len(batch)

    return total


def _insert_company_batch(cur, batch):
    cur.executemany("""
        INSERT INTO company (
            cin, company_name, company_status, company_class,
            paidup_capital, authorized_capital, registered_address,
            state_code, nic_code, industry_classification,
            reg_date, age_days,
            address_cluster_size, capital_percentile_rank, status_flag,
            degree_centrality, address_cluster_flag, low_capital_flag,
            young_company_flag, inactive_flag, high_auth_paid_ratio, opc_flag,
            shell_risk_score, explanation, requires_human_review
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s
        )
        ON CONFLICT (cin) DO NOTHING
    """, batch)


def load_vendor_profiles(cur):
    """Load vendor profiles into vendor_profile table."""
    json_path = PROJECT_DIR / "outputs" / "vendor_profiles.json"
    if not json_path.exists():
        print("  ⚠️  vendor_profiles.json not found, skipping")
        return 0

    with open(json_path, "r", encoding="utf-8") as f:
        profiles = json.load(f)

    batch = []
    total = 0

    for entity_id, p in profiles.items():
        sub = p.get("sub_scores", {})
        batch.append((
            entity_id,
            p.get("cin"),
            p.get("company_name", ""),
            p.get("company_status"),
            p.get("state"),
            safe_float(p.get("composite_risk_score")),
            p.get("risk_tier"),
            safe_float(sub.get("bid_pattern")),
            safe_float(sub.get("shell_risk")),
            safe_float(sub.get("political")),
            safe_float(sub.get("financials")),
            json.dumps(p.get("bid_stats", {})),
            json.dumps(p.get("political_info", {})),
            json.dumps(p.get("connections", [])),
            p.get("shell_explanation"),
            p.get("requires_human_review", False),
        ))

        if len(batch) >= BATCH_SIZE:
            _insert_vendor_batch(cur, batch)
            total += len(batch)
            batch = []

    if batch:
        _insert_vendor_batch(cur, batch)
        total += len(batch)

    return total


def _insert_vendor_batch(cur, batch):
    cur.executemany("""
        INSERT INTO vendor_profile (
            entity_id, cin, company_name, company_status, state,
            composite_risk_score, risk_tier,
            bid_pattern_score, shell_risk_sub_score, political_score, financials_score,
            bid_stats, political_info, connections,
            shell_explanation, requires_human_review
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s
        )
        ON CONFLICT (entity_id) DO NOTHING
    """, batch)


def load_bond_flows(cur):
    """Load political bond flows into bond_flow table."""
    csv_path = PROJECT_DIR / "outputs" / "political_bond_flows.csv"
    if not csv_path.exists():
        print("  ⚠️  political_bond_flows.csv not found, skipping")
        return 0

    with open(csv_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    batch = []
    total = 0

    for row in rows:
        batch.append((
            row.get("purchaser_name", ""),
            row.get("party_name", ""),
            safe_int(row.get("total_bonds")),
            safe_float(row.get("total_value")),
            row.get("first_date"),
            row.get("last_date"),
        ))

        if len(batch) >= BATCH_SIZE:
            _insert_bond_batch(cur, batch)
            total += len(batch)
            batch = []

    if batch:
        _insert_bond_batch(cur, batch)
        total += len(batch)

    return total


def _insert_bond_batch(cur, batch):
    cur.executemany("""
        INSERT INTO bond_flow (
            purchaser_name, party_name, total_bonds,
            total_value, first_date, last_date
        ) VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (purchaser_name, party_name) DO NOTHING
    """, batch)


def main():
    print("=" * 60)
    print("  STREAM — Full Data Migration to Neon PostgreSQL")
    print("=" * 60)

    with psycopg.connect(DB_URL) as conn:
        with conn.cursor() as cur:
            # Create tables
            print("\n📋 Creating tables...")
            cur.execute(DDL_SQL)
            print("   ✅ Tables created")

            # Create indexes
            print("📋 Creating indexes...")
            cur.execute(INDEX_SQL)
            print("   ✅ Indexes created")

            # Truncate new tables only (preserve existing bond data)
            print("\n🗑️  Truncating new tables...")
            cur.execute("""
                TRUNCATE TABLE pipeline_job RESTART IDENTITY CASCADE;
                TRUNCATE TABLE bond_flow RESTART IDENTITY CASCADE;
                TRUNCATE TABLE vendor_profile RESTART IDENTITY CASCADE;
                TRUNCATE TABLE company RESTART IDENTITY CASCADE;
                TRUNCATE TABLE procurement_tender RESTART IDENTITY CASCADE;
            """)
            print("   ✅ Tables truncated")

            # Load data
            print("\n📦 Loading procurement tenders...")
            n = load_procurement_tenders(cur)
            print(f"   ✅ {n:,} tenders loaded")

            print("\n📦 Loading companies...")
            n = load_companies(cur)
            print(f"   ✅ {n:,} companies loaded")

            print("\n📦 Loading vendor profiles...")
            n = load_vendor_profiles(cur)
            print(f"   ✅ {n:,} vendor profiles loaded")

            print("\n📦 Loading bond flows...")
            n = load_bond_flows(cur)
            print(f"   ✅ {n:,} bond flows loaded")

        conn.commit()

    # Verify
    print("\n" + "=" * 60)
    print("  VERIFICATION")
    print("=" * 60)

    with psycopg.connect(DB_URL) as conn:
        with conn.cursor() as cur:
            tables = [
                "procurement_tender", "company", "vendor_profile",
                "bond_flow", "pipeline_job",
                # existing tables
                "download_bonds", "redemption_bonds", "bond_master",
                "bond_purchase_event", "bond_redemption_event",
                "entity", "relationship_edge", "risk_alert", "risk_explanation",
            ]
            for t in tables:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {t}")
                    count = cur.fetchone()[0]
                    print(f"  {t:30s}  {count:>10,}")
                except Exception:
                    print(f"  {t:30s}  (not found)")

    print("\n" + "=" * 60)
    print("  ✅ Migration complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

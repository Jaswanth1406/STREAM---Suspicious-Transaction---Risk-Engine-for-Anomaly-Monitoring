from pathlib import Path
import os
import psycopg
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_CSV = BASE_DIR / "download.csv"
REDEMPTION_CSV = BASE_DIR / "redemption.csv"

# Load .env from data_ingestion/ directory
load_dotenv()

DB_URL = os.environ.get("NEON_DATABASE_URL")
if not DB_URL:
    raise SystemExit("Missing NEON_DATABASE_URL environment variable")

DDL_SQL = """
CREATE TABLE IF NOT EXISTS download_bonds (
  sr_no INTEGER,
  reference_no_urn TEXT,
  journal_date TEXT,
  purchase_date TEXT,
  expiry_date TEXT,
  purchaser_name TEXT,
  prefix TEXT,
  bond_number INTEGER,
  denomination TEXT,
  issue_branch_code TEXT,
  issue_teller TEXT,
  status TEXT
);

CREATE TABLE IF NOT EXISTS redemption_bonds (
  sr_no INTEGER,
  encashment_date TEXT,
  party_name TEXT,
  account_no TEXT,
  prefix TEXT,
  bond_number INTEGER,
  denomination TEXT,
  pay_branch_code TEXT,
  pay_teller TEXT
);

CREATE TABLE IF NOT EXISTS bond_master (
  bond_id BIGSERIAL PRIMARY KEY,
  prefix TEXT NOT NULL,
  bond_number INTEGER NOT NULL,
  denomination TEXT,
  UNIQUE (prefix, bond_number)
);

CREATE TABLE IF NOT EXISTS bond_purchase_event (
  purchase_event_id BIGSERIAL PRIMARY KEY,
  bond_id BIGINT NOT NULL REFERENCES bond_master(bond_id),
  reference_no_urn TEXT NOT NULL,
  journal_date TEXT NOT NULL,
  purchase_date TEXT NOT NULL,
  expiry_date TEXT NOT NULL,
  purchaser_name TEXT NOT NULL,
  issue_branch_code TEXT NOT NULL,
  issue_teller TEXT NOT NULL,
  status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS bond_redemption_event (
  redemption_event_id BIGSERIAL PRIMARY KEY,
  bond_id BIGINT NOT NULL REFERENCES bond_master(bond_id),
  encashment_date TEXT NOT NULL,
  party_name TEXT NOT NULL,
  account_no_masked TEXT NOT NULL,
  pay_branch_code TEXT NOT NULL,
  pay_teller TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS entity (
  entity_id BIGSERIAL PRIMARY KEY,
  entity_type TEXT NOT NULL,
  canonical_name TEXT NOT NULL,
  normalized_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS entity_alias (
  alias_id BIGSERIAL PRIMARY KEY,
  entity_id BIGINT NOT NULL REFERENCES entity(entity_id),
  alias_text TEXT NOT NULL,
  confidence NUMERIC(5,4) NOT NULL
);

CREATE TABLE IF NOT EXISTS relationship_edge (
  edge_id BIGSERIAL PRIMARY KEY,
  src_entity_id BIGINT NOT NULL REFERENCES entity(entity_id),
  dst_entity_id BIGINT NOT NULL REFERENCES entity(entity_id),
  edge_type TEXT NOT NULL,
  bond_id BIGINT NULL REFERENCES bond_master(bond_id),
  event_time TIMESTAMP NULL,
  weight NUMERIC(12,4) NULL,
  evidence_ref TEXT NULL
);

CREATE TABLE IF NOT EXISTS risk_alert (
  alert_id BIGSERIAL PRIMARY KEY,
  entity_id BIGINT NOT NULL REFERENCES entity(entity_id),
  risk_score NUMERIC(6,4) NOT NULL,
  risk_level TEXT NOT NULL,
  generated_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS risk_explanation (
  explanation_id BIGSERIAL PRIMARY KEY,
  alert_id BIGINT NOT NULL REFERENCES risk_alert(alert_id),
  rule_or_model TEXT NOT NULL,
  reason_text TEXT NOT NULL,
  supporting_metrics JSONB NULL
);
"""

INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_download_bonds_prefix_bond
  ON download_bonds(prefix, bond_number);
CREATE INDEX IF NOT EXISTS idx_download_bonds_purchaser_name
  ON download_bonds(purchaser_name);
CREATE INDEX IF NOT EXISTS idx_download_bonds_purchase_date
  ON download_bonds(purchase_date);

CREATE INDEX IF NOT EXISTS idx_redemption_bonds_prefix_bond
  ON redemption_bonds(prefix, bond_number);
CREATE INDEX IF NOT EXISTS idx_redemption_bonds_party_name
  ON redemption_bonds(party_name);
CREATE INDEX IF NOT EXISTS idx_redemption_bonds_encashment_date
  ON redemption_bonds(encashment_date);

CREATE INDEX IF NOT EXISTS idx_bond_purchase_event_bond_id
  ON bond_purchase_event(bond_id);
CREATE INDEX IF NOT EXISTS idx_bond_purchase_event_purchase_date
  ON bond_purchase_event(purchase_date);

CREATE INDEX IF NOT EXISTS idx_bond_redemption_event_bond_id
  ON bond_redemption_event(bond_id);
CREATE INDEX IF NOT EXISTS idx_bond_redemption_event_encashment_date
  ON bond_redemption_event(encashment_date);

CREATE INDEX IF NOT EXISTS idx_entity_type_normalized
  ON entity(entity_type, normalized_name);
CREATE INDEX IF NOT EXISTS idx_entity_alias_entity_id
  ON entity_alias(entity_id);

CREATE INDEX IF NOT EXISTS idx_relationship_edge_src
  ON relationship_edge(src_entity_id);
CREATE INDEX IF NOT EXISTS idx_relationship_edge_dst
  ON relationship_edge(dst_entity_id);
CREATE INDEX IF NOT EXISTS idx_relationship_edge_bond
  ON relationship_edge(bond_id);
CREATE INDEX IF NOT EXISTS idx_relationship_edge_type_time
  ON relationship_edge(edge_type, event_time);

CREATE INDEX IF NOT EXISTS idx_risk_alert_entity
  ON risk_alert(entity_id);
CREATE INDEX IF NOT EXISTS idx_risk_alert_generated_at
  ON risk_alert(generated_at);
CREATE INDEX IF NOT EXISTS idx_risk_explanation_alert
  ON risk_explanation(alert_id);
"""

TRUNCATE_SQL = """
TRUNCATE TABLE
  risk_explanation,
  risk_alert,
  relationship_edge,
  entity_alias,
  entity,
  bond_redemption_event,
  bond_purchase_event,
  bond_master,
  redemption_bonds,
  download_bonds
RESTART IDENTITY CASCADE;
"""

POPULATE_SQL = """
INSERT INTO bond_master (prefix, bond_number, denomination)
SELECT prefix, bond_number, denomination
FROM download_bonds
WHERE prefix IS NOT NULL AND bond_number IS NOT NULL
UNION
SELECT prefix, bond_number, denomination
FROM redemption_bonds
WHERE prefix IS NOT NULL AND bond_number IS NOT NULL;

INSERT INTO bond_purchase_event (
  bond_id, reference_no_urn, journal_date, purchase_date, expiry_date,
  purchaser_name, issue_branch_code, issue_teller, status
)
SELECT
  bm.bond_id,
  d.reference_no_urn,
  d.journal_date,
  d.purchase_date,
  d.expiry_date,
  d.purchaser_name,
  d.issue_branch_code,
  d.issue_teller,
  d.status
FROM download_bonds d
JOIN bond_master bm
  ON bm.prefix = d.prefix
 AND bm.bond_number = d.bond_number;

INSERT INTO bond_redemption_event (
  bond_id, encashment_date, party_name, account_no_masked, pay_branch_code, pay_teller
)
SELECT
  bm.bond_id,
  r.encashment_date,
  r.party_name,
  r.account_no,
  r.pay_branch_code,
  r.pay_teller
FROM redemption_bonds r
JOIN bond_master bm
  ON bm.prefix = r.prefix
 AND bm.bond_number = r.bond_number;

INSERT INTO entity (entity_type, canonical_name, normalized_name)
SELECT 'PURCHASER', purchaser_name, LOWER(TRIM(purchaser_name))
FROM (SELECT DISTINCT purchaser_name FROM download_bonds WHERE purchaser_name IS NOT NULL) d
UNION
SELECT 'PARTY', party_name, LOWER(TRIM(party_name))
FROM (SELECT DISTINCT party_name FROM redemption_bonds WHERE party_name IS NOT NULL) r
UNION
SELECT 'BRANCH', issue_branch_code, LOWER(TRIM(issue_branch_code))
FROM (SELECT DISTINCT issue_branch_code FROM download_bonds WHERE issue_branch_code IS NOT NULL) b1
UNION
SELECT 'BRANCH', pay_branch_code, LOWER(TRIM(pay_branch_code))
FROM (SELECT DISTINCT pay_branch_code FROM redemption_bonds WHERE pay_branch_code IS NOT NULL) b2
UNION
SELECT 'ACCOUNT', account_no, LOWER(TRIM(account_no))
FROM (SELECT DISTINCT account_no FROM redemption_bonds WHERE account_no IS NOT NULL) a;

INSERT INTO entity_alias (entity_id, alias_text, confidence)
SELECT entity_id, canonical_name, 1.0000
FROM entity;

INSERT INTO relationship_edge (
  src_entity_id, dst_entity_id, edge_type, bond_id, event_time, weight, evidence_ref
)
SELECT
  ep.entity_id,
  et.entity_id,
  'PURCHASER_TO_PARTY_VIA_BOND',
  bm.bond_id,
  NULL,
  1.0,
  CONCAT('prefix=', d.prefix, ',bond_number=', d.bond_number)
FROM download_bonds d
JOIN redemption_bonds r
  ON r.prefix = d.prefix
 AND r.bond_number = d.bond_number
JOIN bond_master bm
  ON bm.prefix = d.prefix
 AND bm.bond_number = d.bond_number
JOIN entity ep
  ON ep.entity_type = 'PURCHASER'
 AND ep.normalized_name = LOWER(TRIM(d.purchaser_name))
JOIN entity et
  ON et.entity_type = 'PARTY'
 AND et.normalized_name = LOWER(TRIM(r.party_name));
"""


def copy_csv(cur, csv_path: Path, table_name: str) -> None:
    with csv_path.open("r", encoding="utf-8") as handle:
        with cur.copy(
            f"COPY {table_name} FROM STDIN WITH (FORMAT CSV, HEADER TRUE)"
        ) as copy:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                copy.write(chunk)


def fetch_count(cur, table_name: str) -> int:
    cur.execute(f"SELECT COUNT(*) FROM {table_name}")
    return cur.fetchone()[0]


def main() -> None:
    with psycopg.connect(DB_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(DDL_SQL)
            cur.execute(INDEX_SQL)
            cur.execute(TRUNCATE_SQL)

            copy_csv(cur, DOWNLOAD_CSV, "download_bonds")
            copy_csv(cur, REDEMPTION_CSV, "redemption_bonds")

            cur.execute(POPULATE_SQL)

            tables = [
                "download_bonds",
                "redemption_bonds",
                "bond_master",
                "bond_purchase_event",
                "bond_redemption_event",
                "entity",
                "entity_alias",
                "relationship_edge",
                "risk_alert",
                "risk_explanation",
            ]

            counts = {table: fetch_count(cur, table) for table in tables}

        conn.commit()

    for table, count in counts.items():
        print(f"{table}: {count}")


if __name__ == "__main__":
    main()

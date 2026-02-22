"""
Populate risk_alert and risk_explanation tables in Neon PostgreSQL.

This script:
1. Reads precomputed risk data from outputs/
2. Bulk-upserts entities into the entity table
3. Batch-inserts risk_alert rows for flagged tenders and shell companies
4. Batch-inserts risk_explanation rows with rule/model details

Optimised for remote Neon DB — uses batch inserts to minimise round-trips.

Run:
  cd data_ingestion
  source .venv/bin/activate
  python populate_risk_alerts.py
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
import psycopg
from dotenv import load_dotenv

# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DATASETS_DIR = BASE_DIR / "output_datasets"

# Load .env from data_ingestion/ directory
load_dotenv(Path(__file__).resolve().parent / ".env")

DB_URL = os.environ.get("NEON_DATABASE_URL")
if not DB_URL:
    raise SystemExit("Set NEON_DATABASE_URL env var first.")

BATCH_SIZE = 500  # rows per INSERT … VALUES batch


def load_data():
    """Load precomputed risk data."""
    data = {}

    proc_path = OUTPUT_DATASETS_DIR / "procurement_risk_scores.csv"
    if proc_path.exists():
        data["procurement"] = pd.read_csv(proc_path)
        print(f"  Loaded {len(data['procurement'])} tenders")
    else:
        data["procurement"] = pd.DataFrame()
        print("  ⚠ procurement_risk_scores.csv not found")

    company_path = OUTPUT_DIR / "company_risk_table.csv"
    if company_path.exists():
        data["companies"] = pd.read_csv(company_path)
        print(f"  Loaded {len(data['companies'])} companies")
    else:
        data["companies"] = pd.DataFrame()
        print("  ⚠ company_risk_table.csv not found")

    vendor_path = OUTPUT_DIR / "vendor_profiles.json"
    if vendor_path.exists():
        with open(vendor_path, "r") as f:
            data["vendor_profiles"] = json.load(f)
        print(f"  Loaded {len(data['vendor_profiles'])} vendor profiles")
    else:
        data["vendor_profiles"] = {}
        print("  ⚠ vendor_profiles.json not found")

    bond_path = OUTPUT_DIR / "political_bond_flows.csv"
    if bond_path.exists():
        data["bond_flows"] = pd.read_csv(bond_path)
        print(f"  Loaded {len(data['bond_flows'])} bond flows")
    else:
        data["bond_flows"] = pd.DataFrame()
        print("  ⚠ political_bond_flows.csv not found")

    return data


# ── In-memory entity cache to avoid repeated DB lookups ──
_entity_cache: dict[tuple[str, str], int] = {}


def bulk_ensure_entities(cur, pairs: list[tuple[str, str]]):
    """
    Given a list of (entity_type, canonical_name) pairs,
    ensure they all exist in the entity table and populate the cache.
    Uses a single INSERT … ON CONFLICT per batch.
    """
    # Ensure unique constraint exists
    cur.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_entity_type_norm "
        "ON entity(entity_type, normalized_name)"
    )
    cur.connection.commit()

    # Deduplicate
    unique = set()
    for etype, name in pairs:
        key = (etype, name.strip().upper())
        if key not in _entity_cache:
            unique.add((etype, name.strip(), name.strip().upper()))

    if not unique:
        return

    rows = list(unique)
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        args = []
        placeholders = []
        for etype, canonical, normalized in batch:
            placeholders.append("(%s, %s, %s)")
            args.extend([etype, canonical, normalized])

        sql = (
            "INSERT INTO entity (entity_type, canonical_name, normalized_name) VALUES "
            + ", ".join(placeholders)
            + " ON CONFLICT (entity_type, normalized_name) DO NOTHING"
        )
        cur.execute(sql, args)

    # Now fetch all entity_ids for requested pairs
    all_keys = list({(et, n.strip().upper()) for et, n in pairs})
    for i in range(0, len(all_keys), BATCH_SIZE):
        batch = all_keys[i : i + BATCH_SIZE]
        wheres = []
        args = []
        for etype, norm in batch:
            wheres.append("(entity_type = %s AND normalized_name = %s)")
            args.extend([etype, norm])

        cur.execute(
            "SELECT entity_id, entity_type, normalized_name FROM entity WHERE "
            + " OR ".join(wheres),
            args,
        )
        for eid, etype, norm in cur.fetchall():
            _entity_cache[(etype, norm)] = eid


def get_entity_id(entity_type: str, canonical_name: str) -> int:
    """Get cached entity_id (must call bulk_ensure_entities first)."""
    return _entity_cache[(entity_type, canonical_name.strip().upper())]


def batch_insert_alerts(cur, alert_rows: list[tuple]) -> list[int]:
    """
    Batch-insert into risk_alert and return all alert_ids.
    Each tuple: (entity_id, risk_score, risk_level, generated_at)
    """
    all_ids = []
    for i in range(0, len(alert_rows), BATCH_SIZE):
        batch = alert_rows[i : i + BATCH_SIZE]
        placeholders = []
        args = []
        for entity_id, score, level, ts in batch:
            placeholders.append("(%s, %s, %s, %s)")
            args.extend([entity_id, score, level, ts])

        cur.execute(
            "INSERT INTO risk_alert (entity_id, risk_score, risk_level, generated_at) VALUES "
            + ", ".join(placeholders)
            + " RETURNING alert_id",
            args,
        )
        all_ids.extend([row[0] for row in cur.fetchall()])
    return all_ids


def batch_insert_explanations(cur, explanation_rows: list[tuple]):
    """
    Batch-insert into risk_explanation.
    Each tuple: (alert_id, rule_or_model, reason_text, supporting_metrics_json)
    """
    for i in range(0, len(explanation_rows), BATCH_SIZE):
        batch = explanation_rows[i : i + BATCH_SIZE]
        placeholders = []
        args = []
        for alert_id, rule, reason, metrics_json in batch:
            placeholders.append("(%s, %s, %s, %s)")
            args.extend([alert_id, rule, reason, metrics_json])

        cur.execute(
            "INSERT INTO risk_explanation (alert_id, rule_or_model, reason_text, supporting_metrics) VALUES "
            + ", ".join(placeholders),
            args,
        )


# ─────────────────────────────────────────────
#  BUILD ALERT DATA (pure Python, no DB calls)
# ─────────────────────────────────────────────

def build_tender_alert_data(procurement_df):
    """
    Returns:
      entity_pairs: list of (type, name) for bulk entity creation
      alert_specs: list of dicts with entity_key, risk_score, risk_level, explanations
    """
    if procurement_df.empty:
        return [], []

    flagged = procurement_df[procurement_df["risk_score"] >= 20]
    entity_pairs = []
    alert_specs = []

    for _, row in flagged.iterrows():
        buyer_name = str(row.get("buyer/name", "UNKNOWN"))
        risk_score = float(row.get("risk_score", 0))
        tender_id = str(row.get("tender/id", ""))

        risk_level = "HIGH" if risk_score >= 50 else ("MEDIUM" if risk_score >= 25 else "LOW")

        entity_pairs.append(("PROCUREMENT_BUYER", buyer_name))

        explanations = []
        if row.get("flag_single_bidder", 0):
            explanations.append(("SINGLE_BIDDER",
                f"Tender {tender_id}: only 1 bidder submitted",
                {"num_tenderers": int(row.get("num_tenderers", 1))}))
        if row.get("flag_zero_bidders", 0):
            explanations.append(("ZERO_BIDDERS",
                f"Tender {tender_id}: zero bidders recorded",
                {"num_tenderers": 0}))
        if row.get("flag_short_window", 0):
            explanations.append(("SHORT_WINDOW",
                f"Tender {tender_id}: tender window < 3 days",
                {"duration_days": int(row.get("duration_days", 0))}))
        if row.get("flag_non_open", 0):
            explanations.append(("NON_OPEN_TENDER",
                f"Tender {tender_id}: non-open method ({row.get('tender/procurementMethod', '')})",
                {"method": str(row.get("tender/procurementMethod", ""))}))
        if row.get("flag_high_value", 0):
            explanations.append(("HIGH_VALUE",
                f"Tender {tender_id}: value above 95th percentile",
                {"amount": float(row.get("amount", 0))}))
        if row.get("flag_buyer_concentration", 0):
            explanations.append(("BUYER_CONCENTRATION",
                f"Tender {tender_id}: buyer dominates >70% of category",
                {"buyer_name": buyer_name}))
        if row.get("flag_round_amount", 0):
            explanations.append(("ROUND_AMOUNT",
                f"Tender {tender_id}: suspiciously round amount",
                {"amount": float(row.get("amount", 0))}))
        if row.get("ml_anomaly_flag", 0):
            explanations.append(("ML_ANOMALY",
                f"Tender {tender_id}: Isolation Forest outlier",
                {"anomaly_score": float(row.get("anomaly_score", 0))}))
        if not explanations:
            explanations.append(("COMPOSITE",
                f"Tender {tender_id}: composite risk {risk_score:.1f}/100",
                {"risk_score": risk_score}))

        alert_specs.append({
            "entity_key": ("PROCUREMENT_BUYER", buyer_name),
            "risk_score": round(risk_score / 100, 4),
            "risk_level": risk_level,
            "explanations": explanations,
        })

    return entity_pairs, alert_specs


def build_shell_alert_data(companies_df):
    if companies_df.empty:
        return [], []

    flagged = companies_df[companies_df["shell_risk_score"] >= 25]
    entity_pairs = []
    alert_specs = []

    for _, row in flagged.iterrows():
        company_name = str(row.get("CompanyName", "UNKNOWN"))
        cin = str(row.get("CIN", ""))
        risk_score = float(row.get("shell_risk_score", 0))
        risk_level = "HIGH" if risk_score >= 50 else ("MEDIUM" if risk_score >= 25 else "LOW")

        entity_pairs.append(("COMPANY", company_name))

        explanations = []
        if row.get("address_cluster_flag", 0):
            explanations.append(("ADDRESS_CLUSTER",
                f"{company_name} (CIN: {cin}): shares address with {int(row.get('address_cluster_size', 0))} others",
                {"cluster_size": int(row.get("address_cluster_size", 0))}))
        if row.get("low_capital_flag", 0):
            explanations.append(("LOW_CAPITAL",
                f"{company_name}: authorised capital below ₹1L",
                {"authorized_capital": float(row.get("AuthorizedCapital", 0))}))
        if row.get("young_company_flag", 0):
            explanations.append(("YOUNG_COMPANY",
                f"{company_name}: incorporated < 1 year ago",
                {"date_of_registration": str(row.get("DateOfRegistration", ""))}))
        if row.get("inactive_flag", 0):
            explanations.append(("INACTIVE",
                f"{company_name}: status {row.get('CompanyStatus', 'inactive')}",
                {"status": str(row.get("CompanyStatus", ""))}))
        if row.get("high_auth_paid_ratio", 0):
            explanations.append(("HIGH_AUTH_PAID_RATIO",
                f"{company_name}: extremely high auth/paid ratio (shell indicator)",
                {"authorized_capital": float(row.get("AuthorizedCapital", 0)),
                 "paid_up_capital": float(row.get("PaidUpCapital", 0))}))
        if row.get("opc_flag", 0):
            explanations.append(("ONE_PERSON_COMPANY",
                f"{company_name}: One Person Company",
                {"company_class": str(row.get("CompanyClass", ""))}))
        if not explanations:
            explanations.append(("SHELL_COMPOSITE",
                f"{company_name}: shell risk {risk_score:.1f}/100",
                {"shell_risk_score": risk_score}))

        alert_specs.append({
            "entity_key": ("COMPANY", company_name),
            "risk_score": round(risk_score / 100, 4),
            "risk_level": risk_level,
            "explanations": explanations,
        })

    return entity_pairs, alert_specs


def build_bond_alert_data(bond_flows_df):
    if bond_flows_df.empty:
        return [], [], []

    agg = bond_flows_df.groupby("purchaser_name").agg(
        total_value=("total_value", "sum"),
        total_bonds=("total_bonds", "sum"),
        parties=("party_name", lambda x: list(x.unique())),
    ).reset_index().sort_values("total_value", ascending=False)

    entity_pairs = []
    alert_specs = []
    edge_specs = []

    for _, row in agg.iterrows():
        name = str(row["purchaser_name"])
        val = float(row["total_value"])
        val_cr = val / 1e7
        if val_cr < 1:
            continue

        risk_score = min(val_cr / 1000, 1.0)
        risk_level = "HIGH" if val_cr >= 50 else ("MEDIUM" if val_cr >= 10 else "LOW")
        parties = row["parties"]

        entity_pairs.append(("BOND_PURCHASER", name))

        alert_specs.append({
            "entity_key": ("BOND_PURCHASER", name),
            "risk_score": round(risk_score, 4),
            "risk_level": risk_level,
            "explanations": [("ELECTORAL_BOND",
                f"{name}: {int(row['total_bonds'])} bonds worth ₹{val_cr:.1f}Cr to {len(parties)} parties: {', '.join(parties[:5])}",
                {"total_value": val, "total_bonds": int(row["total_bonds"]), "parties": parties})],
        })

    # Relationship edges (purchaser → party)
    for _, row in bond_flows_df.iterrows():
        purchaser = str(row["purchaser_name"])
        party = str(row["party_name"])
        val = float(row.get("total_value", 0))
        entity_pairs.append(("BOND_PURCHASER", purchaser))
        entity_pairs.append(("POLITICAL_PARTY", party))
        edge_specs.append((purchaser, party, val))

    return entity_pairs, alert_specs, edge_specs


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

def main():
    print("═" * 60)
    print("  STREAM — Populate Risk Alerts in Neon DB")
    print("═" * 60)

    print("\n[1/6] Loading precomputed data …")
    data = load_data()

    # ── Build all data in-memory (no DB) ──────
    print("\n[2/6] Building alert data in memory …")
    t_ents, t_alerts = build_tender_alert_data(data["procurement"])
    print(f"  Tender alerts: {len(t_alerts)}")

    s_ents, s_alerts = build_shell_alert_data(data["companies"])
    print(f"  Shell company alerts: {len(s_alerts)}")

    b_ents, b_alerts, b_edges = build_bond_alert_data(data["bond_flows"])
    print(f"  Bond alerts: {len(b_alerts)}, edges: {len(b_edges)}")

    all_entity_pairs = t_ents + s_ents + b_ents
    all_alert_specs = t_alerts + s_alerts + b_alerts
    print(f"  Total entities to ensure: {len(set((t, n.strip().upper()) for t, n in all_entity_pairs))}")
    print(f"  Total alerts to insert: {len(all_alert_specs)}")

    # ── DB operations ─────────────────────────
    print(f"\n[3/6] Connecting to Neon DB …")
    conn = psycopg.connect(DB_URL)

    try:
        with conn.cursor() as cur:
            print("\n[4/6] Clearing old data …")
            cur.execute("DELETE FROM risk_explanation")
            cur.execute("DELETE FROM risk_alert")
            cur.execute("DELETE FROM relationship_edge")
            # Widen weight column to handle large rupee values
            cur.execute("ALTER TABLE relationship_edge ALTER COLUMN weight TYPE NUMERIC(20,4)")
            conn.commit()
            print("  ✓ Cleared")

            print("\n[5/6] Bulk-inserting entities …")
            bulk_ensure_entities(cur, all_entity_pairs)
            conn.commit()
            print(f"  ✓ {len(_entity_cache)} entities in cache")

            print("\n[6/6] Batch-inserting alerts + explanations …")
            now = datetime.now(timezone.utc)

            # Build alert tuples
            alert_tuples = []
            for spec in all_alert_specs:
                eid = get_entity_id(*spec["entity_key"])
                alert_tuples.append((eid, spec["risk_score"], spec["risk_level"], now))

            # Batch-insert alerts
            alert_ids = batch_insert_alerts(cur, alert_tuples)
            conn.commit()
            print(f"  ✓ {len(alert_ids)} alerts inserted")

            # Build explanation tuples
            explanation_tuples = []
            for alert_id, spec in zip(alert_ids, all_alert_specs):
                for rule, reason, metrics in spec["explanations"]:
                    explanation_tuples.append((alert_id, rule, reason, json.dumps(metrics)))

            batch_insert_explanations(cur, explanation_tuples)
            conn.commit()
            print(f"  ✓ {len(explanation_tuples)} explanations inserted")

            # Relationship edges
            if b_edges:
                print("  Inserting relationship edges …")
                edge_tuples = []
                for purchaser, party, val in b_edges:
                    src = get_entity_id("BOND_PURCHASER", purchaser)
                    dst = get_entity_id("POLITICAL_PARTY", party)
                    edge_tuples.append((src, dst, val, f"Bond: {purchaser} → {party}"))

                for i in range(0, len(edge_tuples), BATCH_SIZE):
                    batch = edge_tuples[i : i + BATCH_SIZE]
                    placeholders = []
                    args = []
                    for src, dst, val, ref in batch:
                        placeholders.append("(%s, %s, 'ELECTORAL_BOND_FLOW', %s, %s)")
                        args.extend([src, dst, round(val, 4), ref])
                    cur.execute(
                        "INSERT INTO relationship_edge (src_entity_id, dst_entity_id, edge_type, weight, evidence_ref) VALUES "
                        + ", ".join(placeholders),
                        args,
                    )
                conn.commit()
                print(f"  ✓ {len(edge_tuples)} edges inserted")

            # Summary
            cur.execute("SELECT COUNT(*) FROM entity")
            n_ent = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM risk_alert")
            n_alert = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM risk_explanation")
            n_exp = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM relationship_edge")
            n_edge = cur.fetchone()[0]

    finally:
        conn.close()

    print("\n" + "═" * 60)
    print("  DONE")
    print(f"  Entities:      {n_ent}")
    print(f"  Risk Alerts:   {n_alert}")
    print(f"  Explanations:  {n_exp}")
    print(f"  Relationships: {n_edge}")
    print("═" * 60)


if __name__ == "__main__":
    main()

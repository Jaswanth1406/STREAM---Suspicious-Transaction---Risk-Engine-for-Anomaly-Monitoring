"""
STREAM — Entity Resolution Module
Links entities across three data domains:
  1. Procurement buyers (government departments)
  2. Electoral bond purchasers (companies/individuals)
  3. Company registry (MCA registered companies)

Also resolves bond purchaser → political party connections.

Matching approach:
  - Exact normalised match (lowercase, stripped, common suffixes removed)
  - Token-overlap match (Jaccard similarity ≥ 0.6)

Output: outputs/entity_matches.csv
"""

import os
import re
import pandas as pd
import numpy as np
from collections import defaultdict

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

COMPANIES_CSV = "datasets/companies.csv"
DOWNLOAD_CSV = "data_ingestion/download.csv"
REDEMPTION_CSV = "data_ingestion/redemption.csv"
PROCUREMENT_CSV = "output_datasets/procurement_risk_scores.csv"
OUTPUT_DIR = "outputs"
MATCH_THRESHOLD = 0.55  # Jaccard token overlap threshold

# Common suffixes/noise to strip for matching
STRIP_SUFFIXES = [
    r"\bprivate\b", r"\blimited\b", r"\bpvt\b", r"\bltd\b",
    r"\bllp\b", r"\bopc\b", r"\binc\b", r"\bcorp\b",
    r"\bcompany\b", r"\benterprises\b", r"\bgroup\b",
    r"\bfoundation\b", r"\btrust\b",
]


# ─────────────────────────────────────────────
# NAME NORMALISATION
# ─────────────────────────────────────────────

def normalise_name(name: str) -> str:
    """Normalise entity name for matching."""
    if not isinstance(name, str):
        return ""
    name = name.lower().strip()
    # Remove punctuation except spaces
    name = re.sub(r"[^a-z0-9\s]", " ", name)
    # Remove common suffixes
    for pattern in STRIP_SUFFIXES:
        name = re.sub(pattern, "", name)
    # Collapse whitespace
    name = re.sub(r"\s+", " ", name).strip()
    return name


def tokenise(name: str) -> set:
    """Get set of significant tokens from a normalised name."""
    tokens = name.split()
    return set(t for t in tokens if len(t) > 1)


def jaccard_similarity(set_a: set, set_b: set) -> float:
    """Compute Jaccard similarity between two token sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


# ─────────────────────────────────────────────
# BUILD INDEX FOR FAST MATCHING
# ─────────────────────────────────────────────

def build_inverted_index(names_with_ids: list) -> dict:
    """Build token → list of (id, name, token_set) index."""
    index = defaultdict(list)
    entries = []
    for entity_id, raw_name in names_with_ids:
        norm = normalise_name(raw_name)
        tokens = tokenise(norm)
        entry = (entity_id, raw_name, norm, tokens)
        entries.append(entry)
        for token in tokens:
            index[token].append(entry)
    return index, entries


def find_matches(query_name: str, index: dict, entries: list, threshold=MATCH_THRESHOLD, top_k=5):
    """Find best matches for a query name using the inverted index."""
    norm_query = normalise_name(query_name)
    query_tokens = tokenise(norm_query)

    if not query_tokens:
        return []

    # Exact normalised match first
    for entry in entries:
        if entry[2] == norm_query:
            return [(entry[0], entry[1], 1.0)]

    # Gather candidates via inverted index (token overlap)
    candidate_scores = defaultdict(float)
    candidate_map = {}
    for token in query_tokens:
        for entry in index.get(token, []):
            eid = entry[0]
            if eid not in candidate_map:
                candidate_map[eid] = entry
                candidate_scores[eid] = jaccard_similarity(query_tokens, entry[3])

    # Filter and sort
    results = [
        (eid, candidate_map[eid][1], score)
        for eid, score in candidate_scores.items()
        if score >= threshold
    ]
    results.sort(key=lambda x: x[2], reverse=True)
    return results[:top_k]


# ─────────────────────────────────────────────
# MAIN ENTITY RESOLUTION
# ─────────────────────────────────────────────

def resolve_entities():
    """Run entity resolution across all three data domains."""

    print(f"\n{'='*60}")
    print(f"  STREAM — Entity Resolution")
    print(f"{'='*60}")

    # ── Load all entity sources ───────────────
    companies = pd.read_csv(COMPANIES_CSV)
    downloads = pd.read_csv(DOWNLOAD_CSV)
    redemptions = pd.read_csv(REDEMPTION_CSV)
    procurement = pd.read_csv(PROCUREMENT_CSV)

    # Unique entities per domain
    company_names = list(zip(companies["CIN"], companies["CompanyName"]))
    bond_purchasers = list(set(zip(
        downloads["purchaser_name"],
        downloads["purchaser_name"]
    )))
    # Use purchaser_name as both id and name
    bond_purchasers = [(name, name) for _, name in bond_purchasers]
    procurement_buyers = list(set(
        (name, name) for name in procurement["buyer/name"].unique()
    ))
    party_names = list(set(
        (name, name) for name in redemptions["party_name"].unique()
    ))

    print(f"  Companies: {len(company_names)}")
    print(f"  Bond purchasers: {len(bond_purchasers)}")
    print(f"  Procurement buyers: {len(procurement_buyers)}")
    print(f"  Political parties: {len(party_names)}")

    # ── Build company index ───────────────────
    print("\n  Building company name index...")
    company_index, company_entries = build_inverted_index(company_names)

    # ── Match 1: Bond Purchasers → Companies ──
    print("  Matching bond purchasers → companies...")
    purchaser_to_company = []
    for pid, pname in bond_purchasers:
        matches = find_matches(pname, company_index, company_entries, threshold=MATCH_THRESHOLD)
        for cin, cname, score in matches:
            purchaser_to_company.append({
                "purchaser_name": pname,
                "matched_cin": cin,
                "matched_company_name": cname,
                "match_score": round(score, 4),
                "match_type": "bond_purchaser_to_company",
            })

    df_p2c = pd.DataFrame(purchaser_to_company)
    print(f"    Found {len(df_p2c)} purchaser→company matches")

    # ── Match 2: Procurement Buyers → Companies ──
    print("  Matching procurement buyers → companies...")
    buyer_to_company = []
    for bid, bname in procurement_buyers:
        matches = find_matches(bname, company_index, company_entries, threshold=MATCH_THRESHOLD)
        for cin, cname, score in matches:
            buyer_to_company.append({
                "buyer_name": bname,
                "matched_cin": cin,
                "matched_company_name": cname,
                "match_score": round(score, 4),
                "match_type": "procurement_buyer_to_company",
            })

    df_b2c = pd.DataFrame(buyer_to_company)
    print(f"    Found {len(df_b2c)} buyer→company matches")

    # ── Build bond flow table: Purchaser → Party ──
    print("  Building bond flow table (purchaser → party)...")
    # Link purchasers to parties via bond prefix+number
    bond_flows = downloads.merge(
        redemptions,
        on=["prefix", "bond_number"],
        how="inner",
        suffixes=("_purchase", "_redeem"),
    )
    # Parse denomination (Indian format: "1,00,000" etc.)
    def parse_denomination(val):
        if isinstance(val, str):
            return int(val.replace(",", ""))
        return int(val) if pd.notna(val) else 0

    bond_flows["denomination_value"] = bond_flows["denomination_purchase"].apply(parse_denomination)

    # Aggregate: purchaser → party flow
    political_flows = bond_flows.groupby(
        ["purchaser_name", "party_name"]
    ).agg(
        total_bonds=("bond_number", "count"),
        total_value=("denomination_value", "sum"),
        first_date=("purchase_date", "min"),
        last_date=("purchase_date", "max"),
    ).reset_index()

    print(f"    Found {len(political_flows)} purchaser→party connections")
    print(f"    Total bond value: ₹{political_flows['total_value'].sum()/1e7:.0f} Cr")

    # ── Save outputs ──────────────────────────
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Save match tables
    if not df_p2c.empty:
        df_p2c.to_csv(os.path.join(OUTPUT_DIR, "entity_matches_purchaser_company.csv"), index=False)
    if not df_b2c.empty:
        df_b2c.to_csv(os.path.join(OUTPUT_DIR, "entity_matches_buyer_company.csv"), index=False)

    political_flows.to_csv(os.path.join(OUTPUT_DIR, "political_bond_flows.csv"), index=False)

    # ── Build unified entity table ────────────
    # All resolved entities with their types and cross-references
    entity_records = []

    # Companies
    for _, row in companies.iterrows():
        entity_records.append({
            "entity_id": row["CIN"],
            "entity_name": row["CompanyName"],
            "entity_type": "COMPANY",
            "source": "companies_registry",
        })

    # Procurement buyers
    for _, bname in procurement_buyers:
        entity_records.append({
            "entity_id": f"BUYER_{normalise_name(bname)[:50]}",
            "entity_name": bname,
            "entity_type": "PROCUREMENT_BUYER",
            "source": "procurement_data",
        })

    # Political parties
    for _, pname in party_names:
        entity_records.append({
            "entity_id": f"PARTY_{normalise_name(pname)[:50]}",
            "entity_name": pname,
            "entity_type": "POLITICAL_PARTY",
            "source": "electoral_bonds",
        })

    df_entities = pd.DataFrame(entity_records)
    df_entities.to_csv(os.path.join(OUTPUT_DIR, "entity_registry.csv"), index=False)
    print(f"\n  Saved entity registry: {len(df_entities)} entities")

    # Summary
    print(f"\n  Outputs saved to {OUTPUT_DIR}/:")
    print(f"    entity_matches_purchaser_company.csv  ({len(df_p2c)} matches)")
    print(f"    entity_matches_buyer_company.csv      ({len(df_b2c)} matches)")
    print(f"    political_bond_flows.csv              ({len(political_flows)} flows)")
    print(f"    entity_registry.csv                   ({len(df_entities)} entities)")

    return df_p2c, df_b2c, political_flows, df_entities


if __name__ == "__main__":
    resolve_entities()

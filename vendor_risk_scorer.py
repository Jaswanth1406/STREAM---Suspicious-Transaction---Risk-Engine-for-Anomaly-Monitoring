"""
STREAM — Composite Vendor Risk Scorer
Combines four risk dimensions into a single vendor profile:
  1. Bid Pattern Score     — from tender anomaly flags
  2. Shell Risk Score      — from company risk scoring
  3. Political Score       — from electoral bond flows
  4. Financials Score      — from company capitalization and status

Also computes per-vendor connections (political, co-bidder, address-cluster).

Output: outputs/vendor_profiles.json
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

COMPANY_RISK_CSV = "outputs/company_risk_table.csv"
PROCUREMENT_CSV = "output_datasets/procurement_risk_scores.csv"
PREDICTIONS_DIR = "output_datasets"
BOND_FLOWS_CSV = "outputs/political_bond_flows.csv"
ENTITY_MATCHES_P2C = "outputs/entity_matches_purchaser_company.csv"
ENTITY_MATCHES_B2C = "outputs/entity_matches_buyer_company.csv"
OUTPUT_DIR = "outputs"

# Sub-score weights (sum = 100)
DIMENSION_WEIGHTS = {
    "bid_pattern": 30,
    "shell_risk": 25,
    "political": 25,
    "financials": 20,
}


# ─────────────────────────────────────────────
# 1. BID PATTERN SCORING
# ─────────────────────────────────────────────

def compute_bid_pattern_scores(procurement_df):
    """
    Per-buyer bid pattern risk score (0-100) based on:
    - % of single-bidder tenders
    - % of short-window tenders
    - % high-value tenders
    - Average anomaly score (ML)
    - Average risk_score from rule engine
    """
    buyer_stats = procurement_df.groupby("buyer/name").agg(
        total_tenders=("ocid", "count"),
        single_bidder_count=("flag_single_bidder", "sum"),
        zero_bidder_count=("flag_zero_bidders", "sum"),
        short_window_count=("flag_short_window", "sum"),
        non_open_count=("flag_non_open", "sum"),
        high_value_count=("flag_high_value", "sum"),
        buyer_conc_count=("flag_buyer_concentration", "sum"),
        round_amount_count=("flag_round_amount", "sum"),
        ml_anomaly_count=("ml_anomaly_flag", "sum"),
        avg_anomaly_score=("anomaly_score", "mean"),
        avg_risk_score=("risk_score", "mean"),
        max_risk_score=("risk_score", "max"),
        total_amount=("amount", "sum"),
        avg_amount=("amount", "mean"),
    ).reset_index()

    # Compute ratios
    n = buyer_stats["total_tenders"]
    buyer_stats["single_bid_pct"] = buyer_stats["single_bidder_count"] / n
    buyer_stats["short_window_pct"] = buyer_stats["short_window_count"] / n
    buyer_stats["high_value_pct"] = buyer_stats["high_value_count"] / n
    buyer_stats["anomaly_pct"] = buyer_stats["ml_anomaly_count"] / n

    # Composite bid pattern score: weighted combination
    buyer_stats["bid_pattern_score"] = (
        buyer_stats["single_bid_pct"] * 35 +
        buyer_stats["short_window_pct"] * 15 +
        buyer_stats["high_value_pct"] * 15 +
        buyer_stats["anomaly_pct"] * 15 +
        (buyer_stats["avg_risk_score"] / 100) * 20
    ).clip(0, 100).round(2)

    return buyer_stats


# ─────────────────────────────────────────────
# 2. POLITICAL CONNECTION SCORING
# ─────────────────────────────────────────────

def compute_political_scores(bond_flows_df, entity_matches_p2c_df):
    """
    Political connection score for companies based on:
    - Number of distinct parties funded
    - Total bond value donated
    - Recency of donations
    """
    if bond_flows_df.empty:
        return pd.DataFrame(columns=["entity_name", "political_score", "parties_funded",
                                      "total_bond_value", "political_connections"])

    # Aggregate per purchaser
    purchaser_stats = bond_flows_df.groupby("purchaser_name").agg(
        parties_funded=("party_name", "nunique"),
        total_bond_value=("total_value", "sum"),
        total_bonds=("total_bonds", "sum"),
        party_list=("party_name", lambda x: list(x.unique())),
    ).reset_index()

    # Normalise to 0-100 score
    max_value = purchaser_stats["total_bond_value"].max()
    max_parties = purchaser_stats["parties_funded"].max()

    purchaser_stats["value_score"] = (
        purchaser_stats["total_bond_value"] / (max_value + 1) * 60
    )
    purchaser_stats["diversity_score"] = (
        purchaser_stats["parties_funded"] / (max_parties + 1) * 40
    )
    purchaser_stats["political_score"] = (
        purchaser_stats["value_score"] + purchaser_stats["diversity_score"]
    ).clip(0, 100).round(2)

    # Build connections list
    connections = []
    for _, row in purchaser_stats.iterrows():
        for party in row["party_list"]:
            party_value = bond_flows_df[
                (bond_flows_df["purchaser_name"] == row["purchaser_name"]) &
                (bond_flows_df["party_name"] == party)
            ]["total_value"].sum()
            connections.append({
                "source": row["purchaser_name"],
                "target": party,
                "type": "electoral_bond",
                "value": int(party_value),
                "label": f"₹{party_value/1e7:.1f}Cr" if party_value >= 1e7 else f"₹{party_value/1e5:.1f}L",
            })

    # Map to CINs via entity matches
    political_by_cin = {}
    if entity_matches_p2c_df is not None and not entity_matches_p2c_df.empty:
        merged = entity_matches_p2c_df.merge(
            purchaser_stats,
            on="purchaser_name",
            how="inner",
        )
        for _, row in merged.iterrows():
            cin = row["matched_cin"]
            if cin not in political_by_cin or row["political_score"] > political_by_cin[cin]["political_score"]:
                political_by_cin[cin] = {
                    "political_score": row["political_score"],
                    "parties_funded": int(row["parties_funded"]),
                    "total_bond_value": int(row["total_bond_value"]),
                    "purchaser_name": row["purchaser_name"],
                }

    return purchaser_stats, connections, political_by_cin


# ─────────────────────────────────────────────
# 3. FINANCIALS SCORING
# ─────────────────────────────────────────────

def compute_financial_scores(company_df):
    """
    Financial risk score per company (0-100) based on:
    - Paid-up capital adequacy
    - Auth/Paid ratio (over-leveraged shell indicator)
    - Company status (inactive = risk)
    - Company age
    """
    df = company_df.copy()

    # Capital adequacy (lower = riskier)
    capital_pct = df["capital_percentile_rank"].fillna(0.5)
    df["capital_risk"] = ((1 - capital_pct) * 30).clip(0, 30)

    # Auth/paid ratio risk
    df["ratio_risk"] = (df["high_auth_paid_ratio"] * 25).clip(0, 25)

    # Status risk
    df["status_risk"] = (df["inactive_flag"] * 25).clip(0, 25)

    # Age risk (younger = riskier)
    df["age_risk"] = (df["young_company_flag"] * 20).clip(0, 20)

    df["financials_score"] = (
        df["capital_risk"] + df["ratio_risk"] + df["status_risk"] + df["age_risk"]
    ).clip(0, 100).round(2)

    return df[["CIN", "CompanyName", "financials_score"]].set_index("CIN")


# ─────────────────────────────────────────────
# 4. COMPOSITE VENDOR PROFILE
# ─────────────────────────────────────────────

def build_vendor_profiles():
    """Build comprehensive vendor profiles combining all risk dimensions."""

    print(f"\n{'='*60}")
    print(f"  STREAM — Composite Vendor Risk Profiler")
    print(f"{'='*60}")

    # ── Load all data ─────────────────────────
    company_df = pd.read_csv(COMPANY_RISK_CSV)
    procurement_df = pd.read_csv(PROCUREMENT_CSV)
    print(f"  Companies: {len(company_df)}, Tenders: {len(procurement_df)}")

    # Load entity matches
    try:
        entity_p2c = pd.read_csv(ENTITY_MATCHES_P2C)
    except FileNotFoundError:
        entity_p2c = pd.DataFrame()

    try:
        entity_b2c = pd.read_csv(ENTITY_MATCHES_B2C)
    except FileNotFoundError:
        entity_b2c = pd.DataFrame()

    try:
        bond_flows = pd.read_csv(BOND_FLOWS_CSV)
    except FileNotFoundError:
        bond_flows = pd.DataFrame()

    # ── Compute sub-scores ────────────────────
    print("  Computing bid pattern scores...")
    buyer_stats = compute_bid_pattern_scores(procurement_df)

    print("  Computing political connection scores...")
    political_stats, political_connections, political_by_cin = compute_political_scores(
        bond_flows, entity_p2c
    )

    print("  Computing financial scores...")
    financial_scores = compute_financial_scores(company_df)

    # ── Build per-vendor profiles ─────────────
    print("  Building vendor profiles...")
    profiles = {}

    for _, row in company_df.iterrows():
        cin = row["CIN"]
        name = row["CompanyName"]

        # Shell risk (already computed)
        shell_score = float(row["shell_risk_score"])

        # Bid pattern — check if company is a procurement buyer
        bid_score = 0.0
        bid_stats = {}
        if not entity_b2c.empty:
            matched = entity_b2c[entity_b2c["matched_cin"] == cin]
            if not matched.empty:
                buyer_name = matched.iloc[0]["buyer_name"]
                buyer_row = buyer_stats[buyer_stats["buyer/name"] == buyer_name]
                if not buyer_row.empty:
                    bid_score = float(buyer_row.iloc[0]["bid_pattern_score"])
                    bid_stats = {
                        "total_tenders": int(buyer_row.iloc[0]["total_tenders"]),
                        "single_bid_pct": round(float(buyer_row.iloc[0]["single_bid_pct"]), 3),
                        "avg_risk_score": round(float(buyer_row.iloc[0]["avg_risk_score"]), 2),
                        "total_amount": float(buyer_row.iloc[0]["total_amount"]),
                    }

        # Political
        political_score = 0.0
        political_info = {}
        if cin in political_by_cin:
            political_score = float(political_by_cin[cin]["political_score"])
            political_info = political_by_cin[cin]

        # Financials
        fin_score = 0.0
        if cin in financial_scores.index:
            fin_score = float(financial_scores.loc[cin, "financials_score"])

        # Composite score
        composite = (
            bid_score * DIMENSION_WEIGHTS["bid_pattern"] / 100 +
            shell_score * DIMENSION_WEIGHTS["shell_risk"] / 100 +
            political_score * DIMENSION_WEIGHTS["political"] / 100 +
            fin_score * DIMENSION_WEIGHTS["financials"] / 100
        )
        composite = round(min(composite, 100), 2)

        # Risk tier
        if composite >= 60:
            risk_tier = "HIGH"
        elif composite >= 30:
            risk_tier = "MEDIUM"
        else:
            risk_tier = "LOW"

        # Connections
        connections = []
        # Political connections
        if cin in political_by_cin:
            pname = political_by_cin[cin].get("purchaser_name", "")
            for conn in political_connections:
                if conn["source"] == pname:
                    connections.append(conn)

        # Address cluster connections
        if row["address_cluster_size"] >= 2:
            connections.append({
                "type": "shared_address",
                "cluster_size": int(row["address_cluster_size"]),
                "label": f"Shares address with {int(row['address_cluster_size'])-1} companies",
            })

        profiles[cin] = {
            "cin": cin,
            "company_name": name,
            "company_status": row.get("CompanyStatus", "Unknown"),
            "state": row.get("CompanyStateCode", ""),
            "composite_risk_score": composite,
            "risk_tier": risk_tier,
            "sub_scores": {
                "bid_pattern": round(bid_score, 2),
                "shell_risk": round(shell_score, 2),
                "political": round(political_score, 2),
                "financials": round(fin_score, 2),
            },
            "bid_stats": bid_stats,
            "political_info": political_info,
            "shell_explanation": row.get("explanation", ""),
            "connections": connections,
            "requires_human_review": composite >= 25,
        }

    # ── Also create profiles for procurement buyers without CIN ──
    for _, brow in buyer_stats.iterrows():
        buyer_name = brow["buyer/name"]
        # Check if already matched to a CIN
        if not entity_b2c.empty:
            if buyer_name in entity_b2c["buyer_name"].values:
                continue  # already handled above

        bid_score = float(brow["bid_pattern_score"])
        entity_id = f"BUYER_{buyer_name[:60]}"

        profiles[entity_id] = {
            "cin": None,
            "company_name": buyer_name,
            "company_status": "Government Entity",
            "state": "",
            "composite_risk_score": round(bid_score * DIMENSION_WEIGHTS["bid_pattern"] / 100, 2),
            "risk_tier": "HIGH" if bid_score >= 60 else ("MEDIUM" if bid_score >= 30 else "LOW"),
            "sub_scores": {
                "bid_pattern": round(bid_score, 2),
                "shell_risk": 0,
                "political": 0,
                "financials": 0,
            },
            "bid_stats": {
                "total_tenders": int(brow["total_tenders"]),
                "single_bid_pct": round(float(brow["single_bid_pct"]), 3),
                "avg_risk_score": round(float(brow["avg_risk_score"]), 2),
                "total_amount": float(brow["total_amount"]),
            },
            "political_info": {},
            "shell_explanation": "",
            "connections": [],
            "requires_human_review": bid_score >= 25,
        }

    # ── Save profiles ─────────────────────────
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(os.path.join(OUTPUT_DIR, "vendor_profiles.json"), "w") as f:
        json.dump(profiles, f, indent=2, default=str)

    # Also save a flat CSV summary for quick lookups
    summary_rows = []
    for pid, p in profiles.items():
        summary_rows.append({
            "entity_id": pid,
            "company_name": p["company_name"],
            "cin": p["cin"],
            "composite_risk_score": p["composite_risk_score"],
            "risk_tier": p["risk_tier"],
            "bid_pattern_score": p["sub_scores"]["bid_pattern"],
            "shell_risk_score": p["sub_scores"]["shell_risk"],
            "political_score": p["sub_scores"]["political"],
            "financials_score": p["sub_scores"]["financials"],
            "num_connections": len(p["connections"]),
            "requires_human_review": p["requires_human_review"],
        })

    df_summary = pd.DataFrame(summary_rows).sort_values("composite_risk_score", ascending=False)
    df_summary.to_csv(os.path.join(OUTPUT_DIR, "vendor_risk_summary.csv"), index=False)

    # ── Summary stats ─────────────────────────
    tiers = df_summary["risk_tier"].value_counts().to_dict()
    print(f"\n  Vendor Risk Distribution:")
    print(f"    🔴 HIGH:   {tiers.get('HIGH', 0)}")
    print(f"    🟡 MEDIUM: {tiers.get('MEDIUM', 0)}")
    print(f"    🟢 LOW:    {tiers.get('LOW', 0)}")
    print(f"    Total profiles: {len(profiles)}")
    print(f"\n  Political connections found: {len([p for p in profiles.values() if p['sub_scores']['political'] > 0])}")
    print(f"  Profiles with bid data: {len([p for p in profiles.values() if p['sub_scores']['bid_pattern'] > 0])}")

    print(f"\n  Saved → {OUTPUT_DIR}/vendor_profiles.json")
    print(f"  Saved → {OUTPUT_DIR}/vendor_risk_summary.csv")

    return profiles


if __name__ == "__main__":
    build_vendor_profiles()

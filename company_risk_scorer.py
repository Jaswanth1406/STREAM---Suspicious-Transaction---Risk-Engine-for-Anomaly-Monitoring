"""
STREAM — Company / Shell-Company Risk Scorer
Scores ALL companies in the registry for shell-company indicators.

Flags
─────
  1. address_cluster_flag   — ≥3 companies at the same normalised address
  2. low_capital_flag       — Paid-up capital in lowest quartile
  3. young_company_flag     — Incorporated < 2 years ago
  4. inactive_flag          — Status is Strike Off / Dissolved / Dormant etc.
  5. high_auth_paid_ratio   — AuthorizedCapital >> PaidupCapital (5×+)
  6. opc_flag               — One-Person Company class (higher shell risk)

Output: outputs/company_risk_table.csv
"""

import os
import re
import numpy as np
import pandas as pd
import networkx as nx
from datetime import datetime

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

COMPANIES_CSV = "datasets/companies.csv"
OUTPUT_DIR = "outputs"
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "company_risk_table.csv")
NETWORK_FILE = os.path.join(OUTPUT_DIR, "company_network.gpickle")

# Today's date for age computation
TODAY = datetime.now()

# Shell risk weights (sum = 100)
WEIGHTS = {
    "address_cluster_flag": 20,
    "low_capital_flag": 15,
    "young_company_flag": 10,
    "inactive_flag": 20,
    "high_auth_paid_ratio": 15,
    "opc_flag": 10,
    "degree_centrality_score": 10,  # from address-based network
}


# ─────────────────────────────────────────────
# ADDRESS NORMALISATION
# ─────────────────────────────────────────────

def normalise_address(addr: str) -> str:
    """Reduce address to a fuzzy-matchable key (pincode + city-ish tokens)."""
    if not isinstance(addr, str):
        return ""
    addr = addr.lower().strip()
    # Extract pincode (6-digit Indian PIN)
    pin_match = re.search(r"\b(\d{6})\b", addr)
    pincode = pin_match.group(1) if pin_match else ""
    # Remove common noise
    for noise in ["india", "c/o", "s/o", "d/o", "w/o", "near", "opp", "behind"]:
        addr = addr.replace(noise, "")
    # Keep only alphanumeric tokens
    tokens = re.findall(r"[a-z]+", addr)
    # Build key from pincode + sorted significant tokens (>3 chars)
    sig_tokens = sorted(set(t for t in tokens if len(t) > 3))
    return pincode + "|" + ",".join(sig_tokens[:5])


# ─────────────────────────────────────────────
# MAIN SCORER
# ─────────────────────────────────────────────

def score_companies(companies_csv=COMPANIES_CSV):
    """Score all companies for shell-company risk indicators."""

    print(f"\n{'='*60}")
    print(f"  STREAM — Company Shell Risk Scorer")
    print(f"{'='*60}")

    df = pd.read_csv(companies_csv)
    print(f"  Loaded {len(df)} companies from {companies_csv}")

    # ── 1. Parse & clean ──────────────────────
    df["PaidupCapital"] = pd.to_numeric(df["PaidupCapital"], errors="coerce").fillna(0)
    df["AuthorizedCapital"] = pd.to_numeric(df["AuthorizedCapital"], errors="coerce").fillna(0)
    df["reg_date"] = pd.to_datetime(df["CompanyRegistrationdate_date"], errors="coerce")
    df["age_days"] = (TODAY - df["reg_date"]).dt.days.fillna(0).astype(int)

    # ── 2. Address clustering ─────────────────
    df["addr_key"] = df["Registered_Office_Address"].apply(normalise_address)
    addr_counts = df["addr_key"].value_counts()
    df["address_cluster_size"] = df["addr_key"].map(addr_counts).fillna(1).astype(int)
    df["address_cluster_flag"] = (df["address_cluster_size"] >= 3).astype(int)

    # ── 3. Capital flags ──────────────────────
    q25 = df.loc[df["PaidupCapital"] > 0, "PaidupCapital"].quantile(0.25)
    df["capital_percentile_rank"] = df["PaidupCapital"].rank(pct=True).round(4)
    df["low_capital_flag"] = ((df["PaidupCapital"] <= q25) & (df["PaidupCapital"] >= 0)).astype(int)

    # Auth/Paid ratio flag
    df["auth_paid_ratio"] = df["AuthorizedCapital"] / (df["PaidupCapital"] + 1)
    df["high_auth_paid_ratio"] = (df["auth_paid_ratio"] >= 5).astype(int)

    # ── 4. Age flag ───────────────────────────
    df["young_company_flag"] = (df["age_days"] < 730).astype(int)  # < 2 years

    # ── 5. Status flag ────────────────────────
    inactive_statuses = [
        "Strike Off", "Dissolved (Liquidated)", "Under Liquidation",
        "Under process of striking off", "Dormant under section 455",
        "Dissolved under section 54", "Dissolved under section 59(8)",
        "Strike Off-AwaitingPublication", "Inactive for e-filing",
    ]
    df["inactive_flag"] = df["CompanyStatus"].isin(inactive_statuses).astype(int)
    # Also encode a numeric status flag: 0=Active, 1=Inactive
    df["status_flag"] = df["inactive_flag"]

    # ── 6. OPC flag ───────────────────────────
    df["opc_flag"] = (df["CompanyClass"] == "One Person Company").astype(int)

    # ── 7. Address-based network & centrality ─
    print("  Building address-cluster network...")
    G = nx.Graph()
    for cin in df["CIN"]:
        G.add_node(cin)

    # Connect companies sharing the same address cluster (size >= 2)
    clusters = df[df["address_cluster_size"] >= 2].groupby("addr_key")["CIN"].apply(list)
    for addr_key, cins in clusters.items():
        if len(cins) > 1 and len(cins) <= 50:  # skip huge clusters (noise)
            for i in range(len(cins)):
                for j in range(i + 1, len(cins)):
                    G.add_edge(cins[i], cins[j], rel="same_address")

    centrality = nx.degree_centrality(G)
    df["degree_centrality"] = df["CIN"].map(centrality).fillna(0).round(6)
    # Normalise centrality to 0–1 for scoring
    max_cent = df["degree_centrality"].max()
    df["degree_centrality_score"] = (
        (df["degree_centrality"] / max_cent).fillna(0) if max_cent > 0 else 0
    )

    # ── 8. Composite shell risk score (0–100) ─
    score = sum(
        df[flag].clip(0, 1) * weight
        for flag, weight in WEIGHTS.items()
    )
    df["shell_risk_score"] = score.clip(0, 100).round(2)

    # ── 9. Explanation ────────────────────────
    def explain(row):
        reasons = []
        if row["address_cluster_flag"]:
            reasons.append(f"Address shared with {int(row['address_cluster_size'])-1} other companies")
        if row["low_capital_flag"]:
            reasons.append("Paid-up capital in lowest quartile")
        if row["young_company_flag"]:
            reasons.append(f"Recently incorporated ({int(row['age_days'])} days)")
        if row["inactive_flag"]:
            reasons.append(f"Company status: {row['CompanyStatus']}")
        if row["high_auth_paid_ratio"]:
            reasons.append(f"Auth/Paid capital ratio = {row['auth_paid_ratio']:.1f}x")
        if row["opc_flag"]:
            reasons.append("One-Person Company")
        if row["degree_centrality"] > 0.01:
            reasons.append(f"High network connectivity (centrality={row['degree_centrality']:.4f})")
        return "; ".join(reasons) if reasons else "No strong shell indicators"

    df["explanation"] = df.apply(explain, axis=1)
    df["requires_human_review"] = (df["shell_risk_score"] >= 20).apply(
        lambda x: "Requires Human Review" if x else "Auto-Cleared"
    )

    # ── 10. Save ──────────────────────────────
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    output_cols = [
        "CIN", "CompanyName", "CompanyStatus", "CompanyClass",
        "PaidupCapital", "AuthorizedCapital", "Registered_Office_Address",
        "CompanyStateCode", "nic_code", "CompanyIndustrialClassification",
        "reg_date", "age_days", "address_cluster_size", "capital_percentile_rank",
        "status_flag", "degree_centrality",
        "address_cluster_flag", "low_capital_flag", "young_company_flag",
        "inactive_flag", "high_auth_paid_ratio", "opc_flag",
        "shell_risk_score", "explanation", "requires_human_review",
    ]
    result = df[output_cols].sort_values("shell_risk_score", ascending=False)
    result.to_csv(OUTPUT_CSV, index=False)
    print(f"  Saved {len(result)} company risk scores → {OUTPUT_CSV}")

    # Save network
    nx.write_gml(G, os.path.join(OUTPUT_DIR, "company_network.gml"))
    print(f"  Saved company network ({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)")

    # ── Summary ───────────────────────────────
    high = (df["shell_risk_score"] >= 50).sum()
    med = ((df["shell_risk_score"] >= 25) & (df["shell_risk_score"] < 50)).sum()
    low = (df["shell_risk_score"] < 25).sum()
    print(f"\n  Shell Risk Distribution:")
    print(f"    🔴 High (≥50): {high}")
    print(f"    🟡 Medium (25–50): {med}")
    print(f"    🟢 Low (<25): {low}")
    print(f"    Address clusters (≥3): {df['address_cluster_flag'].sum()} companies")
    print(f"    Inactive companies: {df['inactive_flag'].sum()}")

    return result, G


if __name__ == "__main__":
    score_companies()

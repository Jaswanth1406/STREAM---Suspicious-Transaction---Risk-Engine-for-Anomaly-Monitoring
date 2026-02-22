"""
STREAM Agent Tool — Vendor / Company Investigation.

Look up vendor risk profiles, company shell-risk assessments, and
connection details by name, entity_id, or CIN.
"""

from langchain_core.tools import tool
from db import fetch_one, fetch_all


@tool
def investigate_vendor(query: str) -> str:
    """
    Investigate a vendor or company's risk profile.
    Searches by company name, entity_id, or CIN and returns the composite
    risk assessment including bid pattern risk, shell company risk,
    political connections, and financial risk.

    Use this when the auditor asks about a specific vendor or company —
    "Investigate vendor X", "What's the risk profile of company Y?",
    "Is company Z a shell company?"

    Args:
        query: A vendor name, entity_id, or CIN to look up.

    Returns:
        Full investigation report string.
    """
    sections = []

    # ── Search vendor_profile ──────────────────────
    vendor = fetch_one(
        """SELECT * FROM vendor_profile
           WHERE entity_id = %s OR cin = %s
           LIMIT 1""",
        (query, query),
    )

    if not vendor:
        # Fuzzy search
        vendors = fetch_all(
            """SELECT * FROM vendor_profile
               WHERE company_name ILIKE %s OR cin ILIKE %s OR entity_id ILIKE %s
               ORDER BY composite_risk_score DESC LIMIT 5""",
            (f"%{query}%", f"%{query}%", f"%{query}%"),
        )
        if vendors:
            vendor = vendors[0]
            if len(vendors) > 1:
                other_names = ", ".join(v["company_name"] for v in vendors[1:])
                sections.append(f"Note: Multiple matches found. Showing top result. Other matches: {other_names}")

    if vendor:
        composite = float(vendor.get("composite_risk_score") or 0)
        tier = vendor.get("risk_tier", "UNKNOWN")

        sections.append(f"=== VENDOR PROFILE: {vendor['company_name']} ===")
        sections.append(f"Entity ID: {vendor['entity_id']}")
        sections.append(f"CIN: {vendor.get('cin', 'N/A')}")
        sections.append(f"Composite Risk Score: {composite:.1f}/100 — Tier: {tier}")
        sections.append("")

        # Sub-scores
        sections.append("Risk Sub-Scores:")
        sections.append(f"  Bid Pattern Risk:    {float(vendor.get('bid_pattern_score') or 0):.1f}/100 (weight: 30%)")
        sections.append(f"  Shell Company Risk:  {float(vendor.get('shell_risk_sub_score') or 0):.1f}/100 (weight: 25%)")
        sections.append(f"  Political Risk:      {float(vendor.get('political_score') or 0):.1f}/100 (weight: 25%)")
        sections.append(f"  Financial Risk:      {float(vendor.get('financials_score') or 0):.1f}/100 (weight: 20%)")

        # Bid stats
        bid_stats = vendor.get("bid_stats") or {}
        if bid_stats:
            sections.append("")
            sections.append("Bid Statistics:")
            for k, v in bid_stats.items():
                sections.append(f"  {k}: {v}")

        # Political info
        political_info = vendor.get("political_info") or {}
        if political_info:
            sections.append("")
            sections.append("Political Connections:")
            for k, v in political_info.items():
                sections.append(f"  {k}: {v}")

        # Connections
        connections = vendor.get("connections") or []
        if connections:
            sections.append("")
            sections.append(f"Connections ({len(connections)} total):")
            for conn in connections[:10]:
                conn_type = conn.get("type", "unknown")
                target = conn.get("target", "unknown")
                label = conn.get("label", "")
                value = conn.get("value", "")
                detail = f"  [{conn_type}] → {target}"
                if label:
                    detail += f" ({label})"
                if value:
                    detail += f" — ₹{float(value)/1e7:.2f}Cr"
                sections.append(detail)
            if len(connections) > 10:
                sections.append(f"  ... and {len(connections) - 10} more")

        # Shell explanation
        shell_expl = vendor.get("shell_explanation")
        if shell_expl:
            sections.append("")
            sections.append(f"Shell Risk Explanation: {shell_expl}")

        if vendor.get("requires_human_review"):
            sections.append("")
            sections.append("⚠️ REQUIRES HUMAN REVIEW")

    # ── Search company table ───────────────────────
    company = fetch_one(
        """SELECT * FROM company
           WHERE cin = %s OR company_name ILIKE %s
           LIMIT 1""",
        (query, f"%{query}%"),
    )

    if company:
        sections.append("")
        sections.append(f"=== COMPANY REGISTRY: {company['company_name']} ===")
        sections.append(f"CIN: {company.get('cin', 'N/A')}")
        sections.append(f"Status: {company.get('company_status', 'N/A')}")
        sections.append(f"Class: {company.get('company_class', 'N/A')}")
        sections.append(f"State: {company.get('state_code', 'N/A')}")
        sections.append(f"Paid-up Capital: ₹{float(company.get('paidup_capital') or 0):,.0f}")
        sections.append(f"Authorized Capital: ₹{float(company.get('authorized_capital') or 0):,.0f}")
        sections.append(f"Shell Risk Score: {float(company.get('shell_risk_score') or 0):.1f}/100")
        sections.append("")

        # Shell flags
        shell_flags = []
        if company.get("address_cluster_flag"):
            shell_flags.append("Address Cluster (shared registered address)")
        if company.get("low_capital_flag"):
            shell_flags.append("Low Capital")
        if company.get("young_company_flag"):
            shell_flags.append("Young Company")
        if company.get("inactive_flag"):
            shell_flags.append("Inactive Status")
        if company.get("high_auth_paid_ratio"):
            shell_flags.append("High Authorized/Paid-up Ratio")
        if company.get("opc_flag"):
            shell_flags.append("One Person Company (OPC)")

        if shell_flags:
            sections.append("Shell Company Flags: " + ", ".join(shell_flags))
        else:
            sections.append("Shell Company Flags: None triggered")

        expl = company.get("explanation")
        if expl:
            sections.append(f"Explanation: {expl}")

        if company.get("requires_human_review"):
            sections.append("⚠️ REQUIRES HUMAN REVIEW")

    if not vendor and not company:
        sections.append(f"No vendor or company found matching '{query}'.")
        sections.append("Try searching with a partial name or use the query_database tool.")

    return "\n".join(sections)

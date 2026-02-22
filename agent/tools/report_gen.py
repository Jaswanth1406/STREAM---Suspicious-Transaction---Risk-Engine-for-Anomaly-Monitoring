"""
STREAM Agent Tool — Audit Report Generator.

Generates structured audit memos / summaries from the database,
formatted for regulatory review.
"""

from langchain_core.tools import tool
from agent.llm import get_llm
from db import fetch_all, fetch_one


@tool
def generate_audit_report(scope: str) -> str:
    """
    Generate a structured audit report / memo based on the given scope.

    Use this tool when the auditor asks for a summary, report, or memo —
    e.g. "Generate a report on the top 10 risky tenders",
    "Audit memo for procurement method Open Tender",
    "Summary of shell companies flagged".

    The scope should describe what the report should cover. Examples:
    - "top 10 highest risk tenders"
    - "vendor XYZ risk profile"
    - "buyer Department of Public Works"
    - "shell company flags summary"
    - "political bond flows above 50 crores"
    - "weekly summary"

    Args:
        scope: Description of what the report should cover.

    Returns:
        Formatted audit report in Markdown.
    """
    # Gather relevant data based on scope keywords
    data_sections = []

    scope_lower = scope.lower()

    # ── Top risk tenders ──
    if any(kw in scope_lower for kw in ("tender", "risk", "top", "highest", "suspicious", "flagged", "weekly", "summary", "overview")):
        tenders = fetch_all(
            """SELECT ocid, tender_id, tender_title, buyer_name, category,
                      procurement_method, amount, num_tenderers, duration_days,
                      risk_score, risk_tier, risk_explanation,
                      predicted_suspicious, suspicion_probability
               FROM procurement_tender
               ORDER BY risk_score DESC LIMIT 15"""
        )
        if tenders:
            lines = ["## High-Risk Tenders (Top 15 by risk score)\n"]
            for t in tenders:
                amount = float(t.get("amount") or 0)
                lines.append(
                    f"- **{t['ocid']}** | {t.get('tender_title', 'N/A')[:60]} | "
                    f"Buyer: {t['buyer_name']} | ₹{amount/1e7:.2f}Cr | "
                    f"Risk: {float(t.get('risk_score') or 0):.0f}/100 ({t.get('risk_tier', '')}) | "
                    f"Suspicion: {float(t.get('suspicion_probability') or 0)*100:.0f}%"
                )
                if t.get("risk_explanation"):
                    lines.append(f"  - Flags: {t['risk_explanation']}")
            data_sections.append("\n".join(lines))

    # ── Shell companies ──
    if any(kw in scope_lower for kw in ("shell", "company", "companies", "summary", "overview")):
        companies = fetch_all(
            """SELECT cin, company_name, company_status, shell_risk_score, explanation
               FROM company
               WHERE shell_risk_score >= 30
               ORDER BY shell_risk_score DESC LIMIT 15"""
        )
        if companies:
            lines = ["## Shell Company Flags (Top 15)\n"]
            for c in companies:
                lines.append(
                    f"- **{c['cin']}** | {c['company_name']} | Status: {c.get('company_status', 'N/A')} | "
                    f"Shell Risk: {float(c.get('shell_risk_score') or 0):.0f}/100"
                )
                if c.get("explanation"):
                    lines.append(f"  - {c['explanation']}")
            data_sections.append("\n".join(lines))

    # ── Vendor profiles ──
    if any(kw in scope_lower for kw in ("vendor", "profile", "summary", "overview")):
        vendors = fetch_all(
            """SELECT entity_id, company_name, composite_risk_score, risk_tier,
                      bid_pattern_score, shell_risk_sub_score, political_score, financials_score
               FROM vendor_profile
               ORDER BY composite_risk_score DESC LIMIT 15"""
        )
        if vendors:
            lines = ["## Highest-Risk Vendors (Top 15)\n"]
            for v in vendors:
                lines.append(
                    f"- **{v['entity_id']}** | {v['company_name']} | "
                    f"Composite: {float(v.get('composite_risk_score') or 0):.0f}/100 ({v.get('risk_tier', '')}) | "
                    f"Bid: {float(v.get('bid_pattern_score') or 0):.0f} | "
                    f"Shell: {float(v.get('shell_risk_sub_score') or 0):.0f} | "
                    f"Political: {float(v.get('political_score') or 0):.0f} | "
                    f"Financial: {float(v.get('financials_score') or 0):.0f}"
                )
            data_sections.append("\n".join(lines))

    # ── Bond flows ──
    if any(kw in scope_lower for kw in ("bond", "political", "electoral", "party", "donation", "summary", "overview")):
        bonds = fetch_all(
            """SELECT purchaser_name, party_name, total_bonds, total_value
               FROM bond_flow
               ORDER BY total_value DESC LIMIT 15"""
        )
        if bonds:
            lines = ["## Electoral Bond Flows (Top 15 by value)\n"]
            for b in bonds:
                value = float(b.get("total_value") or 0)
                lines.append(
                    f"- **{b['purchaser_name']}** → {b['party_name']} | "
                    f"₹{value/1e7:.2f}Cr | {b.get('total_bonds', 0)} bonds"
                )
            data_sections.append("\n".join(lines))

    # ── Aggregate KPIs ──
    kpis = fetch_one(
        """SELECT
               COUNT(*) AS total_tenders,
               COUNT(*) FILTER (WHERE risk_score >= 20) AS flagged_tenders,
               COUNT(*) FILTER (WHERE predicted_suspicious = 1) AS ml_suspicious,
               COALESCE(SUM(amount) FILTER (WHERE risk_score >= 20), 0) AS at_risk_value,
               AVG(risk_score) AS avg_risk
           FROM procurement_tender"""
    )

    company_stats = fetch_one(
        """SELECT COUNT(*) AS total,
                  COUNT(*) FILTER (WHERE shell_risk_score >= 30) AS flagged
           FROM company"""
    )

    kpi_lines = [
        "## Aggregate KPIs\n",
        f"- Total Tenders: {kpis['total_tenders']}",
        f"- Flagged Tenders (risk ≥ 20): {kpis['flagged_tenders']}",
        f"- ML-Suspicious: {kpis['ml_suspicious']}",
        f"- At-Risk Value: ₹{float(kpis['at_risk_value'] or 0)/1e7:.1f} Cr",
        f"- Average Risk Score: {float(kpis['avg_risk'] or 0):.1f}",
        f"- Companies Assessed: {company_stats['total']}",
        f"- Shell Risk Flagged: {company_stats['flagged']}",
    ]
    data_sections.insert(0, "\n".join(kpi_lines))

    # Combine all gathered data
    combined_data = "\n\n".join(data_sections)

    # Use LLM to synthesize into a proper audit report
    llm = get_llm(temperature=0.2)
    synthesis_prompt = f"""You are an expert government procurement auditor.
Based on the data below, write a professional audit report / memo for the scope: "{scope}"

Structure the report with these sections:
1. **Executive Summary** — 2-3 sentence overview of key findings
2. **Key Findings** — Bullet-pointed findings with specific IDs, amounts, and risk scores
3. **Risk Analysis** — Patterns observed, highest-risk areas
4. **Recommendations** — Specific actionable recommendations for the auditor

Format monetary values in Indian numbering (crores/lakhs).
Be factual — cite specific IDs and numbers from the data. Do not invent data.

Data:
{combined_data}

Write the audit report now:"""

    response = llm.invoke(synthesis_prompt)
    return response.content

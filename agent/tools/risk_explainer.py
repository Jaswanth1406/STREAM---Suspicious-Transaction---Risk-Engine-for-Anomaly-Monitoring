"""
STREAM Agent Tool — Risk Explainer.

Given a tender ID or OCID, explains exactly why it was flagged,
breaking down each risk flag, its weight, and the composite score calculation.
"""

from langchain_core.tools import tool
from db import fetch_one, fetch_all
from risk_engine import FLAG_WEIGHTS, explain_flags_detailed


@tool
def explain_tender_risk(tender_identifier: str) -> str:
    """
    Explain the risk assessment for a specific tender.
    Breaks down which red flags fired, their weights, the composite risk score
    calculation, ML prediction confidence, and the stored explanation.

    Use this tool when the auditor asks "Why is tender X flagged?" or
    "Explain the risk for OCID Y".

    Args:
        tender_identifier: A tender ID, OCID, or tender_pk to look up.

    Returns:
        Detailed risk breakdown string.
    """
    # Try exact match on multiple identifier columns
    row = fetch_one(
        """SELECT * FROM procurement_tender
           WHERE ocid = %s OR tender_id = %s
           LIMIT 1""",
        (tender_identifier, tender_identifier),
    )

    # Fallback: case-insensitive / partial match
    if not row:
        row = fetch_one(
            """SELECT * FROM procurement_tender
               WHERE ocid ILIKE %s OR tender_id ILIKE %s OR tender_title ILIKE %s
               LIMIT 1""",
            (f"%{tender_identifier}%", f"%{tender_identifier}%", f"%{tender_identifier}%"),
        )

    # Try as integer PK
    if not row:
        try:
            pk = int(tender_identifier)
            row = fetch_one(
                "SELECT * FROM procurement_tender WHERE tender_pk = %s", (pk,)
            )
        except (ValueError, TypeError):
            pass

    if not row:
        return f"No tender found matching '{tender_identifier}'. Try searching with query_database tool first."

    # Extract flags
    flags = {
        "flag_single_bidder": row.get("flag_single_bidder", 0) or 0,
        "flag_zero_bidders": row.get("flag_zero_bidders", 0) or 0,
        "flag_short_window": row.get("flag_short_window", 0) or 0,
        "flag_non_open": row.get("flag_non_open", 0) or 0,
        "flag_high_value": row.get("flag_high_value", 0) or 0,
        "flag_buyer_concentration": row.get("flag_buyer_concentration", 0) or 0,
        "flag_round_amount": row.get("flag_round_amount", 0) or 0,
    }

    risk_score = float(row.get("risk_score") or 0)
    risk_tier = str(row.get("risk_tier", "Unknown"))
    amount = float(row.get("amount") or 0)
    duration_days = row.get("duration_days")
    procurement_method = row.get("procurement_method", "")

    # Build detailed breakdown
    breakdown = explain_flags_detailed(
        flags, risk_score, risk_tier,
        amount=amount,
        duration_days=duration_days,
        procurement_method=procurement_method,
    )

    # Add ML info
    ml_lines = []
    ml_anomaly = row.get("ml_anomaly_flag", 0) or 0
    anomaly_score = float(row.get("anomaly_score") or 0)
    predicted_suspicious = row.get("predicted_suspicious", 0) or 0
    suspicion_prob = float(row.get("suspicion_probability") or 0)
    predicted_tier = row.get("predicted_risk_tier", "N/A")

    ml_lines.append("")
    ml_lines.append("ML Model Assessment:")
    ml_lines.append(f"  Isolation Forest anomaly flag: {'YES ⚠️' if ml_anomaly else 'no'} (score: {anomaly_score:.4f})")
    ml_lines.append(f"  Supervised prediction: {'SUSPICIOUS ⚠️' if predicted_suspicious else 'Normal'}")
    ml_lines.append(f"  Suspicion probability: {suspicion_prob:.4f} ({suspicion_prob*100:.1f}%)")
    ml_lines.append(f"  Predicted risk tier: {predicted_tier}")

    # Add tender context
    context_lines = [
        "",
        "Tender Details:",
        f"  OCID: {row.get('ocid', 'N/A')}",
        f"  Tender ID: {row.get('tender_id', 'N/A')}",
        f"  Title: {row.get('tender_title', 'N/A')}",
        f"  Buyer: {row.get('buyer_name', 'N/A')}",
        f"  Category: {row.get('category', 'N/A')}",
        f"  Method: {procurement_method}",
        f"  Amount: ₹{amount:,.0f} (₹{amount/1e7:.2f} Cr)",
        f"  Bidders: {row.get('num_tenderers', 'N/A')}",
        f"  Duration: {duration_days} days",
    ]

    stored_explanation = row.get("risk_explanation", "")
    if stored_explanation:
        context_lines.append(f"\n  Stored Explanation: {stored_explanation}")

    return breakdown + "\n".join(ml_lines) + "\n".join(context_lines)

"""
STREAM Agent Tool — ML Prediction.

Score a new (hypothetical or real) tender through the rule-based + ML pipeline
and return the full risk assessment.
"""

import pandas as pd
from langchain_core.tools import tool
from risk_engine import compute_rule_flags, engineer_df, predict_df, load_model_artifacts

# Load artifacts once at module level
_artifacts = load_model_artifacts()


@tool
def predict_tender_risk(
    buyer_name: str,
    amount: float,
    num_tenderers: int,
    duration_days: int,
    procurement_method: str,
    category: str,
) -> str:
    """
    Run the full risk assessment pipeline on a tender.
    Applies rule-based flags (7 red flags) and the ML classifier to produce
    a composite risk score, risk tier, and suspicion probability.

    Use this tool when the auditor wants to:
    - Score a new tender that isn't in the database yet
    - Simulate "what if" scenarios (e.g. "What if there's only 1 bidder?")
    - Validate whether a specific set of tender parameters is suspicious

    Args:
        buyer_name: Name of the buying entity / department.
        amount: Contract value in INR.
        num_tenderers: Number of bidders.
        duration_days: Tender period in days.
        procurement_method: E.g. "Open Tender", "Limited", "Direct Purchase".
        category: Tender classification / category description.

    Returns:
        Full risk assessment including flags, scores, and ML prediction.
    """
    # Step 1: Rule-based flags
    flags, risk_score, risk_tier, explanation = compute_rule_flags(
        amount, num_tenderers, duration_days, procurement_method, category, buyer_name
    )

    lines = [
        "=== TENDER RISK PREDICTION ===",
        "",
        "Input:",
        f"  Buyer: {buyer_name}",
        f"  Amount: ₹{amount:,.0f} (₹{amount/1e7:.2f} Cr)",
        f"  Bidders: {num_tenderers}",
        f"  Duration: {duration_days} days",
        f"  Method: {procurement_method}",
        f"  Category: {category}",
        "",
        "Rule-Based Assessment:",
        f"  Risk Score: {risk_score}/100",
        f"  Risk Tier: {risk_tier}",
        "",
        "Flags:",
    ]

    from risk_engine import FLAG_WEIGHTS
    for flag_name, weight in FLAG_WEIGHTS.items():
        fired = flags.get(flag_name, 0)
        status = "⚠️ YES" if fired else "   no"
        lines.append(f"  {status}  {flag_name} (weight: {weight})")

    if explanation:
        lines.append(f"\n  Explanation: {explanation}")

    # Step 2: ML prediction
    if _artifacts:
        try:
            row = {
                "buyer/name": buyer_name,
                "tender/value/amount": amount,
                "tender/numberOfTenderers": num_tenderers,
                "tender/tenderPeriod/durationInDays": duration_days,
                "tender/procurementMethod": procurement_method,
                "tenderclassification/description": category,
            }
            df = pd.DataFrame([row])
            df = engineer_df(df, _artifacts)
            df = predict_df(df, _artifacts)

            predicted_suspicious = int(df["predicted_suspicious"].iloc[0])
            suspicion_probability = float(df["suspicion_probability"].iloc[0])
            predicted_risk_tier = str(df["predicted_risk_tier"].iloc[0])

            # Blend scores
            ml_boost = suspicion_probability * 15
            blended_score = min(round(risk_score + ml_boost, 2), 100)

            lines.extend([
                "",
                "ML Model Prediction:",
                f"  Predicted Suspicious: {'YES ⚠️' if predicted_suspicious else 'No'}",
                f"  Suspicion Probability: {suspicion_probability:.4f} ({suspicion_probability*100:.1f}%)",
                f"  ML Risk Tier: {predicted_risk_tier}",
                "",
                f"Blended Risk Score (rules + ML): {blended_score}/100",
            ])
        except Exception as e:
            lines.append(f"\nML prediction error: {e}")
    else:
        lines.append("\nML model not loaded — showing rule-based assessment only.")

    return "\n".join(lines)

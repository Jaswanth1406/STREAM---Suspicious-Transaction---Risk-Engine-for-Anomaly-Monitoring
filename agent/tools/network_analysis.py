"""
STREAM Agent Tool — Network / Relationship Analysis.

Explores entity connections, electoral bond flows, and relationship graphs
to surface potential conflicts of interest or suspicious patterns.
"""

from langchain_core.tools import tool
from db import fetch_all, fetch_one


@tool
def analyze_network(entity_query: str) -> str:
    """
    Analyze the network of relationships around an entity — bond flows,
    vendor connections, shared addresses, entity graph edges.

    Use this tool when the auditor asks about connections, relationships,
    networks, or flows — e.g. "Who is connected to vendor X?",
    "Show bond flows for company Y", "What entities are linked to party Z?",
    "Find relationships between purchaser A and party B".

    Args:
        entity_query: Entity name, purchaser name, party name, or entity_id to investigate.

    Returns:
        Network analysis report showing all connections found.
    """
    sections = []
    q = entity_query.strip()

    # ── 1. Bond flow connections ───────────────────
    # As purchaser
    purchaser_flows = fetch_all(
        """SELECT party_name, total_bonds, total_value, first_date, last_date
           FROM bond_flow
           WHERE purchaser_name ILIKE %s
           ORDER BY total_value DESC""",
        (f"%{q}%",),
    )

    if purchaser_flows:
        total_value = sum(float(r["total_value"] or 0) for r in purchaser_flows)
        total_bonds = sum(int(r["total_bonds"] or 0) for r in purchaser_flows)
        sections.append(f"=== BOND FLOWS (as Purchaser matching '{q}') ===")
        sections.append(f"Total: {total_bonds} bonds worth ₹{total_value/1e7:.2f} Cr to {len(purchaser_flows)} parties")
        sections.append("")
        for r in purchaser_flows:
            v = float(r["total_value"] or 0)
            sections.append(
                f"  → {r['party_name']} | {r['total_bonds']} bonds | "
                f"₹{v/1e7:.2f}Cr | {r.get('first_date', '?')} to {r.get('last_date', '?')}"
            )

    # As receiving party
    party_flows = fetch_all(
        """SELECT purchaser_name, total_bonds, total_value, first_date, last_date
           FROM bond_flow
           WHERE party_name ILIKE %s
           ORDER BY total_value DESC""",
        (f"%{q}%",),
    )

    if party_flows:
        total_value = sum(float(r["total_value"] or 0) for r in party_flows)
        total_bonds = sum(int(r["total_bonds"] or 0) for r in party_flows)
        sections.append("")
        sections.append(f"=== BOND FLOWS (as Receiving Party matching '{q}') ===")
        sections.append(f"Total: {total_bonds} bonds worth ₹{total_value/1e7:.2f} Cr from {len(party_flows)} purchasers")
        sections.append("")
        for r in party_flows[:20]:
            v = float(r["total_value"] or 0)
            sections.append(
                f"  ← {r['purchaser_name']} | {r['total_bonds']} bonds | "
                f"₹{v/1e7:.2f}Cr | {r.get('first_date', '?')} to {r.get('last_date', '?')}"
            )
        if len(party_flows) > 20:
            sections.append(f"  ... and {len(party_flows) - 20} more purchasers")

    # ── 2. Vendor profile connections ──────────────
    vendor = fetch_one(
        """SELECT entity_id, company_name, connections, political_info, composite_risk_score, risk_tier
           FROM vendor_profile
           WHERE company_name ILIKE %s OR entity_id ILIKE %s OR cin ILIKE %s
           LIMIT 1""",
        (f"%{q}%", f"%{q}%", f"%{q}%"),
    )

    if vendor:
        sections.append("")
        sections.append(f"=== VENDOR CONNECTIONS: {vendor['company_name']} ===")
        sections.append(f"Composite Risk: {float(vendor.get('composite_risk_score') or 0):.0f}/100 ({vendor.get('risk_tier', '')})")

        connections = vendor.get("connections") or []
        if connections:
            bond_conns = [c for c in connections if c.get("type") == "electoral_bond"]
            addr_conns = [c for c in connections if c.get("type") == "shared_address"]
            other_conns = [c for c in connections if c.get("type") not in ("electoral_bond", "shared_address")]

            if bond_conns:
                sections.append(f"\n  Electoral Bond Links ({len(bond_conns)}):")
                for c in bond_conns:
                    v = float(c.get("value") or 0)
                    sections.append(f"    → {c.get('target', '?')} | ₹{v/1e7:.2f}Cr | {c.get('label', '')}")

            if addr_conns:
                sections.append(f"\n  Shared Address Links ({len(addr_conns)}):")
                for c in addr_conns:
                    sections.append(f"    → Cluster size: {c.get('cluster_size', '?')} | {c.get('label', '')}")

            if other_conns:
                sections.append(f"\n  Other Links ({len(other_conns)}):")
                for c in other_conns[:10]:
                    sections.append(f"    → [{c.get('type', '?')}] {c.get('target', '?')} | {c.get('label', '')}")
        else:
            sections.append("  No connections recorded in vendor profile.")

        political = vendor.get("political_info") or {}
        if political:
            sections.append("\n  Political Info:")
            for k, v in political.items():
                sections.append(f"    {k}: {v}")

    # ── 3. Entity graph (relationship_edge table) ──
    entity = fetch_one(
        """SELECT entity_id, entity_type, canonical_name
           FROM entity
           WHERE canonical_name ILIKE %s OR normalized_name ILIKE %s
           LIMIT 1""",
        (f"%{q}%", f"%{q}%"),
    )

    if entity:
        eid = entity["entity_id"]
        sections.append("")
        sections.append(f"=== ENTITY GRAPH: {entity['canonical_name']} (type: {entity['entity_type']}) ===")

        # Outgoing edges
        outgoing = fetch_all(
            """SELECT re.edge_type, re.weight, re.evidence_ref,
                      e.canonical_name AS target_name, e.entity_type AS target_type
               FROM relationship_edge re
               JOIN entity e ON e.entity_id = re.dst_entity_id
               WHERE re.src_entity_id = %s
               ORDER BY re.weight DESC NULLS LAST
               LIMIT 20""",
            (eid,),
        )

        if outgoing:
            sections.append(f"\n  Outgoing Edges ({len(outgoing)}):")
            for e in outgoing:
                w = f"weight: {float(e['weight']):.2f}" if e.get("weight") else ""
                sections.append(
                    f"    → [{e['edge_type']}] {e['target_name']} ({e['target_type']}) {w}"
                )

        # Incoming edges
        incoming = fetch_all(
            """SELECT re.edge_type, re.weight, re.evidence_ref,
                      e.canonical_name AS source_name, e.entity_type AS source_type
               FROM relationship_edge re
               JOIN entity e ON e.entity_id = re.src_entity_id
               WHERE re.dst_entity_id = %s
               ORDER BY re.weight DESC NULLS LAST
               LIMIT 20""",
            (eid,),
        )

        if incoming:
            sections.append(f"\n  Incoming Edges ({len(incoming)}):")
            for e in incoming:
                w = f"weight: {float(e['weight']):.2f}" if e.get("weight") else ""
                sections.append(
                    f"    ← [{e['edge_type']}] {e['source_name']} ({e['source_type']}) {w}"
                )

        # Risk alerts
        alerts = fetch_all(
            """SELECT ra.risk_score, ra.risk_level, ra.generated_at,
                      re.reason_text, re.rule_or_model
               FROM risk_alert ra
               LEFT JOIN risk_explanation re ON re.alert_id = ra.alert_id
               WHERE ra.entity_id = %s
               ORDER BY ra.risk_score DESC""",
            (eid,),
        )

        if alerts:
            sections.append(f"\n  Risk Alerts ({len(alerts)}):")
            for a in alerts:
                sections.append(
                    f"    Risk: {float(a.get('risk_score') or 0):.2f} ({a.get('risk_level', '?')}) | "
                    f"{a.get('rule_or_model', '')}: {a.get('reason_text', '')}"
                )

    # ── No results ──
    if not sections:
        return (
            f"No network connections found for '{entity_query}'.\n"
            "Try searching with a partial name, or use query_database to find the exact entity name first."
        )

    return "\n".join(sections)

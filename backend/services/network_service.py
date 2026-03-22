# backend/services/network_service.py
# Feature 6: Protein-Drug Interaction Network Visualization
# Builds an interactive network graph using pyvis
# Nodes: proteins, drugs, pathways, disease
# Edges: interactions, mechanisms, associations

import json
import os
import tempfile
from backend.models.schemas import DiseaseAnalysisResult


# ── Node + Edge color schemes ─────────────────────────────────
NODE_COLORS = {
    "disease":  {"bg": "#ef4444", "border": "#dc2626", "font": "#ffffff"},
    "protein":  {"bg": "#3b82f6", "border": "#2563eb", "font": "#ffffff"},
    "drug":     {"bg": "#10b981", "border": "#059669", "font": "#ffffff"},
    "pathway":  {"bg": "#8b5cf6", "border": "#7c3aed", "font": "#ffffff"},
    "risk_high":{"bg": "#ef4444", "border": "#dc2626", "font": "#ffffff"},
    "risk_med": {"bg": "#f59e0b", "border": "#d97706", "font": "#ffffff"},
    "risk_low": {"bg": "#22c55e", "border": "#16a34a", "font": "#ffffff"},
}

EDGE_COLORS = {
    "disease_protein": "#60a5fa",
    "protein_drug":    "#34d399",
    "drug_pathway":    "#a78bfa",
    "risk_signal":     "#f87171",
    "association":     "#64748b"
}


def build_network_data(result: DiseaseAnalysisResult) -> dict:
    """
    Build network graph data from pipeline results.
    Returns nodes and edges as dicts for frontend rendering.

    Network structure:
    Disease → Proteins (association score)
    Proteins → Drugs (mechanism)
    Drugs → Risk nodes (FDA signals)
    Proteins → Pathway nodes (from hypothesis)
    """
    nodes = []
    edges = []
    node_ids = set()

    def add_node(node_id, label, node_type,
                 size=25, title="", score=None):
        if node_id in node_ids:
            return
        node_ids.add(node_id)

        color_scheme = NODE_COLORS.get(node_type, NODE_COLORS["protein"])

        node = {
            "id":     node_id,
            "label":  label,
            "title":  title or label,
            "type":   node_type,
            "size":   size,
            "color": {
                "background": color_scheme["bg"],
                "border":     color_scheme["border"],
                "highlight": {
                    "background": color_scheme["bg"],
                    "border":     "#ffffff"
                }
            },
            "font": {
                "color": color_scheme["font"],
                "size":  13
            },
            "borderWidth": 2,
            "shadow": True
        }
        if score is not None:
            node["title"] = f"{title}\nScore: {score:.3f}"

        nodes.append(node)

    def add_edge(from_id, to_id, label="",
                 edge_type="association", width=2, dashes=False):
        edges.append({
            "from":   from_id,
            "to":     to_id,
            "label":  label,
            "color":  {"color": EDGE_COLORS.get(edge_type, "#64748b"),
                       "opacity": 0.8},
            "width":  width,
            "dashes": dashes,
            "font":   {"size": 10, "color": "#94a3b8"},
            "arrows": {"to": {"enabled": True, "scaleFactor": 0.8}}
        })

    # ── Disease node (center) ─────────────────────────────────
    disease_id = "disease_0"
    add_node(
        disease_id,
        result.disease_name[:20],
        "disease",
        size=45,
        title=f"Disease: {result.disease_name}"
    )

    # ── Protein nodes ─────────────────────────────────────────
    for target in result.protein_targets[:5]:
        p_id = f"protein_{target.gene_symbol}"
        score= target.association_score
        size = 20 + int(score * 20)   # Bigger = higher score

        add_node(
            p_id,
            target.gene_symbol,
            "protein",
            size=size,
            title=(
                f"Protein: {target.protein_name}\n"
                f"Gene: {target.gene_symbol}\n"
                f"Association Score: {score:.3f}\n"
                f"AlphaFold pLDDT: {target.alphafold_plddt:.2f}"
            ),
            score=score
        )

        # Disease → Protein edge
        add_edge(
            disease_id, p_id,
            label=f"{score:.2f}",
            edge_type="disease_protein",
            width=1 + int(score * 4)
        )

    # ── Drug nodes ────────────────────────────────────────────
    for drug in result.drugs[:6]:
        d_id    = f"drug_{drug.drug_name}"
        p_id    = f"protein_{drug.target_gene}"
        risk    = drug.risk_level
        d_type  = (
            "risk_high" if risk == "High"
            else "risk_med" if risk == "Medium"
            else "risk_low" if risk == "Low"
            else "drug"
        )

        phase = drug.clinical_phase or 0
        size  = 15 + (phase * 4)   # Phase 4 = biggest

        fda_note = ""
        if drug.fda_adverse_events:
            top = drug.fda_adverse_events[0]
            fda_note = f"\nFDA Signal: {top.reaction} ({top.count} reports)"

        add_node(
            d_id,
            drug.drug_name[:12],
            d_type,
            size=size,
            title=(
                f"Drug: {drug.drug_name}\n"
                f"Type: {drug.drug_type}\n"
                f"Phase: {drug.clinical_phase}\n"
                f"Mechanism: {drug.mechanism[:60]}\n"
                f"Risk: {risk}{fda_note}"
            )
        )

        # Protein → Drug edge (only if protein exists)
        if p_id in node_ids:
            add_edge(
                p_id, d_id,
                label=drug.mechanism[:15]+"..." if len(drug.mechanism) > 15
                      else drug.mechanism,
                edge_type="protein_drug",
                width=2
            )

    # ── Pathway nodes from hypotheses ────────────────────────
    pathways_added = set()
    for hyp in result.hypotheses[:3]:
        # Extract pathway from title
        pathway_keywords = [
            "amyloidogenic pathway", "gamma-secretase pathway",
            "NMDA receptor excitotoxicity", "APOE lipid transport",
            "neuroinflammation pathway", "mTOR/autophagy",
            "dopaminergic pathway", "PI3K/AKT pathway"
        ]
        pathway = None
        for kw in pathway_keywords:
            if kw.lower() in hyp.title.lower() or \
               kw.lower() in hyp.explanation.lower():
                pathway = kw
                break

        if not pathway:
            # Extract from title after "in the"
            if " in the " in hyp.title.lower():
                pathway = hyp.title.lower().split(" in the ")[-1].strip()
                pathway = pathway[:30]

        if pathway and pathway not in pathways_added:
            pathways_added.add(pathway)
            pw_id = f"pathway_{pathway[:20]}"

            add_node(
                pw_id,
                pathway[:18]+"..." if len(pathway) > 18 else pathway,
                "pathway",
                size=22,
                title=f"Pathway: {pathway}\nScore: {hyp.final_score:.2%}"
            )

            # Connect proteins to pathway
            for protein_sym in hyp.key_proteins:
                p_id = f"protein_{protein_sym}"
                if p_id in node_ids:
                    add_edge(
                        p_id, pw_id,
                        label="via",
                        edge_type="drug_pathway",
                        width=1,
                        dashes=True
                    )

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "proteins":    len([n for n in nodes if n["type"] == "protein"]),
            "drugs":       len([n for n in nodes
                                if n["type"] in ["drug","risk_high",
                                                 "risk_med","risk_low"]]),
            "pathways":    len([n for n in nodes if n["type"] == "pathway"])
        }
    }


def get_network_legend() -> list:
    """Return legend items for the network visualization."""
    return [
        {"color": "#ef4444", "label": "Disease"},
        {"color": "#3b82f6", "label": "Protein Target"},
        {"color": "#10b981", "label": "Drug (Low Risk)"},
        {"color": "#f59e0b", "label": "Drug (Medium Risk)"},
        {"color": "#ef4444", "label": "Drug (High Risk)"},
        {"color": "#8b5cf6", "label": "Biological Pathway"},
    ]


# ── Quick test ────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing Network Service...")

    # Mock test with simple data
    class MockTarget:
        gene_symbol      = "PSEN1"
        protein_name     = "Presenilin 1"
        association_score= 0.867
        alphafold_plddt  = 0.87

    class MockDrug:
        drug_name         = "NIROGACESTAT"
        drug_type         = "Small molecule"
        target_gene       = "PSEN1"
        clinical_phase    = 4
        mechanism         = "Gamma-secretase inhibitor"
        risk_level        = "High"
        fda_adverse_events= []

    class MockHyp:
        title       = "Targeting PSEN1 in amyloidogenic pathway"
        explanation = "PSEN1 inhibition reduces amyloid-beta"
        key_proteins= ["PSEN1"]
        key_drugs   = ["NIROGACESTAT"]
        final_score = 0.74

    class MockResult:
        disease_name    = "Alzheimer disease"
        protein_targets = [MockTarget()]
        drugs           = [MockDrug()]
        hypotheses      = [MockHyp()]

    result = build_network_data(MockResult())
    print(f"Nodes: {result['stats']['total_nodes']}")
    print(f"Edges: {result['stats']['total_edges']}")
    print(f"Stats: {result['stats']}")
    print("✅ Network service working!")
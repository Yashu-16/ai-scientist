# backend/services/knowledge_graph.py
# V4 Feature 8: Persistent Knowledge Graph Memory
#
# Stores proteins, drugs, and relationships as a JSON graph.
# Loads on startup, grows with each analysis.
# Enables cross-session intelligence.

import json
import os
from datetime import datetime
from typing import Optional

# ── Storage path ──────────────────────────────────────────────
import os
GRAPH_FILE = os.getenv("GRAPH_FILE_PATH", "data/knowledge_graph.json")


class KnowledgeGraph:
    """
    Lightweight JSON-based knowledge graph.
    Stores: proteins, drugs, relationships, disease analyses.

    Structure:
    {
        "nodes": {
            "PSEN1": {"type": "protein", "diseases": [...], "score": 0.87},
            "LECANEMAB": {"type": "drug", "phase": 4, "targets": [...]}
        },
        "edges": [
            {"from": "LECANEMAB", "to": "APP", "relation": "inhibits",
             "disease": "Alzheimer disease", "score": 0.79}
        ],
        "disease_analyses": {
            "Alzheimer disease": {"last_analyzed": "...", "top_drug": "..."}
        },
        "stats": {"total_analyses": 0, "total_proteins": 0}
    }
    """

    def __init__(self):
        self._graph = {
            "nodes":            {},
            "edges":            [],
            "disease_analyses": {},
            "stats": {
                "total_analyses": 0,
                "total_proteins": 0,
                "total_drugs":    0,
                "total_edges":    0,
                "created_at":     datetime.now().isoformat(),
                "last_updated":   datetime.now().isoformat()
            }
        }
        self._load()

    def _load(self):
        """Load graph from disk on startup."""
        try:
            os.makedirs("data", exist_ok=True)
            if os.path.exists(GRAPH_FILE):
                with open(GRAPH_FILE, "r") as f:
                    loaded = json.load(f)
                    self._graph.update(loaded)
                    print(
                        f"   📊 Knowledge graph loaded: "
                        f"{len(self._graph['nodes'])} nodes, "
                        f"{len(self._graph['edges'])} edges"
                    )
            else:
                print("   📊 Knowledge graph initialized (empty)")
        except Exception as e:
            print(f"   ⚠️  Knowledge graph load error: {e}")

    def _save(self):
        """Persist graph to disk."""
        try:
            os.makedirs("data", exist_ok=True)
            self._graph["stats"]["last_updated"] = datetime.now().isoformat()
            with open(GRAPH_FILE, "w") as f:
                json.dump(self._graph, f, indent=2)
        except Exception as e:
            print(f"   ⚠️  Knowledge graph save error: {e}")

    def add_protein(self, gene_symbol: str, protein_name: str,
                    disease: str, score: float):
        """Add or update a protein node."""
        if gene_symbol not in self._graph["nodes"]:
            self._graph["nodes"][gene_symbol] = {
                "type":        "protein",
                "protein_name":protein_name,
                "diseases":    [],
                "max_score":   0.0,
                "appearances": 0
            }
            self._graph["stats"]["total_proteins"] += 1

        node = self._graph["nodes"][gene_symbol]
        if disease not in node["diseases"]:
            node["diseases"].append(disease)
        node["max_score"]   = max(node.get("max_score",0), score)
        node["appearances"] = node.get("appearances",0) + 1

    def add_drug(self, drug_name: str, drug_type: str,
                 phase: Optional[int], mechanism: str,
                 risk_level: str):
        """Add or update a drug node."""
        key = drug_name.upper()
        if key not in self._graph["nodes"]:
            self._graph["nodes"][key] = {
                "type":        "drug",
                "drug_name":   drug_name,
                "drug_type":   drug_type,
                "phase":       phase,
                "mechanism":   mechanism[:100],
                "risk_level":  risk_level,
                "appearances": 0
            }
            self._graph["stats"]["total_drugs"] += 1

        self._graph["nodes"][key]["appearances"] = \
            self._graph["nodes"][key].get("appearances",0) + 1

    def add_relationship(self, drug_name: str, protein: str,
                          relation: str, disease: str, score: float):
        """Add a drug-protein relationship edge."""
        # Avoid exact duplicates
        for edge in self._graph["edges"]:
            if (edge["from"].upper() == drug_name.upper() and
                edge["to"].upper()   == protein.upper() and
                edge["disease"]      == disease):
                # Update score if better
                edge["score"] = max(edge.get("score",0), score)
                return

        self._graph["edges"].append({
            "from":     drug_name.upper(),
            "to":       protein.upper(),
            "relation": relation,
            "disease":  disease,
            "score":    round(score, 4),
            "added_at": datetime.now().isoformat()
        })
        self._graph["stats"]["total_edges"] += 1

    def record_analysis(self, disease_name: str,
                        top_drug: str, top_protein: str,
                        confidence: float, decision: str):
        """Record a disease analysis result."""
        self._graph["disease_analyses"][disease_name] = {
            "last_analyzed": datetime.now().isoformat(),
            "top_drug":      top_drug,
            "top_protein":   top_protein,
            "confidence":    confidence,
            "decision":      decision
        }
        self._graph["stats"]["total_analyses"] += 1

    def ingest_pipeline_result(self, result) -> dict:
        """
        Main ingestion function: extract all entities from a
        pipeline result and add to knowledge graph.

        Returns summary of what was added.
        """
        added = {"proteins":0, "drugs":0, "edges":0}

        # Add proteins
        for pt in result.protein_targets:
            self.add_protein(
                gene_symbol  = pt.gene_symbol,
                protein_name = pt.protein_name,
                disease      = result.disease_name,
                score        = pt.association_score
            )
            added["proteins"] += 1

        # Add drugs + relationships
        for drug in result.drugs:
            self.add_drug(
                drug_name  = drug.drug_name,
                drug_type  = drug.drug_type,
                phase      = drug.clinical_phase,
                mechanism  = drug.mechanism,
                risk_level = drug.risk_level
            )
            added["drugs"] += 1

            # Add drug→protein relationship
            self.add_relationship(
                drug_name = drug.drug_name,
                protein   = drug.target_gene,
                relation  = "targets",
                disease   = result.disease_name,
                score     = 0.5  # Base score
            )
            added["edges"] += 1

        # Add hypothesis-based edges with better scores
        for hyp in result.hypotheses:
            for drug_name in hyp.key_drugs:
                for protein in hyp.key_proteins:
                    self.add_relationship(
                        drug_name = drug_name,
                        protein   = protein,
                        relation  = "hypothesis_link",
                        disease   = result.disease_name,
                        score     = hyp.final_score
                    )

        # Record analysis
        ds = result.decision_summary
        if ds:
            self.record_analysis(
                disease_name = result.disease_name,
                top_drug     = ds.recommended_drug,
                top_protein  = ds.target_protein,
                confidence   = ds.confidence_score,
                decision     = ds.go_no_go.decision
                               if ds.go_no_go else "Unknown"
            )

        self._save()
        return added

    def get_stats(self) -> dict:
        return {
            **self._graph["stats"],
            "node_count":    len(self._graph["nodes"]),
            "edge_count":    len(self._graph["edges"]),
            "diseases_analyzed": list(self._graph["disease_analyses"].keys())
        }

    def get_protein_insights(self, gene_symbol: str) -> Optional[dict]:
        """Get accumulated knowledge about a protein."""
        return self._graph["nodes"].get(gene_symbol)

    def get_drug_insights(self, drug_name: str) -> Optional[dict]:
        """Get accumulated knowledge about a drug."""
        return self._graph["nodes"].get(drug_name.upper())

    def get_cross_disease_proteins(self) -> list:
        """Find proteins appearing in multiple diseases."""
        return [
            {"gene_symbol": sym, **data}
            for sym, data in self._graph["nodes"].items()
            if data.get("type") == "protein"
            and len(data.get("diseases",[])) >= 2
        ]

    def get_most_analyzed_drugs(self, top_n: int = 5) -> list:
        """Get most frequently appearing drugs."""
        drugs = [
            {"name": k, **v}
            for k, v in self._graph["nodes"].items()
            if v.get("type") == "drug"
        ]
        return sorted(
            drugs,
            key=lambda x: x.get("appearances",0),
            reverse=True
        )[:top_n]

    def search(self, query: str) -> dict:
        """Search nodes by name."""
        query_upper = query.upper()
        results = {
            "proteins": [],
            "drugs":    []
        }
        for key, node in self._graph["nodes"].items():
            if query_upper in key or query_upper in node.get("protein_name","").upper():
                if node.get("type") == "protein":
                    results["proteins"].append({key: node})
                elif node.get("type") == "drug":
                    results["drugs"].append({key: node})
        return results


# ── Global instance ───────────────────────────────────────────
knowledge_graph = KnowledgeGraph()


# ── Quick test ────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing Knowledge Graph...")
    print("=" * 50)

    kg = KnowledgeGraph()

    # Add some test data
    kg.add_protein("PSEN1","Presenilin 1","Alzheimer disease",0.867)
    kg.add_protein("APP","Amyloid Precursor","Alzheimer disease",0.854)
    kg.add_protein("LRRK2","LRRK2 kinase","Parkinson disease",0.88)
    kg.add_drug("LECANEMAB","Antibody",4,"Amyloid-beta inhibitor","Medium")
    kg.add_drug("NIROGACESTAT","Small molecule",4,"Gamma-secretase inhibitor","High")
    kg.add_relationship("LECANEMAB","APP","inhibits","Alzheimer disease",0.79)
    kg.add_relationship("NIROGACESTAT","PSEN1","inhibits","Alzheimer disease",0.75)

    stats = kg.get_stats()
    print(f"Nodes    : {stats['node_count']}")
    print(f"Edges    : {stats['edge_count']}")
    print(f"Analyses : {stats['total_analyses']}")

    print("\nCross-disease proteins:")
    for p in kg.get_cross_disease_proteins():
        print(f"  {p['gene_symbol']}: {p['diseases']}")

    print("\nMost analyzed drugs:")
    for d in kg.get_most_analyzed_drugs():
        print(f"  {d['name']}: Phase {d.get('phase')} | {d.get('appearances',0)} appearances")

    print("\n✅ Knowledge graph working!")
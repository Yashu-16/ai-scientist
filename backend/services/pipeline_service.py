# backend/services/pipeline_service.py
# Purpose: Orchestrate the full data pipeline.
# This is the "brain" that calls all services in order and
# assembles a complete, structured result ready for the LLM.
#
# Flow:
#   Disease Name
#       ↓
#   [protein_service]  → Protein targets (OpenTargets)
#       ↓
#   [drug_service]     → Drugs + FDA signals (OpenTargets + FDA FAERS)
#       ↓
#   [paper_service]    → Research papers (PubMed + Semantic Scholar)
#       ↓
#   Assembled Pipeline Result → ready for hypothesis_service (LLM)

import time
from backend.services.protein_service import fetch_protein_targets
from backend.services.drug_service    import fetch_drug_data_for_disease
from backend.services.paper_service   import fetch_papers_for_disease
from backend.models.schemas import (
    DiseaseAnalysisResult,
    ProteinTarget,
    Drug,
    FDAAdverseEvent,
    ResearchPaper
)


def run_data_pipeline(
    disease_name: str,
    max_targets:  int = 5,
    max_papers:   int = 5,
    max_drugs:    int = 3
) -> DiseaseAnalysisResult:
    """
    Master pipeline: runs all data fetching services in sequence.
    Returns a fully populated DiseaseAnalysisResult object.

    Args:
        disease_name : e.g. "Alzheimer disease"
        max_targets  : number of protein targets to fetch
        max_papers   : number of papers per source
        max_drugs    : drugs per protein target

    Returns:
        DiseaseAnalysisResult — structured data ready for LLM
    """

    print(f"\n{'='*55}")
    print(f"  🔬 Starting pipeline for: {disease_name}")
    print(f"{'='*55}")

    result = DiseaseAnalysisResult(
        disease_name=disease_name,
        analysis_status="pending"
    )

    # ── STAGE 1: Protein Targets ─────────────────────────────
    print("\n📡 Stage 1/3 — Fetching protein targets...")
    try:
        protein_data = fetch_protein_targets(disease_name, max_targets=max_targets)

        if "error" in protein_data:
            result.analysis_status = "error"
            result.error_message   = f"Protein fetch failed: {protein_data['error']}"
            return result

        result.disease_id = protein_data.get("disease_id", "")

        # Convert raw dicts → Pydantic ProteinTarget objects
        for t in protein_data.get("targets", []):
            result.protein_targets.append(ProteinTarget(
                gene_symbol         = t.get("gene_symbol", ""),
                protein_name        = t.get("protein_name", ""),
                ensembl_id          = t.get("ensembl_id", ""),
                biotype             = t.get("biotype", ""),
                association_score   = t.get("association_score", 0.0),
                function_description= t.get("function_description", "")
            ))

        print(f"  ✅ Found {len(result.protein_targets)} protein targets")
        for pt in result.protein_targets:
            print(f"     • {pt.gene_symbol} (score: {pt.association_score})")

    except Exception as e:
        result.analysis_status = "error"
        result.error_message   = f"Protein stage error: {str(e)}"
        return result

    # ── STAGE 2: Drug Mapping + FDA Signals ──────────────────
    print("\n💊 Stage 2/3 — Fetching drug mappings + FDA signals...")
    try:
        # Convert Pydantic objects back to dicts for drug service
        target_dicts = [t.model_dump() for t in result.protein_targets]
        drug_data    = fetch_drug_data_for_disease(target_dicts, max_drugs_per_protein=max_drugs)

        for d in drug_data.get("drug_data", []):
            # Convert FDA events
            fda_events = [
                FDAAdverseEvent(
                    reaction=ae.get("reaction", ""),
                    count=ae.get("count", 0)
                )
                for ae in d.get("fda_adverse_events", [])
            ]

            result.drugs.append(Drug(
                drug_name          = d.get("drug_name", ""),
                drug_type          = d.get("drug_type", ""),
                clinical_phase     = d.get("clinical_phase"),
                mechanism          = d.get("mechanism", ""),
                description        = d.get("description", ""),
                target_gene        = d.get("target_gene", ""),
                fda_adverse_events = fda_events
            ))

        print(f"  ✅ Found {len(result.drugs)} drug-target associations")
        for drug in result.drugs:
            print(f"     • {drug.drug_name} → {drug.target_gene} (Phase {drug.clinical_phase})")

    except Exception as e:
        # Drug stage failing is non-fatal — continue with empty drugs
        print(f"  ⚠️  Drug stage warning: {str(e)} — continuing without drug data")

    # ── STAGE 3: Research Papers ─────────────────────────────
    print("\n📚 Stage 3/3 — Fetching research papers...")

    # Small delay to avoid rate limiting on sequential API calls
    time.sleep(2)

    try:
        # Use top protein for focused paper search
        top_protein = result.protein_targets[0].gene_symbol if result.protein_targets else ""

        paper_data = fetch_papers_for_disease(
            disease_name   = disease_name,
            protein_symbol = top_protein,
            max_results    = max_papers
        )

        for p in paper_data.get("papers", []):
            result.papers.append(ResearchPaper(
                source        = p.get("source", ""),
                title         = p.get("title", ""),
                abstract      = p.get("abstract", ""),
                summary       = p.get("summary", ""),
                authors       = p.get("authors", []),
                year          = p.get("year"),
                citation_count= p.get("citation_count", 0),
                paper_id      = p.get("paper_id", ""),
                url           = p.get("url", "")
            ))

        print(f"  ✅ Found {len(result.papers)} research papers")
        for paper in result.papers[:3]:
            print(f"     • [{paper.source}] {paper.title[:60]}...")

    except Exception as e:
        print(f"  ⚠️  Paper stage warning: {str(e)} — continuing without papers")

    # ── COMPLETE ─────────────────────────────────────────────
    result.analysis_status = "complete"

    print(f"\n{'='*55}")
    print(f"  ✅ Pipeline complete!")
    print(f"     Proteins : {len(result.protein_targets)}")
    print(f"     Drugs    : {len(result.drugs)}")
    print(f"     Papers   : {len(result.papers)}")
    print(f"{'='*55}\n")

    return result


def build_llm_context(result: DiseaseAnalysisResult) -> str:
    """
    Convert pipeline result into a clean text context block
    for the LLM hypothesis generator.

    This is what gets sent to GPT as the "evidence" context.
    """

    lines = []

    lines.append(f"DISEASE: {result.disease_name}")
    lines.append("")

    # Proteins
    lines.append("── PROTEIN TARGETS ──")
    for pt in result.protein_targets[:5]:
        lines.append(
            f"• {pt.gene_symbol} ({pt.protein_name}) | "
            f"Score: {pt.association_score} | "
            f"Function: {pt.function_description[:120]}"
        )
    lines.append("")

    # Drugs
    lines.append("── KNOWN DRUGS ──")
    for drug in result.drugs[:5]:
        fda_note = ""
        if drug.fda_adverse_events:
            top_ae   = drug.fda_adverse_events[0]
            fda_note = f"| FDA signal: {top_ae.reaction} ({top_ae.count} reports)"
        lines.append(
            f"• {drug.drug_name} → targets {drug.target_gene} | "
            f"Phase {drug.clinical_phase} | "
            f"{drug.mechanism} {fda_note}"
        )
    lines.append("")

    # Papers
    lines.append("── RESEARCH EVIDENCE ──")
    for paper in result.papers[:4]:
        lines.append(
            f"• [{paper.year}] {paper.title[:80]} "
            f"({paper.source}, {paper.citation_count} citations)"
        )
        if paper.summary and paper.summary != "No summary available":
            lines.append(f"  Summary: {paper.summary[:150]}")
    lines.append("")

    return "\n".join(lines)


# ── Quick test ───────────────────────────────────────────────
if __name__ == "__main__":

    # Run full pipeline
    result = run_data_pipeline(
        disease_name = "Alzheimer disease",
        max_targets  = 5,
        max_papers   = 4,
        max_drugs    = 3
    )

    # Show assembled LLM context
    print("\n📋 LLM Context Block (what gets sent to GPT):")
    print("-" * 55)
    context = build_llm_context(result)
    print(context)

    # Show schema validation worked
    print("\n🔍 Schema validation:")
    print(f"  Result type     : {type(result).__name__}")
    print(f"  Protein targets : {len(result.protein_targets)}")
    print(f"  Drugs           : {len(result.drugs)}")
    print(f"  Papers          : {len(result.papers)}")
    print(f"  Status          : {result.analysis_status}")
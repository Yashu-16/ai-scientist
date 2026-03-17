# backend/services/pipeline_service.py
# V2 — Feature 8: Performance optimization
# Changes:
#   1. In-memory cache with TTL (Time To Live)
#   2. Parallel API calls using ThreadPoolExecutor
#   3. Cache stats endpoint support

import time
import hashlib
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from backend.services.protein_service import fetch_protein_targets
from backend.services.drug_service    import fetch_drug_data_for_disease
from backend.services.paper_service   import fetch_papers_for_disease
from backend.models.schemas import (
    DiseaseAnalysisResult,
    ProteinTarget,
    Drug,
    FDAAdverseEvent,
    ResearchPaper,
    EvidenceStrength
)


# ── In-Memory Cache ───────────────────────────────────────────
# Simple dict-based cache with TTL
# Stores full pipeline results keyed by disease name
# TTL: 1 hour (results don't change that fast)

class PipelineCache:
    def __init__(self, ttl_minutes: int = 60):
        self._cache: dict = {}
        self._ttl  = timedelta(minutes=ttl_minutes)

    def _make_key(self, disease_name: str, max_targets: int,
                  max_papers: int, max_drugs: int) -> str:
        """Create a unique cache key from request parameters."""
        raw = f"{disease_name.lower().strip()}_{max_targets}_{max_papers}_{max_drugs}"
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, disease_name: str, max_targets: int,
            max_papers: int, max_drugs: int):
        """Return cached result if valid, else None."""
        key   = self._make_key(disease_name, max_targets, max_papers, max_drugs)
        entry = self._cache.get(key)

        if not entry:
            return None

        # Check TTL
        if datetime.now() - entry["timestamp"] > self._ttl:
            del self._cache[key]
            print(f"   🗑️  Cache expired for: {disease_name}")
            return None

        age_mins = (datetime.now() - entry["timestamp"]).seconds // 60
        print(f"   ✅ Cache HIT for '{disease_name}' (cached {age_mins}m ago)")
        return entry["data"]

    def set(self, disease_name: str, max_targets: int, max_papers: int,
            max_drugs: int, data: DiseaseAnalysisResult):
        """Store result in cache."""
        key = self._make_key(disease_name, max_targets, max_papers, max_drugs)
        self._cache[key] = {
            "timestamp": datetime.now(),
            "data":      data
        }
        print(f"   💾 Cached result for: {disease_name}")

    def clear(self):
        """Clear all cached entries."""
        count = len(self._cache)
        self._cache.clear()
        return count

    def stats(self) -> dict:
        """Return cache statistics."""
        now     = datetime.now()
        entries = []
        for key, entry in self._cache.items():
            age     = (now - entry["timestamp"]).seconds // 60
            expires = int((self._ttl.seconds - (now - entry["timestamp"]).seconds) / 60)
            entries.append({
                "disease": entry["data"].disease_name,
                "age_minutes":     age,
                "expires_minutes": max(0, expires)
            })
        return {
            "total_cached": len(self._cache),
            "ttl_minutes":  int(self._ttl.seconds / 60),
            "entries":      entries
        }


# Global cache instance — shared across all requests
pipeline_cache = PipelineCache(ttl_minutes=60)


# ── Evidence Strength ─────────────────────────────────────────
def compute_evidence_strength(papers: list) -> EvidenceStrength:
    """
    Compute evidence strength from retrieved papers.
    Components: volume (40%) + citation quality (35%) + recency (25%)
    """
    import datetime as dt

    current_year     = dt.datetime.now().year
    RECENT_THRESHOLD = 5
    HIGH_CITE_MIN    = 50

    total_papers     = len(papers)
    high_cite_papers = 0
    recent_papers    = 0
    total_citations  = 0

    for paper in papers:
        citations = (paper.citation_count
                     if hasattr(paper, "citation_count")
                     else paper.get("citation_count", 0))
        year      = (paper.year
                     if hasattr(paper, "year")
                     else paper.get("year"))

        total_citations += citations or 0
        if citations and citations >= HIGH_CITE_MIN:
            high_cite_papers += 1
        if year and (current_year - year) <= RECENT_THRESHOLD:
            recent_papers += 1

    avg_citations = round(total_citations / total_papers, 1) if total_papers > 0 else 0.0

    if total_papers >= 8:        volume_score = 1.0
    elif total_papers >= 5:      volume_score = 0.75
    elif total_papers >= 2:      volume_score = 0.5
    elif total_papers == 1:      volume_score = 0.25
    else:                        volume_score = 0.0

    citation_score = min(1.0, high_cite_papers / max(total_papers, 1))
    recency_score  = min(1.0, recent_papers    / max(total_papers, 1))

    evidence_score = round(
        0.40 * volume_score +
        0.35 * citation_score +
        0.25 * recency_score, 4
    )

    if evidence_score >= 0.65:   label, color = "Strong",   "green"
    elif evidence_score >= 0.35: label, color = "Moderate", "yellow"
    else:                        label, color = "Weak",      "red"

    breakdown = (
        f"{total_papers} papers | "
        f"{high_cite_papers} highly cited (>{HIGH_CITE_MIN} cites) | "
        f"{recent_papers} recent (≤{RECENT_THRESHOLD}yr) | "
        f"avg {avg_citations} citations | "
        f"vol={volume_score:.2f}×0.4 + "
        f"cite={citation_score:.2f}×0.35 + "
        f"recency={recency_score:.2f}×0.25 = {evidence_score:.3f}"
    )

    return EvidenceStrength(
        evidence_score       = evidence_score,
        evidence_label       = label,
        evidence_color       = color,
        total_papers         = total_papers,
        high_citation_papers = high_cite_papers,
        recent_papers        = recent_papers,
        avg_citations        = avg_citations,
        evidence_breakdown   = breakdown
    )


# ── Parallel Data Fetcher ─────────────────────────────────────
def fetch_proteins_stage(disease_name: str, max_targets: int) -> dict:
    """Stage 1 wrapper for parallel execution."""
    print(f"  [Thread] 📡 Fetching proteins for: {disease_name}")
    result = fetch_protein_targets(disease_name, max_targets=max_targets)
    print(f"  [Thread] ✅ Proteins done: {len(result.get('targets', []))} found")
    return result


def fetch_papers_stage(disease_name: str, top_protein: str, max_papers: int) -> dict:
    """Stage 3 wrapper for parallel execution."""
    print(f"  [Thread] 📚 Fetching papers for: {disease_name} + {top_protein}")
    result = fetch_papers_for_disease(
        disease_name   = disease_name,
        protein_symbol = top_protein,
        max_results    = max_papers
    )
    print(f"  [Thread] ✅ Papers done: {len(result.get('papers', []))} found")
    return result


def run_data_pipeline(
    disease_name: str,
    max_targets:  int = 5,
    max_papers:   int = 5,
    max_drugs:    int = 3
) -> DiseaseAnalysisResult:
    """
    Optimized pipeline with:
    1. Cache check first (instant if cached)
    2. Parallel execution of proteins + papers
    3. Drug fetching after proteins (needs protein data)

    Performance improvement:
    Before: proteins(10s) → drugs(15s) → papers(15s) = ~40s sequential
    After:  proteins+papers parallel(15s) → drugs(15s) = ~25s
    """

    print(f"\n{'='*55}")
    print(f"  🔬 Pipeline: {disease_name}")
    print(f"{'='*55}")

    # ── Check cache first ─────────────────────────────────────
    cached = pipeline_cache.get(disease_name, max_targets, max_papers, max_drugs)
    if cached:
        print(f"  ⚡ Returning cached result (skipping all API calls)")
        return cached

    result = DiseaseAnalysisResult(
        disease_name    = disease_name,
        analysis_status = "pending"
    )

    start_time = time.time()

    # ── Stage 1: Proteins first (drugs depend on this) ────────
    print("\n📡 Stage 1/3 — Fetching protein targets...")
    try:
        protein_data = fetch_proteins_stage(disease_name, max_targets)

        if "error" in protein_data:
            result.analysis_status = "error"
            result.error_message   = f"Protein fetch failed: {protein_data['error']}"
            return result

        result.disease_id = protein_data.get("disease_id", "")

        for t in protein_data.get("targets", []):
            result.protein_targets.append(ProteinTarget(
                gene_symbol          = t.get("gene_symbol", ""),
                protein_name         = t.get("protein_name", ""),
                ensembl_id           = t.get("ensembl_id", ""),
                biotype              = t.get("biotype", ""),
                association_score    = t.get("association_score", 0.0),
                function_description = t.get("function_description", ""),
                alphafold_plddt      = t.get("alphafold_plddt", 0.0),
                alphafold_label      = t.get("alphafold_label", ""),
                alphafold_color      = t.get("alphafold_color", ""),
                alphafold_source     = t.get("alphafold_source", "")
            ))

        print(f"  ✅ Found {len(result.protein_targets)} protein targets")
        for pt in result.protein_targets:
            print(f"     • {pt.gene_symbol} (score: {pt.association_score})")

    except Exception as e:
        result.analysis_status = "error"
        result.error_message   = f"Protein stage error: {str(e)}"
        return result

    # ── Stages 2 + 3: Drugs and Papers in PARALLEL ───────────
    print("\n⚡ Stages 2+3 — Fetching drugs + papers IN PARALLEL...")

    top_protein  = result.protein_targets[0].gene_symbol if result.protein_targets else ""
    target_dicts = [t.model_dump() for t in result.protein_targets]

    drug_result  = None
    paper_result = None

    # Use ThreadPoolExecutor to run both API calls simultaneously
    with ThreadPoolExecutor(max_workers=2) as executor:
        # Submit both tasks
        future_drugs  = executor.submit(
            fetch_drug_data_for_disease,
            target_dicts,
            max_drugs
        )
        future_papers = executor.submit(
            fetch_papers_stage,
            disease_name,
            top_protein,
            max_papers
        )

        # Collect results as they complete
        for future in as_completed([future_drugs, future_papers]):
            try:
                result_data = future.result()
                if future == future_drugs:
                    drug_result  = result_data
                    print(f"  ✅ Drugs complete: "
                          f"{drug_result.get('total_drugs', 0)} found")
                else:
                    paper_result = result_data
                    print(f"  ✅ Papers complete: "
                          f"{len(paper_result.get('papers', []))} found")
            except Exception as e:
                print(f"  ⚠️  Parallel task warning: {e}")

    # Process drug results
    if drug_result:
        for d in drug_result.get("drug_data", []):
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
                fda_adverse_events = fda_events,
                risk_level         = d.get("risk_level", "Unknown"),
                risk_description   = d.get("risk_description", "")
            ))

    # Process paper results
    if paper_result:
        for p in paper_result.get("papers", []):
            result.papers.append(ResearchPaper(
                source         = p.get("source", ""),
                title          = p.get("title", ""),
                abstract       = p.get("abstract", ""),
                summary        = p.get("summary", ""),
                authors        = p.get("authors", []),
                year           = p.get("year"),
                citation_count = p.get("citation_count", 0),
                paper_id       = p.get("paper_id", ""),
                url            = p.get("url", "")
            ))

    elapsed = round(time.time() - start_time, 2)

    # ── Evidence Strength ─────────────────────────────────────
    print("\n🔬 Computing evidence strength...")
    result.evidence_strength = compute_evidence_strength(result.papers)
    ev = result.evidence_strength
    print(f"   Evidence: {ev.evidence_label} (score: {ev.evidence_score})")

    result.analysis_status = "complete"

    print(f"\n{'='*55}")
    print(f"  ✅ Pipeline complete in {elapsed}s")
    print(f"     Proteins : {len(result.protein_targets)}")
    print(f"     Drugs    : {len(result.drugs)}")
    print(f"     Papers   : {len(result.papers)}")
    print(f"{'='*55}\n")

    # ── Cache the result ──────────────────────────────────────
    pipeline_cache.set(disease_name, max_targets, max_papers, max_drugs, result)

    return result


def build_llm_context(result: DiseaseAnalysisResult) -> str:
    """
    Convert pipeline result into clean text context for LLM.
    """
    lines = []
    lines.append(f"DISEASE: {result.disease_name}")
    lines.append("")

    lines.append("── PROTEIN TARGETS ──")
    for pt in result.protein_targets[:5]:
        lines.append(
            f"• {pt.gene_symbol} ({pt.protein_name}) | "
            f"Score: {pt.association_score} | "
            f"AlphaFold pLDDT: {pt.alphafold_plddt} | "
            f"Function: {pt.function_description[:120]}"
        )
    lines.append("")

    lines.append("── KNOWN DRUGS ──")
    for drug in result.drugs[:5]:
        fda_note = ""
        if drug.fda_adverse_events:
            top      = drug.fda_adverse_events[0]
            fda_note = f"| FDA: {top.reaction} ({top.count} reports)"
        lines.append(
            f"• {drug.drug_name} → {drug.target_gene} | "
            f"Phase {drug.clinical_phase} | "
            f"{drug.mechanism} | Risk: {drug.risk_level} {fda_note}"
        )
    lines.append("")

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


# ── Quick test ────────────────────────────────────────────────
if __name__ == "__main__":
    print("🧬 Pipeline V2 — Performance Test")
    print("=" * 55)

    # First run — fresh fetch
    print("\n🔄 Run 1 — Fresh fetch (no cache):")
    t1    = time.time()
    r1    = run_data_pipeline("Alzheimer disease", 5, 4, 3)
    time1 = round(time.time() - t1, 2)
    print(f"   ⏱️  Time: {time1}s")

    # Second run — should be instant from cache
    print("\n⚡ Run 2 — From cache:")
    t2    = time.time()
    r2    = run_data_pipeline("Alzheimer disease", 5, 4, 3)
    time2 = round(time.time() - t2, 2)
    print(f"   ⏱️  Time: {time2}s")

    print(f"\n📊 Performance comparison:")
    print(f"   Fresh  : {time1}s")
    print(f"   Cached : {time2}s")
    if time1 > 0:
        print(f"   Speedup: {time1/max(time2,0.01):.0f}x faster")

    # Cache stats
    print(f"\n📋 Cache stats: {pipeline_cache.stats()}")
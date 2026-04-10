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
    EvidenceStrength,
    UncertaintyAnalysis   
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

def compute_decision_summary(
    result: DiseaseAnalysisResult
) -> "DecisionSummary":
    """
    Extract the best actionable recommendation from ranked hypotheses.

    Logic:
    1. Take the highest final_score hypothesis (rank 1)
    2. Extract drug, protein, pathway from it
    3. Get risk level from drug data
    4. Generate reasoning summary
    5. Suggest next action based on clinical phase + risk
    """
    from backend.models.schemas import DecisionSummary

    # Need at least one hypothesis
    if not result.hypotheses:
        return DecisionSummary(
            best_hypothesis   = "Insufficient data",
            reasoning_summary = "Not enough evidence to generate a recommendation.",
            suggested_action  = "Try a different disease name or expand search parameters."
        )

    # Best hypothesis = rank 1 (already sorted by pipeline)
    best = min(result.hypotheses, key=lambda h: h.rank)

    # Extract drug info
    recommended_drug = best.key_drugs[0] if best.key_drugs else "Unknown"
    target_protein   = best.key_proteins[0] if best.key_proteins else "Unknown"

    # Get risk level for the recommended drug
    risk_level = "Unknown"
    risk_color = "#64748b"
    drug_phase = None

    for drug in result.drugs:
        if drug.drug_name.upper() == recommended_drug.upper():
            risk_level = drug.risk_level
            drug_phase = drug.clinical_phase
            risk_color = {
                "High":    "#ef4444",
                "Medium":  "#f59e0b",
                "Low":     "#22c55e",
                "Unknown": "#64748b"
            }.get(risk_level, "#64748b")
            break

    # Extract pathway from hypothesis title or explanation
    pathway_keywords = [
        "amyloidogenic pathway", "NMDA receptor excitotoxicity",
        "APOE lipid transport", "Notch signaling",
        "mTOR/autophagy", "neuroinflammation",
        "gamma-secretase", "dopaminergic pathway",
        "PI3K/AKT", "MAPK signaling", "p53 pathway"
    ]
    target_pathway = "unknown pathway"
    title_lower    = best.title.lower()
    expl_lower     = best.explanation.lower()

    for kw in pathway_keywords:
        if kw.lower() in title_lower or kw.lower() in expl_lower:
            target_pathway = kw
            break

    # Build reasoning summary
    phase_str = f"Phase {drug_phase}" if drug_phase else "clinical"
    reasoning = (
        f"{recommended_drug} ({phase_str}) targeting {target_protein} "
        f"via the {target_pathway} shows the strongest evidence profile "
        f"with a composite score of {best.final_score:.0%}. "
        f"{best.evidence_summary or best.explanation[:150]}"
    )

    # Suggest next action based on phase + risk
    if drug_phase == 4:
        if risk_level == "High":
            action = (
                f"⚠️ {recommended_drug} is FDA-approved (Phase 4) but carries "
                f"high adverse event signals. Recommend benefit-risk analysis "
                f"before pursuing further. Consider monitoring protocols."
            )
        elif risk_level == "Medium":
            action = (
                f"✅ {recommended_drug} is FDA-approved (Phase 4) with manageable "
                f"risk profile. Recommend literature review of combination therapy "
                f"approaches targeting {target_protein}."
            )
        else:
            action = (
                f"🟢 {recommended_drug} (Phase 4, low risk) is a strong candidate. "
                f"Recommend in-vitro validation of {target_protein} interaction "
                f"and review of existing clinical outcomes data."
            )
    elif drug_phase == 3:
        action = (
            f"🔬 {recommended_drug} is in Phase 3 trials. "
            f"Recommend reviewing trial results and designing complementary "
            f"in-vitro assays targeting {target_protein} to support or "
            f"differentiate from existing trial hypotheses."
        )
    elif drug_phase == 2:
        action = (
            f"🧪 {recommended_drug} is in Phase 2. "
            f"Recommend in-vitro validation studies targeting {target_protein} "
            f"and analysis of Phase 2 trial inclusion criteria."
        )
    else:
        action = (
            f"🔭 Early-stage opportunity. Recommend in-vitro assay design "
            f"targeting {target_protein} in {target_pathway} "
            f"and patent landscape analysis for {recommended_drug}."
        )

    # Evidence basis
    paper_count   = len(result.papers)
    ev            = result.evidence_strength
    ev_label      = ev.evidence_label if ev else "Unknown"
    evidence_basis= (
        f"{paper_count} research papers retrieved | "
        f"Evidence strength: {ev_label} | "
        f"Protein association score: {best.protein_score:.2f} | "
        f"Drug clinical phase score: {best.drug_score:.2f}"
    )

    return DecisionSummary(
        best_hypothesis  = best.title,
        recommended_drug = recommended_drug,
        target_protein   = target_protein,
        target_pathway   = target_pathway,
        confidence_score = best.final_score,
        confidence_label = best.confidence_label,
        risk_level       = risk_level,
        risk_color       = risk_color,
        reasoning_summary= reasoning,
        suggested_action = action,
        evidence_basis   = evidence_basis
    )

def compute_uncertainty(
    result: "DiseaseAnalysisResult",
    hypothesis=None
) -> "UncertaintyAnalysis":
    """
    Compute uncertainty score for a pipeline result or hypothesis.

    Uncertainty is HIGH when:
    - Few supporting papers (<3)
    - Weak protein association scores
    - High FDA risk signals present
    - No causal evidence found
    - Limited drug data

    Uncertainty is LOW when:
    - Many papers (>8) with good citations
    - Strong protein associations (>0.8)
    - Low/Medium FDA risk
    - Causal evidence present
    - Multiple drugs found

    Args:
        result     : Full pipeline result (for analysis-level uncertainty)
        hypothesis : Optional specific hypothesis (for hypothesis-level)

    Returns:
        UncertaintyAnalysis object
    """
    from backend.models.schemas import UncertaintyAnalysis, UncertaintyFactor

    factors        = []
    uncertainty_raw= 0.0
    flags          = {}

    # ── Factor 1: Paper count ─────────────────────────────────
    paper_count = len(result.papers)
    if paper_count < 3:
        paper_impact    = "High"
        paper_penalty   = 0.35
        flags["low_paper_count"] = True
    elif paper_count < 6:
        paper_impact    = "Medium"
        paper_penalty   = 0.15
        flags["low_paper_count"] = False
    else:
        paper_impact    = "Low"
        paper_penalty   = 0.05
        flags["low_paper_count"] = False

    uncertainty_raw += paper_penalty
    factors.append(UncertaintyFactor(
        factor      = "Literature Support",
        impact      = paper_impact,
        description = (
            f"{paper_count} papers retrieved. "
            f"{'Insufficient evidence base.' if paper_count < 3 else 'Adequate.' if paper_count < 6 else 'Strong evidence base.'}"
        )
    ))

    # ── Factor 2: Protein association strength ────────────────
    if result.protein_targets:
        top_score = result.protein_targets[0].association_score
        if top_score < 0.6:
            prot_impact  = "High"
            prot_penalty = 0.30
            flags["weak_protein_assoc"] = True
        elif top_score < 0.75:
            prot_impact  = "Medium"
            prot_penalty = 0.15
            flags["weak_protein_assoc"] = False
        else:
            prot_impact  = "Low"
            prot_penalty = 0.05
            flags["weak_protein_assoc"] = False

        uncertainty_raw += prot_penalty
        factors.append(UncertaintyFactor(
            factor      = "Protein Association Strength",
            impact      = prot_impact,
            description = (
                f"Top protein score: {top_score:.3f}. "
                f"{'Weak association — high uncertainty.' if top_score < 0.6 else 'Moderate association.' if top_score < 0.75 else 'Strong association — low uncertainty.'}"
            )
        ))

    # ── Factor 3: FDA risk signals ────────────────────────────
    high_risk_drugs = [
        d for d in result.drugs if d.risk_level == "High"
    ]
    if high_risk_drugs:
        risk_impact  = "High"
        risk_penalty = 0.20
        flags["high_fda_risk"] = True
        risk_desc = (
            f"{len(high_risk_drugs)} high-risk drug(s) detected: "
            f"{', '.join(d.drug_name for d in high_risk_drugs[:2])}. "
            f"Significant adverse event signals increase uncertainty."
        )
    else:
        risk_impact  = "Low"
        risk_penalty = 0.0
        flags["high_fda_risk"] = False
        risk_desc = "No high-risk FDA signals detected."

    uncertainty_raw += risk_penalty
    factors.append(UncertaintyFactor(
        factor      = "FDA Risk Signals",
        impact      = risk_impact,
        description = risk_desc
    ))

    # ── Factor 4: Drug data availability ─────────────────────
    drug_count = len(result.drugs)
    if drug_count < 2:
        drug_impact  = "High"
        drug_penalty = 0.20
        flags["limited_drug_data"] = True
    elif drug_count < 4:
        drug_impact  = "Medium"
        drug_penalty = 0.10
        flags["limited_drug_data"] = False
    else:
        drug_impact  = "Low"
        drug_penalty = 0.0
        flags["limited_drug_data"] = False

    uncertainty_raw += drug_penalty
    factors.append(UncertaintyFactor(
        factor      = "Drug Evidence Coverage",
        impact      = drug_impact,
        description = (
            f"{drug_count} drug-target associations found. "
            f"{'Limited drug data reduces confidence.' if drug_count < 2 else 'Adequate drug coverage.'}"
        )
    ))

    # ── Factor 5: Causal evidence (hypothesis-specific) ──────
    if hypothesis and hasattr(hypothesis, 'causal_analysis') \
       and hypothesis.causal_analysis:
        causal_score = hypothesis.causal_analysis.causal_score
        if causal_score < 0.2:
            causal_impact  = "High"
            causal_penalty = 0.20
            flags["no_causal_evidence"] = True
        elif causal_score < 0.5:
            causal_impact  = "Medium"
            causal_penalty = 0.10
            flags["no_causal_evidence"] = False
        else:
            causal_impact  = "Low"
            causal_penalty = 0.0
            flags["no_causal_evidence"] = False

        uncertainty_raw += causal_penalty
        factors.append(UncertaintyFactor(
            factor      = "Causal Evidence",
            impact      = causal_impact,
            description = (
                f"Causal score: {causal_score:.2f}. "
                f"{'Correlational only — mechanism unproven.' if causal_score < 0.2 else 'Some causal signals present.' if causal_score < 0.5 else 'Good causal evidence.'}"
            )
        ))
    else:
        flags["no_causal_evidence"] = True

    # ── Normalize + Label ─────────────────────────────────────
    uncertainty_score = round(min(1.0, uncertainty_raw), 4)

    if uncertainty_score >= 0.7:
        label = "Very High"
        color = "#ef4444"
        reason= (
            "Multiple critical data gaps detected. "
            "Hypothesis requires substantial additional validation "
            "before drawing conclusions."
        )
        reliability_note = (
            "Increase paper count, find stronger causal evidence, "
            "and verify drug safety profile before proceeding."
        )
    elif uncertainty_score >= 0.45:
        label = "High"
        color = "#f97316"
        reason= (
            "Several uncertainty factors present. "
            "Results are indicative but not definitive. "
            "Additional validation recommended."
        )
        reliability_note = (
            "Retrieve more papers, verify protein associations "
            "experimentally, and check for conflicting studies."
        )
    elif uncertainty_score >= 0.25:
        label = "Medium"
        color = "#f59e0b"
        reason= (
            "Some uncertainty factors present but manageable. "
            "Results are reasonably reliable for exploratory use."
        )
        reliability_note = (
            "Consider expanding literature search and running "
            "targeted validation experiments."
        )
    else:
        label = "Low"
        color = "#22c55e"
        reason= (
            "Strong evidence base with minimal uncertainty factors. "
            "Results are reliable for decision-making purposes."
        )
        reliability_note = (
            "Evidence is sufficient. Proceed with confidence "
            "to experimental validation phase."
        )

    return UncertaintyAnalysis(
        uncertainty_score  = uncertainty_score,
        uncertainty_label  = label,
        uncertainty_color  = color,
        factors            = factors,
        low_paper_count    = flags.get("low_paper_count", False),
        weak_protein_assoc = flags.get("weak_protein_assoc", False),
        high_fda_risk      = flags.get("high_fda_risk", False),
        no_causal_evidence = flags.get("no_causal_evidence", True),
        limited_drug_data  = flags.get("limited_drug_data", False),
        uncertainty_reason = reason,
        reliability_note   = reliability_note
    )

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
            max_drugs,
            result.disease_id,
            disease_name,
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
            from backend.services.drug_service import classify_competition
            from backend.models.schemas import CompetitionIntel

            comp = classify_competition(
                drug_name = d.get("drug_name",""),
                mechanism = d.get("mechanism",""),
                drug_type = d.get("drug_type","")
            )

            result.drugs.append(Drug(
                drug_name          = d.get("drug_name", ""),
                drug_type          = d.get("drug_type", ""),
                clinical_phase     = d.get("clinical_phase"),
                mechanism          = d.get("mechanism", ""),
                description        = d.get("description", ""),
                target_gene        = d.get("target_gene", ""),
                fda_adverse_events = fda_events,
                risk_level         = d.get("risk_level", "Unknown"),
                risk_description   = d.get("risk_description", ""),
                competition_intel  = comp
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

    # ── Compute Analysis-Level Uncertainty ────────────────────
    print("\n📐 Computing uncertainty analysis...")
    result.analysis_uncertainty = compute_uncertainty(result)
    ua = result.analysis_uncertainty
    print(f"   Uncertainty: {ua.uncertainty_label} "
          f"(score: {ua.uncertainty_score:.3f})")
    for f in ua.factors:
        print(f"   • {f.factor}: {f.impact} — {f.description[:60]}")

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
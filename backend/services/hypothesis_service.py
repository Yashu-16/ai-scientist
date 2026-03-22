# backend/services/hypothesis_service.py
# V2 — includes Hypothesis Ranking Engine (Feature 1)

import os
import json
from dotenv import load_dotenv
from backend.models.schemas import Hypothesis, DiseaseAnalysisResult
from backend.services.pipeline_service import build_llm_context
from backend.services.paper_service import extract_causal_evidence

load_dotenv()

# ── 1. LLM Provider Setup ─────────────────────────────────────
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
GROQ_KEY   = os.getenv("GROQ_API_KEY", "")

if OPENAI_KEY and not OPENAI_KEY.startswith("sk-your"):
    from openai import OpenAI
    client       = OpenAI(api_key=OPENAI_KEY)
    LLM_PROVIDER = "openai"
    LLM_MODEL    = "gpt-4o-mini"
    print("🤖 LLM Provider: OpenAI (gpt-4o-mini)")

elif GROQ_KEY and not GROQ_KEY.startswith("gsk_your"):
    from groq import Groq
    client       = Groq(api_key=GROQ_KEY)
    LLM_PROVIDER = "groq"
    LLM_MODEL    = "llama-3.3-70b-versatile"
    print("🤖 LLM Provider: Groq (llama-3.3-70b-versatile) [FREE]")

else:
    client       = None
    LLM_PROVIDER = "mock"
    LLM_MODEL    = "mock"
    print("⚠️  No LLM key found — using mock hypotheses")


# ── 2. Prompt Templates ───────────────────────────────────────

# ── 2. Prompt Templates (V2 — Feature 4 upgrade) ─────────────

SYSTEM_PROMPT = """You are a senior biomedical research scientist specializing in 
drug discovery, molecular biology, and translational medicine.

Your hypotheses are:
- Mechanistically precise: always name the specific biological pathway involved
- Evidence-grounded: reference only proteins and drugs present in the provided data
- Actionable: each hypothesis must suggest a testable experimental approach
- Differentiated: each hypothesis must target a DIFFERENT protein-drug combination

You NEVER:
- Use vague language like "may play a role" or "could be involved"
- Generate hypotheses without naming a specific pathway
- Repeat the same protein-drug pair across multiple hypotheses
- Make claims unsupported by the provided evidence

Pathway vocabulary you must use where applicable:
- Amyloidogenic pathway (APP → PSEN1/2 → Aβ production)
- NMDA receptor excitotoxicity pathway (GRIN1 → Ca2+ influx)
- APOE-mediated lipid transport and Aβ clearance pathway
- Notch signaling pathway (gamma-secretase substrate)
- mTOR/autophagy pathway (lysosomal protein clearance)
- Neuroinflammation pathway (microglial activation)
"""

HYPOTHESIS_PROMPT_TEMPLATE = """
You are analyzing real biomedical evidence for {disease_name}.
Generate exactly {num_hypotheses} mechanistically precise, evidence-backed hypotheses.

═══════════════════════════════════════════════════
EVIDENCE PROVIDED:
═══════════════════════════════════════════════════
{evidence_context}

═══════════════════════════════════════════════════
STRICT REQUIREMENTS — VIOLATING ANY = INVALID OUTPUT:
═══════════════════════════════════════════════════

1. EACH hypothesis MUST name:
   a) A SPECIFIC protein from the evidence (use exact gene symbol e.g. PSEN1)
   b) A SPECIFIC drug from the evidence (use exact drug name e.g. NIROGACESTAT)
   c) A SPECIFIC biological pathway (e.g. "amyloidogenic pathway", "NMDA excitotoxicity")
   d) A SPECIFIC mechanism of action (e.g. "gamma-secretase inhibition", "NMDA antagonism")

2. EACH hypothesis MUST be UNIQUE — different protein-drug pair from others

3. reasoning_steps MUST contain 3-4 bullet points showing your logical chain:
   Step 1: What the protein does in disease context
   Step 2: What the drug does mechanistically  
   Step 3: How they interact at the pathway level
   Step 4: Why this is therapeutically relevant

4. confidence_score MUST reflect evidence quality:
   - Phase 4 drug + high protein score + papers → 0.75-0.90
   - Phase 3 drug + moderate evidence → 0.55-0.74
   - Phase 1-2 drug or weak evidence → 0.30-0.54

5. explanation MUST:
   - Name the exact pathway (not just "Alzheimer's pathway")
   - Describe the molecular mechanism (not just "reduces amyloid")
   - Be 3-4 sentences minimum
   - Avoid these phrases: "may play a role", "could be involved", "might help"

Return ONLY a valid JSON array — no markdown, no text outside JSON:

[
  {{
    "title": "Specific mechanism-based hypothesis in ≤25 words naming protein, drug, and pathway",
    "explanation": "3-4 sentences. Name exact pathway. Describe molecular mechanism. Explain therapeutic relevance. Reference specific evidence.",
    "simple_explanation": "2-3 sentences using ONE clear analogy. Explain what the protein does, what the drug does, and why it matters.",
    "confidence_score": 0.0,
    "confidence_reasoning": "Cite exact evidence: protein score, drug phase, paper count. Explain score numerically.",
    "key_proteins": ["EXACT_GENE_SYMBOL"],
    "key_drugs": ["EXACT_DRUG_NAME"],
    "evidence_summary": "One sentence citing specific data points from the evidence provided.",
    "reasoning_steps": [
      "Step 1 — Protein role: [specific function in disease pathway]",
      "Step 2 — Drug mechanism: [exact mechanism of action]",
      "Step 3 — Pathway interaction: [how drug modulates protein in pathway]",
      "Step 4 — Therapeutic logic: [why this could work clinically]"
    ]
  }}
]
"""


# ── 3. Ranking Engine ─────────────────────────────────────────

def compute_protein_score(
    hypothesis:      Hypothesis,
    pipeline_result: DiseaseAnalysisResult
) -> float:
    """
    Score based on OpenTargets association scores of proteins
    mentioned in this hypothesis. Returns average of matched scores.
    """
    if not hypothesis.key_proteins:
        return 0.3

    scores = []
    for gene_symbol in hypothesis.key_proteins:
        for target in pipeline_result.protein_targets:
            if target.gene_symbol.upper() == gene_symbol.upper():
                scores.append(target.association_score)
                break

    return round(sum(scores) / len(scores), 4) if scores else 0.3


def compute_drug_score(
    hypothesis:      Hypothesis,
    pipeline_result: DiseaseAnalysisResult
) -> float:
    """
    Score based on highest clinical trial phase among mentioned drugs.
    Phase 4=1.0, Phase 3=0.75, Phase 2=0.5, Phase 1=0.25, None=0.1
    """
    PHASE_SCORES = {4: 1.0, 3: 0.75, 2: 0.5, 1: 0.25}

    if not hypothesis.key_drugs:
        return 0.1

    scores = []
    for drug_name in hypothesis.key_drugs:
        for drug in pipeline_result.drugs:
            if drug.drug_name.upper() == drug_name.upper():
                scores.append(PHASE_SCORES.get(drug.clinical_phase, 0.1))
                break

    return round(max(scores), 4) if scores else 0.1


def compute_paper_score(pipeline_result: DiseaseAnalysisResult) -> float:
    """
    Score based on total research papers retrieved.
    ≥8=1.0, 5-7=0.75, 2-4=0.5, 1=0.25, 0=0.0
    """
    total = len(pipeline_result.papers)
    if total >= 8:   return 1.0
    elif total >= 5: return 0.75
    elif total >= 2: return 0.5
    elif total == 1: return 0.25
    else:            return 0.0


def compute_fda_risk_penalty(
    hypothesis:      Hypothesis,
    pipeline_result: DiseaseAnalysisResult
) -> float:
    """
    Penalty based on FDA adverse event counts for mentioned drugs.
    >200 reports=1.0 (high), 50-200=0.5 (medium), <50=0.1 (low)
    """
    if not hypothesis.key_drugs:
        return 0.0

    max_penalty = 0.0
    for drug_name in hypothesis.key_drugs:
        for drug in pipeline_result.drugs:
            if drug.drug_name.upper() == drug_name.upper():
                if drug.fda_adverse_events:
                    count = drug.fda_adverse_events[0].count
                    penalty = 1.0 if count > 200 else 0.5 if count >= 50 else 0.1
                    max_penalty = max(max_penalty, penalty)
                break

    return round(max_penalty, 4)


def build_score_breakdown(
    protein_score: float,
    drug_score:    float,
    paper_score:   float,
    risk_penalty:  float,
    final_score:   float
) -> str:
    """Human-readable explanation of score components."""
    risk_label = (
        "High risk"   if risk_penalty >= 0.8 else
        "Medium risk" if risk_penalty >= 0.4 else
        "Low risk"    if risk_penalty >  0.0 else
        "No FDA data"
    )
    return (
        f"Protein: {protein_score:.2f}×0.4 | "
        f"Drug phase: {drug_score:.2f}×0.3 | "
        f"Papers: {paper_score:.2f}×0.2 | "
        f"FDA penalty: -{risk_penalty:.2f}×0.1 ({risk_label}) | "
        f"Final: {final_score:.3f}"
    )


def rank_hypotheses(
    hypotheses:      list,
    pipeline_result: DiseaseAnalysisResult
) -> list:
    """
    Compute weighted score for each hypothesis and sort best-first.

    Formula:
        final = 0.4×protein + 0.3×drug + 0.2×papers - 0.1×risk_penalty
    """
    print("\n📊 Running Hypothesis Ranking Engine...")

    shared_paper_score = compute_paper_score(pipeline_result)

    for hyp in hypotheses:
        p  = compute_protein_score(hyp, pipeline_result)
        d  = compute_drug_score(hyp, pipeline_result)
        pa = shared_paper_score
        r  = compute_fda_risk_penalty(hyp, pipeline_result)

        final = round(max(0.0, min(1.0, 0.4*p + 0.3*d + 0.2*pa - 0.1*r)), 4)

        hyp.protein_score   = p
        hyp.drug_score      = d
        hyp.paper_score     = pa
        hyp.risk_penalty    = r
        hyp.final_score     = final
        hyp.score_breakdown = build_score_breakdown(p, d, pa, r, final)

        print(
            f"   • {hyp.title[:50]}...\n"
            f"     protein={p:.2f} drug={d:.2f} "
            f"papers={pa:.2f} risk=-{r:.2f} → final={final:.4f}"
        )

    # Sort descending by final_score, assign ranks
    hypotheses.sort(key=lambda h: h.final_score, reverse=True)
    for i, hyp in enumerate(hypotheses, 1):
        hyp.rank = i

    print(f"\n   🏆 Ranking complete:")
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    for hyp in hypotheses:
        medal = medals.get(hyp.rank, f"#{hyp.rank}")
        print(f"   {medal} Rank {hyp.rank}: score={hyp.final_score:.4f} — "
              f"{hyp.title[:45]}...")

    return hypotheses


# ── 4. Mock Hypotheses ────────────────────────────────────────

def get_mock_hypotheses(disease_name: str) -> list[Hypothesis]:
    """Fallback hypotheses when no LLM key is configured."""
    return [
        Hypothesis(
            title             = f"PSEN1 gamma-secretase inhibition via Nirogacestat may reduce amyloid-beta in {disease_name}",
            explanation       = "PSEN1 encodes presenilin-1, the catalytic subunit of gamma-secretase which cleaves APP into amyloid-beta. Nirogacestat blocks this cleavage, reducing neurotoxic amyloid-beta42 production targeting the amyloid cascade directly.",
            simple_explanation= "Think of PSEN1 as scissors cutting a protein into toxic pieces. Nirogacestat acts like a blade guard — stopping the cut that produces harmful fragments.",
            confidence_score  = 0.82,
            confidence_label  = "High",
            key_proteins      = ["PSEN1"],
            key_drugs         = ["NIROGACESTAT"],
            evidence_summary  = "PSEN1 highest association score (0.867), Nirogacestat Phase 4 gamma-secretase inhibitor"
        ),
        Hypothesis(
            title             = "Lecanemab-mediated APP clearance may synergize with APOE modulation to reduce neurodegeneration",
            explanation       = "APP-derived amyloid-beta oligomers drive neurodegeneration. Lecanemab targets these for clearance while APOE4 impairs clearance. Combining both addresses production and clearance failure simultaneously.",
            simple_explanation= "Alzheimer's is like a clogged drain — plaques are the blockage. Lecanemab is drain cleaner, APOE therapy improves the drain's natural ability. Together they clear faster.",
            confidence_score  = 0.71,
            confidence_label  = "Medium-High",
            key_proteins      = ["APP", "APOE"],
            key_drugs         = ["LECANEMAB"],
            evidence_summary  = "APP score 0.854, APOE score 0.782; Lecanemab FDA-approved Phase 4"
        ),
        Hypothesis(
            title             = "GRIN1 NMDA modulation may protect neurons from amyloid-induced excitotoxicity",
            explanation       = "GRIN1 mediates glutamate excitotoxicity — secondary neuronal death in Alzheimer's. Amyloid-beta sensitizes NMDA receptors causing calcium overload. NMDA antagonists reduce excitotoxic calcium influx.",
            simple_explanation= "Brain cells get overstimulated and burn out in Alzheimer's. GRIN1 is the volume knob. Turning it down partially prevents the speakers from blowing out.",
            confidence_score  = 0.65,
            confidence_label  = "Medium-High",
            key_proteins      = ["GRIN1"],
            key_drugs         = ["Memantine"],
            evidence_summary  = "GRIN1 score 0.684, Memantine established NMDA antagonist"
        )
    ]


# ── 5. Helper Functions ───────────────────────────────────────

def calculate_confidence_label(score: float) -> str:
    if score >= 0.8:   return "High"
    elif score >= 0.6: return "Medium-High"
    elif score >= 0.4: return "Medium"
    elif score >= 0.2: return "Low-Medium"
    else:              return "Low"


def validate_hypothesis_quality(hyp_data: dict) -> tuple[bool, str]:
    """
    Validate that a hypothesis meets quality standards.
    Returns (is_valid, reason_if_invalid)
    """
    title       = hyp_data.get("title", "")
    explanation = hyp_data.get("explanation", "")
    reasoning   = hyp_data.get("reasoning_steps", [])
    proteins    = hyp_data.get("key_proteins", [])
    drugs       = hyp_data.get("key_drugs", [])

    # Must have proteins tagged
    if not proteins:
        return False, "No key_proteins tagged"

    # Must have drugs tagged
    if not drugs:
        return False, "No key_drugs tagged"

    # Explanation must be substantial
    if len(explanation) < 100:
        return False, f"Explanation too short ({len(explanation)} chars)"

    # Must have reasoning steps
    if len(reasoning) < 2:
        return False, f"Insufficient reasoning steps ({len(reasoning)})"

    # Check for banned vague phrases
    vague_phrases = ["may play a role", "could be involved", "might help with"]
    for phrase in vague_phrases:
        if phrase.lower() in explanation.lower():
            return False, f"Contains vague phrase: '{phrase}'"

    # Must mention a pathway keyword
    pathway_keywords = [
        "pathway", "cascade", "receptor", "inhibit", "modulate",
        "cleav", "aggregat", "secretase", "kinase", "signaling"
    ]
    if not any(kw in explanation.lower() for kw in pathway_keywords):
        return False, "No pathway/mechanism terminology detected"

    return True, "OK"


def parse_hypothesis_response(raw_json: str, disease_name: str) -> list[Hypothesis]:
    """
    Parse, validate, and convert LLM JSON into Hypothesis objects.
    Filters out low-quality hypotheses with detailed logging.
    """
    cleaned = raw_json.strip()
    if cleaned.startswith("```"):
        lines   = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1])

    try:
        data = json.loads(cleaned)
        if not isinstance(data, list):
            data = [data]

        hypotheses = []
        rejected   = 0

        for item in data:
            # Validate quality
            is_valid, reason = validate_hypothesis_quality(item)
            if not is_valid:
                print(f"   ⚠️  Hypothesis rejected — {reason}: "
                      f"{item.get('title','?')[:40]}")
                rejected += 1
                continue

            score = float(item.get("confidence_score", 0.5))
            score = max(0.0, min(1.0, score))

            hypotheses.append(Hypothesis(
                title              = item.get("title", "Untitled"),
                explanation        = item.get("explanation", ""),
                simple_explanation = item.get("simple_explanation", ""),
                confidence_score   = round(score, 3),
                confidence_label   = calculate_confidence_label(score),
                key_proteins       = item.get("key_proteins", []),
                key_drugs          = item.get("key_drugs", []),
                evidence_summary   = item.get("evidence_summary", ""),
                reasoning_steps    = item.get("reasoning_steps", [])
            ))

        if rejected > 0:
            print(f"   ⚠️  {rejected} hypothesis(es) rejected for quality")

        if not hypotheses:
            print("   ⚠️  All hypotheses failed validation — using mocks")
            return get_mock_hypotheses(disease_name)

        print(f"   ✅ Parsed {len(hypotheses)} valid hypotheses")
        return hypotheses

    except json.JSONDecodeError as e:
        print(f"   ❌ JSON parse error: {e}")
        return get_mock_hypotheses(disease_name)

def add_causal_analysis(
    hypotheses:      list,
    pipeline_result: DiseaseAnalysisResult
) -> list:
    """
    Add causal analysis to each hypothesis by scanning
    supporting papers for causal language related to
    each hypothesis's proteins and drugs.
    """
    from backend.models.schemas import CausalAnalysis, CausalEvidence

    print("\n🔬 Running causal reasoning analysis...")

    # Convert papers to dicts for the extractor
    papers = [
        p.model_dump() if hasattr(p, "model_dump") else p
        for p in pipeline_result.papers
    ]

    for hyp in hypotheses:
        causal_data = extract_causal_evidence(
            papers       = papers,
            gene_symbols = hyp.key_proteins,
            drug_names   = hyp.key_drugs
        )

        # Convert evidence dicts to CausalEvidence objects
        evidence_objects = [
            CausalEvidence(
                text        = e.get("text",""),
                causal_verb = e.get("causal_verb",""),
                source      = e.get("source",""),
                strength    = e.get("strength","")
            )
            for e in causal_data.get("causal_evidence", [])
        ]

        hyp.causal_analysis = CausalAnalysis(
            causal_score         = causal_data["causal_score"],
            causal_label         = causal_data["causal_label"],
            causal_color         = causal_data["causal_color"],
            causal_evidence      = evidence_objects,
            causal_verbs_found   = causal_data["causal_verbs_found"],
            correlation_note     = causal_data["correlation_note"],
            causal_chain         = causal_data["causal_chain"],
            total_causal_hits    = causal_data["total_causal_hits"],
            total_papers_scanned = causal_data["total_papers_scanned"]
        )

        label = hyp.causal_analysis.causal_label
        score = hyp.causal_analysis.causal_score
        print(f"   • {hyp.title[:50]}...")
        print(f"     Causal: {label} (score: {score:.2f}) | "
              f"hits: {causal_data['total_causal_hits']} | "
              f"verbs: {causal_data['causal_verbs_found'][:3]}")

    return hypotheses

def generate_validation_suggestions(
    hypotheses:      list,
    pipeline_result: DiseaseAnalysisResult
) -> list:
    """
    Feature 4: Add experimental validation suggestions to each hypothesis.

    Uses a focused LLM prompt to suggest:
    - In-vitro assay (cell culture experiments)
    - In-vivo model (animal studies)
    - Clinical approach (human trials/biomarkers)

    Runs as a single batched LLM call for efficiency.
    """
    from backend.models.schemas import ValidationSuggestion

    if LLM_PROVIDER == "mock" or client is None:
        # Add mock validation suggestions
        for hyp in hypotheses:
            hyp.validation_suggestion = _mock_validation(hyp)
        return hypotheses

    print("\n🧪 Generating experimental validation suggestions...")

    # Build batched prompt for all hypotheses at once
    hyp_list = "\n\n".join([
        f"Hypothesis {i+1}:\n"
        f"Title: {hyp.title}\n"
        f"Protein: {', '.join(hyp.key_proteins)}\n"
        f"Drug: {', '.join(hyp.key_drugs)}\n"
        f"Explanation: {hyp.explanation[:200]}"
        for i, hyp in enumerate(hypotheses)
    ])

    prompt = f"""
You are an experimental biologist and drug discovery scientist.

For each hypothesis below, suggest ONE specific experimental validation method.

DISEASE CONTEXT: {pipeline_result.disease_name}

HYPOTHESES:
{hyp_list}

For each hypothesis, choose the MOST appropriate validation type:
- "In-vitro": Cell culture, protein assays, biochemical experiments
- "In-vivo": Animal models (mouse, rat, zebrafish)
- "Clinical": Biomarker analysis, patient data, clinical trials

Return ONLY a JSON array with exactly {len(hypotheses)} objects:
[
  {{
    "hypothesis_index": 0,
    "validation_type": "In-vitro",
    "experiment_title": "Short name of the experiment (max 8 words)",
    "experiment_description": "2-3 sentences describing exact protocol, cell line or model, measurement method, and what you are testing.",
    "required_tools": ["tool1", "tool2", "tool3"],
    "expected_outcome": "One sentence: what does a positive result look like?",
    "estimated_timeline": "X-Y months",
    "difficulty": "Low"
  }}
]

VALIDATION TYPE GUIDELINES:
- Phase 4 drugs → Clinical (already proven, test biomarkers)
- Phase 2-3 drugs → In-vivo (needs animal validation)
- Phase 1 or unknown → In-vitro (start with cell models)
- Proteins with known cell lines → In-vitro
- Neurodegeneration targets → In-vivo (mouse models preferred)

DIFFICULTY GUIDELINES:
- Low: Standard assays, common cell lines, 1-3 months
- Medium: Specialized models, complex protocols, 3-6 months
- High: Transgenic animals, clinical samples, 6+ months

Return ONLY valid JSON array. No markdown, no text outside JSON.
"""

    try:
        response = client.chat.completions.create(
            model       = LLM_MODEL,
            messages    = [
                {"role": "system", "content":
                 "You are an expert experimental biologist. "
                 "Always return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature = 0.3,
            max_tokens  = 1500,
        )

        raw = response.choices[0].message.content.strip()
        print(f"   ✅ Validation LLM responded ({len(raw)} chars)")

        # Clean JSON
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw   = "\n".join(lines[1:-1])

        suggestions = json.loads(raw)

        for item in suggestions:
            idx = item.get("hypothesis_index", 0)
            if idx < len(hypotheses):
                v_type  = item.get("validation_type", "In-vitro")
                v_color = {
                    "In-vitro": "#3b82f6",
                    "In-vivo":  "#8b5cf6",
                    "Clinical": "#f59e0b"
                }.get(v_type, "#64748b")

                diff       = item.get("difficulty", "Medium")
                diff_color = {
                    "Low":    "#22c55e",
                    "Medium": "#f59e0b",
                    "High":   "#ef4444"
                }.get(diff, "#64748b")

                hypotheses[idx].validation_suggestion = ValidationSuggestion(
                    validation_type        = v_type,
                    validation_color       = v_color,
                    experiment_title       = item.get("experiment_title", ""),
                    experiment_description = item.get("experiment_description", ""),
                    required_tools         = item.get("required_tools", []),
                    expected_outcome       = item.get("expected_outcome", ""),
                    estimated_timeline     = item.get("estimated_timeline", ""),
                    difficulty             = diff,
                    difficulty_color       = diff_color
                )

                hyp = hypotheses[idx]
                print(f"   • {hyp.title[:45]}...")
                print(f"     → {v_type} | {diff} difficulty | "
                      f"{item.get('estimated_timeline','?')}")

    except Exception as e:
        print(f"   ⚠️  Validation generation error: {e}")
        print("   ℹ️  Using mock validation suggestions")
        for hyp in hypotheses:
            if not hyp.validation_suggestion:
                hyp.validation_suggestion = _mock_validation(hyp)

    return hypotheses


def _mock_validation(hyp) -> "ValidationSuggestion":
    """Fallback mock validation suggestion."""
    from backend.models.schemas import ValidationSuggestion

    proteins = hyp.key_proteins
    drugs    = hyp.key_drugs
    drug     = drugs[0] if drugs else "the compound"
    protein  = proteins[0] if proteins else "the target protein"

    # Pick type based on drug name patterns
    drug_upper = drug.upper()
    if any(x in drug_upper for x in ["MAB","UMAB","ZUMAB","NUMAB"]):
        v_type = "Clinical"
        v_color= "#f59e0b"
    elif any(x in drug_upper for x in ["STAT","STAT","CEMAB"]):
        v_type = "In-vivo"
        v_color= "#8b5cf6"
    else:
        v_type = "In-vitro"
        v_color= "#3b82f6"

    return ValidationSuggestion(
        validation_type        = v_type,
        validation_color       = v_color,
        experiment_title       = f"{protein} activity assay with {drug}",
        experiment_description = (
            f"Treat {protein}-expressing cell lines with increasing "
            f"concentrations of {drug}. Measure protein activity, "
            f"downstream pathway markers, and cell viability using "
            f"standard biochemical assays."
        ),
        required_tools         = [
            "Cell culture facility",
            "Western blot apparatus",
            "ELISA kit",
            "Flow cytometer"
        ],
        expected_outcome       = (
            f"Dose-dependent reduction in {protein} activity "
            f"with corresponding decrease in disease-relevant biomarkers."
        ),
        estimated_timeline     = "3-6 months",
        difficulty             = "Medium",
        difficulty_color       = "#f59e0b"
    )

def generate_hypothesis_critiques(
    hypotheses:      list,
    pipeline_result: DiseaseAnalysisResult
) -> list:
    """
    Feature 5: Critically evaluate each hypothesis.

    Uses a second LLM pass to identify:
    - Scientific weaknesses
    - Contradictory evidence
    - Clinical/safety risks
    - How to strengthen the hypothesis

    Runs as a single batched LLM call for efficiency.
    """
    from backend.models.schemas import HypothesisCritique

    if LLM_PROVIDER == "mock" or client is None:
        for hyp in hypotheses:
            hyp.critique = _mock_critique(hyp)
        return hypotheses

    print("\n🔍 Generating hypothesis critiques...")

    hyp_list = "\n\n".join([
        f"Hypothesis {i+1}:\n"
        f"Title: {hyp.title}\n"
        f"Protein: {', '.join(hyp.key_proteins)}\n"
        f"Drug: {', '.join(hyp.key_drugs)}\n"
        f"Confidence: {hyp.confidence_score}\n"
        f"Explanation: {hyp.explanation[:250]}"
        for i, hyp in enumerate(hypotheses)
    ])

    prompt = f"""
You are a senior peer reviewer and critical biomedical scientist.

Critically evaluate each hypothesis below for {pipeline_result.disease_name}.
Be scientifically rigorous and honest about limitations.

HYPOTHESES TO CRITIQUE:
{hyp_list}

AVAILABLE EVIDENCE CONTEXT:
- Proteins: {', '.join([p.gene_symbol for p in pipeline_result.protein_targets[:5]])}
- Drugs in pipeline: {', '.join([d.drug_name for d in pipeline_result.drugs[:5]])}
- Papers available: {len(pipeline_result.papers)}

For each hypothesis, provide a critical evaluation.

Return ONLY a JSON array with exactly {len(hypotheses)} objects:
[
  {{
    "hypothesis_index": 0,
    "overall_assessment": "One sentence verdict on the hypothesis strength",
    "weaknesses": [
      "Specific weakness 1 (be concrete, not generic)",
      "Specific weakness 2",
      "Specific weakness 3"
    ],
    "contradictory_evidence": [
      "Known fact or study that contradicts or complicates this hypothesis",
      "Second contradiction if applicable"
    ],
    "risks": [
      "Specific clinical or scientific risk",
      "Second risk if applicable"
    ],
    "confidence_impact": "One sentence: how do these critiques affect overall confidence?",
    "salvage_suggestion": "One concrete suggestion to strengthen or validate this hypothesis",
    "critique_severity": "Minor"
  }}
]

SEVERITY GUIDELINES:
- "Minor": Small gaps, hypothesis still strong, easy to address
- "Moderate": Real limitations, needs additional validation, confidence reduced
- "Major": Significant contradictions or safety concerns, high-risk hypothesis

IMPORTANT RULES:
- Be specific, not generic (avoid "more research is needed")
- Reference actual biology (mention specific pathways, proteins, mechanisms)
- For Phase 4 drugs, focus on known clinical failures or safety signals
- Keep weaknesses to 2-3 most important ones
- Return ONLY valid JSON. No markdown.
"""

    try:
        response = client.chat.completions.create(
            model       = LLM_MODEL,
            messages    = [
                {"role": "system", "content":
                 "You are a rigorous peer reviewer. "
                 "Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature = 0.3,
            max_tokens  = 2000,
        )

        raw = response.choices[0].message.content.strip()
        print(f"   ✅ Critique LLM responded ({len(raw)} chars)")

        if raw.startswith("```"):
            lines = raw.split("\n")
            raw   = "\n".join(lines[1:-1])

        critiques = json.loads(raw)

        severity_colors = {
            "Minor":    "#22c55e",
            "Moderate": "#f59e0b",
            "Major":    "#ef4444"
        }

        for item in critiques:
            idx = item.get("hypothesis_index", 0)
            if idx < len(hypotheses):
                severity = item.get("critique_severity", "Moderate")
                hypotheses[idx].critique = HypothesisCritique(
                    overall_assessment      = item.get("overall_assessment",""),
                    weaknesses              = item.get("weaknesses",[]),
                    contradictory_evidence  = item.get("contradictory_evidence",[]),
                    risks                   = item.get("risks",[]),
                    confidence_impact       = item.get("confidence_impact",""),
                    salvage_suggestion      = item.get("salvage_suggestion",""),
                    critique_severity       = severity,
                    severity_color          = severity_colors.get(severity,"#f59e0b")
                )
                print(f"   • {hypotheses[idx].title[:45]}...")
                print(f"     Severity: {severity} | "
                      f"Weaknesses: {len(item.get('weaknesses',[]))} | "
                      f"Risks: {len(item.get('risks',[]))}")

    except Exception as e:
        print(f"   ⚠️  Critique generation error: {e}")
        for hyp in hypotheses:
            if not hyp.critique:
                hyp.critique = _mock_critique(hyp)

    return hypotheses


def _mock_critique(hyp) -> "HypothesisCritique":
    """Fallback mock critique."""
    from backend.models.schemas import HypothesisCritique

    protein = hyp.key_proteins[0] if hyp.key_proteins else "the target"
    drug    = hyp.key_drugs[0] if hyp.key_drugs else "the compound"

    return HypothesisCritique(
        overall_assessment     = (
            f"Hypothesis is plausible but requires additional validation "
            f"to establish direct causality."
        ),
        weaknesses             = [
            f"Limited direct evidence linking {drug} specifically to "
            f"{protein} modulation in disease context.",
            f"Association score from OpenTargets reflects correlation, "
            f"not confirmed mechanistic causality.",
            "Available paper evidence is insufficient to rule out "
            "off-target effects."
        ],
        contradictory_evidence = [
            f"Some clinical trials targeting similar pathways have shown "
            f"limited cognitive benefit despite reducing biomarkers.",
            "Blood-brain barrier penetration of compound not confirmed "
            "in all patient populations."
        ],
        risks                  = [
            f"FDA adverse event signals suggest monitoring required "
            f"for {drug}.",
            "Pathway redundancy may reduce therapeutic impact if "
            "compensatory mechanisms activate."
        ],
        confidence_impact      = (
            "These limitations reduce certainty from High to Medium-High. "
            "Hypothesis remains viable but needs experimental confirmation."
        ),
        salvage_suggestion     = (
            f"Design an in-vitro assay specifically measuring {protein} "
            f"activity changes after {drug} treatment in disease-relevant "
            f"cell models to establish direct mechanistic link."
        ),
        critique_severity  = "Moderate",
        severity_color     = "#f59e0b"
    )


# ── 6. Main Generation Function ───────────────────────────────

def generate_hypotheses(
    pipeline_result: DiseaseAnalysisResult,
    num_hypotheses:  int = 3
) -> list[Hypothesis]:
    """Generate hypotheses via LLM then rank them."""

    if LLM_PROVIDER == "mock" or client is None:
        print("   ℹ️  Using mock hypotheses (no LLM key configured)")
        hypotheses = get_mock_hypotheses(pipeline_result.disease_name)
        return rank_hypotheses(hypotheses, pipeline_result)

    evidence_context = build_llm_context(pipeline_result)
    user_prompt = HYPOTHESIS_PROMPT_TEMPLATE.format(
        disease_name     = pipeline_result.disease_name,
        num_hypotheses   = num_hypotheses,
        evidence_context = evidence_context
    )

    print(f"\n🤖 Sending evidence to {LLM_MODEL}...")
    print(f"   Evidence context : {len(evidence_context)} characters")
    print(f"   Requesting       : {num_hypotheses} hypotheses")

    try:
        response = client.chat.completions.create(
            model       = LLM_MODEL,
            messages    = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt}
            ],
            temperature = 0.4,
            max_tokens  = 3000,
        )
        raw_response = response.choices[0].message.content.strip()
        print(f"   ✅ LLM responded ({len(raw_response)} chars)")
        hypotheses = parse_hypothesis_response(raw_response, pipeline_result.disease_name)

    except Exception as e:
        print(f"   ❌ LLM error: {e}")
        print("   ℹ️  Falling back to mock hypotheses")
        hypotheses = get_mock_hypotheses(pipeline_result.disease_name)

    # ── Stage 1: Rank ─────────────────────────────────────────
    ranked = rank_hypotheses(hypotheses, pipeline_result)

    # ── Stage 2: Causal analysis ──────────────────────────────
    ranked = add_causal_analysis(ranked, pipeline_result)

    # ── Stage 3: Experimental validation ─────────────────────
    ranked = generate_validation_suggestions(ranked, pipeline_result)

    # ── Stage 4: Critical evaluation ─────────────────────────
    ranked = generate_hypothesis_critiques(ranked, pipeline_result)

    return ranked


# ── Quick test ────────────────────────────────────────────────
if __name__ == "__main__":
    from backend.services.pipeline_service import run_data_pipeline

    print("🧬 AI Scientist V2 — Ranking Engine Test")
    print("=" * 55)

    pipeline_result = run_data_pipeline(
        disease_name = "Alzheimer disease",
        max_targets  = 5,
        max_papers   = 4,
        max_drugs    = 3
    )

    hypotheses = generate_hypotheses(pipeline_result, num_hypotheses=3)

    print("\n" + "=" * 55)
    print("📊 RANKED HYPOTHESES")
    print("=" * 55)

    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    for h in hypotheses:
        medal = medals.get(h.rank, f"#{h.rank}")
        print(f"\n{medal} Rank {h.rank} — Final Score: {h.final_score:.4f}")
        print(f"   Title      : {h.title}")
        print(f"   Confidence : {h.confidence_score} ({h.confidence_label})")
        print(f"   Proteins   : {', '.join(h.key_proteins)}")
        print(f"   Drugs      : {', '.join(h.key_drugs)}")
        print(f"   Breakdown  : {h.score_breakdown}")
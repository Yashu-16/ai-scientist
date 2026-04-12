# backend/services/hypothesis_service.py
# V4 — All stages: Rank, Causal, Validation, Critique,
#       Uncertainty, GO/NO-GO, Failure Prediction
# V5 — Fixed mock fallback to use real disease proteins/drugs

import os
import json
from dotenv import load_dotenv
from backend.models.schemas import Hypothesis, DiseaseAnalysisResult
from backend.services.pipeline_service import build_llm_context
from backend.services.paper_service import extract_causal_evidence
from backend.services.decision_service import compute_hypothesis_go_no_go

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
   b) A SPECIFIC drug from the evidence — use exact name if available, OR use
      "Potential Inhibitor" / "Investigational Compound" if no drugs in evidence
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
    "simple_explanation": "2-3 sentences using ONE clear analogy.",
    "confidence_score": 0.0,
    "confidence_reasoning": "Cite exact evidence: protein score, drug phase, paper count.",
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

def compute_protein_score(hypothesis, pipeline_result):
    if not hypothesis.key_proteins:
        return 0.3
    scores = []
    for gene_symbol in hypothesis.key_proteins:
        for target in pipeline_result.protein_targets:
            if target.gene_symbol.upper() == gene_symbol.upper():
                scores.append(target.association_score)
                break
    return round(sum(scores) / len(scores), 4) if scores else 0.3


def compute_drug_score(hypothesis, pipeline_result):
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


def compute_paper_score(pipeline_result):
    total = len(pipeline_result.papers)
    if total >= 8:   return 1.0
    elif total >= 5: return 0.75
    elif total >= 2: return 0.5
    elif total == 1: return 0.25
    else:            return 0.0


def compute_fda_risk_penalty(hypothesis, pipeline_result):
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


def build_score_breakdown(p, d, pa, r, final):
    risk_label = (
        "High risk"   if r >= 0.8 else
        "Medium risk" if r >= 0.4 else
        "Low risk"    if r >  0.0 else
        "No FDA data"
    )
    return (
        f"Protein: {p:.2f}×0.4 | Drug phase: {d:.2f}×0.3 | "
        f"Papers: {pa:.2f}×0.2 | FDA penalty: -{r:.2f}×0.1 "
        f"({risk_label}) | Final: {final:.3f}"
    )


def rank_hypotheses(hypotheses, pipeline_result):
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

        print(f"   • {hyp.title[:50]}...\n"
              f"     protein={p:.2f} drug={d:.2f} "
              f"papers={pa:.2f} risk=-{r:.2f} → final={final:.4f}")

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

def get_mock_hypotheses(
    disease_name:    str,
    protein_targets: list = None,
    drugs:           list = None
) -> list:
    """
    Generate disease-specific fallback hypotheses using
    actual protein targets and drugs from the pipeline.
    Only used when GPT fails or no LLM key is configured.
    Never uses hardcoded Alzheimer data.
    """
    # Use actual proteins from analysis
    p1 = protein_targets[0].gene_symbol    if protein_targets and len(protein_targets) > 0 else "TARGET1"
    p2 = protein_targets[1].gene_symbol    if protein_targets and len(protein_targets) > 1 else "TARGET2"
    p3 = protein_targets[2].gene_symbol    if protein_targets and len(protein_targets) > 2 else "TARGET3"
    s1 = protein_targets[0].association_score if protein_targets and len(protein_targets) > 0 else 0.5
    s2 = protein_targets[1].association_score if protein_targets and len(protein_targets) > 1 else 0.3

    # Use actual drugs from analysis
    d1   = drugs[0].drug_name       if drugs and len(drugs) > 0 else "Investigational Compound"
    d2   = drugs[1].drug_name       if drugs and len(drugs) > 1 else "Potential Inhibitor"
    d3   = drugs[2].drug_name       if drugs and len(drugs) > 2 else "Combination Therapy"
    ph1  = drugs[0].clinical_phase  if drugs and len(drugs) > 0 else 0
    moa1 = drugs[0].mechanism       if drugs and len(drugs) > 0 else "mechanism under investigation"

    conf1 = min(0.85, round(s1 * 0.9, 2))
    conf2 = min(0.65, round(s2 * 0.8, 2))

    print(f"   ℹ️  Mock hypotheses using: proteins=[{p1},{p2},{p3}] drugs=[{d1},{d2}]")

    return [
        Hypothesis(
            title              = f"{p1} inhibition via {d1} in {disease_name}",
            explanation        = (
                f"{p1} shows the highest association score ({s1:.2f}) with {disease_name} "
                f"based on OpenTargets genetic and molecular evidence. "
                f"{d1} targets this protein through {moa1}. "
                f"Inhibiting {p1} may reduce disease progression by modulating "
                f"the primary pathological pathway in {disease_name}. "
                f"This approach is supported by the available protein-disease association data."
            ),
            simple_explanation = (
                f"Think of {p1} as a key driver of {disease_name}. "
                f"{d1} acts as a blocker to slow the disease process."
            ),
            confidence_score   = conf1,
            confidence_label   = "High" if conf1 >= 0.8 else "Medium-High" if conf1 >= 0.6 else "Medium",
            key_proteins       = [p1],
            key_drugs          = [d1],
            evidence_summary   = (
                f"{p1} has association score {s1:.2f} in OpenTargets; "
                f"{d1} is Phase {ph1 or 'unknown'} clinical candidate"
            ),
            reasoning_steps    = [
                f"Step 1 — Protein role: {p1} is the top-ranked protein for {disease_name} "
                f"with association score {s1:.2f}",
                f"Step 2 — Drug mechanism: {d1} acts via {moa1}",
                f"Step 3 — Pathway interaction: {d1} modulates {p1} activity "
                f"reducing downstream disease signaling",
                f"Step 4 — Therapeutic logic: Highest association score suggests "
                f"strongest causal link to {disease_name}"
            ]
        ),
        Hypothesis(
            title              = f"{p2} modulation via {d2} in {disease_name}",
            explanation        = (
                f"{p2} represents a secondary protein target with documented association "
                f"to {disease_name} (score: {s2:.2f}). "
                f"{d2} targeting {p2} could provide therapeutic benefit through "
                f"an alternative pathway. "
                f"This approach may be particularly relevant for patients who do not "
                f"respond to {p1}-targeted therapy in {disease_name}."
            ),
            simple_explanation = (
                f"{p2} is a secondary target in {disease_name}. "
                f"{d2} offers an alternative treatment route."
            ),
            confidence_score   = conf2,
            confidence_label   = "Medium-High" if conf2 >= 0.6 else "Medium",
            key_proteins       = [p2],
            key_drugs          = [d2],
            evidence_summary   = (
                f"{p2} has association score {s2:.2f}; "
                f"{d2} is an investigational candidate for this pathway"
            ),
            reasoning_steps    = [
                f"Step 1 — Protein role: {p2} has documented involvement "
                f"in {disease_name} pathology (score: {s2:.2f})",
                f"Step 2 — Drug mechanism: {d2} modulates {p2} activity",
                f"Step 3 — Pathway interaction: {p2} and {p1} may act "
                f"in complementary pathways",
                f"Step 4 — Therapeutic logic: Alternative target provides "
                f"treatment option for non-responders to {p1}-targeted therapy"
            ]
        ),
        Hypothesis(
            title              = f"Combination targeting {p1} and {p3} via {d3} in {disease_name}",
            explanation        = (
                f"Simultaneously targeting {p1} and {p3} may provide synergistic "
                f"therapeutic effects in {disease_name}. "
                f"Both proteins show association with the disease, suggesting they "
                f"may act in related or complementary pathways. "
                f"{d3} approaches addressing both targets could overcome "
                f"the limitations of single-target therapy in {disease_name}."
            ),
            simple_explanation = (
                f"Attacking {disease_name} from two angles at once — "
                f"targeting both {p1} and {p3} simultaneously."
            ),
            confidence_score   = round(conf2 * 0.8, 2),
            confidence_label   = "Medium",
            key_proteins       = [p1, p3],
            key_drugs          = [d3],
            evidence_summary   = (
                f"Multi-target strategy using {p1} and {p3} co-association "
                f"in {disease_name}"
            ),
            reasoning_steps    = [
                f"Step 1 — Protein role: Both {p1} and {p3} are associated "
                f"with {disease_name}",
                f"Step 2 — Drug mechanism: {d3} addresses multiple targets",
                f"Step 3 — Pathway interaction: Dual inhibition prevents "
                f"pathway compensation",
                f"Step 4 — Therapeutic logic: Reduces risk of single-target resistance"
            ]
        ),
    ]


# ── 5. Helper Functions ───────────────────────────────────────

def calculate_confidence_label(score: float) -> str:
    if score >= 0.8:   return "High"
    elif score >= 0.6: return "Medium-High"
    elif score >= 0.4: return "Medium"
    elif score >= 0.2: return "Low-Medium"
    else:              return "Low"


def validate_hypothesis_quality(hyp_data: dict) -> tuple:
    proteins    = hyp_data.get("key_proteins", [])
    drugs       = hyp_data.get("key_drugs", [])
    explanation = hyp_data.get("explanation", "")
    reasoning   = hyp_data.get("reasoning_steps", [])

    if not proteins:
        return False, "No key_proteins tagged"
    if not drugs:
        return False, "No key_drugs tagged"
    if len(explanation) < 100:
        return False, f"Explanation too short ({len(explanation)} chars)"
    if len(reasoning) < 2:
        return False, f"Insufficient reasoning steps ({len(reasoning)})"

    vague_phrases = ["may play a role", "could be involved", "might help with"]
    for phrase in vague_phrases:
        if phrase.lower() in explanation.lower():
            return False, f"Contains vague phrase: '{phrase}'"

    pathway_keywords = [
        "pathway", "cascade", "receptor", "inhibit", "modulate",
        "cleav", "aggregat", "secretase", "kinase", "signaling"
    ]
    if not any(kw in explanation.lower() for kw in pathway_keywords):
        return False, "No pathway/mechanism terminology detected"

    return True, "OK"


def parse_hypothesis_response(
    raw_json:        str,
    disease_name:    str,
    protein_targets: list = None,
    drugs:           list = None
) -> list:
    """
    Parse LLM JSON response into Hypothesis objects.
    Falls back to disease-specific mock hypotheses on failure.
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
            print("   ⚠️  All hypotheses failed validation — using disease-specific mocks")
            # ← FIXED: pass real proteins and drugs
            return get_mock_hypotheses(disease_name, protein_targets, drugs)

        print(f"   ✅ Parsed {len(hypotheses)} valid hypotheses")
        return hypotheses

    except json.JSONDecodeError as e:
        print(f"   ❌ JSON parse error: {e}")
        # ← FIXED: pass real proteins and drugs
        return get_mock_hypotheses(disease_name, protein_targets, drugs)


# ── 6. Stage Functions ────────────────────────────────────────

def add_causal_analysis(hypotheses, pipeline_result):
    from backend.models.schemas import CausalAnalysis, CausalEvidence

    print("\n🔬 Running causal reasoning analysis...")
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
        print(f"   • {hyp.title[:50]}...\n"
              f"     Causal: {hyp.causal_analysis.causal_label} "
              f"(score: {hyp.causal_analysis.causal_score:.2f}) | "
              f"hits: {causal_data['total_causal_hits']} | "
              f"verbs: {causal_data['causal_verbs_found'][:3]}")

    return hypotheses


def generate_validation_suggestions(hypotheses, pipeline_result):
    from backend.models.schemas import ValidationSuggestion

    if LLM_PROVIDER == "mock" or client is None:
        for hyp in hypotheses:
            hyp.validation_suggestion = _mock_validation(hyp)
        return hypotheses

    print("\n🧪 Generating experimental validation suggestions...")

    hyp_list = "\n\n".join([
        f"Hypothesis {i+1}:\nTitle: {hyp.title}\n"
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

Return ONLY a JSON array with exactly {len(hypotheses)} objects:
[
  {{
    "hypothesis_index": 0,
    "validation_type": "In-vitro",
    "experiment_title": "Short name (max 8 words)",
    "experiment_description": "2-3 sentences describing protocol.",
    "required_tools": ["tool1", "tool2", "tool3"],
    "expected_outcome": "One sentence: what does success look like?",
    "estimated_timeline": "X-Y months",
    "difficulty": "Low"
  }}
]
VALIDATION TYPE: Phase 4 → Clinical, Phase 2-3 → In-vivo, Phase 1 → In-vitro
DIFFICULTY: Low=1-3mo, Medium=3-6mo, High=6+mo
Return ONLY valid JSON. No markdown.
"""

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "Expert experimental biologist. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3, max_tokens=1500,
        )
        raw = response.choices[0].message.content.strip()
        print(f"   ✅ Validation LLM responded ({len(raw)} chars)")
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw   = "\n".join(lines[1:-1])

        suggestions = json.loads(raw)
        for item in suggestions:
            idx = item.get("hypothesis_index", 0)
            if idx < len(hypotheses):
                v_type  = item.get("validation_type", "In-vitro")
                v_color = {"In-vitro":"#3b82f6","In-vivo":"#8b5cf6","Clinical":"#f59e0b"}.get(v_type,"#64748b")
                diff    = item.get("difficulty","Medium")
                d_color = {"Low":"#22c55e","Medium":"#f59e0b","High":"#ef4444"}.get(diff,"#64748b")
                hypotheses[idx].validation_suggestion = ValidationSuggestion(
                    validation_type        = v_type,
                    validation_color       = v_color,
                    experiment_title       = item.get("experiment_title",""),
                    experiment_description = item.get("experiment_description",""),
                    required_tools         = item.get("required_tools",[]),
                    expected_outcome       = item.get("expected_outcome",""),
                    estimated_timeline     = item.get("estimated_timeline",""),
                    difficulty             = diff,
                    difficulty_color       = d_color
                )
                print(f"   • {hypotheses[idx].title[:45]}...\n"
                      f"     → {v_type} | {diff} | {item.get('estimated_timeline','?')}")

    except Exception as e:
        print(f"   ⚠️  Validation generation error: {e}")
        for hyp in hypotheses:
            if not hyp.validation_suggestion:
                hyp.validation_suggestion = _mock_validation(hyp)

    return hypotheses


def _mock_validation(hyp):
    from backend.models.schemas import ValidationSuggestion
    drug       = hyp.key_drugs[0]    if hyp.key_drugs    else "the compound"
    protein    = hyp.key_proteins[0] if hyp.key_proteins else "the target"
    drug_upper = drug.upper()
    if any(x in drug_upper for x in ["MAB","UMAB","ZUMAB","NUMAB"]):
        v_type, v_color = "Clinical", "#f59e0b"
    elif any(x in drug_upper for x in ["STAT","CEMAB"]):
        v_type, v_color = "In-vivo", "#8b5cf6"
    else:
        v_type, v_color = "In-vitro", "#3b82f6"

    return ValidationSuggestion(
        validation_type        = v_type,
        validation_color       = v_color,
        experiment_title       = f"{protein} activity assay with {drug}",
        experiment_description = (
            f"Treat {protein}-expressing cell lines with increasing "
            f"concentrations of {drug}. Measure protein activity and "
            f"downstream pathway markers using standard biochemical assays."
        ),
        required_tools     = ["Cell culture facility","Western blot","ELISA kit","Flow cytometer"],
        expected_outcome   = f"Dose-dependent reduction in {protein} activity.",
        estimated_timeline = "3-6 months",
        difficulty         = "Medium",
        difficulty_color   = "#f59e0b"
    )


def generate_hypothesis_critiques(hypotheses, pipeline_result):
    from backend.models.schemas import HypothesisCritique

    if LLM_PROVIDER == "mock" or client is None:
        for hyp in hypotheses:
            hyp.critique = _mock_critique(hyp)
        return hypotheses

    print("\n🔍 Generating hypothesis critiques...")

    hyp_list = "\n\n".join([
        f"Hypothesis {i+1}:\nTitle: {hyp.title}\n"
        f"Protein: {', '.join(hyp.key_proteins)}\n"
        f"Drug: {', '.join(hyp.key_drugs)}\n"
        f"Confidence: {hyp.confidence_score}\n"
        f"Explanation: {hyp.explanation[:250]}"
        for i, hyp in enumerate(hypotheses)
    ])

    prompt = f"""
You are a senior peer reviewer and critical biomedical scientist.
Critically evaluate each hypothesis for {pipeline_result.disease_name}.

HYPOTHESES:
{hyp_list}

Return ONLY a JSON array with exactly {len(hypotheses)} objects:
[
  {{
    "hypothesis_index": 0,
    "overall_assessment": "One sentence verdict",
    "weaknesses": ["Weakness 1","Weakness 2","Weakness 3"],
    "contradictory_evidence": ["Contradiction 1","Contradiction 2"],
    "risks": ["Risk 1","Risk 2"],
    "confidence_impact": "One sentence on confidence impact",
    "salvage_suggestion": "One concrete suggestion",
    "critique_severity": "Moderate"
  }}
]
SEVERITY: Minor / Moderate / Major. Return ONLY valid JSON.
"""

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role":"system","content":"Rigorous peer reviewer. Return only valid JSON."},
                {"role":"user","content":prompt}
            ],
            temperature=0.3, max_tokens=2000,
        )
        raw = response.choices[0].message.content.strip()
        print(f"   ✅ Critique LLM responded ({len(raw)} chars)")
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw   = "\n".join(lines[1:-1])

        severity_colors = {"Minor":"#22c55e","Moderate":"#f59e0b","Major":"#ef4444"}
        for item in json.loads(raw):
            idx = item.get("hypothesis_index",0)
            if idx < len(hypotheses):
                sev = item.get("critique_severity","Moderate")
                hypotheses[idx].critique = HypothesisCritique(
                    overall_assessment     = item.get("overall_assessment",""),
                    weaknesses             = item.get("weaknesses",[]),
                    contradictory_evidence = item.get("contradictory_evidence",[]),
                    risks                  = item.get("risks",[]),
                    confidence_impact      = item.get("confidence_impact",""),
                    salvage_suggestion     = item.get("salvage_suggestion",""),
                    critique_severity      = sev,
                    severity_color         = severity_colors.get(sev,"#f59e0b")
                )
                print(f"   • {hypotheses[idx].title[:45]}...\n"
                      f"     Severity: {sev} | "
                      f"Weaknesses: {len(item.get('weaknesses',[]))} | "
                      f"Risks: {len(item.get('risks',[]))}")

    except Exception as e:
        print(f"   ⚠️  Critique generation error: {e}")
        for hyp in hypotheses:
            if not hyp.critique:
                hyp.critique = _mock_critique(hyp)

    return hypotheses


def _mock_critique(hyp):
    from backend.models.schemas import HypothesisCritique
    protein = hyp.key_proteins[0] if hyp.key_proteins else "the target"
    drug    = hyp.key_drugs[0]    if hyp.key_drugs    else "the compound"
    return HypothesisCritique(
        overall_assessment     = "Hypothesis is plausible but requires additional validation.",
        weaknesses             = [
            f"Limited direct evidence linking {drug} to {protein} modulation.",
            "Association score reflects correlation, not confirmed causality.",
            "Insufficient paper evidence to rule out off-target effects."
        ],
        contradictory_evidence = [
            "Some trials targeting similar pathways show limited benefit.",
            "Systemic exposure and target engagement not confirmed."
        ],
        risks                  = [
            f"FDA adverse event signals require monitoring for {drug}.",
            "Pathway redundancy may reduce therapeutic impact."
        ],
        confidence_impact      = "Reduces certainty from High to Medium-High.",
        salvage_suggestion     = f"Design in-vitro assay measuring {protein} activity after {drug} treatment.",
        critique_severity      = "Moderate",
        severity_color         = "#f59e0b"
    )


def add_hypothesis_uncertainty(hypotheses, pipeline_result):
    from backend.services.pipeline_service import compute_uncertainty

    print("\n📐 Computing per-hypothesis uncertainty...")
    for hyp in hypotheses:
        hyp.uncertainty = compute_uncertainty(pipeline_result, hyp)
        print(f"   • {hyp.title[:45]}...\n"
              f"     Uncertainty: {hyp.uncertainty.uncertainty_label} "
              f"({hyp.uncertainty.uncertainty_score:.3f})")
    return hypotheses


def add_hypothesis_go_no_go(hypotheses, pipeline_result):
    from backend.services.decision_service import compute_hypothesis_go_no_go

    print("\n🚦 Computing GO/NO-GO decisions...")
    for hyp in hypotheses:
        hyp.go_no_go = compute_hypothesis_go_no_go(hyp, pipeline_result)
        print(f"   {hyp.go_no_go.decision_emoji} {hyp.go_no_go.decision}"
              f" — {hyp.title[:45]}...")
    return hypotheses


def generate_failure_predictions(hypotheses, pipeline_result):
    from backend.models.schemas import FailurePrediction, FailureReason

    if LLM_PROVIDER == "mock" or client is None:
        for hyp in hypotheses:
            hyp.failure_prediction = _mock_failure_prediction(hyp)
        return hypotheses

    print("\n⚠️  Predicting failure risks...")

    hyp_list = "\n\n".join([
        f"Hypothesis {i+1}:\nTitle: {hyp.title}\n"
        f"Drug: {', '.join(hyp.key_drugs)}\n"
        f"Protein: {', '.join(hyp.key_proteins)}\n"
        f"Mechanism: {hyp.explanation[:200]}\n"
        f"Clinical Phase: {_get_drug_phase(hyp.key_drugs, pipeline_result)}\n"
        f"FDA Risk: {_get_drug_risk(hyp.key_drugs, pipeline_result)}"
        for i, hyp in enumerate(hypotheses)
    ])

    prompt = f"""
You are a drug development expert with deep knowledge of clinical trial failures.
Analyze each hypothesis for {pipeline_result.disease_name} and predict failure risks.

HYPOTHESES:
{hyp_list}

CONTEXT:
- Disease: {pipeline_result.disease_name}
- Papers: {len(pipeline_result.papers)}
- Evidence: {pipeline_result.evidence_strength.evidence_label if pipeline_result.evidence_strength else 'Unknown'}

Return ONLY a JSON array with exactly {len(hypotheses)} objects:
[
  {{
    "hypothesis_index": 0,
    "failure_risk_score": 0.45,
    "top_failure_reason": "Single most likely failure mode",
    "historical_context": "1-2 sentences about similar failed drugs",
    "success_probability": 0.65,
    "failure_reasons": [
      {{
        "category": "Safety",
        "reason": "Specific failure reason",
        "severity": "High",
        "evidence": "Supporting evidence",
        "mitigation": "How to address"
      }}
    ],
    "recommended_safeguards": ["Safeguard 1","Safeguard 2"]
  }}
]

IMPORTANT: success_probability MUST be a decimal 0.0-1.0 (e.g. 0.65 NOT 65).
FAILURE RISK: 0.0-0.3=Low, 0.3-0.5=Medium, 0.5-0.7=High, 0.7-1.0=Very High
SUCCESS PROBABILITY: Phase 4=0.60-0.80, Phase 3=0.40-0.60, Phase 2=0.20-0.40
CATEGORIES: Safety, Efficacy, Mechanism, Trial Design, Market
Return ONLY valid JSON. No markdown.
"""

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role":"system","content":"Drug development expert. Return only valid JSON."},
                {"role":"user","content":prompt}
            ],
            temperature=0.3, max_tokens=2000,
        )
        raw = response.choices[0].message.content.strip()
        print(f"   ✅ Failure prediction LLM responded ({len(raw)} chars)")
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw   = "\n".join(lines[1:-1])

        risk_colors = {"Low":"#22c55e","Medium":"#f59e0b",
                       "High":"#f97316","Very High":"#ef4444"}

        for item in json.loads(raw):
            idx = item.get("hypothesis_index",0)
            if idx >= len(hypotheses):
                continue

            risk_score = max(0.0, min(1.0, float(item.get("failure_risk_score",0.5))))

            if risk_score >= 0.7:   risk_label = "Very High"
            elif risk_score >= 0.5: risk_label = "High"
            elif risk_score >= 0.3: risk_label = "Medium"
            else:                   risk_label = "Low"

            raw_sp       = float(item.get("success_probability", 0.5))
            success_prob = raw_sp / 100.0 if raw_sp > 1.0 else raw_sp
            success_prob = round(max(0.0, min(1.0, success_prob)), 3)

            reasons = [
                FailureReason(
                    category   = r.get("category",""),
                    reason     = r.get("reason",""),
                    severity   = r.get("severity","Medium"),
                    evidence   = r.get("evidence",""),
                    mitigation = r.get("mitigation","")
                )
                for r in item.get("failure_reasons",[])
            ]

            hypotheses[idx].failure_prediction = FailurePrediction(
                failure_risk_score     = round(risk_score, 3),
                failure_risk_label     = risk_label,
                failure_risk_color     = risk_colors.get(risk_label,"#64748b"),
                failure_reasons        = reasons,
                top_failure_reason     = item.get("top_failure_reason",""),
                historical_context     = item.get("historical_context",""),
                success_probability    = success_prob,
                recommended_safeguards = item.get("recommended_safeguards",[])
            )

            hyp = hypotheses[idx]
            print(f"   • {hyp.title[:45]}...\n"
                  f"     Failure risk: {risk_label} ({risk_score:.2f}) | "
                  f"Success prob: {success_prob:.0%} | "
                  f"Reasons: {len(reasons)}")

    except Exception as e:
        print(f"   ⚠️  Failure prediction error: {e}")
        for hyp in hypotheses:
            if not hyp.failure_prediction:
                hyp.failure_prediction = _mock_failure_prediction(hyp)

    return hypotheses


def _get_drug_phase(drug_names, pipeline_result):
    for name in drug_names:
        for drug in pipeline_result.drugs:
            if drug.drug_name.upper() == name.upper():
                return str(drug.clinical_phase or "Unknown")
    return "Unknown"


def _get_drug_risk(drug_names, pipeline_result):
    for name in drug_names:
        for drug in pipeline_result.drugs:
            if drug.drug_name.upper() == name.upper():
                return drug.risk_level
    return "Unknown"


def _mock_failure_prediction(hyp):
    from backend.models.schemas import FailurePrediction, FailureReason
    drug    = hyp.key_drugs[0]    if hyp.key_drugs    else "the compound"
    protein = hyp.key_proteins[0] if hyp.key_proteins else "the target"
    return FailurePrediction(
        failure_risk_score   = 0.45,
        failure_risk_label   = "Medium",
        failure_risk_color   = "#f59e0b",
        top_failure_reason   = f"Pathway redundancy may limit {drug}'s efficacy.",
        historical_context   = "Multiple drugs targeting similar pathways failed Phase 3 due to insufficient efficacy.",
        success_probability  = 0.45,
        failure_reasons      = [
            FailureReason(
                category="Efficacy", reason="Biomarker improvement may not translate to clinical benefit",
                severity="High", evidence="Historical precedent in similar drug class",
                mitigation="Include clinical endpoints alongside biomarker measures"
            ),
            FailureReason(
                category="Mechanism", reason=f"Pathway redundancy around {protein} target",
                severity="Medium", evidence="Known compensatory pathways in literature",
                mitigation="Consider combination therapy approach"
            ),
            FailureReason(
                category="Safety", reason="Long-term safety profile not fully established",
                severity="Medium", evidence="Limited long-term follow-up data",
                mitigation="Design extended safety monitoring protocol"
            )
        ],
        recommended_safeguards=[
            "Include biomarker + clinical endpoints",
            "Design adaptive trial with interim analysis",
            "Monitor for pathway compensation in pre-clinical models",
            "Establish clear stopping rules for safety signals"
        ]
    )


def generate_evidence_explanation(hypothesis, detail_level="scientist"):
    if client is None:
        return hypothesis.explanation
    prompt = (
        f"Explain simply with analogy in 3-4 sentences.\n"
        f"Hypothesis: {hypothesis.title}\nContext: {hypothesis.explanation[:300]}"
        if detail_level == "simple"
        else
        f"Expand with molecular pathway, validation, implications, limitations. 4-5 sentences.\n"
        f"Hypothesis: {hypothesis.title}\nContext: {hypothesis.explanation[:300]}"
    )
    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}],
            temperature=0.3, max_tokens=400,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Explanation unavailable: {str(e)}"


def compute_time_to_impact(
    hypothesis:      "Hypothesis",
    pipeline_result: DiseaseAnalysisResult
) -> "TimeToImpact":
    from backend.models.schemas import TimeToImpact

    drug_name  = hypothesis.key_drugs[0] if hypothesis.key_drugs else ""
    phase      = 0
    risk_level = "Unknown"

    for drug in pipeline_result.drugs:
        if drug.drug_name.upper() == drug_name.upper():
            phase      = drug.clinical_phase or 0
            risk_level = drug.risk_level
            break

    PHASE_DATA = {
        4: {"stage":"Phase 4 / FDA Approved","next":"Post-market surveillance + label expansion",
            "years_base":1.0,"years_range":"0–2 years","success":0.85,"speed":"Fast",
            "timeline":["Currently approved / Phase 4 post-market",
                        "Label expansion studies: 1–2 years",
                        "New indication approval: 2–4 years if applicable"]},
        3: {"stage":"Phase 3 Clinical Trial","next":"Complete Phase 3, file NDA/BLA with FDA",
            "years_base":3.0,"years_range":"2–5 years","success":0.58,"speed":"Medium",
            "timeline":["Complete ongoing Phase 3 trial: 1–3 years",
                        "FDA NDA/BLA submission and review: 1–2 years",
                        "Potential approval and launch: +6–12 months"]},
        2: {"stage":"Phase 2 Clinical Trial","next":"Complete Phase 2, design Phase 3, seek funding",
            "years_base":6.0,"years_range":"5–9 years","success":0.32,"speed":"Medium",
            "timeline":["Complete Phase 2 trials: 2–3 years",
                        "Design and fund Phase 3: 1–2 years",
                        "Phase 3 trials: 2–4 years",
                        "FDA review and approval: 1–2 years"]},
        1: {"stage":"Phase 1 Clinical Trial","next":"Complete Phase 1 safety, advance to Phase 2",
            "years_base":9.0,"years_range":"8–12 years","success":0.15,"speed":"Slow",
            "timeline":["Complete Phase 1 safety studies: 1–2 years",
                        "Phase 2 efficacy trials: 2–4 years",
                        "Phase 3 confirmatory trials: 3–5 years",
                        "FDA review and approval: 1–2 years"]},
        0: {"stage":"Preclinical / Research Stage","next":"Complete preclinical validation, file IND",
            "years_base":12.0,"years_range":"10–15 years","success":0.10,"speed":"Slow",
            "timeline":["Preclinical validation: 2–4 years",
                        "IND filing and Phase 1: 2–3 years",
                        "Phase 2 + Phase 3: 5–8 years",
                        "FDA review: 1–2 years"]},
    }

    data       = PHASE_DATA.get(phase, PHASE_DATA[0])
    years_base = data["years_base"]
    success    = data["success"]

    risk_adjustments = {
        "High":    (2.0, -0.20),
        "Medium":  (0.5, -0.05),
        "Low":     (0.0,  0.05),
        "Unknown": (1.0, -0.10)
    }
    year_adj, success_adj = risk_adjustments.get(risk_level, (1.0, -0.10))
    years_final   = round(years_base + year_adj, 1)
    success_final = round(max(0.05, min(0.95, success + success_adj)), 3)

    bottlenecks = []
    if risk_level == "High":
        bottlenecks.append("High FDA adverse event burden requires additional safety studies")
    if phase <= 2:
        bottlenecks.append("Multiple trial phases required before regulatory submission")
    if pipeline_result.evidence_strength and \
       pipeline_result.evidence_strength.evidence_label in ["Weak","Moderate"]:
        bottlenecks.append("Limited evidence base may slow regulatory acceptance")
    if not bottlenecks:
        bottlenecks.append("Strong profile — main bottleneck is standard regulatory timeline")

    speed_colors = {"Fast":"#22c55e","Medium":"#f59e0b","Slow":"#ef4444"}

    return TimeToImpact(
        years_to_market     = years_final,
        years_range         = data["years_range"],
        current_stage       = data["stage"],
        next_milestone      = data["next"],
        success_probability = success_final,
        speed_category      = data["speed"],
        speed_color         = speed_colors.get(data["speed"],"#64748b"),
        timeline_breakdown  = data["timeline"],
        key_bottlenecks     = bottlenecks
    )


def generate_executive_summaries(
    hypotheses:      list,
    pipeline_result: DiseaseAnalysisResult
) -> list:
    from backend.models.schemas import ExecutiveSummary

    if LLM_PROVIDER == "mock" or client is None:
        for hyp in hypotheses:
            hyp.executive_summary = _mock_executive_summary(hyp, pipeline_result.disease_name)
        return hypotheses

    print("\n📋 Generating executive summaries...")

    hyp_list = "\n\n".join([
        f"Hypothesis {i+1}:\n"
        f"Title: {hyp.title}\n"
        f"Drug: {', '.join(hyp.key_drugs)} (Phase {_get_drug_phase(hyp.key_drugs, pipeline_result)})\n"
        f"Protein: {', '.join(hyp.key_proteins)}\n"
        f"Score: {hyp.final_score:.0%}\n"
        f"Decision: {hyp.go_no_go.decision if hyp.go_no_go else 'Unknown'}\n"
        f"Explanation: {hyp.explanation[:200]}"
        for i, hyp in enumerate(hypotheses)
    ])

    prompt = f"""
You are a biotech communications expert writing for C-suite executives and investors.
Summarize each hypothesis for {pipeline_result.disease_name} in plain business language.
No jargon. Focus on: what it is, why it matters, what to do, what the risk is.

HYPOTHESES:
{hyp_list}

Return ONLY a JSON array with exactly {len(hypotheses)} objects:
[
  {{
    "hypothesis_index": 0,
    "headline": "One punchy sentence (max 15 words) — the elevator pitch",
    "body": "3-4 sentences for a non-scientist executive.",
    "market_opportunity": "One sentence about business/market value",
    "bottom_line": "One sentence: what decision should be made?"
  }}
]
Return ONLY valid JSON. No markdown.
"""

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role":"system","content":"Biotech communications expert. Return only valid JSON."},
                {"role":"user","content":prompt}
            ],
            temperature=0.4, max_tokens=1500,
        )
        raw = response.choices[0].message.content.strip()
        print(f"   ✅ Executive summary LLM responded ({len(raw)} chars)")
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw   = "\n".join(lines[1:-1])

        for item in json.loads(raw):
            idx = item.get("hypothesis_index",0)
            if idx < len(hypotheses):
                hypotheses[idx].executive_summary = ExecutiveSummary(
                    headline           = item.get("headline",""),
                    body               = item.get("body",""),
                    market_opportunity = item.get("market_opportunity",""),
                    bottom_line        = item.get("bottom_line",""),
                    audience_level     = "Executive"
                )
                print(f"   • {hypotheses[idx].title[:45]}...")
                print(f"     Headline: {item.get('headline','')[:50]}")

    except Exception as e:
        print(f"   ⚠️  Executive summary error: {e}")
        for hyp in hypotheses:
            if not hyp.executive_summary:
                hyp.executive_summary = _mock_executive_summary(hyp, pipeline_result.disease_name)

    return hypotheses


def _mock_executive_summary(hyp, disease_name: str = "this disease") -> "ExecutiveSummary":
    from backend.models.schemas import ExecutiveSummary
    drug    = hyp.key_drugs[0]    if hyp.key_drugs    else "this compound"
    protein = hyp.key_proteins[0] if hyp.key_proteins else "this target"
    return ExecutiveSummary(
        headline           = f"{drug} shows potential for treating {disease_name}",
        body               = (
            f"{drug} is a clinical-stage treatment targeting {protein}, "
            f"a key driver of {disease_name}. "
            f"Current evidence supports a {hyp.final_score:.0%} confidence score. "
            f"The drug has an established safety profile from clinical trials."
        ),
        market_opportunity = (
            f"{disease_name} represents a significant unmet medical need. "
            f"{drug} addresses this with a differentiated mechanism."
        ),
        bottom_line        = f"Recommend proceeding with validation studies for {drug} in {disease_name}.",
        audience_level     = "Executive"
    )


def generate_literature_review(
    pipeline_result: DiseaseAnalysisResult
) -> "LiteratureReview":
    from backend.models.schemas import LiteratureReview
    from datetime import datetime

    if LLM_PROVIDER == "mock" or client is None:
        return _mock_literature_review(pipeline_result)

    print("\n📄 Generating literature review...")

    best_hyp = None
    if pipeline_result.hypotheses:
        best_hyp = min(pipeline_result.hypotheses, key=lambda h: h.rank)

    proteins_str = ", ".join(
        [f"{p.gene_symbol} (score: {p.association_score:.2f})"
         for p in pipeline_result.protein_targets[:4]]
    )
    drugs_str = ", ".join(
        [f"{d.drug_name} (Phase {d.clinical_phase})"
         for d in pipeline_result.drugs[:4]]
    )
    papers_str = "\n".join(
        [f"- [{p.year}] {p.title[:70]}"
         for p in pipeline_result.papers[:5]]
    )

    prompt = f"""
You are a biomedical research writer. Generate a structured literature review
for {pipeline_result.disease_name}.

AVAILABLE EVIDENCE:
- Top proteins: {proteins_str}
- Known drugs: {drugs_str}
- Key papers:
{papers_str}
- Best hypothesis: {best_hyp.title if best_hyp else 'None'}
- Evidence strength: {pipeline_result.evidence_strength.evidence_label if pipeline_result.evidence_strength else 'Unknown'}

Return ONLY a JSON object:
{{
  "background": "2-3 sentences: what is {pipeline_result.disease_name}, prevalence, current treatment landscape",
  "current_research": "2-3 sentences: active research directions",
  "research_gaps": "2-3 sentences: unanswered questions",
  "proposed_hypothesis": "2-3 sentences: best hypothesis in scientific terms",
  "supporting_evidence": "2-3 sentences: specific evidence supporting this direction",
  "risks_limitations": "2-3 sentences: key risks and uncertainties",
  "conclusion": "2-3 sentences: overall assessment and next steps"
}}
Return ONLY valid JSON. No markdown.
"""

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role":"system","content":"Expert biomedical research writer. Return only valid JSON."},
                {"role":"user","content":prompt}
            ],
            temperature=0.3, max_tokens=1500,
        )
        raw = response.choices[0].message.content.strip()
        print(f"   ✅ Literature review LLM responded ({len(raw)} chars)")
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw   = "\n".join(lines[1:-1])

        data = json.loads(raw)
        return LiteratureReview(
            disease_name        = pipeline_result.disease_name,
            background          = data.get("background",""),
            current_research    = data.get("current_research",""),
            research_gaps       = data.get("research_gaps",""),
            proposed_hypothesis = data.get("proposed_hypothesis",""),
            supporting_evidence = data.get("supporting_evidence",""),
            risks_limitations   = data.get("risks_limitations",""),
            conclusion          = data.get("conclusion",""),
            generated_at        = datetime.now().strftime("%Y-%m-%d %H:%M")
        )

    except Exception as e:
        print(f"   ⚠️  Literature review error: {e}")
        return _mock_literature_review(pipeline_result)


def _mock_literature_review(pipeline_result) -> "LiteratureReview":
    from backend.models.schemas import LiteratureReview
    from datetime import datetime
    disease  = pipeline_result.disease_name
    proteins = ", ".join([p.gene_symbol for p in pipeline_result.protein_targets[:3]])
    drugs    = ", ".join([d.drug_name   for d in pipeline_result.drugs[:3]])
    return LiteratureReview(
        disease_name        = disease,
        background          = (
            f"{disease} is a complex disorder with significant unmet medical need. "
            f"Current treatments address symptoms but do not modify disease progression. "
            f"Significant research investment is ongoing to find disease-modifying therapies."
        ),
        current_research    = (
            f"Research has focused on key protein targets including {proteins}. "
            f"Multiple drug candidates including {drugs} have entered clinical evaluation. "
            f"The field is moving toward combination approaches and precision medicine strategies."
        ),
        research_gaps       = (
            "Direct causality between protein targets and disease progression remains incompletely established. "
            "Long-term efficacy of current drug candidates is uncertain. "
            "Biomarker development for patient stratification lags behind drug development."
        ),
        proposed_hypothesis = (
            f"The leading hypothesis proposes targeting key proteins in the {disease} pathway. "
            "This approach addresses core pathological mechanisms based on available evidence. "
            "Validation studies are needed to confirm causal relationships."
        ),
        supporting_evidence = (
            "OpenTargets association scores support protein-disease links. "
            "FDA-approved or late-stage clinical drugs provide mechanistic validation. "
            "Research papers from PubMed support pathway involvement."
        ),
        risks_limitations   = (
            "Correlation vs causation remains a key limitation. "
            "Safety signals detected in FDA FAERS require monitoring. "
            "Evidence base is moderate and may not fully support all conclusions."
        ),
        conclusion          = (
            f"Based on current evidence, {disease} represents a tractable target for intervention. "
            "The identified protein-drug combinations warrant further investigation. "
            "Experimental validation is recommended as an immediate next step."
        ),
        generated_at        = datetime.now().strftime("%Y-%m-%d %H:%M")
    )


# ── 7. Main Generation Function ───────────────────────────────

def generate_hypotheses(
    pipeline_result: DiseaseAnalysisResult,
    num_hypotheses:  int = 3
) -> list:
    """Generate hypotheses via LLM then run all 9 analysis stages."""

    if LLM_PROVIDER == "mock" or client is None:
        print("   ℹ️  Using mock hypotheses (no LLM key configured)")
        # ← FIXED: pass real proteins and drugs
        hypotheses = get_mock_hypotheses(
            pipeline_result.disease_name,
            pipeline_result.protein_targets,
            pipeline_result.drugs
        )
    else:
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
                model=LLM_MODEL,
                messages=[
                    {"role":"system","content":SYSTEM_PROMPT},
                    {"role":"user","content":user_prompt}
                ],
                temperature=0.4, max_tokens=3000,
            )
            raw_response = response.choices[0].message.content.strip()
            print(f"   ✅ LLM responded ({len(raw_response)} chars)")
            # ← FIXED: pass real proteins and drugs to parse function
            hypotheses = parse_hypothesis_response(
                raw_response,
                pipeline_result.disease_name,
                pipeline_result.protein_targets,
                pipeline_result.drugs
            )
        except Exception as e:
            print(f"   ❌ LLM error: {e}")
            print("   ℹ️  Falling back to disease-specific mock hypotheses")
            # ← FIXED: pass real proteins and drugs
            hypotheses = get_mock_hypotheses(
                pipeline_result.disease_name,
                pipeline_result.protein_targets,
                pipeline_result.drugs
            )

    # ── All 9 stages ──────────────────────────────────────────
    ranked = rank_hypotheses(hypotheses, pipeline_result)
    ranked = add_causal_analysis(ranked, pipeline_result)
    ranked = generate_validation_suggestions(ranked, pipeline_result)
    ranked = generate_hypothesis_critiques(ranked, pipeline_result)
    ranked = add_hypothesis_uncertainty(ranked, pipeline_result)
    ranked = add_hypothesis_go_no_go(ranked, pipeline_result)
    ranked = generate_failure_predictions(ranked, pipeline_result)

    # Stage 8: Time-to-impact
    print("\n⏱️  Computing time-to-impact estimates...")
    for hyp in ranked:
        hyp.time_to_impact = compute_time_to_impact(hyp, pipeline_result)
        tti = hyp.time_to_impact
        print(f"   • {hyp.title[:45]}...\n"
              f"     {tti.speed_category} track | "
              f"{tti.years_range} | "
              f"Success: {tti.success_probability:.0%}")

    # Stage 9: Executive summaries
    ranked = generate_executive_summaries(ranked, pipeline_result)

    return ranked


# ── Quick test ────────────────────────────────────────────────
if __name__ == "__main__":
    from backend.services.pipeline_service import run_data_pipeline

    print("🧬 Causyn AI V5 — Mock Fallback Test")
    print("=" * 55)

    # Test that mock uses real disease proteins
    for disease in ["Alkaptonuria", "Alzheimer disease", "Parkinson disease"]:
        print(f"\n{'='*55}")
        print(f"Testing: {disease}")
        result = run_data_pipeline(disease, 5, 4, 3)
        mocks  = get_mock_hypotheses(
            disease,
            result.protein_targets,
            result.drugs
        )
        print(f"Mock hypothesis 1: {mocks[0].title}")
        print(f"Mock hypothesis 2: {mocks[1].title}")
        print(f"Mock hypothesis 3: {mocks[2].title}")

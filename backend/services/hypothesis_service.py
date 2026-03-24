# backend/services/hypothesis_service.py
# V4 — All stages: Rank, Causal, Validation, Critique,
#       Uncertainty, GO/NO-GO, Failure Prediction

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

def get_mock_hypotheses(disease_name: str) -> list:
    return [
        Hypothesis(
            title             = f"PSEN1 gamma-secretase inhibition via Nirogacestat in {disease_name}",
            explanation       = "PSEN1 encodes presenilin-1, the catalytic subunit of gamma-secretase which cleaves APP into amyloid-beta. Nirogacestat blocks this cleavage, reducing neurotoxic amyloid-beta42 production targeting the amyloid cascade directly.",
            simple_explanation= "Think of PSEN1 as scissors cutting a protein into toxic pieces. Nirogacestat acts like a blade guard.",
            confidence_score  = 0.82,
            confidence_label  = "High",
            key_proteins      = ["PSEN1"],
            key_drugs         = ["NIROGACESTAT"],
            evidence_summary  = "PSEN1 highest association score (0.867), Nirogacestat Phase 4"
        ),
        Hypothesis(
            title             = "Lecanemab APP clearance via amyloidogenic pathway in {disease_name}",
            explanation       = "APP-derived amyloid-beta oligomers drive neurodegeneration. Lecanemab targets these for clearance in the amyloidogenic pathway.",
            simple_explanation= "Alzheimer's is like a clogged drain. Lecanemab is drain cleaner.",
            confidence_score  = 0.71,
            confidence_label  = "Medium-High",
            key_proteins      = ["APP"],
            key_drugs         = ["LECANEMAB"],
            evidence_summary  = "APP score 0.854; Lecanemab FDA-approved Phase 4"
        ),
        Hypothesis(
            title             = "GRIN1 NMDA modulation protects against excitotoxicity in {disease_name}",
            explanation       = "GRIN1 mediates glutamate excitotoxicity via NMDA receptor pathway. NMDA antagonists reduce excitotoxic calcium influx.",
            simple_explanation= "Brain cells get overstimulated. GRIN1 is the volume knob.",
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


def validate_hypothesis_quality(hyp_data: dict) -> tuple:
    proteins  = hyp_data.get("key_proteins", [])
    drugs     = hyp_data.get("key_drugs", [])
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


def parse_hypothesis_response(raw_json: str, disease_name: str) -> list:
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
            print("   ⚠️  All hypotheses failed validation — using mocks")
            return get_mock_hypotheses(disease_name)

        print(f"   ✅ Parsed {len(hypotheses)} valid hypotheses")
        return hypotheses

    except json.JSONDecodeError as e:
        print(f"   ❌ JSON parse error: {e}")
        return get_mock_hypotheses(disease_name)


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
                v_type = item.get("validation_type", "In-vitro")
                v_color= {"In-vitro":"#3b82f6","In-vivo":"#8b5cf6","Clinical":"#f59e0b"}.get(v_type,"#64748b")
                diff   = item.get("difficulty","Medium")
                d_color= {"Low":"#22c55e","Medium":"#f59e0b","High":"#ef4444"}.get(diff,"#64748b")
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
    drug    = hyp.key_drugs[0] if hyp.key_drugs else "the compound"
    protein = hyp.key_proteins[0] if hyp.key_proteins else "the target"
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
        required_tools   = ["Cell culture facility","Western blot","ELISA kit","Flow cytometer"],
        expected_outcome = f"Dose-dependent reduction in {protein} activity.",
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
    drug    = hyp.key_drugs[0] if hyp.key_drugs else "the compound"
    return HypothesisCritique(
        overall_assessment     = "Hypothesis is plausible but requires additional validation.",
        weaknesses             = [
            f"Limited direct evidence linking {drug} to {protein} modulation.",
            "Association score reflects correlation, not confirmed causality.",
            "Insufficient paper evidence to rule out off-target effects."
        ],
        contradictory_evidence = [
            "Some trials targeting similar pathways show limited cognitive benefit.",
            "Blood-brain barrier penetration not confirmed in all populations."
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

FAILURE RISK SCORE: 0.0-0.3=Low, 0.3-0.5=Medium, 0.5-0.7=High, 0.7-1.0=Very High

SUCCESS PROBABILITY (decimal 0.0-1.0):
- Phase 4: 0.60-0.80
- Phase 3: 0.40-0.60
- Phase 2: 0.20-0.40
- Phase 1: 0.10-0.20

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

            if risk_score >= 0.7:        risk_label = "Very High"
            elif risk_score >= 0.5:      risk_label = "High"
            elif risk_score >= 0.3:      risk_label = "Medium"
            else:                        risk_label = "Low"

            # ── Fix: normalize success_probability ────────────
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
    drug    = hyp.key_drugs[0] if hyp.key_drugs else "the compound"
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
                category="Efficacy",reason="Biomarker improvement may not translate to clinical benefit",
                severity="High",evidence="Historical precedent in similar drug class",
                mitigation="Include cognitive endpoints alongside biomarker measures"
            ),
            FailureReason(
                category="Mechanism",reason=f"Pathway redundancy around {protein} target",
                severity="Medium",evidence="Known compensatory pathways in literature",
                mitigation="Consider combination therapy approach"
            ),
            FailureReason(
                category="Safety",reason="Long-term safety profile not fully established",
                severity="Medium",evidence="Limited long-term follow-up data",
                mitigation="Design extended safety monitoring protocol"
            )
        ],
        recommended_safeguards=[
            "Include biomarker + clinical cognitive endpoints",
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


# ── 7. Main Generation Function ───────────────────────────────

def generate_hypotheses(
    pipeline_result: DiseaseAnalysisResult,
    num_hypotheses:  int = 3
) -> list:
    """Generate hypotheses via LLM then run all 7 analysis stages."""

    if LLM_PROVIDER == "mock" or client is None:
        print("   ℹ️  Using mock hypotheses (no LLM key configured)")
        hypotheses = get_mock_hypotheses(pipeline_result.disease_name)
        ranked = rank_hypotheses(hypotheses, pipeline_result)
        ranked = add_causal_analysis(ranked, pipeline_result)
        ranked = generate_validation_suggestions(ranked, pipeline_result)
        ranked = generate_hypothesis_critiques(ranked, pipeline_result)
        ranked = add_hypothesis_uncertainty(ranked, pipeline_result)
        ranked = add_hypothesis_go_no_go(ranked, pipeline_result)
        ranked = generate_failure_predictions(ranked, pipeline_result)
        return ranked

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
        hypotheses = parse_hypothesis_response(raw_response, pipeline_result.disease_name)

    except Exception as e:
        print(f"   ❌ LLM error: {e}")
        print("   ℹ️  Falling back to mock hypotheses")
        hypotheses = get_mock_hypotheses(pipeline_result.disease_name)

    # ── All 7 stages ──────────────────────────────────────────
    ranked = rank_hypotheses(hypotheses, pipeline_result)
    ranked = add_causal_analysis(ranked, pipeline_result)
    ranked = generate_validation_suggestions(ranked, pipeline_result)
    ranked = generate_hypothesis_critiques(ranked, pipeline_result)
    ranked = add_hypothesis_uncertainty(ranked, pipeline_result)
    ranked = add_hypothesis_go_no_go(ranked, pipeline_result)
    ranked = generate_failure_predictions(ranked, pipeline_result)

    return ranked


# ── Quick test ────────────────────────────────────────────────
if __name__ == "__main__":
    from backend.services.pipeline_service import run_data_pipeline

    print("🧬 AI Scientist V4 — Full Pipeline Test")
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

    medals = {1:"🥇",2:"🥈",3:"🥉"}
    for h in hypotheses:
        medal = medals.get(h.rank, f"#{h.rank}")
        gng   = h.go_no_go
        fp    = h.failure_prediction
        print(f"\n{medal} Rank {h.rank} — Final Score: {h.final_score:.4f}")
        print(f"   Title       : {h.title}")
        print(f"   Confidence  : {h.confidence_score} ({h.confidence_label})")
        print(f"   Decision    : {gng.decision_emoji} {gng.decision}" if gng else "   Decision: N/A")
        print(f"   Failure Risk: {fp.failure_risk_label} | Success: {fp.success_probability:.0%}" if fp else "   Failure: N/A")
        print(f"   Breakdown   : {h.score_breakdown}")
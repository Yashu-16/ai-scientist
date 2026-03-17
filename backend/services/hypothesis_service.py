# backend/services/hypothesis_service.py
# V2 — includes Hypothesis Ranking Engine (Feature 1)

import os
import json
from dotenv import load_dotenv
from backend.models.schemas import Hypothesis, DiseaseAnalysisResult
from backend.services.pipeline_service import build_llm_context

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

    return rank_hypotheses(hypotheses, pipeline_result)


def generate_evidence_explanation(
    hypothesis:   Hypothesis,
    detail_level: str = "scientist"
) -> str:
    """Generate expanded explanation for a single hypothesis."""
    if client is None:
        return hypothesis.explanation

    prompt = (
        f"Explain simply with analogy in 3-4 sentences.\n"
        f"Hypothesis: {hypothesis.title}\nContext: {hypothesis.explanation[:300]}"
        if detail_level == "simple"
        else
        f"Expand with molecular pathway, validation approach, therapeutic implications, "
        f"limitations. 4-5 sentences.\n"
        f"Hypothesis: {hypothesis.title}\nContext: {hypothesis.explanation[:300]}"
    )

    try:
        response = client.chat.completions.create(
            model       = LLM_MODEL,
            messages    = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt}
            ],
            temperature = 0.3,
            max_tokens  = 400,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Explanation unavailable: {str(e)}"


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
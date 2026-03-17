# backend/services/hypothesis_service.py
# Purpose: Use OpenAI GPT to generate evidence-backed biomedical hypotheses
# from the structured data assembled by the pipeline.
#
# This is the CORE of the entire project.
# We use a carefully engineered prompt that:
#   1. Gives GPT the structured evidence context
#   2. Asks for specific hypothesis format
#   3. Requests confidence scoring with reasoning
#   4. Asks for both scientific and simple explanations

import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from backend.models.schemas import Hypothesis, DiseaseAnalysisResult
from backend.services.pipeline_service import build_llm_context

load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ── Prompt Templates ─────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert biomedical research scientist and drug discovery specialist.
Your role is to analyze structured scientific evidence and generate novel, evidence-backed 
biomedical hypotheses about disease mechanisms and potential treatments.

You always:
- Base hypotheses strictly on provided evidence
- Explain biological mechanisms clearly
- Acknowledge uncertainty appropriately  
- Generate actionable, testable hypotheses
- Provide both technical and simplified explanations

You never:
- Fabricate data or references
- Make claims beyond what evidence supports
- Give medical advice
"""

HYPOTHESIS_PROMPT_TEMPLATE = """
Analyze the following structured scientific evidence about {disease_name} and generate 
{num_hypotheses} distinct, evidence-backed biomedical hypotheses.

═══════════════════════════════════════
SCIENTIFIC EVIDENCE:
═══════════════════════════════════════
{evidence_context}

═══════════════════════════════════════
YOUR TASK:
═══════════════════════════════════════
Generate exactly {num_hypotheses} biomedical hypotheses. Each hypothesis must:

1. Connect at least ONE protein target with ONE drug/compound
2. Propose a specific biological mechanism
3. Be grounded in the provided evidence
4. Be novel and testable

Return your response as a JSON array with exactly this structure:
[
  {{
    "title": "One clear sentence stating the hypothesis (max 30 words)",
    "explanation": "2-3 paragraph scientific explanation covering: the protein's role, 
                   the drug's mechanism, why this combination matters for the disease, 
                   and what biological pathway is involved. Be specific and technical.",
    "simple_explanation": "2-3 sentences explaining this to a non-scientist. 
                          Use an analogy if helpful.",
    "confidence_score": 0.0,
    "confidence_reasoning": "2-3 sentences explaining WHY you assigned this confidence score.
                            Reference specific evidence that supports or limits confidence.",
    "key_proteins": ["GENE1", "GENE2"],
    "key_drugs": ["DrugName1"],
    "evidence_summary": "One sentence summarizing the key evidence supporting this hypothesis"
  }}
]

CONFIDENCE SCORE GUIDELINES:
- 0.8 - 1.0 : Multiple Phase 3/4 drugs + multiple supporting papers + high protein scores
- 0.6 - 0.79: Some clinical evidence OR strong protein association + papers
- 0.4 - 0.59: Preliminary evidence, early phase drugs, limited papers
- 0.2 - 0.39: Speculative, indirect evidence only
- Below 0.2 : Very weak or contradictory evidence

IMPORTANT: Return ONLY the JSON array. No markdown, no explanation outside the JSON.
"""


def calculate_confidence_label(score: float) -> str:
    """Convert numeric confidence score to human-readable label."""
    if score >= 0.8:
        return "High"
    elif score >= 0.6:
        return "Medium-High"
    elif score >= 0.4:
        return "Medium"
    elif score >= 0.2:
        return "Low-Medium"
    else:
        return "Low"


def generate_hypotheses(
    pipeline_result: DiseaseAnalysisResult,
    num_hypotheses: int = 3
) -> list[Hypothesis]:
    """
    Core function: Generate biomedical hypotheses using GPT.

    Args:
        pipeline_result : Complete pipeline result with proteins, drugs, papers
        num_hypotheses  : How many hypotheses to generate (default 3)

    Returns:
        List of validated Hypothesis objects
    """

    # Build the evidence context string
    evidence_context = build_llm_context(pipeline_result)

    # Fill in the prompt template
    user_prompt = HYPOTHESIS_PROMPT_TEMPLATE.format(
        disease_name    = pipeline_result.disease_name,
        num_hypotheses  = num_hypotheses,
        evidence_context= evidence_context
    )

    print(f"\n🤖 Sending evidence to GPT-4o-mini...")
    print(f"   Evidence context: {len(evidence_context)} characters")
    print(f"   Requesting: {num_hypotheses} hypotheses")

    try:
        response = client.chat.completions.create(
            model      = "gpt-4o-mini",   # Fast + cheap + smart enough for this
            messages   = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt}
            ],
            temperature= 0.4,    # Lower = more consistent, evidence-based output
            max_tokens = 3000,
            response_format={"type": "text"}
        )

        raw_response = response.choices[0].message.content.strip()
        print(f"   ✅ GPT responded ({len(raw_response)} chars)")

        # Parse JSON response
        hypotheses = parse_hypothesis_response(raw_response, pipeline_result.disease_name)
        return hypotheses

    except Exception as e:
        print(f"   ❌ GPT error: {e}")
        return []


def parse_hypothesis_response(raw_json: str, disease_name: str) -> list[Hypothesis]:
    """
    Parse and validate GPT's JSON response into Hypothesis objects.
    Handles common JSON formatting issues.
    """

    # Clean up response — remove markdown code blocks if present
    cleaned = raw_json.strip()
    if cleaned.startswith("```"):
        lines   = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1])  # Remove first and last line

    try:
        data = json.loads(cleaned)

        if not isinstance(data, list):
            print("  ⚠️  GPT returned non-list JSON — wrapping in list")
            data = [data]

        hypotheses = []
        for item in data:
            score = float(item.get("confidence_score", 0.5))
            score = max(0.0, min(1.0, score))  # Clamp to [0, 1]

            hypothesis = Hypothesis(
                title             = item.get("title", "Untitled hypothesis"),
                explanation       = item.get("explanation", ""),
                simple_explanation= item.get("simple_explanation", ""),
                confidence_score  = round(score, 3),
                confidence_label  = calculate_confidence_label(score),
                key_proteins      = item.get("key_proteins", []),
                key_drugs         = item.get("key_drugs", []),
                evidence_summary  = item.get("evidence_summary", "")
            )
            hypotheses.append(hypothesis)

        print(f"   ✅ Parsed {len(hypotheses)} hypotheses successfully")
        return hypotheses

    except json.JSONDecodeError as e:
        print(f"   ❌ JSON parse error: {e}")
        print(f"   Raw response preview: {raw_json[:200]}")
        return []


def generate_evidence_explanation(
    hypothesis: Hypothesis,
    detail_level: str = "scientist"
) -> str:
    """
    Generate an expanded explanation for a single hypothesis.

    Args:
        hypothesis   : A Hypothesis object
        detail_level : "scientist" or "simple"

    Returns:
        Expanded explanation string
    """

    if detail_level == "simple":
        prompt = f"""
        Explain this biomedical hypothesis in simple terms a curious teenager could understand.
        Use an everyday analogy. Keep it to 3-4 sentences.
        
        Hypothesis: {hypothesis.title}
        Scientific context: {hypothesis.explanation[:300]}
        """
    else:
        prompt = f"""
        Expand this hypothesis with deeper scientific detail.
        Cover: molecular pathway, experimental validation approach, 
        potential therapeutic implications, and known limitations.
        Keep to 4-5 sentences.
        
        Hypothesis: {hypothesis.title}
        Context: {hypothesis.explanation[:300]}
        """

    try:
        response = client.chat.completions.create(
            model      = "gpt-4o-mini",
            messages   = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt}
            ],
            temperature= 0.3,
            max_tokens = 400
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Explanation unavailable: {str(e)}"


# ── Quick test ───────────────────────────────────────────────
if __name__ == "__main__":
    from backend.services.pipeline_service import run_data_pipeline

    print("🧬 AI Scientist — Full Pipeline Test")
    print("=" * 55)

    # Step 1: Run data pipeline
    pipeline_result = run_data_pipeline(
        disease_name = "Alzheimer disease",
        max_targets  = 5,
        max_papers   = 4,
        max_drugs    = 3
    )

    # Step 2: Generate hypotheses
    print("\n" + "=" * 55)
    hypotheses = generate_hypotheses(pipeline_result, num_hypotheses=3)

    # Step 3: Display results
    print("\n" + "=" * 55)
    print("📊 GENERATED HYPOTHESES")
    print("=" * 55)

    for i, h in enumerate(hypotheses, 1):
        print(f"\n{'─'*55}")
        print(f"Hypothesis {i}: {h.title}")
        print(f"{'─'*55}")
        print(f"🎯 Confidence : {h.confidence_score} ({h.confidence_label})")
        print(f"🧬 Proteins   : {', '.join(h.key_proteins)}")
        print(f"💊 Drugs      : {', '.join(h.key_drugs)}")
        print(f"\n📖 Scientific Explanation:")
        print(f"   {h.explanation[:400]}...")
        print(f"\n🧒 Simple Explanation:")
        print(f"   {h.simple_explanation}")
        print(f"\n📚 Evidence Summary:")
        print(f"   {h.evidence_summary}")
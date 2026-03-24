# backend/services/decision_service.py
# V4 Feature 2: GO/NO-GO Decision Engine
#
# Produces a final binary + nuanced decision for each hypothesis
# and the overall analysis.
#
# Decision Logic:
#   GO          → composite_score > 0.7 AND risk != High
#                 AND uncertainty <= Medium
#   INVESTIGATE → composite_score 0.5–0.7 OR medium uncertainty
#                 OR medium risk
#   NO-GO       → composite_score < 0.5 OR risk == High
#                 OR uncertainty >= High

from backend.models.schemas import (
    GoNoGoDecision,
    Hypothesis,
    DiseaseAnalysisResult
)


# ── Decision Thresholds ───────────────────────────────────────
SCORE_GO          = 0.70   # Minimum composite score to GO
SCORE_INVESTIGATE = 0.50   # Minimum to INVESTIGATE (below = NO-GO)

RISK_BLOCKER      = {"High"}          # Risk levels that block GO
UNCERTAINTY_BLOCKER= {"High","Very High"}  # Uncertainty that blocks GO
UNCERTAINTY_CAUTION= {"Medium"}       # Uncertainty that triggers INVESTIGATE


def make_go_no_go(
    composite_score:   float,
    risk_level:        str,
    uncertainty_label: str,
    uncertainty_score: float,
    evidence_label:    str,
    drug_name:         str = "",
    protein_name:      str = "",
    context:           str = ""
) -> GoNoGoDecision:
    """
    Core decision function. Takes key signals and returns a decision.

    Args:
        composite_score   : Weighted hypothesis score (0.0–1.0)
        risk_level        : FDA risk classification
        uncertainty_label : Uncertainty tier label
        uncertainty_score : Numeric uncertainty (0.0–1.0)
        evidence_label    : Evidence strength label
        drug_name         : Drug being evaluated
        protein_name      : Target protein
        context           : Additional context for reasoning

    Returns:
        GoNoGoDecision object
    """

    supporting  = []
    blocking    = []
    decision    = ""
    color       = ""
    emoji       = ""
    primary     = ""
    action      = ""
    flip_cond   = ""
    conf_in_dec = 0.0

    # ── Evaluate each signal ──────────────────────────────────

    # Composite score signal
    if composite_score >= SCORE_GO:
        supporting.append(
            f"Strong composite score ({composite_score:.0%}) "
            f"exceeds GO threshold (70%)"
        )
    elif composite_score >= SCORE_INVESTIGATE:
        supporting.append(
            f"Moderate composite score ({composite_score:.0%}) — "
            f"warrants investigation"
        )
    else:
        blocking.append(
            f"Weak composite score ({composite_score:.0%}) "
            f"below minimum threshold (50%)"
        )

    # Risk signal
    if risk_level in RISK_BLOCKER:
        blocking.append(
            f"High FDA adverse event risk detected for {drug_name}. "
            f"Significant safety signals require benefit-risk evaluation."
        )
    elif risk_level == "Medium":
        supporting.append(
            f"Medium risk level for {drug_name} — manageable with "
            f"standard monitoring protocols."
        )
    elif risk_level == "Low":
        supporting.append(
            f"Low FDA risk profile for {drug_name} — "
            f"favorable safety signal."
        )
    else:
        supporting.append(
            f"No FDA risk data for {drug_name} — "
            f"monitor closely in any trial."
        )

    # Uncertainty signal
    if uncertainty_label in UNCERTAINTY_BLOCKER:
        blocking.append(
            f"{uncertainty_label} uncertainty detected "
            f"(score: {uncertainty_score:.2f}). "
            f"Insufficient evidence for confident decision."
        )
    elif uncertainty_label in UNCERTAINTY_CAUTION:
        supporting.append(
            f"Medium uncertainty present — additional validation "
            f"recommended before full commitment."
        )
    else:
        supporting.append(
            f"Low uncertainty (score: {uncertainty_score:.2f}) — "
            f"evidence base is reliable."
        )

    # Evidence signal
    if evidence_label in ["Strong", "Moderate"]:
        supporting.append(
            f"Evidence strength: {evidence_label} — "
            f"sufficient literature backing."
        )
    else:
        blocking.append(
            f"Weak evidence base ({evidence_label}) — "
            f"limited literature support reduces reliability."
        )

    # ── Make final decision ───────────────────────────────────
    has_blockers    = len(blocking) > 0
    score_strong    = composite_score >= SCORE_GO
    score_moderate  = SCORE_INVESTIGATE <= composite_score < SCORE_GO
    risk_clear      = risk_level not in RISK_BLOCKER
    uncertainty_ok  = uncertainty_label not in UNCERTAINTY_BLOCKER

    if score_strong and risk_clear and uncertainty_ok:
        decision    = "GO"
        color       = "#22c55e"
        emoji       = "✅"
        primary     = (
            f"Strong evidence profile supports pursuing "
            f"{drug_name} → {protein_name} hypothesis."
        )
        action      = (
            f"Proceed to experimental validation. "
            f"Recommended: design {_suggest_experiment(composite_score)} "
            f"targeting {protein_name}."
        )
        flip_cond   = (
            f"Decision would flip to NO-GO if: FDA adverse events "
            f"increase significantly, or replication studies fail."
        )
        conf_in_dec = min(0.95, composite_score * (1 - uncertainty_score * 0.5))

    elif not score_strong and not has_blockers:
        decision    = "INVESTIGATE"
        color       = "#f59e0b"
        emoji       = "🔍"
        primary     = (
            f"Moderate evidence for {drug_name} → {protein_name}. "
            f"Requires additional data before committing resources."
        )
        action      = (
            f"Gather more evidence: expand literature search, "
            f"check for recent clinical trial results for {drug_name}, "
            f"and run preliminary in-vitro assay."
        )
        flip_cond   = (
            f"Would flip to GO if: composite score exceeds 70%, "
            f"or new causal evidence emerges."
        )
        conf_in_dec = 0.55 + (composite_score - SCORE_INVESTIGATE) * 0.3

    elif has_blockers and (score_strong or score_moderate):
        decision    = "INVESTIGATE"
        color       = "#f59e0b"
        emoji       = "🔍"
        primary     = (
            f"Hypothesis shows promise but blocking factors "
            f"prevent immediate GO recommendation."
        )
        action      = (
            f"Address blocking factors: "
            f"{blocking[0][:80] if blocking else 'resolve identified issues'}. "
            f"Then re-evaluate."
        )
        flip_cond   = (
            f"Would flip to GO if blocking factors are resolved: "
            f"{', '.join([b[:40] for b in blocking[:2]])}."
        )
        conf_in_dec = 0.45

    else:
        decision    = "NO-GO"
        color       = "#ef4444"
        emoji       = "❌"
        primary     = (
            f"Evidence does not support pursuing "
            f"{drug_name} → {protein_name} at this time."
        )
        action      = (
            f"Do not allocate resources to this hypothesis currently. "
            f"Consider alternative targets or wait for stronger evidence."
        )
        flip_cond   = (
            f"Would reconsider if: {blocking[0][:80] if blocking else 'evidence improves'}."
        )
        conf_in_dec = max(0.1, 1.0 - composite_score)

    conf_in_dec = round(min(0.99, max(0.01, conf_in_dec)), 3)

    return GoNoGoDecision(
        decision               = decision,
        decision_color         = color,
        decision_emoji         = emoji,
        confidence_in_decision = conf_in_dec,
        composite_score        = composite_score,
        uncertainty_score      = uncertainty_score,
        risk_level             = risk_level,
        evidence_label         = evidence_label,
        primary_reason         = primary,
        supporting_reasons     = supporting,
        blocking_reasons       = blocking,
        recommended_action     = action,
        conditions_to_flip     = flip_cond
    )


def _suggest_experiment(score: float) -> str:
    """Suggest experiment type based on score strength."""
    if score >= 0.8:
        return "Phase 2 clinical biomarker study"
    elif score >= 0.65:
        return "in-vivo animal model study"
    else:
        return "in-vitro cell assay"


def compute_hypothesis_go_no_go(
    hypothesis:      Hypothesis,
    pipeline_result: DiseaseAnalysisResult
) -> GoNoGoDecision:
    """
    Compute GO/NO-GO decision for a single hypothesis.
    Uses hypothesis scores + uncertainty + risk data.
    """
    # Get uncertainty
    unc_label = "Medium"
    unc_score = 0.3
    if hypothesis.uncertainty:
        unc_label = hypothesis.uncertainty.uncertainty_label
        unc_score = hypothesis.uncertainty.uncertainty_score

    # Get risk for this hypothesis's drug
    drug_name  = hypothesis.key_drugs[0] if hypothesis.key_drugs else ""
    risk_level = "Unknown"
    for drug in pipeline_result.drugs:
        if drug.drug_name.upper() == drug_name.upper():
            risk_level = drug.risk_level
            break

    # Get evidence label
    ev_label = "Moderate"
    if pipeline_result.evidence_strength:
        ev_label = pipeline_result.evidence_strength.evidence_label

    protein_name = hypothesis.key_proteins[0] if hypothesis.key_proteins else ""

    return make_go_no_go(
        composite_score   = hypothesis.final_score,
        risk_level        = risk_level,
        uncertainty_label = unc_label,
        uncertainty_score = unc_score,
        evidence_label    = ev_label,
        drug_name         = drug_name,
        protein_name      = protein_name
    )


def compute_analysis_go_no_go(
    pipeline_result: DiseaseAnalysisResult
) -> GoNoGoDecision:
    """
    Compute overall GO/NO-GO for the full analysis
    (based on best hypothesis).
    """
    if not pipeline_result.hypotheses:
        return GoNoGoDecision(
            decision        = "NO-GO",
            decision_color  = "#ef4444",
            decision_emoji  = "❌",
            primary_reason  = "No hypotheses generated — insufficient data.",
            recommended_action = "Try a different disease or expand search parameters."
        )

    best = min(pipeline_result.hypotheses, key=lambda h: h.rank)

    unc_label = "Medium"
    unc_score = 0.3
    if best.uncertainty:
        unc_label = best.uncertainty.uncertainty_label
        unc_score = best.uncertainty.uncertainty_score

    drug_name    = best.key_drugs[0] if best.key_drugs else ""
    protein_name = best.key_proteins[0] if best.key_proteins else ""
    risk_level   = "Unknown"

    for drug in pipeline_result.drugs:
        if drug.drug_name.upper() == drug_name.upper():
            risk_level = drug.risk_level
            break

    ev_label = "Moderate"
    if pipeline_result.evidence_strength:
        ev_label = pipeline_result.evidence_strength.evidence_label

    return make_go_no_go(
        composite_score   = best.final_score,
        risk_level        = risk_level,
        uncertainty_label = unc_label,
        uncertainty_score = unc_score,
        evidence_label    = ev_label,
        drug_name         = drug_name,
        protein_name      = protein_name
    )


# ── Quick test ────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing GO/NO-GO Decision Engine")
    print("=" * 50)

    test_cases = [
        {
            "name":        "Strong GO case",
            "composite":   0.79,
            "risk":        "Medium",
            "uncertainty": "Low",
            "unc_score":   0.15,
            "evidence":    "Moderate",
            "drug":        "LECANEMAB",
            "protein":     "APP"
        },
        {
            "name":        "NO-GO: High risk",
            "composite":   0.75,
            "risk":        "High",
            "uncertainty": "Medium",
            "unc_score":   0.35,
            "evidence":    "Moderate",
            "drug":        "NIROGACESTAT",
            "protein":     "PSEN1"
        },
        {
            "name":        "INVESTIGATE: Moderate score",
            "composite":   0.55,
            "risk":        "Low",
            "uncertainty": "Medium",
            "unc_score":   0.30,
            "evidence":    "Weak",
            "drug":        "DRUG_X",
            "protein":     "GENE_Y"
        },
        {
            "name":        "NO-GO: Very high uncertainty",
            "composite":   0.72,
            "risk":        "Low",
            "uncertainty": "Very High",
            "unc_score":   0.85,
            "evidence":    "Weak",
            "drug":        "DRUG_Z",
            "protein":     "GENE_Z"
        }
    ]

    for tc in test_cases:
        result = make_go_no_go(
            composite_score   = tc["composite"],
            risk_level        = tc["risk"],
            uncertainty_label = tc["uncertainty"],
            uncertainty_score = tc["unc_score"],
            evidence_label    = tc["evidence"],
            drug_name         = tc["drug"],
            protein_name      = tc["protein"]
        )
        print(f"\n📋 {tc['name']}")
        print(f"   {result.decision_emoji} Decision    : {result.decision}")
        print(f"   Confidence  : {result.confidence_in_decision:.0%}")
        print(f"   Reason      : {result.primary_reason[:60]}...")
        print(f"   Supporting  : {len(result.supporting_reasons)} factors")
        print(f"   Blocking    : {len(result.blocking_reasons)} factors")
        print(f"   Action      : {result.recommended_action[:60]}...")
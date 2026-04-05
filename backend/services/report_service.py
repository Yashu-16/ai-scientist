# backend/services/report_service.py
# V5 Feature 1: PDF Research Report Export
# Generates a professional PDF from pipeline + hypothesis results
# Uses ReportLab — lightweight, no external dependencies

import io
from datetime import datetime
from typing import Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT


# ── Color Palette ─────────────────────────────────────────────
DARK_BG    = colors.HexColor("#0f172a")
BLUE       = colors.HexColor("#3b82f6")
PURPLE     = colors.HexColor("#8b5cf6")
GREEN      = colors.HexColor("#22c55e")
AMBER      = colors.HexColor("#f59e0b")
RED        = colors.HexColor("#ef4444")
LIGHT_GRAY = colors.HexColor("#94a3b8")
SLATE      = colors.HexColor("#1e293b")
WHITE      = colors.white
TEXT_DARK  = colors.HexColor("#1e293b")
TEXT_MID   = colors.HexColor("#475569")


def _build_styles() -> dict:
    """Build all paragraph styles for the report."""
    base = getSampleStyleSheet()

    styles = {
        "title": ParagraphStyle(
            "ReportTitle",
            fontSize=26, fontName="Helvetica-Bold",
            textColor=TEXT_DARK, spaceAfter=4,
            alignment=TA_CENTER
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle",
            fontSize=12, fontName="Helvetica",
            textColor=LIGHT_GRAY, spaceAfter=2,
            alignment=TA_CENTER
        ),
        "section": ParagraphStyle(
            "SectionHeader",
            fontSize=14, fontName="Helvetica-Bold",
            textColor=BLUE, spaceBefore=14, spaceAfter=6,
            borderPad=4
        ),
        "subsection": ParagraphStyle(
            "SubsectionHeader",
            fontSize=11, fontName="Helvetica-Bold",
            textColor=TEXT_DARK, spaceBefore=8, spaceAfter=4
        ),
        "body": ParagraphStyle(
            "BodyText",
            fontSize=10, fontName="Helvetica",
            textColor=TEXT_DARK, spaceAfter=4,
            leading=15
        ),
        "body_sm": ParagraphStyle(
            "BodySmall",
            fontSize=9, fontName="Helvetica",
            textColor=TEXT_MID, spaceAfter=3,
            leading=13
        ),
        "caption": ParagraphStyle(
            "Caption",
            fontSize=8, fontName="Helvetica-Oblique",
            textColor=LIGHT_GRAY, spaceAfter=2
        ),
        "badge_go": ParagraphStyle(
            "BadgeGO",
            fontSize=11, fontName="Helvetica-Bold",
            textColor=GREEN, spaceAfter=4
        ),
        "badge_nogo": ParagraphStyle(
            "BadgeNoGO",
            fontSize=11, fontName="Helvetica-Bold",
            textColor=RED, spaceAfter=4
        ),
        "badge_invest": ParagraphStyle(
            "BadgeInvest",
            fontSize=11, fontName="Helvetica-Bold",
            textColor=AMBER, spaceAfter=4
        ),
        "metric_label": ParagraphStyle(
            "MetricLabel",
            fontSize=8, fontName="Helvetica",
            textColor=LIGHT_GRAY, alignment=TA_CENTER
        ),
        "metric_value": ParagraphStyle(
            "MetricValue",
            fontSize=16, fontName="Helvetica-Bold",
            textColor=TEXT_DARK, alignment=TA_CENTER
        ),
        "bullet": ParagraphStyle(
            "BulletText",
            fontSize=9, fontName="Helvetica",
            textColor=TEXT_DARK, spaceAfter=3,
            leftIndent=12, leading=13
        ),
        "footer": ParagraphStyle(
            "Footer",
            fontSize=7, fontName="Helvetica",
            textColor=LIGHT_GRAY, alignment=TA_CENTER
        )
    }
    return styles


def _divider(color=BLUE, thickness=0.5) -> HRFlowable:
    return HRFlowable(
        width="100%", thickness=thickness,
        color=color, spaceAfter=4, spaceBefore=4
    )


def _metric_table(metrics: list) -> Table:
    """
    Build a row of metric boxes.
    metrics = [{"label": str, "value": str, "color": color}, ...]
    """
    styles = _build_styles()
    headers = [Paragraph(m["label"], styles["metric_label"]) for m in metrics]
    values  = [
        Paragraph(
            f'<font color="#{m.get("color_hex","1e293b")}">{m["value"]}</font>',
            styles["metric_value"]
        )
        for m in metrics
    ]

    data = [headers, values]
    col_w = 170 / len(metrics) * mm

    tbl = Table(data, colWidths=[col_w]*len(metrics))
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ("BOX",        (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ("INNERGRID",  (0,0), (-1,-1), 0.3, colors.HexColor("#e2e8f0")),
        ("ALIGN",      (0,0), (-1,-1), "CENTER"),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",(0,0),(-1,-1),6),
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.HexColor("#f8fafc")]),
    ]))
    return tbl


def generate_pdf_report(data: dict) -> bytes:
    """
    Main function: generate a complete PDF report from analysis data.

    Args:
        data: The full analysis result dict from /analyze-disease

    Returns:
        PDF bytes ready for download
    """
    buf    = io.BytesIO()
    doc    = SimpleDocTemplate(
        buf,
        pagesize    = A4,
        leftMargin  = 20*mm,
        rightMargin = 20*mm,
        topMargin   = 18*mm,
        bottomMargin= 18*mm
    )
    styles  = _build_styles()
    story   = []
    W       = 170*mm  # usable width

    disease     = data.get("disease_name","Unknown Disease")
    hypotheses  = data.get("hypotheses",[])
    proteins    = data.get("protein_targets",[])
    drugs       = data.get("drugs",[])
    papers      = data.get("papers",[])
    ds          = data.get("decision_summary") or {}
    ev          = data.get("evidence_strength") or {}
    au          = data.get("analysis_uncertainty") or {}
    lr          = data.get("literature_review") or {}
    best_hyp    = hypotheses[0] if hypotheses else {}

    # ── COVER / HEADER ────────────────────────────────────────
    story.append(Spacer(1, 8*mm))

    # Title block — no emoji (ReportLab can't render them)
    story.append(Paragraph("AI Scientist", styles["title"]))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        "Decision &amp; Risk Intelligence Platform for Drug Discovery",
        styles["subtitle"]
    ))
    story.append(Spacer(1, 4*mm))
    story.append(_divider(BLUE, 1.5))
    story.append(Spacer(1, 3*mm))

    # Report meta — plain text only
    now = datetime.now().strftime("%B %d, %Y at %H:%M")
    story.append(Paragraph(
        f"Disease: {disease}     |     Generated: {now}     |     Powered by: GPT-4o-mini + OpenTargets + FDA FAERS",
        styles["caption"]
    ))
    story.append(Spacer(1, 5*mm))

    # ── SECTION 1: EXECUTIVE DECISION ────────────────────────
    story.append(Paragraph("1. Executive Decision", styles["section"]))
    story.append(_divider(BLUE))

    # GO/NO-GO badge
    gng = ds.get("go_no_go") or {}
    decision   = gng.get("decision","INVESTIGATE")
    dec_emoji  = {"GO":"✅","NO-GO":"❌","INVESTIGATE":"🔍"}.get(decision,"🔍")
    dec_conf   = float(gng.get("confidence_in_decision") or 0)
    dec_color  = {"GO":"22c55e","NO-GO":"ef4444","INVESTIGATE":"f59e0b"}.get(decision,"64748b")
    dec_style  = {"GO": styles["badge_go"], "NO-GO": styles["badge_nogo"],
                  "INVESTIGATE": styles["badge_invest"]}.get(decision, styles["badge_invest"])

    story.append(Paragraph(
        f"{dec_emoji} Final Decision: <b>{decision}</b> "
        f"({dec_conf:.0%} decision confidence)",
        dec_style
    ))

    # Key metrics table
    conf  = float(ds.get("confidence_score") or 0)
    risk  = ds.get("risk_level","Unknown")
    drug  = ds.get("recommended_drug","—")
    prot  = ds.get("target_protein","—")

    risk_hex = {"High":"ef4444","Medium":"f59e0b","Low":"22c55e"}.get(risk,"64748b")
    conf_hex = "22c55e" if conf >= 0.8 else "f59e0b" if conf >= 0.6 else "ef4444"

    story.append(Spacer(1,3*mm))
    story.append(_metric_table([
        {"label":"Recommended Drug",  "value": drug,          "color_hex":"3b82f6"},
        {"label":"Target Protein",    "value": prot,          "color_hex":"8b5cf6"},
        {"label":"Confidence Score",  "value": f"{conf:.0%}", "color_hex":conf_hex},
        {"label":"Risk Level",        "value": risk,          "color_hex":risk_hex},
    ]))
    story.append(Spacer(1,3*mm))

    # Primary reason
    primary = str(gng.get("primary_reason") or ds.get("reasoning_summary",""))
    if primary:
        story.append(Paragraph(f"<b>Decision Basis:</b> {primary}", styles["body"]))

    # Suggested action
    action = str(ds.get("suggested_action") or gng.get("recommended_action",""))
    if action:
        story.append(Paragraph(f"<b>Recommended Action:</b> {action}", styles["body"]))

    story.append(Spacer(1, 4*mm))

    # ── SECTION 2: TOP HYPOTHESIS ─────────────────────────────
    story.append(Paragraph("2. Top Hypothesis", styles["section"]))
    story.append(_divider(PURPLE))

    if best_hyp:
        title = str(best_hyp.get("title",""))
        final = float(best_hyp.get("final_score") or 0)
        expl  = str(best_hyp.get("explanation",""))
        simple= str(best_hyp.get("simple_explanation",""))

        story.append(Paragraph(f"<b>{title}</b>", styles["subsection"]))
        story.append(Paragraph(
            f"Composite Score: <b>{final:.0%}</b> &nbsp;|&nbsp; "
            f"Proteins: <b>{', '.join(best_hyp.get('key_proteins',[]))}</b> &nbsp;|&nbsp; "
            f"Drugs: <b>{', '.join(best_hyp.get('key_drugs',[]))}</b>",
            styles["body_sm"]
        ))
        story.append(Spacer(1,2*mm))
        story.append(Paragraph(f"<b>Scientific Explanation:</b>", styles["subsection"]))
        story.append(Paragraph(expl, styles["body"]))

        if simple:
            story.append(Paragraph(f"<b>Simple Explanation:</b>", styles["subsection"]))
            story.append(Paragraph(simple, styles["body"]))

        # Reasoning steps
        steps = best_hyp.get("reasoning_steps") or []
        if steps:
            story.append(Paragraph("<b>Reasoning Chain:</b>", styles["subsection"]))
            for step in steps:
                story.append(Paragraph(f"• {step}", styles["bullet"]))

        # GO/NO-GO for this hypothesis
        h_gng = best_hyp.get("go_no_go") or {}
        h_dec = h_gng.get("decision","")
        if h_dec:
            story.append(Spacer(1,2*mm))
            h_conf = float(h_gng.get("confidence_in_decision") or 0)
            story.append(Paragraph(
                f"<b>Hypothesis Decision:</b> {h_dec} ({h_conf:.0%} confident)",
                styles["body"]
            ))

    story.append(Spacer(1, 4*mm))

    # ── SECTION 3: EVIDENCE ANALYSIS ─────────────────────────
    story.append(Paragraph("3. Evidence Analysis", styles["section"]))
    story.append(_divider(GREEN))

    # Evidence strength
    ev_label = str(ev.get("evidence_label","Unknown"))
    ev_score = float(ev.get("evidence_score") or 0)
    ev_bd    = str(ev.get("evidence_breakdown",""))
    story.append(Paragraph(
        f"<b>Evidence Strength:</b> {ev_label} ({ev_score:.2f}/1.00)",
        styles["body"]
    ))
    if ev_bd:
        story.append(Paragraph(f"<i>{ev_bd}</i>", styles["caption"]))
    story.append(Spacer(1,2*mm))

    # Uncertainty
    au_label = str(au.get("uncertainty_label","Unknown"))
    au_score = float(au.get("uncertainty_score") or 0)
    au_reason= str(au.get("uncertainty_reason",""))
    story.append(Paragraph(
        f"<b>Analysis Uncertainty:</b> {au_label} ({au_score:.2f}/1.00)",
        styles["body"]
    ))
    if au_reason:
        story.append(Paragraph(au_reason, styles["body_sm"]))
    story.append(Spacer(1,2*mm))

    # Protein targets table
    if proteins:
        story.append(Paragraph("<b>Top Protein Targets:</b>", styles["subsection"]))
        prot_data = [["Gene", "Protein Name", "Assoc. Score", "AlphaFold pLDDT"]]
        for pt in proteins[:5]:
            prot_data.append([
                pt.get("gene_symbol",""),
                pt.get("protein_name","")[:35],
                f"{pt.get('association_score',0):.3f}",
                f"{pt.get('alphafold_plddt',0):.2f}"
            ])
        prot_tbl = Table(prot_data, colWidths=[25*mm, 70*mm, 35*mm, 40*mm])
        prot_tbl.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0), SLATE),
            ("TEXTCOLOR", (0,0),(-1,0), WHITE),
            ("FONTNAME",  (0,0),(-1,0), "Helvetica-Bold"),
            ("FONTSIZE",  (0,0),(-1,-1), 9),
            ("ALIGN",     (0,0),(-1,-1), "LEFT"),
            ("ALIGN",     (2,0),(-1,-1), "CENTER"),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#f8fafc")]),
            ("GRID",      (0,0),(-1,-1), 0.3, colors.HexColor("#e2e8f0")),
            ("TOPPADDING",(0,0),(-1,-1),5),
            ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ]))
        story.append(prot_tbl)

    story.append(Spacer(1, 4*mm))

    # ── SECTION 4: RISK ANALYSIS ──────────────────────────────
    story.append(Paragraph("4. Risk Analysis", styles["section"]))
    story.append(_divider(AMBER))

    if drugs:
        drug_data = [["Drug", "Phase", "Target", "FDA Risk", "Competition"]]
        for d in drugs:
            comp = d.get("competition_intel") or {}
            drug_data.append([
                d.get("drug_name",""),
                str(d.get("clinical_phase","N/A")),
                d.get("target_gene",""),
                d.get("risk_level","Unknown"),
                comp.get("competition_level","Unknown")
            ])
        drug_tbl = Table(drug_data, colWidths=[40*mm, 18*mm, 25*mm, 25*mm, 62*mm])
        drug_tbl.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0), colors.HexColor("#92400e")),
            ("TEXTCOLOR", (0,0),(-1,0), WHITE),
            ("FONTNAME",  (0,0),(-1,0), "Helvetica-Bold"),
            ("FONTSIZE",  (0,0),(-1,-1), 9),
            ("ALIGN",     (0,0),(-1,-1), "LEFT"),
            ("ALIGN",     (1,0),(-1,-1), "CENTER"),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#fffbeb")]),
            ("GRID",      (0,0),(-1,-1), 0.3, colors.HexColor("#e2e8f0")),
            ("TOPPADDING",(0,0),(-1,-1),5),
            ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ]))
        story.append(drug_tbl)

    story.append(Spacer(1,3*mm))

    # FDA adverse events for best drug
    if drugs:
        top_drug = drugs[0]
        fda_aes  = top_drug.get("fda_adverse_events") or []
        if fda_aes:
            story.append(Paragraph(
                f"<b>Top FDA Signals for {top_drug.get('drug_name','')}:</b>",
                styles["subsection"]
            ))
            for ae in fda_aes[:3]:
                story.append(Paragraph(
                    f"• {ae.get('reaction','')}: {ae.get('count',0):,} reports",
                    styles["bullet"]
                ))

    story.append(Spacer(1, 4*mm))

    # ── SECTION 5: FAILURE PREDICTION ────────────────────────
    story.append(Paragraph("5. Failure Prediction", styles["section"]))
    story.append(_divider(RED))

    if best_hyp:
        fp = best_hyp.get("failure_prediction") or {}
        if fp:
            fr_label  = str(fp.get("failure_risk_label","Unknown"))
            fr_score  = float(fp.get("failure_risk_score") or 0)
            success_p = float(fp.get("success_probability") or 0)
            top_fail  = str(fp.get("top_failure_reason",""))
            hist_ctx  = str(fp.get("historical_context",""))

            story.append(_metric_table([
                {"label":"Failure Risk",        "value":fr_label,          "color_hex":"ef4444"},
                {"label":"Failure Risk Score",  "value":f"{fr_score:.0%}", "color_hex":"f97316"},
                {"label":"Success Probability", "value":f"{success_p:.0%}","color_hex":"22c55e"},
            ]))
            story.append(Spacer(1,2*mm))

            if top_fail:
                story.append(Paragraph(
                    f"<b>Top Failure Mode:</b> {top_fail}", styles["body"]
                ))
            if hist_ctx:
                story.append(Paragraph(
                    f"<b>Historical Context:</b> {hist_ctx}", styles["body_sm"]
                ))

            reasons = fp.get("failure_reasons") or []
            if reasons:
                story.append(Paragraph("<b>Predicted Failure Reasons:</b>", styles["subsection"]))
                for r in reasons[:3]:
                    story.append(Paragraph(
                        f"• [{r.get('category','')}] {r.get('reason','')} "
                        f"(Severity: {r.get('severity','')})",
                        styles["bullet"]
                    ))
                    mit = r.get("mitigation","")
                    if mit:
                        story.append(Paragraph(f"  → Mitigation: {mit}", styles["caption"]))

            safeguards = fp.get("recommended_safeguards") or []
            if safeguards:
                story.append(Paragraph("<b>Recommended Safeguards:</b>", styles["subsection"]))
                for sg in safeguards[:3]:
                    story.append(Paragraph(f"• {sg}", styles["bullet"]))

    story.append(Spacer(1, 4*mm))

    # ── SECTION 6: TIME-TO-IMPACT ─────────────────────────────
    story.append(Paragraph("6. Time-to-Market Estimate", styles["section"]))
    story.append(_divider(PURPLE))

    if best_hyp:
        tti = best_hyp.get("time_to_impact") or {}
        if tti:
            story.append(_metric_table([
                {"label":"Timeline",            "value":tti.get("years_range","?"),         "color_hex":"8b5cf6"},
                {"label":"Track",               "value":tti.get("speed_category","?"),       "color_hex":"6366f1"},
                {"label":"Current Stage",       "value":tti.get("current_stage","?")[:20],  "color_hex":"3b82f6"},
                {"label":"Success Probability", "value":f"{float(tti.get('success_probability',0)):.0%}", "color_hex":"22c55e"},
            ]))
            story.append(Spacer(1,2*mm))

            timeline = tti.get("timeline_breakdown") or []
            if timeline:
                story.append(Paragraph("<b>Timeline Breakdown:</b>", styles["subsection"]))
                for i, step in enumerate(timeline, 1):
                    story.append(Paragraph(f"{i}. {step}", styles["bullet"]))

            bottlenecks = tti.get("key_bottlenecks") or []
            if bottlenecks:
                story.append(Paragraph("<b>Key Bottlenecks:</b>", styles["subsection"]))
                for b in bottlenecks:
                    story.append(Paragraph(f"• {b}", styles["bullet"]))

    story.append(Spacer(1, 4*mm))

    # ── SECTION 7: EXECUTIVE SUMMARY ─────────────────────────
    story.append(Paragraph("7. Executive Summary", styles["section"]))
    story.append(_divider(BLUE))

    if best_hyp:
        es = best_hyp.get("executive_summary") or {}
        if es:
            headline = str(es.get("headline",""))
            body     = str(es.get("body",""))
            market   = str(es.get("market_opportunity",""))
            bottom   = str(es.get("bottom_line",""))

            if headline:
                story.append(Paragraph(f"<b>{headline}</b>", styles["subsection"]))
            if body:
                story.append(Paragraph(body, styles["body"]))
            if market:
                story.append(Paragraph(f"<b>Market Opportunity:</b> {market}", styles["body_sm"]))
            if bottom:
                story.append(Paragraph(f"<b>Bottom Line:</b> {bottom}", styles["body"]))

    story.append(Spacer(1, 4*mm))

    # ── SECTION 8: LITERATURE SUMMARY ────────────────────────
    if lr:
        story.append(Paragraph("8. Literature Overview", styles["section"]))
        story.append(_divider(GREEN))

        lr_sections = [
            ("Background",          "background"),
            ("Current Research",    "current_research"),
            ("Research Gaps",       "research_gaps"),
            ("Risks & Limitations", "risks_limitations"),
            ("Conclusion",          "conclusion"),
        ]
        for title, key in lr_sections:
            content = lr.get(key,"")
            if content:
                story.append(Paragraph(f"<b>{title}:</b>", styles["subsection"]))
                story.append(Paragraph(content, styles["body_sm"]))

        story.append(Spacer(1, 4*mm))

    # ── SECTION 9: ALL HYPOTHESES SUMMARY ────────────────────
    if len(hypotheses) > 1:
        story.append(Paragraph("9. Hypothesis Comparison", styles["section"]))
        story.append(_divider(PURPLE))

        hyp_data = [["Rank","Hypothesis","Score","Decision","Failure Risk"]]
        medals   = {1:"#1",2:"#2",3:"#3"}
        for h in hypotheses:
            h_gng = h.get("go_no_go") or {}
            h_fp  = h.get("failure_prediction") or {}
            hyp_data.append([
                medals.get(h.get("rank",0), f"#{h.get('rank',0)}"),
                str(h.get("title",""))[:55],
                f"{float(h.get('final_score',0)):.0%}",
                h_gng.get("decision","—"),
                h_fp.get("failure_risk_label","—")
            ])

        hyp_tbl = Table(hyp_data, colWidths=[12*mm, 85*mm, 18*mm, 30*mm, 25*mm])
        hyp_tbl.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0), SLATE),
            ("TEXTCOLOR", (0,0),(-1,0), WHITE),
            ("FONTNAME",  (0,0),(-1,0), "Helvetica-Bold"),
            ("FONTSIZE",  (0,0),(-1,-1), 9),
            ("ALIGN",     (0,0),(-1,-1), "LEFT"),
            ("ALIGN",     (0,0),(0,-1),  "CENTER"),
            ("ALIGN",     (2,0),(-1,-1), "CENTER"),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#f8fafc")]),
            ("GRID",      (0,0),(-1,-1), 0.3, colors.HexColor("#e2e8f0")),
            ("TOPPADDING",(0,0),(-1,-1),5),
            ("BOTTOMPADDING",(0,0),(-1,-1),5),
            ("WORDWRAP",  (1,0),(1,-1),  True),
        ]))
        story.append(hyp_tbl)

    # ── FOOTER ────────────────────────────────────────────────
    story.append(Spacer(1, 8*mm))
    story.append(_divider(LIGHT_GRAY, 0.5))
    story.append(Paragraph(
        f"Generated by AI Scientist V5 — {now} | "
        f"For exploratory research only. Not for clinical use. | "
        f"Powered by GPT-4o-mini, OpenTargets, FDA FAERS, PubMed",
        styles["footer"]
    ))

    doc.build(story)
    buf.seek(0)
    return buf.read()


# ── Quick test ────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing PDF Report Service...")

    mock_data = {
        "disease_name": "Alzheimer disease",
        "hypotheses": [{
            "rank": 1,
            "title": "Lecanemab targets APP in the amyloidogenic pathway",
            "final_score": 0.80,
            "key_proteins": ["APP"],
            "key_drugs":    ["Lecanemab"],
            "explanation":  "Lecanemab inhibits Aβ aggregation by targeting APP cleavage products.",
            "simple_explanation": "Lecanemab acts like a sponge, soaking up harmful proteins.",
            "reasoning_steps": [
                "Step 1 — APP produces amyloid-beta when cleaved.",
                "Step 2 — Lecanemab binds to Aβ aggregates.",
                "Step 3 — Reduces plaque burden in amyloidogenic pathway.",
                "Step 4 — Clinical Phase 4 confirms therapeutic potential."
            ],
            "go_no_go": {
                "decision":"GO","confidence_in_decision":0.72,
                "primary_reason":"Strong score exceeds GO threshold.",
                "decision_color":"#22c55e","decision_emoji":"✅"
            },
            "failure_prediction": {
                "failure_risk_label":"Medium","failure_risk_score":0.45,
                "success_probability":0.65,
                "top_failure_reason":"Amyloid clearance may not correlate with cognitive benefit.",
                "historical_context":"Similar antibodies showed mixed Phase 3 results.",
                "failure_reasons":[{
                    "category":"Efficacy","severity":"High",
                    "reason":"Biomarker benefit ≠ cognitive improvement",
                    "mitigation":"Use cognitive endpoints alongside biomarkers"
                }],
                "recommended_safeguards":["Include MMSE cognitive endpoint","Adaptive trial design"]
            },
            "time_to_impact": {
                "years_range":"0–2 years","speed_category":"Fast",
                "current_stage":"Phase 4 / FDA Approved",
                "success_probability":0.80,
                "timeline_breakdown":["Currently Phase 4","Label expansion 1-2yr"],
                "key_bottlenecks":["Standard regulatory timeline"]
            },
            "executive_summary": {
                "headline":"Lecanemab offers a promising Alzheimer's treatment",
                "body":"Lecanemab is an FDA-approved amyloid-targeting therapy showing strong clinical evidence.",
                "market_opportunity":"$15B+ Alzheimer's market with significant unmet need.",
                "bottom_line":"Proceed with validation studies."
            }
        }],
        "protein_targets": [
            {"gene_symbol":"APP","protein_name":"Amyloid Precursor Protein",
             "association_score":0.87,"alphafold_plddt":0.85}
        ],
        "drugs": [{
            "drug_name":"Lecanemab","clinical_phase":4,"target_gene":"APP",
            "risk_level":"Medium","competition_intel":{"competition_level":"High"},
            "fda_adverse_events":[{"reaction":"ARIA","count":51}]
        }],
        "papers": [],
        "decision_summary": {
            "recommended_drug":"Lecanemab","target_protein":"APP",
            "confidence_score":0.80,"risk_level":"Medium",
            "reasoning_summary":"Strong evidence profile supports this hypothesis.",
            "suggested_action":"Proceed to validation studies.",
            "go_no_go":{
                "decision":"GO","confidence_in_decision":0.72,
                "primary_reason":"Score exceeds GO threshold.",
                "recommended_action":"Design in-vivo study."
            }
        },
        "evidence_strength": {
            "evidence_label":"Strong","evidence_score":0.65,
            "evidence_breakdown":"9 papers, strong association"
        },
        "analysis_uncertainty": {
            "uncertainty_label":"Low","uncertainty_score":0.20,
            "uncertainty_reason":"Strong evidence base."
        },
        "literature_review": {
            "background":"Alzheimer disease is a progressive neurodegenerative disorder.",
            "current_research":"Amyloid-targeting therapies are the leading research direction.",
            "research_gaps":"Causality between amyloid clearance and cognitive benefit unclear.",
            "risks_limitations":"ARIA side effects and trial design challenges.",
            "conclusion":"Lecanemab represents the strongest current candidate."
        }
    }

    pdf_bytes = generate_pdf_report(mock_data)
    with open("test_report.pdf","wb") as f:
        f.write(pdf_bytes)
    print(f"✅ PDF generated: test_report.pdf ({len(pdf_bytes):,} bytes)")
    print("   Open with: Invoke-Item test_report.pdf")
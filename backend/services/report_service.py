# backend/services/report_service.py
# V6 — Professional PDF redesign
# Clean layout, proper alignment, enterprise-grade styling

import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus.flowables import Flowable


# ── Color Palette ─────────────────────────────────────────────
C_NAVY      = colors.HexColor("#0f172a")
C_BLUE      = colors.HexColor("#2563eb")
C_BLUE_LT   = colors.HexColor("#eff6ff")
C_PURPLE    = colors.HexColor("#7c3aed")
C_PURPLE_LT = colors.HexColor("#f5f3ff")
C_GREEN     = colors.HexColor("#16a34a")
C_GREEN_LT  = colors.HexColor("#f0fdf4")
C_AMBER     = colors.HexColor("#d97706")
C_AMBER_LT  = colors.HexColor("#fffbeb")
C_RED       = colors.HexColor("#dc2626")
C_RED_LT    = colors.HexColor("#fef2f2")
C_GRAY      = colors.HexColor("#64748b")
C_GRAY_LT   = colors.HexColor("#f8fafc")
C_BORDER    = colors.HexColor("#e2e8f0")
C_WHITE     = colors.white
C_TEXT      = colors.HexColor("#1e293b")
C_TEXT_MID  = colors.HexColor("#475569")
C_TEXT_LIGHT= colors.HexColor("#94a3b8")

PAGE_W = 170 * mm   # usable width (A4 - margins)


# ── Styles ─────────────────────────────────────────────────────
def S():
    return {
        "cover_title": ParagraphStyle("CoverTitle",
            fontSize=32, fontName="Helvetica-Bold",
            textColor=C_WHITE, alignment=TA_LEFT,
            spaceAfter=4, leading=36),

        "cover_sub": ParagraphStyle("CoverSub",
            fontSize=13, fontName="Helvetica",
            textColor=colors.HexColor("#93c5fd"),
            alignment=TA_LEFT, spaceAfter=2),

        "cover_meta": ParagraphStyle("CoverMeta",
            fontSize=9, fontName="Helvetica",
            textColor=colors.HexColor("#cbd5e1"),
            alignment=TA_LEFT),

        "section_num": ParagraphStyle("SectionNum",
            fontSize=9, fontName="Helvetica-Bold",
            textColor=C_BLUE, spaceBefore=2),

        "section_title": ParagraphStyle("SectionTitle",
            fontSize=16, fontName="Helvetica-Bold",
            textColor=C_TEXT, spaceBefore=6, spaceAfter=4),

        "subsection": ParagraphStyle("Subsection",
            fontSize=11, fontName="Helvetica-Bold",
            textColor=C_TEXT, spaceBefore=6, spaceAfter=3),

        "body": ParagraphStyle("Body",
            fontSize=10, fontName="Helvetica",
            textColor=C_TEXT, spaceAfter=5,
            leading=16, alignment=TA_JUSTIFY),

        "body_sm": ParagraphStyle("BodySm",
            fontSize=9, fontName="Helvetica",
            textColor=C_TEXT_MID, spaceAfter=4,
            leading=14, alignment=TA_JUSTIFY),

        "label": ParagraphStyle("Label",
            fontSize=8, fontName="Helvetica-Bold",
            textColor=C_TEXT_LIGHT, spaceAfter=1,
            alignment=TA_CENTER),

        "value": ParagraphStyle("Value",
            fontSize=15, fontName="Helvetica-Bold",
            textColor=C_TEXT, alignment=TA_CENTER),

        "value_sm": ParagraphStyle("ValueSm",
            fontSize=11, fontName="Helvetica-Bold",
            textColor=C_TEXT, alignment=TA_CENTER),

        "bullet": ParagraphStyle("Bullet",
            fontSize=9.5, fontName="Helvetica",
            textColor=C_TEXT, spaceAfter=3,
            leftIndent=10, leading=14),

        "caption": ParagraphStyle("Caption",
            fontSize=8, fontName="Helvetica-Oblique",
            textColor=C_TEXT_LIGHT, spaceAfter=2),

        "footer": ParagraphStyle("Footer",
            fontSize=7.5, fontName="Helvetica",
            textColor=C_TEXT_LIGHT, alignment=TA_CENTER),

        "tbl_header": ParagraphStyle("TblHeader",
            fontSize=9, fontName="Helvetica-Bold",
            textColor=C_WHITE),

        "tbl_cell": ParagraphStyle("TblCell",
            fontSize=9, fontName="Helvetica",
            textColor=C_TEXT, leading=13),

        "tbl_cell_sm": ParagraphStyle("TblCellSm",
            fontSize=8, fontName="Helvetica",
            textColor=C_TEXT_MID, leading=12),

        "decision_go": ParagraphStyle("DecisionGO",
            fontSize=22, fontName="Helvetica-Bold",
            textColor=C_GREEN, alignment=TA_CENTER),

        "decision_nogo": ParagraphStyle("DecisionNoGO",
            fontSize=22, fontName="Helvetica-Bold",
            textColor=C_RED, alignment=TA_CENTER),

        "decision_inv": ParagraphStyle("DecisionInv",
            fontSize=22, fontName="Helvetica-Bold",
            textColor=C_AMBER, alignment=TA_CENTER),
    }


# ── Helper Flowables ───────────────────────────────────────────
def divider(color=C_BORDER, thickness=0.5, space=3):
    return HRFlowable(width="100%", thickness=thickness,
                      color=color, spaceBefore=space, spaceAfter=space)


def spacer(h=4):
    return Spacer(1, h * mm)


def section_header(num: str, title: str, color=C_BLUE) -> list:
    """Returns a styled section header block."""
    st = S()
    line = HRFlowable(width="100%", thickness=2, color=color,
                      spaceBefore=0, spaceAfter=2)
    return [
        spacer(5),
        Paragraph(num, st["section_num"]),
        Paragraph(title, st["section_title"]),
        line,
        spacer(2),
    ]


def kv_row(label: str, value: str, style_label, style_value) -> list:
    """Label + value pair."""
    return [Paragraph(label, style_label), Paragraph(value, style_value)]


# ── Cover Page ─────────────────────────────────────────────────
def build_cover(disease: str, now: str, ds: dict, ev: dict) -> list:
    """Full-width dark cover page."""
    story = []

    # Dark header band via table
    decision    = (ds.get("go_no_go") or {}).get("decision", "INVESTIGATE")
    dec_color   = {"GO": "#22c55e", "NO-GO": "#ef4444", "INVESTIGATE": "#f59e0b"}.get(decision, "#f59e0b")
    conf        = float(ds.get("confidence_score") or 0)
    ev_label    = ev.get("evidence_label", "Unknown")
    drug        = ds.get("recommended_drug", "-")
    protein     = ds.get("target_protein", "-")

    st = S()

    # Cover table — dark background
    cover_content = [
        [Paragraph("CAUSYN AI", ParagraphStyle("BrandLg",
            fontSize=11, fontName="Helvetica-Bold",
            textColor=colors.HexColor("#60a5fa")))],
        [Paragraph("Drug Discovery Intelligence Report", st["cover_sub"])],
        [Spacer(1, 6*mm)],
        [Paragraph(disease, ParagraphStyle("DiseaseTitle",
            fontSize=28, fontName="Helvetica-Bold",
            textColor=C_WHITE, leading=32))],
        [Spacer(1, 4*mm)],
        [Paragraph(
            f'Final Decision: <font color="{dec_color}"><b>{decision}</b></font>  |  '
            f'Confidence: <b>{conf:.0%}</b>  |  Evidence: <b>{ev_label}</b>',
            ParagraphStyle("DecLine", fontSize=11, fontName="Helvetica",
                textColor=colors.HexColor("#cbd5e1"), leading=16))],
        [Spacer(1, 3*mm)],
        [Paragraph(
            f'Drug: <b>{drug}</b>   |   Target: <b>{protein}</b>',
            ParagraphStyle("DrugLine", fontSize=10, fontName="Helvetica",
                textColor=colors.HexColor("#94a3b8")))],
        [Spacer(1, 8*mm)],
        [Paragraph(f'Generated: {now}', st["cover_meta"])],
        [Paragraph(
            'Powered by OpenTargets | AlphaFold | FDA FAERS | ClinicalTrials.gov | PubMed | GPT-4o-mini',
            st["cover_meta"])],
    ]

    cover_tbl = Table([[row[0]] for row in cover_content], colWidths=[PAGE_W])
    cover_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_NAVY),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("TOPPADDING",    (0, 0), (0, 0),   14),
        ("BOTTOMPADDING", (0, -1),(0, -1),  14),
    ]))

    story.append(cover_tbl)
    story.append(spacer(6))

    # Disclaimer banner
    disclaimer_tbl = Table(
        [[Paragraph(
            "FOR EXPLORATORY RESEARCH PURPOSES ONLY — NOT FOR CLINICAL USE. "
            "AI-generated hypotheses are based on real scientific data but require experimental validation.",
            ParagraphStyle("Disc", fontSize=8, fontName="Helvetica",
                textColor=C_AMBER, alignment=TA_CENTER)
        )]],
        colWidths=[PAGE_W]
    )
    disclaimer_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), C_AMBER_LT),
        ("BOX",           (0,0), (-1,-1), 0.5, C_AMBER),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("RIGHTPADDING",  (0,0), (-1,-1), 8),
    ]))
    story.append(disclaimer_tbl)

    return story


# ── Metric Cards ───────────────────────────────────────────────
def metric_cards(metrics: list) -> Table:
    """
    Render a row of metric cards.
    metrics = [{"label": str, "value": str, "bg": color, "fg": color}]
    """
    st   = S()
    n    = len(metrics)
    w    = PAGE_W / n

    headers = []
    values  = []
    for m in metrics:
        headers.append(Paragraph(m["label"].upper(), ParagraphStyle("CardLabel",
            fontSize=7.5, fontName="Helvetica-Bold",
            textColor=m.get("fg", C_TEXT_LIGHT), alignment=TA_CENTER)))
        values.append(Paragraph(str(m["value"]), ParagraphStyle("CardValue",
            fontSize=m.get("size", 14), fontName="Helvetica-Bold",
            textColor=m.get("fg", C_TEXT), alignment=TA_CENTER)))

    tbl = Table([headers, values], colWidths=[w] * n)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_GRAY_LT),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ("LINEABOVE",     (0, 0), (-1, 0),  2,   C_BLUE),
        ("INNERGRID",     (0, 0), (-1, -1), 0.3, C_BORDER),
        ("BOX",           (0, 0), (-1, -1), 0.5, C_BORDER),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))

    # Apply individual background colors per column
    for i, m in enumerate(metrics):
        if "bg" in m:
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (i, 0), (i, -1), m["bg"]),
            ]))

    return tbl


# ── Info Box ──────────────────────────────────────────────────
def info_box(content: str, bg=C_BLUE_LT, border=C_BLUE,
             label: str = "") -> Table:
    """Colored info/callout box."""
    st    = S()
    inner = Paragraph(f"<b>{label}</b> {content}" if label else content,
                      ParagraphStyle("InfoBox", fontSize=9.5,
                          fontName="Helvetica", textColor=C_TEXT,
                          leading=15))
    tbl = Table([[inner]], colWidths=[PAGE_W])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), bg),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("RIGHTPADDING",  (0,0), (-1,-1), 10),
        ("TOPPADDING",    (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("LINEBEFORE",    (0,0), (0,-1),  3, border),
        ("BOX",           (0,0), (-1,-1), 0.3, border),
    ]))
    return tbl


# ── Standard Table ─────────────────────────────────────────────
def data_table(headers: list, rows: list, col_widths: list,
               header_color=C_NAVY) -> Table:
    """Build a clean data table."""
    st = S()

    header_row = [Paragraph(h, st["tbl_header"]) for h in headers]
    data_rows  = []
    for row in rows:
        data_rows.append([
            Paragraph(str(cell), st["tbl_cell"]) for cell in row
        ])

    tbl = Table([header_row] + data_rows, colWidths=col_widths)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",     (0,0),  (-1,0),  header_color),
        ("TEXTCOLOR",      (0,0),  (-1,0),  C_WHITE),
        ("FONTNAME",       (0,0),  (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",       (0,0),  (-1,-1), 9),
        ("ALIGN",          (0,0),  (-1,-1), "LEFT"),
        ("VALIGN",         (0,0),  (-1,-1), "MIDDLE"),
        ("TOPPADDING",     (0,0),  (-1,-1), 6),
        ("BOTTOMPADDING",  (0,0),  (-1,-1), 6),
        ("LEFTPADDING",    (0,0),  (-1,-1), 6),
        ("RIGHTPADDING",   (0,0),  (-1,-1), 6),
        ("ROWBACKGROUNDS", (0,1),  (-1,-1),
         [C_WHITE, colors.HexColor("#f8fafc")]),
        ("GRID",           (0,0),  (-1,-1), 0.3, C_BORDER),
        ("LINEBELOW",      (0,0),  (-1,0),  0.5, C_BORDER),
    ]))
    return tbl


# ── Main PDF Generator ─────────────────────────────────────────
def generate_pdf_report(data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=16*mm, bottomMargin=16*mm
    )

    st        = S()
    story     = []
    now       = datetime.now().strftime("%B %d, %Y  %H:%M UTC")

    disease   = data.get("disease_name", "Unknown Disease")
    hyps      = data.get("hypotheses", [])
    proteins  = data.get("protein_targets", [])
    drugs     = data.get("drugs", [])
    papers    = data.get("papers", [])
    ds        = data.get("decision_summary") or {}
    ev        = data.get("evidence_strength") or {}
    au        = data.get("analysis_uncertainty") or {}
    lr        = data.get("literature_review") or {}
    best      = hyps[0] if hyps else {}

    # ══════════════════════════════════════════════════════════
    # COVER
    # ══════════════════════════════════════════════════════════
    story += build_cover(disease, now, ds, ev)

    # ══════════════════════════════════════════════════════════
    # SECTION 1 — EXECUTIVE DECISION
    # ══════════════════════════════════════════════════════════
    story += section_header("SECTION 01", "Executive Decision", C_BLUE)

    gng       = ds.get("go_no_go") or {}
    decision  = gng.get("decision", "INVESTIGATE")
    dec_conf  = float(gng.get("confidence_in_decision") or 0)
    conf      = float(ds.get("confidence_score") or 0)
    risk      = ds.get("risk_level", "Unknown")
    drug_name = ds.get("recommended_drug", "-")
    prot_name = ds.get("target_protein", "-")
    pathway   = ds.get("target_pathway", "-")

    # Decision banner
    dec_bg  = {"GO": C_GREEN_LT, "NO-GO": C_RED_LT, "INVESTIGATE": C_AMBER_LT}.get(decision, C_AMBER_LT)
    dec_brd = {"GO": C_GREEN,    "NO-GO": C_RED,    "INVESTIGATE": C_AMBER}.get(decision, C_AMBER)
    dec_txt = {"GO": "GO — Proceed to Validation",
               "NO-GO": "NO-GO — Do Not Proceed",
               "INVESTIGATE": "INVESTIGATE — Further Analysis Required"}.get(decision, decision)

    decision_banner = Table(
        [[Paragraph(dec_txt, ParagraphStyle("DecBanner",
            fontSize=18, fontName="Helvetica-Bold",
            textColor=dec_brd, alignment=TA_CENTER)),
          Paragraph(f"{dec_conf:.0%}<br/><font size='8'>Decision Confidence</font>",
            ParagraphStyle("DecConf",
            fontSize=22, fontName="Helvetica-Bold",
            textColor=dec_brd, alignment=TA_CENTER))]],
        colWidths=[PAGE_W * 0.72, PAGE_W * 0.28]
    )
    decision_banner.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), dec_bg),
        ("BOX",           (0,0), (-1,-1), 1.5, dec_brd),
        ("TOPPADDING",    (0,0), (-1,-1), 12),
        ("BOTTOMPADDING", (0,0), (-1,-1), 12),
        ("LEFTPADDING",   (0,0), (-1,-1), 12),
        ("RIGHTPADDING",  (0,0), (-1,-1), 12),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("LINEAFTER",     (0,0), (0,-1),  0.5, dec_brd),
    ]))
    story.append(decision_banner)
    story.append(spacer(3))

    # Key metrics
    risk_fg = {"High": C_RED, "Medium": C_AMBER, "Low": C_GREEN}.get(risk, C_GRAY)
    conf_fg = C_GREEN if conf >= 0.7 else C_AMBER if conf >= 0.5 else C_RED

    story.append(metric_cards([
        {"label": "Recommended Drug",  "value": drug_name, "fg": C_BLUE,   "size": 12},
        {"label": "Target Protein",    "value": prot_name, "fg": C_PURPLE, "size": 12},
        {"label": "Confidence Score",  "value": f"{conf:.0%}", "fg": conf_fg},
        {"label": "Risk Level",        "value": risk,          "fg": risk_fg},
    ]))
    story.append(spacer(3))

    # Reasoning
    primary = str(gng.get("primary_reason") or ds.get("reasoning_summary", ""))
    action  = str(ds.get("suggested_action") or gng.get("recommended_action", ""))
    basis   = str(ds.get("evidence_basis", ""))

    if primary:
        story.append(info_box(primary, C_BLUE_LT, C_BLUE, "Decision Basis:"))
        story.append(spacer(2))
    if action:
        story.append(info_box(action, C_GREEN_LT, C_GREEN, "Recommended Action:"))
        story.append(spacer(2))

    # Supporting vs blocking
    supporting = gng.get("supporting_reasons") or []
    blocking   = gng.get("blocking_reasons") or []

    if supporting or blocking:
        story.append(spacer(2))
        cols = []
        if supporting:
            sup_content = [Paragraph("<b>Supporting Factors</b>",
                ParagraphStyle("ColHead", fontSize=10,
                    fontName="Helvetica-Bold", textColor=C_GREEN))]
            for s in supporting[:4]:
                sup_content.append(
                    Paragraph(f"+ {s}", ParagraphStyle("SupItem",
                        fontSize=8.5, fontName="Helvetica",
                        textColor=C_TEXT, leading=13, spaceAfter=2)))
            cols.append(sup_content)

        if blocking:
            blk_content = [Paragraph("<b>Blocking Factors</b>",
                ParagraphStyle("ColHead2", fontSize=10,
                    fontName="Helvetica-Bold", textColor=C_RED))]
            for b in blocking[:4]:
                blk_content.append(
                    Paragraph(f"- {b}", ParagraphStyle("BlkItem",
                        fontSize=8.5, fontName="Helvetica",
                        textColor=C_TEXT, leading=13, spaceAfter=2)))
            cols.append(blk_content)

        if len(cols) == 2:
            max_rows = max(len(cols[0]), len(cols[1]))
            while len(cols[0]) < max_rows: cols[0].append(Spacer(1,1))
            while len(cols[1]) < max_rows: cols[1].append(Spacer(1,1))

            factors_tbl = Table(
                [[cols[0][i], cols[1][i]] for i in range(max_rows)],
                colWidths=[PAGE_W/2 - 2*mm, PAGE_W/2 - 2*mm]
            )
            factors_tbl.setStyle(TableStyle([
                ("BACKGROUND",  (0,0), (0,-1), C_GREEN_LT),
                ("BACKGROUND",  (1,0), (1,-1), C_RED_LT),
                ("TOPPADDING",  (0,0), (-1,-1), 4),
                ("BOTTOMPADDING",(0,0),(-1,-1), 4),
                ("LEFTPADDING", (0,0), (-1,-1), 8),
                ("RIGHTPADDING",(0,0), (-1,-1), 8),
                ("BOX",         (0,0), (0,-1),  0.5, C_GREEN),
                ("BOX",         (1,0), (1,-1),  0.5, C_RED),
                ("INNERGRID",   (0,0), (-1,-1), 0.2, C_BORDER),
            ]))
            story.append(factors_tbl)

    # ══════════════════════════════════════════════════════════
    # SECTION 2 — TOP HYPOTHESIS
    # ══════════════════════════════════════════════════════════
    story += section_header("SECTION 02", "Top Hypothesis", C_PURPLE)

    if best:
        title  = str(best.get("title", ""))
        final  = float(best.get("final_score") or 0)
        expl   = str(best.get("explanation", ""))
        simple = str(best.get("simple_explanation", ""))
        steps  = best.get("reasoning_steps") or []

        # Hypothesis title card
        hyp_title_tbl = Table(
            [[Paragraph(title, ParagraphStyle("HypTitle",
                fontSize=12, fontName="Helvetica-Bold",
                textColor=C_TEXT, leading=17)),
              Paragraph(f"{final:.0%}", ParagraphStyle("HypScore",
                fontSize=20, fontName="Helvetica-Bold",
                textColor=C_PURPLE, alignment=TA_CENTER))]],
            colWidths=[PAGE_W * 0.8, PAGE_W * 0.2]
        )
        hyp_title_tbl.setStyle(TableStyle([
            ("BACKGROUND",   (0,0), (-1,-1), C_PURPLE_LT),
            ("BOX",          (0,0), (-1,-1), 1, C_PURPLE),
            ("TOPPADDING",   (0,0), (-1,-1), 10),
            ("BOTTOMPADDING",(0,0), (-1,-1), 10),
            ("LEFTPADDING",  (0,0), (-1,-1), 10),
            ("RIGHTPADDING", (0,0), (-1,-1), 10),
            ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
            ("LINEAFTER",    (0,0), (0,-1),  0.5, C_PURPLE),
        ]))
        story.append(hyp_title_tbl)
        story.append(spacer(2))

        # Key entities
        prots = ", ".join(best.get("key_proteins", []))
        drgs  = ", ".join(best.get("key_drugs", []))
        story.append(metric_cards([
            {"label": "Key Protein(s)", "value": prots or "-", "fg": C_BLUE,   "size": 11},
            {"label": "Key Drug(s)",    "value": drgs  or "-", "fg": C_GREEN,  "size": 11},
            {"label": "Composite Score","value": f"{final:.0%}","fg": C_PURPLE,"size": 14},
        ]))
        story.append(spacer(3))

        if expl:
            story.append(Paragraph("<b>Scientific Explanation</b>", st["subsection"]))
            story.append(Paragraph(expl, st["body"]))
            story.append(spacer(1))

        if simple:
            story.append(info_box(simple, C_BLUE_LT, C_BLUE, "Plain Language:"))
            story.append(spacer(2))

        # Reasoning steps
        if steps:
            story.append(Paragraph("<b>Reasoning Chain</b>", st["subsection"]))
            steps_data = [[
                Paragraph(f"<b>{i+1}</b>", ParagraphStyle("StepNum",
                    fontSize=11, fontName="Helvetica-Bold",
                    textColor=C_WHITE, alignment=TA_CENTER)),
                Paragraph(str(step), st["bullet"])
            ] for i, step in enumerate(steps)]

            steps_tbl = Table(steps_data,
                colWidths=[8*mm, PAGE_W - 8*mm])
            steps_tbl.setStyle(TableStyle([
                ("BACKGROUND",    (0,0), (0,-1), C_BLUE),
                ("BACKGROUND",    (1,0), (1,-1), C_GRAY_LT),
                ("TOPPADDING",    (0,0), (-1,-1), 6),
                ("BOTTOMPADDING", (0,0), (-1,-1), 6),
                ("LEFTPADDING",   (0,0), (-1,-1), 6),
                ("RIGHTPADDING",  (0,0), (-1,-1), 6),
                ("VALIGN",        (0,0), (-1,-1), "TOP"),
                ("INNERGRID",     (0,0), (-1,-1), 0.3, C_BORDER),
                ("BOX",           (0,0), (-1,-1), 0.5, C_BORDER),
            ]))
            story.append(steps_tbl)

    # ══════════════════════════════════════════════════════════
    # SECTION 3 — EVIDENCE & PROTEINS
    # ══════════════════════════════════════════════════════════
    story += section_header("SECTION 03", "Evidence Analysis & Protein Targets", C_GREEN)

    # Evidence + uncertainty side by side
    ev_label  = str(ev.get("evidence_label", "Unknown"))
    ev_score  = float(ev.get("evidence_score") or 0)
    au_label  = str(au.get("uncertainty_label", "Unknown"))
    au_score  = float(au.get("uncertainty_score") or 0)
    au_reason = str(au.get("uncertainty_reason", ""))

    ev_fg  = C_GREEN if ev_label == "Strong" else C_AMBER if ev_label == "Moderate" else C_RED
    au_fg  = C_RED   if "High" in au_label   else C_AMBER if au_label == "Medium"   else C_GREEN

    story.append(metric_cards([
        {"label": "Evidence Strength", "value": ev_label,        "fg": ev_fg},
        {"label": "Evidence Score",    "value": f"{ev_score:.2f}/1.00", "fg": ev_fg},
        {"label": "Uncertainty",       "value": au_label,        "fg": au_fg},
        {"label": "Uncertainty Score", "value": f"{au_score:.2f}/1.00", "fg": au_fg},
    ]))
    story.append(spacer(2))

    if au_reason:
        story.append(info_box(au_reason, C_GRAY_LT, C_GRAY))
        story.append(spacer(2))

    # Protein targets table
    if proteins:
        story.append(Paragraph("<b>Top Protein Targets</b>", st["subsection"]))
        prot_rows = []
        for p in proteins[:5]:
            af = float(p.get("alphafold_plddt") or 0)
            af_label = "V.High" if af >= 0.9 else "High" if af >= 0.7 else "Medium" if af >= 0.5 else "Low"
            prot_rows.append([
                p.get("gene_symbol", ""),
                p.get("protein_name", "")[:40],
                f"{p.get('association_score', 0):.3f}",
                f"{af:.2f} ({af_label})",
                p.get("alphafold_source", ""),
            ])
        story.append(data_table(
            ["Gene Symbol", "Protein Name", "Assoc. Score", "AlphaFold pLDDT", "Source"],
            prot_rows,
            [22*mm, 65*mm, 25*mm, 35*mm, 23*mm],
            header_color=C_NAVY
        ))

    # Research papers
    if papers:
        story.append(spacer(3))
        story.append(Paragraph("<b>Supporting Research Papers</b>", st["subsection"]))
        for i, p in enumerate(papers[:5], 1):
            story.append(Paragraph(
                f"<b>{i}.</b> {p.get('title','')[:90]}",
                st["body_sm"]))
            story.append(Paragraph(
                f"    {p.get('source','')} | {p.get('year','')} | "
                f"{p.get('citation_count',0)} citations | "
                f'<a href="{p.get("url","")}" color="#2563eb">View</a>',
                st["caption"]))

    # ══════════════════════════════════════════════════════════
    # SECTION 4 — DRUG & RISK ANALYSIS
    # ══════════════════════════════════════════════════════════
    story += section_header("SECTION 04", "Drug & Risk Analysis", C_AMBER)

    if drugs:
        drug_rows = []
        for d in drugs:
            comp     = d.get("competition_intel") or {}
            fda_aes  = d.get("fda_adverse_events") or []
            top_ae   = f"{fda_aes[0].get('reaction','')} ({fda_aes[0].get('count',0):,})" if fda_aes else "None"
            drug_rows.append([
                d.get("drug_name", ""),
                str(d.get("clinical_phase", "N/A")),
                d.get("target_gene", ""),
                d.get("risk_level", "Unknown"),
                comp.get("competition_level", "-"),
                top_ae,
            ])

        story.append(data_table(
            ["Drug Name", "Phase", "Target Gene", "FDA Risk", "Competition", "Top FDA Signal"],
            drug_rows,
            [35*mm, 14*mm, 22*mm, 20*mm, 24*mm, 55*mm],
            header_color=colors.HexColor("#92400e")
        ))
        story.append(spacer(3))

        # Drug details cards
        for d in drugs[:3]:
            comp    = d.get("competition_intel") or {}
            fda_aes = d.get("fda_adverse_events") or []
            trials  = d.get("clinical_trials") or []
            mech    = str(d.get("mechanism", ""))[:120]
            risk    = d.get("risk_level", "Unknown")
            risk_bg = {"High": C_RED_LT, "Medium": C_AMBER_LT, "Low": C_GREEN_LT}.get(risk, C_GRAY_LT)
            risk_bd = {"High": C_RED,    "Medium": C_AMBER,    "Low": C_GREEN}.get(risk, C_GRAY)

            detail_content = []
            detail_content.append(Paragraph(
                f"<b>{d.get('drug_name','')}</b>  |  "
                f"Phase {d.get('clinical_phase','?')}  |  "
                f"Type: {d.get('drug_type','')}  |  "
                f"Risk: <b>{risk}</b>",
                ParagraphStyle("DrugCard", fontSize=10,
                    fontName="Helvetica-Bold", textColor=C_TEXT)))

            if mech:
                detail_content.append(Paragraph(
                    f"Mechanism: {mech}",
                    ParagraphStyle("DrugMech", fontSize=8.5,
                        fontName="Helvetica", textColor=C_TEXT_MID,
                        leading=13, spaceBefore=3)))

            if fda_aes:
                ae_str = "  |  ".join([
                    f"{ae.get('reaction','')} ({ae.get('count',0):,} reports)"
                    for ae in fda_aes[:3]
                ])
                detail_content.append(Paragraph(
                    f"FDA Adverse Events: {ae_str}",
                    ParagraphStyle("DrugAE", fontSize=8.5,
                        fontName="Helvetica", textColor=C_RED,
                        leading=13, spaceBefore=2)))

            if trials:
                trial_str = "  |  ".join([
                    f"{t.get('nct_id','')} ({t.get('status_label','?')})"
                    for t in trials[:2]
                ])
                detail_content.append(Paragraph(
                    f"Clinical Trials: {trial_str}",
                    ParagraphStyle("DrugTrials", fontSize=8.5,
                        fontName="Helvetica", textColor=C_BLUE,
                        leading=13, spaceBefore=2)))

            if comp:
                detail_content.append(Paragraph(
                    f"Competition: {comp.get('competition_level','?')} | "
                    f"Market: {comp.get('market_opportunity','?')} | "
                    f"{comp.get('strategic_note','')}",
                    ParagraphStyle("DrugComp", fontSize=8.5,
                        fontName="Helvetica", textColor=C_TEXT_MID,
                        leading=13, spaceBefore=2)))

            card_tbl = Table([[cell] for cell in detail_content],
                colWidths=[PAGE_W])
            card_tbl.setStyle(TableStyle([
                ("BACKGROUND",    (0,0), (-1,-1), risk_bg),
                ("TOPPADDING",    (0,0), (-1,-1), 4),
                ("BOTTOMPADDING", (0,0), (-1,-1), 4),
                ("LEFTPADDING",   (0,0), (-1,-1), 10),
                ("RIGHTPADDING",  (0,0), (-1,-1), 10),
                ("TOPPADDING",    (0,0), (0, 0),  8),
                ("BOTTOMPADDING", (0,-1),(0,-1),  8),
                ("LINEBEFORE",    (0,0), (0,-1),  3, risk_bd),
                ("BOX",           (0,0), (-1,-1), 0.3, risk_bd),
            ]))
            story.append(card_tbl)
            story.append(spacer(2))

    # ══════════════════════════════════════════════════════════
    # SECTION 5 — FAILURE PREDICTION
    # ══════════════════════════════════════════════════════════
    story += section_header("SECTION 05", "Failure Prediction & Risk Factors", C_RED)

    if best:
        fp = best.get("failure_prediction") or {}
        if fp:
            fr_label  = str(fp.get("failure_risk_label", "Unknown"))
            fr_score  = float(fp.get("failure_risk_score") or 0)
            success_p = float(fp.get("success_probability") or 0)
            top_fail  = str(fp.get("top_failure_reason", ""))
            hist_ctx  = str(fp.get("historical_context", ""))

            fr_fg = C_RED if "High" in fr_label else C_AMBER if fr_label == "Medium" else C_GREEN

            story.append(metric_cards([
                {"label": "Failure Risk",         "value": fr_label,         "fg": fr_fg},
                {"label": "Failure Risk Score",   "value": f"{fr_score:.0%}","fg": fr_fg},
                {"label": "Success Probability",  "value": f"{success_p:.0%}","fg": C_GREEN},
            ]))
            story.append(spacer(3))

            if top_fail:
                story.append(info_box(top_fail, C_RED_LT, C_RED, "Primary Failure Mode:"))
                story.append(spacer(2))

            if hist_ctx:
                story.append(info_box(hist_ctx, C_GRAY_LT, C_GRAY, "Historical Context:"))
                story.append(spacer(2))

            reasons = fp.get("failure_reasons") or []
            if reasons:
                story.append(Paragraph("<b>Predicted Failure Reasons</b>", st["subsection"]))
                reason_rows = []
                for r in reasons[:4]:
                    reason_rows.append([
                        r.get("category", ""),
                        r.get("severity", ""),
                        r.get("reason", "")[:60],
                        r.get("mitigation", "")[:50],
                    ])
                story.append(data_table(
                    ["Category", "Severity", "Failure Reason", "Mitigation"],
                    reason_rows,
                    [25*mm, 20*mm, 65*mm, 60*mm],
                    header_color=C_RED
                ))
                story.append(spacer(2))

            safeguards = fp.get("recommended_safeguards") or []
            if safeguards:
                story.append(Paragraph("<b>Recommended Safeguards</b>", st["subsection"]))
                for sg in safeguards[:4]:
                    story.append(Paragraph(f"+ {sg}", st["bullet"]))

    # ══════════════════════════════════════════════════════════
    # SECTION 6 — TIME-TO-MARKET
    # ══════════════════════════════════════════════════════════
    story += section_header("SECTION 06", "Time-to-Market Estimate", C_PURPLE)

    if best:
        tti = best.get("time_to_impact") or {}
        if tti:
            sp    = float(tti.get("success_probability") or 0)
            sp_fg = C_GREEN if sp >= 0.7 else C_AMBER if sp >= 0.4 else C_RED

            story.append(metric_cards([
                {"label": "Timeline",             "value": tti.get("years_range","?"),       "fg": C_PURPLE},
                {"label": "Track",                "value": tti.get("speed_category","?"),     "fg": C_BLUE},
                {"label": "Current Stage",        "value": tti.get("current_stage","?")[:22],"fg": C_GRAY},
                {"label": "Success Probability",  "value": f"{sp:.0%}",                       "fg": sp_fg},
            ]))
            story.append(spacer(3))

            timeline    = tti.get("timeline_breakdown") or []
            bottlenecks = tti.get("key_bottlenecks") or []

            if timeline:
                story.append(Paragraph("<b>Timeline Breakdown</b>", st["subsection"]))
                tl_data = [[
                    Paragraph(f"<b>{i+1}</b>", ParagraphStyle("TLNum",
                        fontSize=10, fontName="Helvetica-Bold",
                        textColor=C_WHITE, alignment=TA_CENTER)),
                    Paragraph(step, st["bullet"])
                ] for i, step in enumerate(timeline)]
                tl_tbl = Table(tl_data, colWidths=[8*mm, PAGE_W - 8*mm])
                tl_tbl.setStyle(TableStyle([
                    ("BACKGROUND",    (0,0), (0,-1), C_PURPLE),
                    ("BACKGROUND",    (1,0), (1,-1), C_PURPLE_LT),
                    ("TOPPADDING",    (0,0), (-1,-1), 6),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 6),
                    ("LEFTPADDING",   (0,0), (-1,-1), 6),
                    ("RIGHTPADDING",  (0,0), (-1,-1), 6),
                    ("VALIGN",        (0,0), (-1,-1), "TOP"),
                    ("INNERGRID",     (0,0), (-1,-1), 0.3, C_BORDER),
                    ("BOX",           (0,0), (-1,-1), 0.5, C_BORDER),
                ]))
                story.append(tl_tbl)
                story.append(spacer(2))

            if bottlenecks:
                story.append(Paragraph("<b>Key Bottlenecks</b>", st["subsection"]))
                for b in bottlenecks:
                    story.append(Paragraph(f"- {b}", st["bullet"]))

    # ══════════════════════════════════════════════════════════
    # SECTION 7 — EXECUTIVE SUMMARY
    # ══════════════════════════════════════════════════════════
    story += section_header("SECTION 07", "Executive Summary", C_BLUE)

    if best:
        es = best.get("executive_summary") or {}
        if es:
            headline = str(es.get("headline", ""))
            body     = str(es.get("body", ""))
            market   = str(es.get("market_opportunity", ""))
            bottom   = str(es.get("bottom_line", ""))

            if headline:
                story.append(info_box(headline, C_NAVY,
                    C_BLUE, ""))
                story.append(spacer(2))

            if body:
                story.append(Paragraph(body, st["body"]))
                story.append(spacer(1))

            if market or bottom:
                mkt_data = []
                if market:
                    mkt_data.append(["Market Opportunity", market])
                if bottom:
                    mkt_data.append(["Bottom Line", bottom])

                mkt_tbl = Table(mkt_data,
                    colWidths=[38*mm, PAGE_W - 38*mm])
                mkt_tbl.setStyle(TableStyle([
                    ("BACKGROUND",    (0,0), (0,-1), C_NAVY),
                    ("TEXTCOLOR",     (0,0), (0,-1), C_WHITE),
                    ("FONTNAME",      (0,0), (0,-1), "Helvetica-Bold"),
                    ("FONTSIZE",      (0,0), (-1,-1), 9),
                    ("BACKGROUND",    (1,0), (1,-1), C_BLUE_LT),
                    ("TOPPADDING",    (0,0), (-1,-1), 7),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 7),
                    ("LEFTPADDING",   (0,0), (-1,-1), 8),
                    ("RIGHTPADDING",  (0,0), (-1,-1), 8),
                    ("GRID",          (0,0), (-1,-1), 0.3, C_BORDER),
                    ("VALIGN",        (0,0), (-1,-1), "TOP"),
                ]))
                story.append(mkt_tbl)

    # ══════════════════════════════════════════════════════════
    # SECTION 8 — LITERATURE OVERVIEW
    # ══════════════════════════════════════════════════════════
    if lr:
        story += section_header("SECTION 08", "Literature Overview", C_GREEN)

        lr_sections = [
            ("Background",          "background",       C_BLUE_LT,   C_BLUE),
            ("Current Research",    "current_research", C_GREEN_LT,  C_GREEN),
            ("Research Gaps",       "research_gaps",    C_AMBER_LT,  C_AMBER),
            ("Risks & Limitations", "risks_limitations",C_RED_LT,    C_RED),
            ("Conclusion",          "conclusion",       C_PURPLE_LT, C_PURPLE),
        ]
        for title, key, bg, border in lr_sections:
            content = lr.get(key, "")
            if content:
                story.append(info_box(content, bg, border, f"{title}:"))
                story.append(spacer(1))

    # ══════════════════════════════════════════════════════════
    # SECTION 9 — HYPOTHESIS COMPARISON
    # ══════════════════════════════════════════════════════════
    if len(hyps) > 1:
        story += section_header("SECTION 09", "All Hypotheses Comparison", C_PURPLE)

        hyp_rows = []
        for h in hyps:
            h_gng = h.get("go_no_go") or {}
            h_fp  = h.get("failure_prediction") or {}
            hyp_rows.append([
                f"#{h.get('rank',0)}",
                str(h.get("title",""))[:60],
                f"{float(h.get('final_score',0)):.0%}",
                h_gng.get("decision", "-"),
                h_fp.get("failure_risk_label", "-"),
            ])

        story.append(data_table(
            ["Rank", "Hypothesis Title", "Score", "Decision", "Failure Risk"],
            hyp_rows,
            [12*mm, 90*mm, 16*mm, 28*mm, 24*mm],
            header_color=C_NAVY
        ))

    # ══════════════════════════════════════════════════════════
    # FOOTER
    # ══════════════════════════════════════════════════════════
    story.append(spacer(6))
    story.append(divider(C_BORDER, 0.5, 0))
    story.append(Paragraph(
        f"Causyn AI V6  |  Generated: {now}  |  "
        f"Disease: {disease}  |  "
        f"Data: OpenTargets, AlphaFold EBI, FDA FAERS, ClinicalTrials.gov, PubMed  |  "
        f"For exploratory research only. Not for clinical use.",
        st["footer"]
    ))

    doc.build(story)
    buf.seek(0)
    return buf.read()


# ── Quick test ────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing PDF Report Service V6...")

    mock_data = {
        "disease_name": "Alzheimer disease",
        "hypotheses": [{
            "rank": 1,
            "title": "Lecanemab targets APP in the amyloidogenic pathway",
            "final_score": 0.80,
            "key_proteins": ["APP"],
            "key_drugs": ["Lecanemab"],
            "explanation": (
                "Lecanemab inhibits amyloid-beta aggregation by targeting APP cleavage "
                "products in the amyloidogenic pathway. The drug binds specifically to "
                "protofibrils, the most toxic form of amyloid-beta, reducing plaque burden "
                "and slowing neurodegeneration."
            ),
            "simple_explanation": (
                "Think of amyloid plaques like rust building up in an engine. "
                "Lecanemab acts like a rust remover, targeting the harmful protein "
                "before it clumps together and damages brain cells."
            ),
            "reasoning_steps": [
                "Step 1 - Protein role: APP is cleaved to produce amyloid-beta, the primary toxic species in Alzheimer disease.",
                "Step 2 - Drug mechanism: Lecanemab binds selectively to amyloid-beta protofibrils with high affinity.",
                "Step 3 - Pathway interaction: Binding prevents aggregation in the amyloidogenic pathway, reducing plaque load.",
                "Step 4 - Therapeutic logic: Phase 4 FDA approval confirms clinical efficacy with 27% slowing of decline."
            ],
            "go_no_go": {
                "decision": "GO",
                "confidence_in_decision": 0.82,
                "primary_reason": "Strong composite score (80%) exceeds GO threshold with Phase 4 approval and Low-Medium risk.",
                "recommended_action": "Proceed to experimental validation targeting APP.",
                "supporting_reasons": [
                    "Score 80% exceeds GO threshold of 70%",
                    "Phase 4 FDA approved drug - established safety profile",
                    "Low-Medium FDA risk profile"
                ],
                "blocking_reasons": []
            },
            "failure_prediction": {
                "failure_risk_label": "Medium",
                "failure_risk_score": 0.45,
                "success_probability": 0.65,
                "top_failure_reason": "Amyloid clearance may not fully translate to cognitive benefit.",
                "historical_context": "Aducanumab showed amyloid reduction but controversial cognitive benefit; Lecanemab shows stronger evidence.",
                "failure_reasons": [
                    {"category": "Efficacy", "severity": "High",
                     "reason": "Biomarker benefit may not equal cognitive improvement",
                     "evidence": "Mixed results across amyloid-targeting trials",
                     "mitigation": "Include MMSE and CDR cognitive endpoints alongside biomarkers"},
                    {"category": "Safety", "severity": "Medium",
                     "reason": "ARIA (brain swelling) in ~21% of patients",
                     "evidence": "Phase 3 CLARITY AD trial data",
                     "mitigation": "MRI monitoring protocol every 3 months"}
                ],
                "recommended_safeguards": [
                    "Cognitive endpoint monitoring alongside biomarkers",
                    "Regular MRI monitoring for ARIA",
                    "Adaptive trial design with interim analysis"
                ]
            },
            "time_to_impact": {
                "years_range": "0-2 years",
                "speed_category": "Fast",
                "current_stage": "Phase 4 / FDA Approved",
                "success_probability": 0.80,
                "timeline_breakdown": [
                    "Currently approved for early Alzheimer disease (FDA 2023)",
                    "Label expansion studies ongoing: 1-2 years",
                    "New indication approval possible: 2-4 years"
                ],
                "key_bottlenecks": [
                    "Standard regulatory timeline for label expansion",
                    "ARIA safety monitoring requirements"
                ]
            },
            "executive_summary": {
                "headline": "Lecanemab represents the strongest near-term opportunity in Alzheimer drug development",
                "body": (
                    "Lecanemab (Leqembi) is FDA-approved for early Alzheimer disease and has demonstrated "
                    "a 27% slowing of cognitive decline in Phase 3 trials. With APP as its target and a "
                    "well-characterized mechanism of action, it represents the best-evidenced opportunity "
                    "in this analysis. The drug's Phase 4 status means market entry is already achieved."
                ),
                "market_opportunity": "$15B+ Alzheimer's therapeutics market with 6.5M patients in the US alone. Lecanemab addresses early-stage disease with a differentiated mechanism.",
                "bottom_line": "Recommend proceeding with validation studies for label expansion to moderate Alzheimer disease."
            }
        }],
        "protein_targets": [
            {"gene_symbol": "APP", "protein_name": "Amyloid Precursor Protein",
             "association_score": 0.870, "alphafold_plddt": 0.67, "alphafold_source": "AlphaFold API"},
            {"gene_symbol": "PSEN1", "protein_name": "Presenilin-1",
             "association_score": 0.866, "alphafold_plddt": 0.72, "alphafold_source": "AlphaFold API"},
            {"gene_symbol": "APOE", "protein_name": "Apolipoprotein E",
             "association_score": 0.775, "alphafold_plddt": 0.76, "alphafold_source": "AlphaFold API"},
        ],
        "drugs": [
            {"drug_name": "Lecanemab", "clinical_phase": 4, "drug_type": "Antibody",
             "target_gene": "APP", "mechanism": "Amyloid-beta protofibril inhibitor",
             "risk_level": "Medium", "risk_description": "ARIA risk in ~21% of patients",
             "competition_intel": {"competition_level": "High", "market_opportunity": "Crowded",
                                   "strategic_note": "3 amyloid antibodies now approved",
                                   "drug_class": "Amyloid-beta antibody"},
             "fda_adverse_events": [
                 {"reaction": "Amyloid Related Imaging Abnormality", "count": 1823},
                 {"reaction": "Headache", "count": 942}
             ],
             "clinical_trials": [
                 {"nct_id": "NCT03887455", "title": "CLARITY AD - Phase 3 Lecanemab Trial",
                  "status": "COMPLETED", "status_label": "Completed", "phase": "Phase 3",
                  "sponsor": "Eisai Inc", "start_date": "2019-03",
                  "url": "https://clinicaltrials.gov/study/NCT03887455"},
             ],
             "trial_count": 1, "active_trial_count": 0, "completed_trial_count": 1},
        ],
        "papers": [
            {"title": "Lecanemab in Early Alzheimer's Disease", "year": 2023,
             "source": "PubMed", "citation_count": 892,
             "url": "https://pubmed.ncbi.nlm.nih.gov/36449413/"},
        ],
        "decision_summary": {
            "recommended_drug": "Lecanemab", "target_protein": "APP",
            "target_pathway": "amyloidogenic pathway",
            "confidence_score": 0.80, "risk_level": "Medium",
            "reasoning_summary": "Lecanemab (Phase 4) targeting APP via the amyloidogenic pathway shows 80% composite score.",
            "suggested_action": "Proceed with label expansion validation studies for moderate Alzheimer disease.",
            "evidence_basis": "9 research papers | Evidence: Strong | Protein score: 0.87",
            "go_no_go": {
                "decision": "GO", "confidence_in_decision": 0.82,
                "primary_reason": "Score exceeds GO threshold with FDA approval.",
                "recommended_action": "Design in-vivo study targeting APP.",
                "supporting_reasons": ["Score 80% exceeds threshold", "Phase 4 approved", "Moderate risk"],
                "blocking_reasons": []
            }
        },
        "evidence_strength": {
            "evidence_label": "Strong", "evidence_score": 0.72,
            "evidence_breakdown": "9 papers | 3 highly cited | 4 recent | avg 287 citations"
        },
        "analysis_uncertainty": {
            "uncertainty_label": "Low", "uncertainty_score": 0.20,
            "uncertainty_reason": "Strong evidence base with established clinical data. Results are reliable for decision-making."
        },
        "literature_review": {
            "background": "Alzheimer disease is a progressive neurodegenerative disorder affecting 50M people worldwide. Current approved therapies include cholinesterase inhibitors and the recently approved amyloid-targeting antibodies lecanemab and donanemab.",
            "current_research": "The field has shifted toward amyloid-targeting immunotherapies following FDA approvals. LRRK2 inhibitors and tau-targeting approaches represent emerging directions. Combination therapies are gaining traction.",
            "research_gaps": "The causal relationship between amyloid clearance and cognitive benefit remains debated. Biomarker development for patient stratification and identification of early intervention windows are critical unmet needs.",
            "risks_limitations": "ARIA (amyloid-related imaging abnormalities) affects 21% of lecanemab patients. The long-term cognitive benefit profile requires further characterization. Access and cost remain significant barriers.",
            "conclusion": "Based on current evidence, lecanemab targeting APP represents the strongest therapeutic opportunity in Alzheimer disease. Experimental validation of combination approaches and biomarker-guided patient selection are recommended next steps."
        }
    }

    pdf_bytes = generate_pdf_report(mock_data)
    with open("test_report_v6.pdf", "wb") as f:
        f.write(pdf_bytes)
    print(f"PDF generated: test_report_v6.pdf ({len(pdf_bytes):,} bytes)")
    print("Open with: Invoke-Item test_report_v6.pdf")

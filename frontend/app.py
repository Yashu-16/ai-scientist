# frontend/app.py
# V3 Decision Intelligence Platform
# Features: Decision Panel, Multi-Disease Comparison, Causal Reasoning,
#           4 tabs, Ranking, Evidence, Risk Analysis

import streamlit as st
import requests
import time
import json

# ── Page Configuration ────────────────────────────────────────
st.set_page_config(
    page_title = "AI Scientist — Decision Intelligence",
    page_icon  = "🧬",
    layout     = "wide",
    initial_sidebar_state = "expanded"
)

API_BASE_URL = "http://localhost:8000"

# ── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    .protein-badge {
        background-color: #1e3a5f; color: #60a5fa;
        padding: 4px 10px; border-radius: 20px;
        font-size: 13px; font-weight: 600;
        margin-right: 6px; display: inline-block;
    }
    .drug-badge {
        background-color: #1e3a2f; color: #34d399;
        padding: 4px 10px; border-radius: 20px;
        font-size: 13px; font-weight: 600;
        margin-right: 6px; display: inline-block;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ── Helper Functions ──────────────────────────────────────────
def confidence_color(score: float) -> str:
    if score >= 0.8:   return "#22c55e"
    elif score >= 0.6: return "#84cc16"
    elif score >= 0.4: return "#f59e0b"
    else:              return "#ef4444"

def confidence_emoji(score: float) -> str:
    if score >= 0.8:   return "🟢"
    elif score >= 0.6: return "🟡"
    elif score >= 0.4: return "🟠"
    else:              return "🔴"

def render_confidence_bar(score: float, label: str):
    color = confidence_color(score)
    emoji = confidence_emoji(score)
    col1, col2 = st.columns([3, 1])
    with col1:
        st.progress(score)
    with col2:
        st.markdown(
            f"<span style='color:{color}; font-weight:700; font-size:16px;'>"
            f"{emoji} {score:.0%} {label}</span>",
            unsafe_allow_html=True
        )

def call_api(disease_name, max_targets, max_papers, max_drugs):
    try:
        r = requests.post(
            f"{API_BASE_URL}/analyze-disease",
            json={"disease_name": disease_name,
                  "max_targets": max_targets,
                  "max_papers":  max_papers,
                  "max_drugs":   max_drugs},
            timeout=180
        )
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to backend. Run: uvicorn backend.main:app --reload --port 8000"}
    except requests.exceptions.Timeout:
        return {"error": "Request timed out. Please try again."}
    except Exception as e:
        return {"error": str(e)}

def call_compare_api(diseases, max_targets, max_papers, max_drugs):
    try:
        r = requests.post(
            f"{API_BASE_URL}/compare-diseases",
            json={"diseases":    diseases,
                  "max_targets": max_targets,
                  "max_papers":  max_papers,
                  "max_drugs":   max_drugs},
            timeout=300
        )
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to backend."}
    except requests.exceptions.Timeout:
        return {"error": "Request timed out. Multi-disease takes ~2min."}
    except Exception as e:
        return {"error": str(e)}

def get_example_diseases():
    try:
        r = requests.get(f"{API_BASE_URL}/diseases/examples", timeout=5)
        return r.json().get("examples", [])
    except:
        return ["Alzheimer disease", "Parkinson disease",
                "breast cancer", "type 2 diabetes",
                "rheumatoid arthritis", "lung cancer"]

def render_causal_analysis(ca: dict):
    """Render causal reasoning section inside a hypothesis expander."""
    if not ca:
        return

    causal_score = float(ca.get("causal_score") or 0)
    causal_label = str(ca.get("causal_label") or "Unknown")
    causal_color = str(ca.get("causal_color") or "#64748b")
    causal_note  = str(ca.get("correlation_note") or "")
    causal_chain = ca.get("causal_chain") or []
    causal_verbs = ca.get("causal_verbs_found") or []
    causal_evid  = ca.get("causal_evidence") or []
    total_hits   = int(ca.get("total_causal_hits") or 0)

    st.markdown("**🔗 Causal Reasoning**")

    ca_emoji = ("✅" if causal_label == "Likely Causal"
                else "⚠️" if causal_label == "Possibly Causal"
                else "ℹ️")

    col_ca1, col_ca2 = st.columns([2, 3])
    with col_ca1:
        st.markdown(
            f"<div style='background:{causal_color}22;"
            f"border:1px solid {causal_color}55;"
            f"border-radius:10px;padding:14px;text-align:center;'>"
            f"<div style='font-size:24px;'>{ca_emoji}</div>"
            f"<div style='color:{causal_color};font-weight:800;"
            f"font-size:16px;margin-top:6px;'>{causal_label}</div>"
            f"<div style='color:#64748b;font-size:12px;margin-top:4px;'>"
            f"Score: {causal_score:.2f} | {total_hits} causal hits"
            f"</div></div>",
            unsafe_allow_html=True
        )
    with col_ca2:
        st.markdown(
            f"<div style='background:#0f172a;border-radius:8px;"
            f"padding:12px;font-size:13px;color:#94a3b8;"
            f"line-height:1.6;'>{causal_note}</div>",
            unsafe_allow_html=True
        )
        if causal_verbs:
            st.markdown(
                "**Causal verbs detected:** " +
                " ".join([f"`{v}`" for v in causal_verbs[:6]])
            )

    # Causal chain
    if causal_chain:
        st.markdown("**⛓️ Causal Chain**")
        chain_html = " → ".join([
            f"<span style='background:#1e293b;color:#e2e8f0;"
            f"padding:4px 10px;border-radius:6px;font-size:12px;"
            f"font-weight:600;'>{node}</span>"
            for node in causal_chain
        ])
        st.markdown(
            f"<div style='padding:10px 0;'>{chain_html}</div>",
            unsafe_allow_html=True
        )

    # Evidence snippets
    if causal_evid:
        with st.expander(
            f"📄 View {len(causal_evid)} causal evidence snippets"
        ):
            for ev in causal_evid[:3]:
                strength = ev.get("strength","")
                ev_color = ("#22c55e" if strength == "strong"
                            else "#f59e0b" if strength == "moderate"
                            else "#64748b")
                st.markdown(
                    f"<div style='background:#0f172a;"
                    f"border-left:3px solid {ev_color};"
                    f"padding:8px 12px;margin:4px 0;"
                    f"border-radius:0 6px 6px 0;'>"
                    f"<div style='color:{ev_color};font-size:10px;"
                    f"font-weight:700;text-transform:uppercase;"
                    f"margin-bottom:4px;'>"
                    f"{strength} signal — verb: "
                    f"'{ev.get('causal_verb','')}'</div>"
                    f"<div style='color:#cbd5e1;font-size:12px;"
                    f"line-height:1.5;'>"
                    f"\"{ev.get('text','')}\"</div>"
                    f"<div style='color:#475569;font-size:10px;"
                    f"margin-top:4px;'>Source: {ev.get('source','')}"
                    f"</div></div>",
                    unsafe_allow_html=True
                )


def render_hypothesis_card(hyp: dict, data: dict, expanded: bool = False):
    """Render a full hypothesis expander card with all sections."""
    rank    = int(hyp.get("rank") or 0) or 1
    final   = float(hyp.get("final_score") or 0.0)
    score   = float(hyp.get("confidence_score") or 0.0)
    p_score = float(hyp.get("protein_score") or 0.0)
    d_score = float(hyp.get("drug_score") or 0.0)
    pa_score= float(hyp.get("paper_score") or 0.0)
    r_pen   = float(hyp.get("risk_penalty") or 0.0)
    display = final if final > 0 else score
    medals  = {1:"🥇", 2:"🥈", 3:"🥉"}
    medal   = medals.get(rank, f"#{rank}")

    # Get causal label for expander title
    ca         = hyp.get("causal_analysis") or {}
    causal_lbl = ca.get("causal_label","")
    causal_tag = f" | {causal_lbl}" if causal_lbl else ""

    with st.expander(
        f"{medal} Rank {rank} | Score: {display:.0%}{causal_tag} | {hyp['title']}",
        expanded=expanded
    ):

        # ── GO/NO-GO Badge ────────────────────────────────────
        gng = hyp.get("go_no_go") or {}
        if gng:
            render_go_no_go_badge(gng, size="large")
            st.markdown("---")

        # Score breakdown
        st.markdown("**📊 Ranking Score Breakdown**")
        bc1,bc2,bc3,bc4,bc5 = st.columns(5)
        bc1.metric("🧬 Protein",    f"{p_score:.2f}",
                   help="OpenTargets association (×0.4)")
        bc2.metric("💊 Drug Phase", f"{d_score:.2f}",
                   help="Clinical trial phase (×0.3)")
        bc3.metric("📚 Papers",     f"{pa_score:.2f}",
                   help="Paper support (×0.2)")
        bc4.metric("⚠️ Risk",       f"-{r_pen:.2f}",
                   help="FDA penalty (×0.1)")
        bc5.metric("🎯 Final",
                   f"{final:.2%}" if final > 0 else f"{score:.2%}",
                   help="Weighted composite score")
        if hyp.get("score_breakdown"):
            st.caption(f"📐 {hyp['score_breakdown']}")
        st.markdown("---")

        # LLM Confidence
        st.markdown("**LLM Confidence**")
        render_confidence_bar(score, hyp.get("confidence_label",""))

        # Protein + Drug tags
        ct1, ct2 = st.columns(2)
        with ct1:
            st.markdown("**🧬 Key Proteins**")
            proteins = hyp.get("key_proteins") or []
            if proteins:
                st.markdown(" ".join([
                    f"<span class='protein-badge'>{p}</span>"
                    for p in proteins
                ]), unsafe_allow_html=True)
            else:
                st.caption("None tagged")
        with ct2:
            st.markdown("**💊 Key Drugs**")
            drugs = hyp.get("key_drugs") or []
            if drugs:
                st.markdown(" ".join([
                    f"<span class='drug-badge'>{d}</span>"
                    for d in drugs
                ]), unsafe_allow_html=True)
            else:
                st.caption("None tagged")

        st.markdown("---")

        # Explanations
        cs, ce = st.columns(2)
        with cs:
            st.markdown("**🔬 Scientific Explanation**")
            st.markdown(
                f"<div style='background:#0f172a;padding:14px;"
                f"border-radius:8px;font-size:14px;"
                f"line-height:1.7;color:#cbd5e1;'>"
                f"{hyp.get('explanation','')}</div>",
                unsafe_allow_html=True)
        with ce:
            st.markdown("**🧒 Simple Explanation**")
            st.markdown(
                f"<div style='background:#0f172a;padding:14px;"
                f"border-radius:8px;font-size:14px;"
                f"line-height:1.7;color:#cbd5e1;'>"
                f"{hyp.get('simple_explanation','')}</div>",
                unsafe_allow_html=True)

        if hyp.get("evidence_summary"):
            st.info(f"📌 {hyp['evidence_summary']}")

        # Reasoning chain
        steps = hyp.get("reasoning_steps") or []
        if steps:
            st.markdown("**🔗 Reasoning Chain**")
            for step in steps:
                st.markdown(
                    f"<div style='background:#0f172a;"
                    f"border-left:3px solid #6366f1;"
                    f"padding:8px 14px;margin:4px 0;"
                    f"border-radius:0 6px 6px 0;"
                    f"font-size:13px;color:#c4b5fd;'>"
                    f"{step}</div>",
                    unsafe_allow_html=True)

        # Causal analysis
        render_causal_analysis(hyp.get("causal_analysis") or {})

        # ── Experimental Validation ───────────────────────────
        vs = hyp.get("validation_suggestion") or {}
        if vs:
            render_validation_suggestion(vs)
        
        # ── Hypothesis Critique ───────────────────────────────
        cr = hyp.get("critique") or {}
        if cr:
            render_hypothesis_critique(cr)

        # ── Failure Prediction ────────────────────────────────
        fp = hyp.get("failure_prediction") or {}
        if fp:
            render_failure_prediction(fp)


        # ── Time-to-Impact ────────────────────────────────────
        tti = hyp.get("time_to_impact") or {}
        if tti:
            render_time_to_impact(tti)

        # ── Executive Summary ─────────────────────────────────
        es = hyp.get("executive_summary") or {}
        if es:
            render_executive_summary(es)

        # ── Uncertainty Analysis ──────────────────────────────
        unc = hyp.get("uncertainty") or {}
        if unc:
            render_uncertainty_indicator(unc, compact=False)

def render_validation_suggestion(vs: dict):
    """Render experimental validation suggestion inside hypothesis card."""
    if not vs:
        return

    v_type   = str(vs.get("validation_type") or "Unknown")
    v_color  = str(vs.get("validation_color") or "#64748b")
    title    = str(vs.get("experiment_title") or "")
    desc     = str(vs.get("experiment_description") or "")
    tools    = vs.get("required_tools") or []
    outcome  = str(vs.get("expected_outcome") or "")
    timeline = str(vs.get("estimated_timeline") or "")
    diff     = str(vs.get("difficulty") or "")
    diff_col = str(vs.get("difficulty_color") or "#64748b")

    type_emoji = {
        "In-vitro": "🧫",
        "In-vivo":  "🐭",
        "Clinical": "🏥"
    }.get(v_type, "🔬")

    st.markdown("**🧪 Experimental Validation Suggestion**")

    # Header bar
    st.markdown(
        f"<div style='background:{v_color}15;border:1px solid {v_color}44;"
        f"border-radius:10px;padding:14px 16px;margin-bottom:8px;'>"
        f"<div style='display:flex;justify-content:space-between;"
        f"align-items:flex-start;'>"
        f"<div>"
        f"<span style='background:{v_color};color:white;padding:3px 12px;"
        f"border-radius:20px;font-size:12px;font-weight:700;'>"
        f"{type_emoji} {v_type}</span>"
        f"<span style='margin-left:10px;background:{diff_col}22;"
        f"color:{diff_col};padding:3px 10px;border-radius:20px;"
        f"font-size:11px;font-weight:600;'>{diff} Difficulty</span>"
        f"<span style='margin-left:10px;color:#64748b;font-size:12px;'>"
        f"⏱️ {timeline}</span>"
        f"</div></div>"
        f"<div style='margin-top:10px;font-size:14px;font-weight:600;"
        f"color:#e2e8f0;'>{title}</div>"
        f"</div>",
        unsafe_allow_html=True
    )

    col_desc, col_tools = st.columns([3, 2])

    with col_desc:
        st.markdown(
            f"<div style='background:#0f172a;border-radius:8px;"
            f"padding:12px;font-size:13px;color:#cbd5e1;"
            f"line-height:1.7;'>"
            f"<div style='color:#94a3b8;font-size:10px;"
            f"text-transform:uppercase;letter-spacing:1px;"
            f"margin-bottom:6px;'>Protocol</div>"
            f"{desc}</div>",
            unsafe_allow_html=True
        )

    with col_tools:
        if tools:
            tools_html = "".join([
                f"<div style='background:#1e293b;color:#94a3b8;"
                f"padding:4px 10px;border-radius:6px;font-size:12px;"
                f"margin-bottom:4px;'>🔧 {t}</div>"
                for t in tools[:4]
            ])
            st.markdown(
                f"<div style='background:#0f172a;border-radius:8px;"
                f"padding:12px;'>"
                f"<div style='color:#94a3b8;font-size:10px;"
                f"text-transform:uppercase;letter-spacing:1px;"
                f"margin-bottom:6px;'>Required Tools</div>"
                f"{tools_html}</div>",
                unsafe_allow_html=True
            )

    if outcome:
        st.markdown(
            f"<div style='background:#0a1f0a;border:1px solid #166534;"
            f"border-radius:8px;padding:10px 14px;margin-top:6px;'>"
            f"<span style='color:#4ade80;font-size:11px;font-weight:700;"
            f"text-transform:uppercase;letter-spacing:1px;'>"
            f"✅ Expected Outcome: </span>"
            f"<span style='color:#bbf7d0;font-size:13px;'>{outcome}</span>"
            f"</div>",
            unsafe_allow_html=True
        )

def render_hypothesis_critique(critique: dict):
    """Render hypothesis critique section inside hypothesis card."""
    if not critique:
        return

    assessment = str(critique.get("overall_assessment") or "")
    weaknesses = critique.get("weaknesses") or []
    contradictions = critique.get("contradictory_evidence") or []
    risks      = critique.get("risks") or []
    conf_impact= str(critique.get("confidence_impact") or "")
    salvage    = str(critique.get("salvage_suggestion") or "")
    severity   = str(critique.get("critique_severity") or "Moderate")
    sev_color  = str(critique.get("severity_color") or "#f59e0b")

    sev_emoji  = {
        "Minor":    "🟢",
        "Moderate": "🟡",
        "Major":    "🔴"
    }.get(severity, "🟡")

    st.markdown("**🔍 Critical Evaluation**")

    # Severity header
    st.markdown(
        f"<div style='background:{sev_color}15;"
        f"border:1px solid {sev_color}44;"
        f"border-radius:10px;padding:14px 16px;margin-bottom:10px;'>"
        f"<div style='display:flex;justify-content:space-between;"
        f"align-items:center;margin-bottom:8px;'>"
        f"<span style='background:{sev_color}33;color:{sev_color};"
        f"padding:3px 12px;border-radius:20px;font-size:12px;"
        f"font-weight:700;'>{sev_emoji} {severity} Limitations</span>"
        f"</div>"
        f"<div style='font-size:13px;color:#cbd5e1;"
        f"line-height:1.6;font-style:italic;'>\"{assessment}\"</div>"
        f"</div>",
        unsafe_allow_html=True
    )

    col_w, col_r = st.columns(2)

    with col_w:
        if weaknesses:
            st.markdown(
                "<div style='color:#f87171;font-size:11px;font-weight:700;"
                "text-transform:uppercase;letter-spacing:1px;"
                "margin-bottom:6px;'>⚠️ Weaknesses</div>",
                unsafe_allow_html=True
            )
            for w in weaknesses:
                st.markdown(
                    f"<div style='background:#1a0a0a;"
                    f"border-left:3px solid #ef444455;"
                    f"padding:8px 12px;margin:4px 0;"
                    f"border-radius:0 6px 6px 0;"
                    f"font-size:12px;color:#fca5a5;"
                    f"line-height:1.5;'>• {w}</div>",
                    unsafe_allow_html=True
                )

        if contradictions:
            st.markdown(
                "<div style='color:#fb923c;font-size:11px;font-weight:700;"
                "text-transform:uppercase;letter-spacing:1px;"
                "margin:10px 0 6px;'>🔄 Contradictory Evidence</div>",
                unsafe_allow_html=True
            )
            for c in contradictions:
                st.markdown(
                    f"<div style='background:#1a0d05;"
                    f"border-left:3px solid #f97316;"
                    f"padding:8px 12px;margin:4px 0;"
                    f"border-radius:0 6px 6px 0;"
                    f"font-size:12px;color:#fdba74;"
                    f"line-height:1.5;'>• {c}</div>",
                    unsafe_allow_html=True
                )

    with col_r:
        if risks:
            st.markdown(
                "<div style='color:#fbbf24;font-size:11px;font-weight:700;"
                "text-transform:uppercase;letter-spacing:1px;"
                "margin-bottom:6px;'>🚨 Risks</div>",
                unsafe_allow_html=True
            )
            for r in risks:
                st.markdown(
                    f"<div style='background:#1a1505;"
                    f"border-left:3px solid #f59e0b;"
                    f"padding:8px 12px;margin:4px 0;"
                    f"border-radius:0 6px 6px 0;"
                    f"font-size:12px;color:#fde68a;"
                    f"line-height:1.5;'>• {r}</div>",
                    unsafe_allow_html=True
                )

        if conf_impact:
            st.markdown(
                "<div style='color:#94a3b8;font-size:11px;font-weight:700;"
                "text-transform:uppercase;letter-spacing:1px;"
                "margin:10px 0 6px;'>📊 Confidence Impact</div>",
                unsafe_allow_html=True
            )
            st.markdown(
                f"<div style='background:#0f172a;"
                f"padding:8px 12px;border-radius:6px;"
                f"font-size:12px;color:#94a3b8;"
                f"line-height:1.5;'>{conf_impact}</div>",
                unsafe_allow_html=True
            )

    # Salvage suggestion
    if salvage:
        st.markdown(
            f"<div style='background:#0f1f0f;"
            f"border:1px solid #16653488;"
            f"border-radius:8px;padding:12px 14px;margin-top:8px;'>"
            f"<div style='color:#4ade80;font-size:11px;font-weight:700;"
            f"text-transform:uppercase;letter-spacing:1px;"
            f"margin-bottom:6px;'>💡 How to Strengthen This Hypothesis</div>"
            f"<div style='font-size:13px;color:#bbf7d0;"
            f"line-height:1.6;'>{salvage}</div>"
            f"</div>",
            unsafe_allow_html=True
        )

def render_uncertainty_indicator(uncertainty: dict,
                                  compact: bool = False):
    """Render uncertainty indicator for a hypothesis or analysis."""
    if not uncertainty:
        return

    score  = float(uncertainty.get("uncertainty_score") or 0)
    label  = str(uncertainty.get("uncertainty_label") or "Unknown")
    color  = str(uncertainty.get("uncertainty_color") or "#64748b")
    reason = str(uncertainty.get("uncertainty_reason") or "")
    note   = str(uncertainty.get("reliability_note") or "")
    factors= uncertainty.get("factors") or []

    emoji  = {
        "Low":      "✅",
        "Medium":   "⚠️",
        "High":     "🔶",
        "Very High":"❌"
    }.get(label, "❓")

    if compact:
        # Compact version for comparison table / summary
        st.markdown(
            f"<span style='background:{color}22;color:{color};"
            f"padding:3px 10px;border-radius:12px;font-size:12px;"
            f"font-weight:700;'>{emoji} {label} Uncertainty</span>",
            unsafe_allow_html=True
        )
        return

    # Full version for hypothesis card
    st.markdown("**📐 Uncertainty & Reliability**")

    # Header
    col_u1, col_u2 = st.columns([1, 2])
    with col_u1:
        st.markdown(
            f"<div style='background:{color}15;"
            f"border:2px solid {color}44;"
            f"border-radius:12px;padding:16px;"
            f"text-align:center;'>"
            f"<div style='font-size:28px;'>{emoji}</div>"
            f"<div style='color:{color};font-weight:800;"
            f"font-size:18px;margin-top:6px;'>{label}</div>"
            f"<div style='color:#64748b;font-size:12px;"
            f"margin-top:4px;'>Uncertainty</div>"
            f"<div style='color:{color};font-size:22px;"
            f"font-weight:700;margin-top:6px;'>"
            f"{score:.0%}</div>"
            f"</div>",
            unsafe_allow_html=True
        )

    with col_u2:
        st.markdown(
            f"<div style='background:#0f172a;border-radius:8px;"
            f"padding:12px;font-size:13px;color:#cbd5e1;"
            f"line-height:1.7;margin-bottom:8px;'>{reason}</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div style='background:#0a1f0a;"
            f"border:1px solid #166534;"
            f"border-radius:8px;padding:10px;font-size:12px;"
            f"color:#bbf7d0;'>"
            f"💡 <strong>To reduce uncertainty:</strong> {note}"
            f"</div>",
            unsafe_allow_html=True
        )

    # Factors breakdown
    if factors:
        st.markdown("**Contributing Factors:**")
        for factor in factors:
            f_impact = factor.get("impact","")
            f_color  = {
                "High":   "#ef4444",
                "Medium": "#f59e0b",
                "Low":    "#22c55e"
            }.get(f_impact, "#64748b")
            f_emoji  = {
                "High":"🔴","Medium":"🟡","Low":"🟢"
            }.get(f_impact,"⚪")

            st.markdown(
                f"<div style='background:#0f172a;"
                f"border-left:3px solid {f_color};"
                f"padding:6px 12px;margin:3px 0;"
                f"border-radius:0 6px 6px 0;'>"
                f"<span style='color:{f_color};font-weight:700;"
                f"font-size:12px;'>{f_emoji} {factor.get('factor','')}: "
                f"{f_impact}</span>"
                f"<span style='color:#64748b;font-size:11px;"
                f"margin-left:8px;'>{factor.get('description','')[:80]}"
                f"</span></div>",
                unsafe_allow_html=True
            )

    # Data quality flags
    flags_html = []
    flag_map = [
        ("low_paper_count",    "🔴 Low paper count"),
        ("weak_protein_assoc", "🔴 Weak protein association"),
        ("high_fda_risk",      "🔴 High FDA risk"),
        ("no_causal_evidence", "🟡 No causal evidence"),
        ("limited_drug_data",  "🟡 Limited drug data"),
    ]
    for key, label_text in flag_map:
        if uncertainty.get(key):
            flags_html.append(
                f"<span style='background:#1a1a2e;color:#94a3b8;"
                f"padding:2px 8px;border-radius:8px;"
                f"font-size:11px;margin:2px;display:inline-block;'>"
                f"{label_text}</span>"
            )

    if flags_html:
        st.markdown(
            "<div style='margin-top:8px;'>" +
            "".join(flags_html) + "</div>",
            unsafe_allow_html=True
        )

def render_go_no_go_badge(gng: dict, size: str = "large"):
    """
    Render GO/NO-GO decision badge.
    size: 'large' (full card) or 'compact' (inline badge)
    """
    if not gng:
        return

    decision   = str(gng.get("decision") or "")
    color      = str(gng.get("decision_color") or "#64748b")
    emoji      = str(gng.get("decision_emoji") or "❓")
    conf       = float(gng.get("confidence_in_decision") or 0)
    primary    = str(gng.get("primary_reason") or "")
    action     = str(gng.get("recommended_action") or "")
    flip       = str(gng.get("conditions_to_flip") or "")
    supporting = gng.get("supporting_reasons") or []
    blocking   = gng.get("blocking_reasons") or []

    if size == "compact":
        st.markdown(
            f"<span style='background:{color};color:white;"
            f"padding:4px 14px;border-radius:20px;"
            f"font-size:13px;font-weight:800;"
            f"letter-spacing:1px;'>{emoji} {decision}</span>",
            unsafe_allow_html=True
        )
        return

    # Large version — full decision card
    bg_gradient = {
        "GO":          "linear-gradient(135deg,#052e16,#0a3d1f)",
        "NO-GO":       "linear-gradient(135deg,#2d0a0a,#3d1010)",
        "INVESTIGATE": "linear-gradient(135deg,#1c1202,#2d1f02)"
    }.get(decision, "linear-gradient(135deg,#0f172a,#1e293b)")

    st.markdown(
        f"<div style='background:{bg_gradient};"
        f"border:2px solid {color}55;"
        f"border-radius:14px;padding:20px 24px;margin:8px 0;'>"

        # Decision header
        f"<div style='display:flex;align-items:center;"
        f"justify-content:space-between;margin-bottom:14px;'>"
        f"<div style='display:flex;align-items:center;gap:12px;'>"
        f"<div style='font-size:36px;'>{emoji}</div>"
        f"<div>"
        f"<div style='font-size:11px;color:#94a3b8;"
        f"text-transform:uppercase;letter-spacing:2px;"
        f"font-weight:700;'>Final Decision</div>"
        f"<div style='font-size:28px;font-weight:900;"
        f"color:{color};letter-spacing:2px;'>{decision}</div>"
        f"</div></div>"
        f"<div style='text-align:right;'>"
        f"<div style='color:#64748b;font-size:11px;'>Decision confidence</div>"
        f"<div style='color:{color};font-size:24px;"
        f"font-weight:700;'>{conf:.0%}</div>"
        f"</div></div>"

        # Primary reason
        f"<div style='background:rgba(0,0,0,0.3);"
        f"border-radius:8px;padding:12px;margin-bottom:12px;"
        f"font-size:13px;color:#e2e8f0;line-height:1.6;'>"
        f"<strong style='color:{color};'>📋 Decision Basis: </strong>"
        f"{primary}</div>"

        f"</div>",
        unsafe_allow_html=True
    )

    # Supporting and blocking in columns
    if supporting or blocking:
        col_s, col_b = st.columns(2)

        with col_s:
            if supporting:
                st.markdown(
                    "<div style='color:#22c55e;font-size:11px;"
                    "font-weight:700;text-transform:uppercase;"
                    "letter-spacing:1px;margin-bottom:6px;'>"
                    "✅ Supporting Factors</div>",
                    unsafe_allow_html=True
                )
                for s in supporting:
                    st.markdown(
                        f"<div style='background:#052e1688;"
                        f"border-left:3px solid #22c55e;"
                        f"padding:6px 10px;margin:3px 0;"
                        f"border-radius:0 6px 6px 0;"
                        f"font-size:12px;color:#86efac;'>"
                        f"• {s}</div>",
                        unsafe_allow_html=True
                    )

        with col_b:
            if blocking:
                st.markdown(
                    "<div style='color:#ef4444;font-size:11px;"
                    "font-weight:700;text-transform:uppercase;"
                    "letter-spacing:1px;margin-bottom:6px;'>"
                    "❌ Blocking Factors</div>",
                    unsafe_allow_html=True
                )
                for b in blocking:
                    st.markdown(
                        f"<div style='background:#2d0a0a88;"
                        f"border-left:3px solid #ef4444;"
                        f"padding:6px 10px;margin:3px 0;"
                        f"border-radius:0 6px 6px 0;"
                        f"font-size:12px;color:#fca5a5;'>"
                        f"• {b}</div>",
                        unsafe_allow_html=True
                    )

    # Action + flip condition
    if action:
        st.markdown(
            f"<div style='background:#0f1f0f;"
            f"border:1px solid #16653488;"
            f"border-radius:8px;padding:10px 14px;margin-top:8px;'>"
            f"<span style='color:#4ade80;font-size:11px;"
            f"font-weight:700;text-transform:uppercase;"
            f"letter-spacing:1px;'>🚀 Recommended Action: </span>"
            f"<span style='font-size:13px;color:#bbf7d0;'>{action}</span>"
            f"</div>",
            unsafe_allow_html=True
        )

    if flip:
        st.markdown(
            f"<div style='background:#111827;"
            f"border-radius:8px;padding:8px 14px;margin-top:6px;'>"
            f"<span style='color:#64748b;font-size:11px;'>"
            f"🔄 <em>{flip}</em></span>"
            f"</div>",
            unsafe_allow_html=True
        )

def render_failure_prediction(fp: dict):
    """Render failure prediction section inside hypothesis card."""
    if not fp:
        return

    risk_score  = float(fp.get("failure_risk_score") or 0)
    risk_label  = str(fp.get("failure_risk_label") or "Unknown")
    risk_color  = str(fp.get("failure_risk_color") or "#64748b")
    top_reason  = str(fp.get("top_failure_reason") or "")
    hist_ctx    = str(fp.get("historical_context") or "")
    success_p   = float(fp.get("success_probability") or 0)
    reasons     = fp.get("failure_reasons") or []
    safeguards  = fp.get("recommended_safeguards") or []

    risk_emoji  = {
        "Low":       "🟢",
        "Medium":    "🟡",
        "High":      "🔶",
        "Very High": "🔴"
    }.get(risk_label, "❓")

    st.markdown("**⚠️ Failure Prediction Analysis**")

    # Header row
    col_f1, col_f2, col_f3 = st.columns([1, 1, 2])

    with col_f1:
        st.markdown(
            f"<div style='background:{risk_color}15;"
            f"border:2px solid {risk_color}44;"
            f"border-radius:10px;padding:14px;text-align:center;'>"
            f"<div style='font-size:11px;color:#94a3b8;"
            f"text-transform:uppercase;letter-spacing:1px;"
            f"margin-bottom:6px;'>Failure Risk</div>"
            f"<div style='font-size:24px;'>{risk_emoji}</div>"
            f"<div style='color:{risk_color};font-weight:800;"
            f"font-size:16px;margin-top:4px;'>{risk_label}</div>"
            f"<div style='color:#64748b;font-size:13px;"
            f"margin-top:2px;'>{risk_score:.0%}</div>"
            f"</div>",
            unsafe_allow_html=True
        )

    with col_f2:
        # Success probability gauge
        sp_color = confidence_color(success_p)
        st.markdown(
            f"<div style='background:#0f172a;"
            f"border:1px solid #1e293b;"
            f"border-radius:10px;padding:14px;text-align:center;'>"
            f"<div style='font-size:11px;color:#94a3b8;"
            f"text-transform:uppercase;letter-spacing:1px;"
            f"margin-bottom:6px;'>Success Probability</div>"
            f"<div style='color:{sp_color};font-weight:800;"
            f"font-size:28px;'>{success_p:.0%}</div>"
            f"<div style='color:#64748b;font-size:11px;'>"
            f"estimated</div>"
            f"</div>",
            unsafe_allow_html=True
        )

    with col_f3:
        if top_reason:
            st.markdown(
                f"<div style='background:#1a0d0d;"
                f"border-left:3px solid {risk_color};"
                f"border-radius:0 8px 8px 0;"
                f"padding:12px;height:100%;'>"
                f"<div style='color:{risk_color};font-size:11px;"
                f"font-weight:700;text-transform:uppercase;"
                f"letter-spacing:1px;margin-bottom:6px;'>"
                f"Top Failure Mode</div>"
                f"<div style='color:#fca5a5;font-size:13px;"
                f"line-height:1.5;'>{top_reason}</div>"
                f"</div>",
                unsafe_allow_html=True
            )

    # Historical context
    if hist_ctx:
        st.markdown(
            f"<div style='background:#0f172a;"
            f"border-radius:8px;padding:10px 14px;margin:8px 0;"
            f"font-size:12px;color:#94a3b8;line-height:1.6;'>"
            f"<strong style='color:#60a5fa;'>📚 Historical Context: </strong>"
            f"{hist_ctx}</div>",
            unsafe_allow_html=True
        )

    # Failure reasons grid
    if reasons:
        st.markdown("**Predicted Failure Reasons:**")
        cat_colors = {
            "Safety":      "#ef4444",
            "Efficacy":    "#f59e0b",
            "Mechanism":   "#8b5cf6",
            "Trial Design":"#3b82f6",
            "Market":      "#10b981"
        }
        for r in reasons[:4]:
            cat   = r.get("category","")
            sev   = r.get("severity","Medium")
            c_col = cat_colors.get(cat, "#64748b")
            sev_badge = {
                "High":   "🔴 High",
                "Medium": "🟡 Med",
                "Low":    "🟢 Low"
            }.get(sev, sev)

            with st.expander(
                f"[{cat}] {r.get('reason','')[:60]}... "
                f"— {sev_badge}"
            ):
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    st.markdown(
                        f"<div style='font-size:12px;color:#94a3b8;"
                        f"margin-bottom:4px;'><strong style='color:{c_col};'>"
                        f"Evidence:</strong> {r.get('evidence','')}</div>",
                        unsafe_allow_html=True
                    )
                with col_r2:
                    st.markdown(
                        f"<div style='font-size:12px;color:#86efac;'>"
                        f"<strong>Mitigation:</strong> "
                        f"{r.get('mitigation','')}</div>",
                        unsafe_allow_html=True
                    )

    # Safeguards
    if safeguards:
        st.markdown(
            "<div style='background:#0f1f0f;"
            "border:1px solid #166534;"
            "border-radius:8px;padding:12px 14px;margin-top:8px;'>"
            "<div style='color:#4ade80;font-size:11px;font-weight:700;"
            "text-transform:uppercase;letter-spacing:1px;"
            "margin-bottom:6px;'>🛡️ Recommended Safeguards</div>" +
            "".join([
                f"<div style='color:#bbf7d0;font-size:12px;"
                f"margin:3px 0;'>• {sg}</div>"
                for sg in safeguards[:4]
            ]) +
            "</div>",
            unsafe_allow_html=True
        )

def _similar_drugs_html(similar: list) -> str:
    """Helper to build similar drugs HTML without backslashes in f-string."""
    if not similar:
        return ""
    drugs_str = ", ".join(similar[:4])
    return (
        f"<div style='font-size:11px;color:#64748b;'>"
        f"Similar drugs: {drugs_str}</div>"
    )

def render_competition_badge(drug: dict, compact: bool = False):
    """Render competition intelligence for a drug."""
    comp = drug.get("competition_intel") or {}
    if not comp:
        return

    level     = str(comp.get("competition_level") or "Unknown")
    color     = str(comp.get("competition_color") or "#64748b")
    opp       = str(comp.get("market_opportunity") or "")
    note      = str(comp.get("strategic_note") or "")
    drug_class= str(comp.get("drug_class") or "")
    n_similar = int(comp.get("num_similar_drugs") or 0)
    similar   = comp.get("similar_drug_names") or []

    opp_color = {"Strong":"#22c55e","Moderate":"#f59e0b",
                 "Crowded":"#ef4444"}.get(opp,"#64748b")
    level_emoji = {"Low":"🟢","Medium":"🟡","High":"🔴"}.get(level,"⚪")
    opp_emoji   = {"Strong":"🌟","Moderate":"⚡","Crowded":"🏁"}.get(opp,"❓")

    if compact:
        st.markdown(
            f"<span style='background:{color}22;color:{color};"
            f"padding:3px 8px;border-radius:8px;font-size:11px;"
            f"font-weight:600;'>{level_emoji} {level} Competition</span>",
            unsafe_allow_html=True
        )
        return

    st.markdown(
        f"<div style='background:#0f172a;border:1px solid #1e293b;"
        f"border-radius:10px;padding:14px;margin:6px 0;'>"
        f"<div style='display:flex;justify-content:space-between;"
        f"align-items:flex-start;margin-bottom:10px;'>"
        f"<div>"
        f"<div style='font-size:11px;color:#94a3b8;text-transform:uppercase;"
        f"letter-spacing:1px;margin-bottom:4px;'>Drug Class</div>"
        f"<div style='color:#e2e8f0;font-size:13px;font-weight:600;'>"
        f"{drug_class}</div>"
        f"</div>"
        f"<div style='display:flex;gap:8px;'>"
        f"<span style='background:{color}22;color:{color};"
        f"padding:4px 10px;border-radius:8px;font-size:12px;"
        f"font-weight:700;'>{level_emoji} {level} Competition</span>"
        f"<span style='background:{opp_color}22;color:{opp_color};"
        f"padding:4px 10px;border-radius:8px;font-size:12px;"
        f"font-weight:700;'>{opp_emoji} {opp}</span>"
        f"</div></div>"
        f"<div style='font-size:12px;color:#94a3b8;"
        f"margin-bottom:8px;'>{note}</div>"
        f"{_similar_drugs_html(similar)}"
        f"</div>",
        unsafe_allow_html=True
    )

def render_time_to_impact(tti: dict):
    """Render time-to-impact prediction."""
    if not tti:
        return

    years   = float(tti.get("years_to_market") or 0)
    yr_rng  = str(tti.get("years_range") or "")
    stage   = str(tti.get("current_stage") or "")
    next_m  = str(tti.get("next_milestone") or "")
    success = float(tti.get("success_probability") or 0)
    speed   = str(tti.get("speed_category") or "")
    color   = str(tti.get("speed_color") or "#64748b")
    timeline= tti.get("timeline_breakdown") or []
    bottlenecks = tti.get("key_bottlenecks") or []

    speed_emoji = {"Fast":"🚀","Medium":"⚡","Slow":"🐢"}.get(speed,"⏱️")

    st.markdown("**⏱️ Time-to-Market Estimate**")

    t1,t2,t3 = st.columns(3)
    with t1:
        st.markdown(
            f"<div style='background:#0f172a;border:1px solid #1e293b;"
            f"border-radius:10px;padding:14px;text-align:center;'>"
            f"<div style='font-size:11px;color:#94a3b8;margin-bottom:4px;'>"
            f"Estimated Timeline</div>"
            f"<div style='color:{color};font-size:24px;font-weight:800;'>"
            f"{speed_emoji} {yr_rng}</div>"
            f"<div style='color:#64748b;font-size:11px;'>{speed} track</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    with t2:
        sc_color = confidence_color(success)
        st.markdown(
            f"<div style='background:#0f172a;border:1px solid #1e293b;"
            f"border-radius:10px;padding:14px;text-align:center;'>"
            f"<div style='font-size:11px;color:#94a3b8;margin-bottom:4px;'>"
            f"Success Probability</div>"
            f"<div style='color:{sc_color};font-size:24px;font-weight:800;'>"
            f"{success:.0%}</div>"
            f"<div style='color:#64748b;font-size:11px;'>to market</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    with t3:
        st.markdown(
            f"<div style='background:#0f172a;border:1px solid #1e293b;"
            f"border-radius:10px;padding:14px;'>"
            f"<div style='font-size:11px;color:#94a3b8;margin-bottom:4px;'>"
            f"Current Stage</div>"
            f"<div style='color:#e2e8f0;font-size:12px;font-weight:600;'>"
            f"{stage}</div>"
            f"<div style='color:#64748b;font-size:11px;margin-top:4px;'>"
            f"Next: {next_m[:50]}...</div>"
            f"</div>",
            unsafe_allow_html=True
        )

    if timeline:
        st.markdown("**📅 Timeline Breakdown:**")
        for i, step in enumerate(timeline, 1):
            st.markdown(
                f"<div style='background:#0f172a;"
                f"border-left:3px solid {color};"
                f"padding:6px 12px;margin:3px 0;"
                f"border-radius:0 6px 6px 0;"
                f"font-size:12px;color:#cbd5e1;'>"
                f"<strong style='color:{color};'>{i}.</strong> {step}"
                f"</div>",
                unsafe_allow_html=True
            )

    if bottlenecks:
        st.markdown(
            "<div style='background:#1a1105;border:1px solid #92400e44;"
            "border-radius:8px;padding:10px 14px;margin-top:6px;'>"
            "<div style='color:#fbbf24;font-size:11px;font-weight:700;"
            "text-transform:uppercase;letter-spacing:1px;"
            "margin-bottom:4px;'>⚠️ Key Bottlenecks</div>" +
            "".join([
                f"<div style='color:#fde68a;font-size:12px;"
                f"margin:2px 0;'>• {b}</div>"
                for b in bottlenecks
            ]) +
            "</div>",
            unsafe_allow_html=True
        )


def render_executive_summary(es: dict):
    """Render executive summary card."""
    if not es:
        return

    headline = str(es.get("headline") or "")
    body     = str(es.get("body") or "")
    market   = str(es.get("market_opportunity") or "")
    bottom   = str(es.get("bottom_line") or "")

    st.markdown("**📋 Executive Summary**")
    st.markdown(
        f"<div style='background:linear-gradient(135deg,#0f1b2d,#1a2744);"
        f"border:1px solid #2d4a7a;border-radius:10px;padding:16px;'>"
        f"<div style='color:#60a5fa;font-size:16px;font-weight:700;"
        f"margin-bottom:10px;'>💼 {headline}</div>"
        f"<div style='color:#cbd5e1;font-size:13px;line-height:1.7;"
        f"margin-bottom:10px;'>{body}</div>"
        f"<div style='background:#0a1628;border-radius:6px;padding:8px 12px;"
        f"margin-bottom:8px;font-size:12px;color:#94a3b8;'>"
        f"💰 {market}</div>"
        f"<div style='background:#0a1f0a;border-radius:6px;padding:8px 12px;"
        f"font-size:13px;color:#4ade80;font-weight:600;'>"
        f"✅ Bottom Line: {bottom}</div>"
        f"</div>",
        unsafe_allow_html=True
    )

def render_network_graph(network_data: dict, disease_name: str):
    """
    Render interactive protein-drug network using vis.js via HTML component.
    """
    if not network_data:
        st.info("No network data available")
        return

    nodes  = network_data.get("nodes", [])
    edges  = network_data.get("edges", [])
    stats  = network_data.get("stats", {})

    if not nodes:
        st.info("No nodes to display")
        return

    # Metrics
    n1,n2,n3,n4 = st.columns(4)
    n1.metric("🔵 Total Nodes", stats.get("total_nodes",0))
    n2.metric("🧬 Proteins",    stats.get("proteins",0))
    n3.metric("💊 Drugs",       stats.get("drugs",0))
    n4.metric("🔮 Pathways",    stats.get("pathways",0))

    # Legend
    st.markdown(
        "<div style='display:flex;gap:16px;flex-wrap:wrap;"
        "margin:8px 0 16px 0;'>" +
        "".join([
            f"<span style='display:flex;align-items:center;gap:6px;"
            f"font-size:12px;color:#94a3b8;'>"
            f"<span style='width:12px;height:12px;border-radius:50%;"
            f"background:{item['color']};display:inline-block;'></span>"
            f"{item['label']}</span>"
            for item in [
                {"color":"#ef4444","label":"Disease"},
                {"color":"#3b82f6","label":"Protein"},
                {"color":"#10b981","label":"Drug (Low Risk)"},
                {"color":"#f59e0b","label":"Drug (Med Risk)"},
                {"color":"#ef4444","label":"Drug (High Risk)"},
                {"color":"#8b5cf6","label":"Pathway"},
            ]
        ]) +
        "</div>",
        unsafe_allow_html=True
    )

    # Build vis.js HTML
    nodes_json = json.dumps(nodes)
    edges_json = json.dumps(edges)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.js"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.css"
              rel="stylesheet">
        <style>
            body {{
                margin: 0; padding: 0;
                background-color: #0e1117;
                font-family: sans-serif;
            }}
            #network {{
                width: 100%;
                height: 520px;
                background-color: #0e1117;
                border: 1px solid #1e293b;
                border-radius: 10px;
            }}
            #info-panel {{
                position: absolute;
                top: 10px; right: 10px;
                background: rgba(15,23,42,0.95);
                border: 1px solid #1e293b;
                border-radius: 8px;
                padding: 10px 14px;
                color: #94a3b8;
                font-size: 12px;
                max-width: 220px;
                display: none;
            }}
            #info-panel h4 {{
                color: #e2e8f0;
                margin: 0 0 6px 0;
                font-size: 13px;
            }}
        </style>
    </head>
    <body>
        <div style="position:relative;">
            <div id="network"></div>
            <div id="info-panel">
                <h4 id="node-title">Node Info</h4>
                <div id="node-details"></div>
            </div>
        </div>
        <script>
            var nodes = new vis.DataSet({nodes_json});
            var edges = new vis.DataSet({edges_json});

            var container = document.getElementById('network');
            var data      = {{ nodes: nodes, edges: edges }};

            var options = {{
                nodes: {{
                    shape: 'dot',
                    borderWidth: 2,
                    shadow: true,
                    font: {{ face: 'monospace', size: 13 }}
                }},
                edges: {{
                    smooth: {{
                        type: 'continuous',
                        roundness: 0.3
                    }},
                    font: {{
                        size: 10,
                        color: '#64748b',
                        align: 'middle'
                    }},
                    shadow: false
                }},
                physics: {{
                    enabled: true,
                    forceAtlas2Based: {{
                        gravitationalConstant: -50,
                        centralGravity: 0.01,
                        springLength: 120,
                        springConstant: 0.08,
                        damping: 0.4
                    }},
                    solver: 'forceAtlas2Based',
                    stabilization: {{
                        enabled: true,
                        iterations: 200,
                        fit: true
                    }}
                }},
                interaction: {{
                    hover: true,
                    tooltipDelay: 100,
                    hideEdgesOnDrag: false,
                    navigationButtons: true,
                    keyboard: true
                }},
                layout: {{
                    improvedLayout: true
                }}
            }};

            var network = new vis.Network(container, data, options);

            // Show node info on click
            network.on('click', function(params) {{
                if (params.nodes.length > 0) {{
                    var nodeId   = params.nodes[0];
                    var nodeData = nodes.get(nodeId);
                    var panel    = document.getElementById('info-panel');
                    document.getElementById('node-title').innerText =
                        nodeData.label;
                    document.getElementById('node-details').innerText =
                        nodeData.title || '';
                    panel.style.display = 'block';
                }} else {{
                    document.getElementById('info-panel').style.display =
                        'none';
                }}
            }});

            // Fit network after stabilization
            network.once('stabilizationIterationsDone', function() {{
                network.fit({{
                    animation: {{ duration: 500, easingFunction: 'easeInOutQuad' }}
                }});
            }});
        </script>
    </body>
    </html>
    """

    import streamlit.components.v1 as components
    components.html(html_content, height=560, scrolling=False)

    st.caption(
        "💡 Click nodes to see details | Scroll to zoom | "
        "Drag to pan | Nodes sized by association score"
    )

def render_updates_panel(disease_name: str):
    """Render latest scientific updates for a disease."""
    try:
        r = requests.get(
            f"{API_BASE_URL}/latest-updates",
            params={"disease": disease_name},
            timeout=10
        )
        if r.status_code != 200:
            return

        data     = r.json()
        updates  = data.get("updates", {})
        stats    = data.get("stats", {})
        papers   = updates.get(disease_name, [])

        if not papers:
            st.info(
                f"📡 No recent updates found for {disease_name}. "
                f"The system checks PubMed daily at 06:00 UTC."
            )
            return

        st.markdown(
            f"<div style='background:#0f1b2d;"
            f"border:1px solid #1e3a5f;"
            f"border-radius:10px;padding:14px 18px;margin-bottom:12px;'>"
            f"<div style='color:#60a5fa;font-size:11px;font-weight:700;"
            f"text-transform:uppercase;letter-spacing:1px;'>"
            f"📡 Live Feed</div>"
            f"<div style='color:#e2e8f0;font-size:13px;margin-top:4px;'>"
            f"{len(papers)} recent papers | "
            f"Last check: {stats.get('last_check','Never')[:19] if stats.get('last_check') else 'Pending'}"
            f"</div></div>",
            unsafe_allow_html=True
        )

        for paper in papers[:5]:
            is_new = paper.get("is_new", False)
            new_badge = (
                "<span style='background:#22c55e;color:white;"
                "padding:1px 8px;border-radius:10px;font-size:10px;"
                "font-weight:700;margin-left:8px;'>NEW</span>"
                if is_new else ""
            )
            st.markdown(
                f"<div style='background:#0f172a;"
                f"border-left:3px solid #3b82f6;"
                f"border-radius:0 8px 8px 0;"
                f"padding:10px 14px;margin:6px 0;'>"
                f"<div style='font-size:13px;color:#e2e8f0;"
                f"font-weight:500;'>{paper.get('title','')}"
                f"{new_badge}</div>"
                f"<div style='font-size:11px;color:#64748b;"
                f"margin-top:4px;'>"
                f"📅 {paper.get('year','?')} | "
                f"PubMed ID: {paper.get('pmid','')}</div>"
                f"</div>",
                unsafe_allow_html=True
            )
            if paper.get("url"):
                st.markdown(
                    f"[🔗 Read paper]({paper['url']})",
                    unsafe_allow_html=False
                )

    except Exception as e:
        st.caption(f"Updates unavailable: {str(e)}")

def render_comparison_table(data: dict):
    """Render the hypothesis comparison table."""
    table_rows = []
    for hyp in data["hypotheses"]:
        rank    = int(hyp.get("rank") or 0) or 1
        final   = float(hyp.get("final_score") or 0.0)
        score   = float(hyp.get("confidence_score") or 0.0)
        display = final if final > 0 else score
        drugs   = hyp.get("key_drugs", [])
        drug_risk = "Unknown"
        if drugs:
            for d in data["drugs"]:
                if d["drug_name"].upper() == drugs[0].upper():
                    drug_risk = d.get("risk_level","Unknown")
                    break
        # Causal label
        ca         = hyp.get("causal_analysis") or {}
        causal_lbl = ca.get("causal_label","")
        causal_col = ca.get("causal_color","#64748b")

        medals   = {1:"🥇",2:"🥈",3:"🥉"}
        risk_ems = {"High":"🔴","Medium":"🟡","Low":"🟢","Unknown":"⚪"}
        table_rows.append({
            "rank":rank,"medal":medals.get(rank,f"#{rank}"),
            "title":hyp["title"],
            "proteins":", ".join(hyp.get("key_proteins") or []),
            "drugs":", ".join(hyp.get("key_drugs") or []),
            "final":display,"color":confidence_color(display),
            "risk":drug_risk,"risk_emoji":risk_ems.get(drug_risk,"⚪"),
            "causal_label":causal_lbl,"causal_color":causal_col,
            "hyp_rank":rank
        })

    # Header
    h1,h2,h3,h4,h5,h6,h7,h8,h9 = st.columns(
        [0.5,2.5,1.0,1.0,0.8,1.0,0.8,1.0,1.0]
    )
    for col,lbl in zip([h1,h2,h3,h4,h5,h6,h7,h8,h9],
                       ["Rank","Hypothesis","Proteins",
                        "Drugs","Score","Causal","Risk",
                        "Uncertainty","Decision"]):
        col.markdown(
            f"<div style='color:#64748b;font-size:11px;"
            f"font-weight:700;text-transform:uppercase;"
            f"letter-spacing:1px;'>{lbl}</div>",
            unsafe_allow_html=True
        )
    st.markdown("<hr style='border:none;border-top:1px solid "
                "#1e293b;margin:4px 0;'>", unsafe_allow_html=True)

    for row in table_rows:
        c1,c2,c3,c4,c5,c6,c7,c8,c9 = st.columns(
            [0.5,2.5,1.0,1.0,0.8,1.0,0.8,1.0,1.0]
        )
        with c1:
            st.markdown(
                f"<div style='font-size:22px;text-align:center;"
                f"padding-top:6px;'>{row['medal']}</div>",
                unsafe_allow_html=True)
        with c2:
            st.markdown(
                f"<div style='font-size:13px;color:#e2e8f0;"
                f"padding:6px 0;line-height:1.4;'>"
                f"{row['title']}</div>",
                unsafe_allow_html=True)
        with c3:
            if row["proteins"]:
                st.markdown(" ".join([
                    f"<span style='background:#1e3a5f;color:#60a5fa;"
                    f"padding:2px 8px;border-radius:10px;font-size:11px;"
                    f"font-weight:600;margin:2px;display:inline-block;'>"
                    f"{p}</span>"
                    for p in row["proteins"].split(", ")
                ]), unsafe_allow_html=True)
        with c4:
            if row["drugs"]:
                st.markdown(" ".join([
                    f"<span style='background:#1e3a2f;color:#34d399;"
                    f"padding:2px 8px;border-radius:10px;font-size:11px;"
                    f"font-weight:600;margin:2px;display:inline-block;'>"
                    f"{d}</span>"
                    for d in row["drugs"].split(", ")
                ]), unsafe_allow_html=True)
            else:
                st.markdown(
                    "<span style='color:#475569;font-size:11px;'>—</span>",
                    unsafe_allow_html=True)
        with c5:
            pct  = row["final"]; color = row["color"]
            bar_w= int(pct*60)
            st.markdown(
                f"<div style='padding-top:4px;'>"
                f"<div style='color:{color};font-weight:700;"
                f"font-size:15px;'>{pct:.0%}</div>"
                f"<div style='background:#1e293b;border-radius:4px;"
                f"height:4px;width:60px;margin-top:2px;'>"
                f"<div style='background:{color};height:4px;"
                f"border-radius:4px;width:{bar_w}px;'>"
                f"</div></div></div>",
                unsafe_allow_html=True)
        with c6:
            if row["causal_label"]:
                cc = row["causal_color"]
                ca_em = ("✅" if row["causal_label"] == "Likely Causal"
                         else "⚠️" if row["causal_label"] == "Possibly Causal"
                         else "ℹ️")
                st.markdown(
                    f"<div style='background:{cc}22;color:{cc};"
                    f"padding:4px 8px;border-radius:8px;font-size:11px;"
                    f"font-weight:600;text-align:center;margin-top:4px;'>"
                    f"{ca_em} {row['causal_label']}</div>",
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    "<span style='color:#475569;font-size:11px;'>—</span>",
                    unsafe_allow_html=True)
        with c7:
            rc = {"High":("#ef4444","#2d0a0a"),
                  "Medium":("#f59e0b","#2d1f02"),
                  "Low":("#22c55e","#052e16"),
                  "Unknown":("#64748b","#1a1f2e")}
            fg,bg = rc.get(row["risk"],rc["Unknown"])
            st.markdown(
                f"<div style='background:{bg};color:{fg};"
                f"padding:4px 10px;border-radius:8px;font-size:12px;"
                f"font-weight:600;text-align:center;margin-top:4px;'>"
                f"{row['risk_emoji']} {row['risk']}</div>",
                unsafe_allow_html=True)

        with c8:
            unc = {}
            for hyp_data in data["hypotheses"]:
                if hyp_data.get("rank") == row["rank"]:
                    unc = hyp_data.get("uncertainty") or {}
                    break
            if unc:
                u_label = unc.get("uncertainty_label","")
                u_color = unc.get("uncertainty_color","#64748b")
                u_emoji = {"Low":"✅","Medium":"⚠️",
                           "High":"🔶","Very High":"❌"
                           }.get(u_label,"❓")
                st.markdown(
                    f"<div style='background:{u_color}22;"
                    f"color:{u_color};padding:4px 8px;"
                    f"border-radius:8px;font-size:11px;"
                    f"font-weight:600;text-align:center;"
                    f"margin-top:4px;'>"
                    f"{u_emoji} {u_label}</div>",
                    unsafe_allow_html=True
                )

        with c9:
            gng = {}
            for hyp_data in data["hypotheses"]:
                if hyp_data.get("rank") == row["rank"]:
                    gng = hyp_data.get("go_no_go") or {}
                    break
            if gng:
                g_dec   = gng.get("decision","")
                g_color = gng.get("decision_color","#64748b")
                g_emoji = gng.get("decision_emoji","❓")
                st.markdown(
                    f"<div style='background:{g_color}22;"
                    f"color:{g_color};border:1px solid {g_color}55;"
                    f"padding:4px 8px;border-radius:8px;"
                    f"font-size:12px;font-weight:800;"
                    f"text-align:center;margin-top:4px;"
                    f"letter-spacing:1px;'>"
                    f"{g_emoji} {g_dec}</div>",
                    unsafe_allow_html=True
                )
        st.markdown("<hr style='border:none;border-top:1px solid "
                    "#0f172a;margin:2px 0;'>", unsafe_allow_html=True)

    st.caption("💡 Score = 0.4×protein + 0.3×drug_phase + "
               "0.2×papers − 0.1×fda_risk")


# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧬 AI Scientist")
    st.markdown("*V3 Decision Intelligence Platform*")
    st.divider()
    st.markdown("### ⚙️ Settings")
    max_targets = st.slider("Protein Targets",   3, 10, 5)
    max_drugs   = st.slider("Drugs per Protein", 1,  5, 3)
    max_papers  = st.slider("Research Papers",   3, 10, 5)
    st.divider()
    st.markdown("### 📡 Data Sources")
    st.markdown("""
    - 🧬 **OpenTargets** — Proteins
    - 💊 **FDA FAERS** — Risk signals
    - 📚 **PubMed** — Literature
    - 📖 **Semantic Scholar** — Summaries
    - 🤖 **GPT-4o-mini** — Hypotheses
    - 🔬 **AlphaFold** — Structure scores
    """)
    st.divider()
    st.caption("For exploratory research only. Not for clinical use.")
    st.divider()
    st.markdown("### 🔑 API Access")
    st.markdown("""
    Use the REST API directly:
```
    POST /api/v1/generate-hypothesis
    POST /api/v1/rank-drugs
    POST /api/v1/analyze-risk
    GET  /api/v1/decision-summary/{disease}
```
    """)
    st.markdown(
        f"[📖 API Docs]({API_BASE_URL}/docs) | "
        f"[🔑 Get Keys]({API_BASE_URL}/api/v1/keys)"
    )


# ── Header ────────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center; padding:20px 0 10px 0;'>
    <h1 style='font-size:2.8em; font-weight:800;
               background:linear-gradient(90deg,#60a5fa,#a78bfa,#34d399);
               -webkit-background-clip:text;
               -webkit-text-fill-color:transparent;'>
        🧬 AI Scientist
    </h1>
    <p style='color:#94a3b8; font-size:1.1em; margin-top:-10px;'>
        V3 Decision Intelligence Platform for Drug Discovery
    </p>
</div>
""", unsafe_allow_html=True)

# ── Search Mode ───────────────────────────────────────────────
examples = get_example_diseases()

search_mode = st.radio(
    "Mode", ["🔬 Single Disease", "🔀 Multi-Disease Comparison"],
    horizontal=True, label_visibility="collapsed"
)

if search_mode == "🔬 Single Disease":
    st.markdown("### 🔍 Enter a Disease to Analyze")
    col_input, col_button = st.columns([4, 1])
    with col_input:
        disease_input = st.text_input(
            "Disease",
            placeholder="e.g. Alzheimer disease, breast cancer...",
            label_visibility="collapsed"
        )
    with col_button:
        analyze_clicked = st.button("🔬 Analyze", type="primary",
                                    use_container_width=True)
    st.markdown("**Quick select:**")
    q_cols = st.columns(len(examples[:4]))
    for i, d in enumerate(examples[:4]):
        with q_cols[i]:
            if st.button(d, key=f"qs_{i}", use_container_width=True):
                disease_input   = d
                analyze_clicked = True
    multi_diseases  = []
    compare_clicked = False

else:
    st.markdown("### 🔀 Multi-Disease Comparison")
    st.caption("Select 2-4 diseases to compare shared proteins, "
               "drugs, and repurposing opportunities")
    all_diseases = examples or [
        "Alzheimer disease", "Parkinson disease",
        "breast cancer", "type 2 diabetes",
        "rheumatoid arthritis", "lung cancer"
    ]
    multi_diseases = st.multiselect(
        "Select diseases to compare (2-4):",
        options=all_diseases,
        default=all_diseases[:2],
        max_selections=4
    )
    compare_clicked = st.button(
        f"🔀 Compare {len(multi_diseases)} Diseases",
        type="primary",
        disabled=(len(multi_diseases) < 2)
    )
    disease_input   = ""
    analyze_clicked = False

st.divider()


# ════════════════════════════════════════════════════════════
# MULTI-DISEASE COMPARISON
# ════════════════════════════════════════════════════════════
if compare_clicked and len(multi_diseases) >= 2:

    with st.spinner(
        f"🔀 Comparing {len(multi_diseases)} diseases — "
        f"~{len(multi_diseases)*40}s..."
    ):
        pb   = st.progress(0)
        stat = st.empty()
        stat.markdown(
            f"🚀 Running parallel pipelines for: "
            f"**{', '.join(multi_diseases)}**"
        )
        pb.progress(20)
        cmp_result = call_compare_api(
            multi_diseases, max_targets, max_papers, max_drugs
        )
        pb.progress(100); pb.empty(); stat.empty()

    if "error" in cmp_result:
        st.error(f"❌ {cmp_result['error']}")
        st.stop()

    cmp     = cmp_result.get("comparison", {})
    individ = cmp_result.get("individual", {})
    diseases= cmp.get("diseases_analyzed", [])

    st.success(
        f"✅ Compared **{len(diseases)} diseases** in "
        f"{cmp_result.get('elapsed','?')}s — "
        f"{cmp.get('total_shared_proteins',0)} shared proteins, "
        f"{cmp.get('total_shared_drugs',0)} shared drugs"
    )

    sm1,sm2,sm3,sm4 = st.columns(4)
    sm1.metric("🔬 Diseases",        len(diseases))
    sm2.metric("🧬 Shared Proteins", cmp.get("total_shared_proteins",0))
    sm3.metric("💊 Shared Drugs",    cmp.get("total_shared_drugs",0))
    sm4.metric("🔁 Repurposing",
               len(cmp.get("repurposing_opportunities",[])))

    repurp = cmp.get("repurposing_opportunities", [])
    if repurp:
        st.markdown("### 💡 Drug Repurposing Opportunities")
        for opp in repurp:
            st.markdown(
                f"<div style='background:#0f1f0f;border:1px solid #166534;"
                f"border-radius:8px;padding:12px 16px;margin:6px 0;'>"
                f"<span style='color:#4ade80;font-size:13px;'>"
                f"🔁 {opp}</span></div>",
                unsafe_allow_html=True
            )

    st.divider()
    st.markdown("### 💊 Drug Comparison Across Diseases")
    st.caption("Drugs ranked by cross-disease appearance and average score")

    drug_rows  = cmp.get("drug_comparison", [])
    n_diseases = len(diseases)

    if drug_rows:
        header_cols = st.columns([2,1.5]+[1.5]*n_diseases+[1,1])
        for col,lbl in zip(
            header_cols,
            ["Drug","Target"]+[d[:12]+"..." for d in diseases]+["Avg","Overlap"]
        ):
            col.markdown(
                f"<div style='color:#64748b;font-size:11px;font-weight:700;"
                f"text-transform:uppercase;letter-spacing:1px;'>{lbl}</div>",
                unsafe_allow_html=True
            )
        st.markdown("<hr style='border:none;border-top:1px solid "
                    "#1e293b;margin:4px 0;'>", unsafe_allow_html=True)

        for row in drug_rows[:10]:
            row_cols = st.columns([2,1.5]+[1.5]*n_diseases+[1,1])
            appears  = row.get("appears_in",1)
            badge_col= "#22c55e" if appears >= 2 else "#60a5fa"

            with row_cols[0]:
                st.markdown(
                    f"<div style='padding:4px 0;'>"
                    f"<div style='color:#e2e8f0;font-weight:600;"
                    f"font-size:13px;'>{row['drug_name']}</div>"
                    f"<span style='background:{badge_col}22;"
                    f"color:{badge_col};padding:1px 6px;"
                    f"border-radius:8px;font-size:10px;'>"
                    f"{'🔁 Multi-disease' if appears>=2 else '1 disease'}"
                    f"</span></div>",
                    unsafe_allow_html=True)
            with row_cols[1]:
                st.markdown(
                    f"<div style='color:#a78bfa;font-size:12px;"
                    f"padding-top:4px;font-weight:600;'>"
                    f"{row.get('target_protein','—')}</div>",
                    unsafe_allow_html=True)

            disease_entries = {
                e["disease_name"]: e
                for e in row.get("diseases",[])
            }
            for i, d in enumerate(diseases):
                with row_cols[2+i]:
                    entry = disease_entries.get(d)
                    if entry and entry.get("final_score",0) > 0:
                        sc     = entry["final_score"]
                        sc_col = confidence_color(sc)
                        risk   = entry.get("risk_level","Unknown")
                        r_em   = {"High":"🔴","Medium":"🟡",
                                  "Low":"🟢","Unknown":"⚪"}.get(risk,"⚪")
                        st.markdown(
                            f"<div style='text-align:center;'>"
                            f"<div style='color:{sc_col};font-weight:700;"
                            f"font-size:14px;'>{sc:.0%}</div>"
                            f"<div style='font-size:10px;color:#64748b;'>"
                            f"{r_em} {risk}</div></div>",
                            unsafe_allow_html=True)
                    else:
                        st.markdown(
                            "<div style='text-align:center;color:#374151;"
                            "font-size:18px;padding-top:4px;'>—</div>",
                            unsafe_allow_html=True)

            with row_cols[-2]:
                avg = row.get("avg_score",0)
                if avg > 0:
                    ac = confidence_color(avg)
                    st.markdown(
                        f"<div style='text-align:center;color:{ac};"
                        f"font-weight:700;font-size:14px;"
                        f"padding-top:4px;'>{avg:.0%}</div>",
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        "<div style='text-align:center;"
                        "color:#374151;'>—</div>",
                        unsafe_allow_html=True)

            with row_cols[-1]:
                ov     = row.get("overlap_score",0)
                ov_col = confidence_color(ov)
                st.markdown(
                    f"<div style='text-align:center;color:{ov_col};"
                    f"font-weight:700;font-size:14px;"
                    f"padding-top:4px;'>{ov:.0%}</div>",
                    unsafe_allow_html=True)

            st.markdown("<hr style='border:none;border-top:1px solid "
                        "#0f172a;margin:2px 0;'>", unsafe_allow_html=True)

    shared = cmp.get("shared_proteins",[])
    if shared:
        st.divider()
        st.markdown("### 🧬 Shared Protein Targets")
        for sp in shared:
            appears   = sp.get("appears_in",1)
            avg_assoc = sp.get("avg_association",0)
            sp_color  = confidence_color(avg_assoc)
            d_list    = ", ".join(sp.get("diseases",[]))
            col1,col2,col3 = st.columns([1,4,1])
            with col1:
                st.markdown(
                    f"<div style='background:#1e3a5f;color:#60a5fa;"
                    f"padding:10px;border-radius:8px;text-align:center;"
                    f"font-weight:700;font-size:18px;'>"
                    f"{sp['gene_symbol']}</div>",
                    unsafe_allow_html=True)
            with col2:
                st.markdown(f"**{sp.get('protein_name','')}**")
                st.caption(f"Found in: {d_list}")
                st.markdown(
                    f"<span style='background:#22c55e22;color:#22c55e;"
                    f"padding:2px 10px;border-radius:12px;font-size:11px;"
                    f"font-weight:600;'>🔁 Appears in {appears} diseases"
                    f"</span>",
                    unsafe_allow_html=True)
            with col3:
                st.markdown(
                    f"<div style='text-align:center;'>"
                    f"<div style='color:{sp_color};font-size:20px;"
                    f"font-weight:700;'>{avg_assoc:.2f}</div>"
                    f"<div style='color:#64748b;font-size:10px;'>"
                    f"Avg Assoc.</div></div>",
                    unsafe_allow_html=True)
            st.divider()

    if individ:
        st.markdown("### 🎯 Individual Disease Recommendations")
        ind_cols = st.columns(len(individ))
        for i,(dname,ddata) in enumerate(individ.items()):
            with ind_cols[i]:
                ds       = ddata.get("decision_summary") or {}
                drug     = ds.get("recommended_drug","—")
                prot     = ds.get("target_protein","—")
                conf     = float(ds.get("confidence_score") or 0)
                risk     = ds.get("risk_level","Unknown")
                risk_em  = {"High":"🔴","Medium":"🟡",
                            "Low":"🟢","Unknown":"⚪"}.get(risk,"⚪")
                conf_col = confidence_color(conf)
                st.markdown(
                    f"<div style='background:#0f1b2d;"
                    f"border:1px solid #2d4a7a;"
                    f"border-radius:10px;padding:16px;'>"
                    f"<div style='font-size:11px;color:#60a5fa;"
                    f"text-transform:uppercase;letter-spacing:1px;"
                    f"margin-bottom:8px;font-weight:700;'>"
                    f"🎯 {dname}</div>"
                    f"<div style='color:#60a5fa;font-size:16px;"
                    f"font-weight:700;margin-bottom:4px;'>💊 {drug}</div>"
                    f"<div style='color:#a78bfa;font-size:13px;"
                    f"margin-bottom:8px;'>🧬 {prot}</div>"
                    f"<div style='color:{conf_col};font-weight:700;"
                    f"font-size:18px;'>{conf:.0%}</div>"
                    f"<div style='color:#64748b;font-size:11px;'>"
                    f"confidence</div>"
                    f"<div style='margin-top:8px;'>"
                    f"<span style='font-size:13px;'>"
                    f"{risk_em} {risk} Risk</span></div>"
                    f"</div>",
                    unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# SINGLE DISEASE ANALYSIS
# ════════════════════════════════════════════════════════════
elif analyze_clicked and disease_input.strip():

    with st.spinner(f"🔬 Analyzing **{disease_input}** — ~60 seconds..."):
        pb   = st.progress(0)
        stat = st.empty()
        stat.markdown("📡 **Stage 1/4** — Fetching protein targets...")
        pb.progress(10); time.sleep(0.3)
        stat.markdown("💊 **Stage 2/4** — Mapping drugs + FDA signals...")
        pb.progress(25)
        result = call_api(disease_input.strip(), max_targets,
                          max_papers, max_drugs)
        pb.progress(75)
        stat.markdown("📚 **Stage 3/4** — Retrieving papers...")
        time.sleep(0.2)
        pb.progress(90)
        stat.markdown("🤖 **Stage 4/4** — Generating hypotheses...")
        time.sleep(0.2)
        pb.progress(100); stat.empty(); pb.empty()

    if "error" in result:
        st.error(f"❌ {result['error']}")
        st.stop()
    if not result.get("success"):
        st.error(f"❌ {result.get('message','Unknown error')}")
        st.stop()

    data = result["data"]
    st.success(
        f"✅ Analysis complete for **{data['disease_name']}** "
        f"— {result['message']}"
    )

    # Metrics
    m1,m2,m3,m4 = st.columns(4)
    m1.metric("🧬 Proteins",   len(data["protein_targets"]))
    m2.metric("💊 Drugs",      len(data["drugs"]))
    m3.metric("📚 Papers",     len(data["papers"]))
    m4.metric("💡 Hypotheses", len(data["hypotheses"]))

    # Evidence banner
    ev = data.get("evidence_strength") or {}
    if ev:
        ev_score = float(ev.get("evidence_score") or 0)
        ev_label = str(ev.get("evidence_label") or "Unknown")
        ev_color = str(ev.get("evidence_color") or "yellow")
        ev_bd    = str(ev.get("evidence_breakdown") or "")
        bg_map   = {"green":("#052e16","#22c55e"),
                    "yellow":("#1c1a02","#eab308"),
                    "red":("#2d0a0a","#ef4444")}
        em_map   = {"green":"🟢","yellow":"🟡","red":"🔴"}
        bg,fg    = bg_map.get(ev_color, bg_map["yellow"])
        ev_em    = em_map.get(ev_color,"🟡")
        st.markdown(
            f"<div style='background:{bg};border:1px solid {fg}55;"
            f"border-radius:10px;padding:14px 20px;margin:10px 0;'>"
            f"<div style='display:flex;justify-content:space-between;"
            f"align-items:center;'>"
            f"<div><div style='font-size:11px;color:#94a3b8;"
            f"text-transform:uppercase;letter-spacing:1px;'>"
            f"Evidence Strength</div>"
            f"<div style='margin-top:2px;'>"
            f"<span style='font-size:20px;font-weight:800;color:{fg};'>"
            f"{ev_em} {ev_label}</span>"
            f"<span style='color:#64748b;font-size:13px;margin-left:10px;'>"
            f"Score: {ev_score:.2f}/1.00</span></div></div>"
            f"<div style='color:#64748b;font-size:12px;text-align:right;'>"
            f"📄 {ev.get('total_papers',0)} papers | "
            f"⭐ {ev.get('high_citation_papers',0)} cited | "
            f"🕐 {ev.get('recent_papers',0)} recent</div></div>"
            f"<div style='margin-top:6px;font-size:11px;color:#475569;'>"
            f"📐 {ev_bd}</div></div>",
            unsafe_allow_html=True
        )

    # ── Analysis Uncertainty Banner ───────────────────────────
    au = data.get("analysis_uncertainty") or {}
    if au:
        au_score = float(au.get("uncertainty_score") or 0)
        au_label = str(au.get("uncertainty_label") or "Unknown")
        au_color = str(au.get("uncertainty_color") or "#64748b")
        au_reason= str(au.get("uncertainty_reason") or "")
        au_emoji = {"Low":"✅","Medium":"⚠️",
                    "High":"🔶","Very High":"❌"}.get(au_label,"❓")

        # Flags row
        flag_items = []
        flag_checks = [
            ("low_paper_count",    "Low Paper Count"),
            ("weak_protein_assoc", "Weak Protein Assoc."),
            ("high_fda_risk",      "High FDA Risk"),
            ("no_causal_evidence", "No Causal Evidence"),
            ("limited_drug_data",  "Limited Drug Data"),
        ]
        for key, lbl in flag_checks:
            if au.get(key):
                flag_items.append(
                    f"<span style='background:#2d1a1a;"
                    f"color:#f87171;padding:2px 8px;"
                    f"border-radius:8px;font-size:11px;"
                    f"margin:2px;display:inline-block;'>"
                    f"⚠️ {lbl}</span>"
                )

        flags_html = "".join(flag_items) if flag_items else (
            "<span style='color:#22c55e;font-size:11px;'>"
            "✅ No critical uncertainty flags</span>"
        )

        st.markdown(
            f"<div style='background:{au_color}0d;"
            f"border:1px solid {au_color}44;"
            f"border-radius:10px;padding:14px 20px;margin:8px 0;'>"
            f"<div style='display:flex;justify-content:space-between;"
            f"align-items:center;margin-bottom:8px;'>"
            f"<div>"
            f"<span style='font-size:11px;color:#94a3b8;"
            f"text-transform:uppercase;letter-spacing:1px;'>"
            f"Analysis Reliability</span>"
            f"<div style='margin-top:3px;'>"
            f"<span style='font-size:18px;font-weight:800;"
            f"color:{au_color};'>{au_emoji} {au_label} Uncertainty</span>"
            f"<span style='color:#64748b;font-size:13px;"
            f"margin-left:10px;'>Score: {au_score:.2f}/1.00</span>"
            f"</div></div></div>"
            f"<div style='font-size:12px;color:#94a3b8;"
            f"margin-bottom:8px;'>{au_reason}</div>"
            f"<div>{flags_html}</div>"
            f"</div>",
            unsafe_allow_html=True
        )

    st.divider()

    # ── Decision Summary Panel ────────────────────────────────
    ds = data.get("decision_summary") or {}
    if ds and ds.get("recommended_drug"):
        conf       = float(ds.get("confidence_score") or 0)
        risk       = str(ds.get("risk_level") or "Unknown")
        drug       = str(ds.get("recommended_drug") or "—")
        protein    = str(ds.get("target_protein") or "—")
        pathway    = str(ds.get("target_pathway") or "—")
        conf_label = str(ds.get("confidence_label") or "")
        reasoning  = str(ds.get("reasoning_summary") or "")
        action     = str(ds.get("suggested_action") or "")
        evidence_b = str(ds.get("evidence_basis") or "")
        best_hyp   = str(ds.get("best_hypothesis") or "")
        conf_color = confidence_color(conf)
        conf_emoji = confidence_emoji(conf)
        risk_emoji = {"High":"🔴","Medium":"🟡",
                      "Low":"🟢","Unknown":"⚪"}.get(risk,"⚪")
        risk_col   = {"High":"#ef4444","Medium":"#f59e0b",
                      "Low":"#22c55e","Unknown":"#64748b"}.get(risk,"#64748b")

        st.markdown(
            "<div style='font-size:11px;color:#94a3b8;"
            "text-transform:uppercase;letter-spacing:2px;"
            "font-weight:700;margin-bottom:8px;'>"
            "🎯 V3 DECISION INTELLIGENCE</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div style='background:linear-gradient(135deg,#0f1b2d,#1a2744);"
            f"border:1px solid #2d4a7a;border-radius:12px;"
            f"padding:16px 20px;margin-bottom:12px;'>"
            f"<div style='font-size:11px;color:#60a5fa;"
            f"text-transform:uppercase;letter-spacing:2px;"
            f"font-weight:700;margin-bottom:6px;'>"
            f"✅ Best Recommendation for {data['disease_name']}</div>"
            f"<div style='font-size:15px;color:#e2e8f0;"
            f"font-weight:500;line-height:1.5;'>{best_hyp}</div>"
            f"</div>",
            unsafe_allow_html=True
        )

        k1,k2,k3,k4 = st.columns(4)
        with k1:
            st.markdown(
                f"<div style='background:#0a1628;border:1px solid #1e3a5f;"
                f"border-radius:10px;padding:16px;text-align:center;'>"
                f"<div style='font-size:11px;color:#60a5fa;"
                f"text-transform:uppercase;letter-spacing:1px;"
                f"margin-bottom:8px;'>💊 Recommended Drug</div>"
                f"<div style='font-size:22px;font-weight:800;"
                f"color:#60a5fa;'>{drug}</div></div>",
                unsafe_allow_html=True)
        with k2:
            st.markdown(
                f"<div style='background:#0a1628;border:1px solid #2d1f5e;"
                f"border-radius:10px;padding:16px;text-align:center;'>"
                f"<div style='font-size:11px;color:#a78bfa;"
                f"text-transform:uppercase;letter-spacing:1px;"
                f"margin-bottom:8px;'>🧬 Target Protein</div>"
                f"<div style='font-size:22px;font-weight:800;"
                f"color:#a78bfa;'>{protein}</div></div>",
                unsafe_allow_html=True)
        with k3:
            st.markdown(
                f"<div style='background:#0a1628;border:1px solid #1e3a1e;"
                f"border-radius:10px;padding:16px;text-align:center;'>"
                f"<div style='font-size:11px;color:{conf_color};"
                f"text-transform:uppercase;letter-spacing:1px;"
                f"margin-bottom:8px;'>📊 Confidence</div>"
                f"<div style='font-size:22px;font-weight:800;"
                f"color:{conf_color};'>{conf_emoji} {conf:.0%}</div>"
                f"<div style='font-size:11px;color:#64748b;"
                f"margin-top:4px;'>{conf_label}</div></div>",
                unsafe_allow_html=True)
        with k4:
            st.markdown(
                f"<div style='background:#0a1628;border:1px solid #3a2000;"
                f"border-radius:10px;padding:16px;text-align:center;'>"
                f"<div style='font-size:11px;color:{risk_col};"
                f"text-transform:uppercase;letter-spacing:1px;"
                f"margin-bottom:8px;'>⚠️ Risk Level</div>"
                f"<div style='font-size:22px;font-weight:800;"
                f"color:{risk_col};'>{risk_emoji} {risk}</div></div>",
                unsafe_allow_html=True)

        # ── GO/NO-GO Badge ────────────────────────────────────
        gng = ds.get("go_no_go") or {}
        if gng:
            render_go_no_go_badge(gng, size="large")
        st.markdown("<div style='margin-top:8px;'></div>",
                    unsafe_allow_html=True)

        st.markdown("<div style='margin-top:10px;'></div>",
                    unsafe_allow_html=True)
        st.markdown(
            f"<span style='background:#1e3a5f;color:#93c5fd;"
            f"padding:5px 14px;border-radius:20px;"
            f"font-size:12px;font-weight:600;'>"
            f"🔬 Pathway: {pathway}</span>",
            unsafe_allow_html=True)
        st.markdown("<div style='margin-top:10px;'></div>",
                    unsafe_allow_html=True)
        st.markdown(
            f"<div style='background:#070e1a;border-radius:8px;"
            f"padding:14px;margin-bottom:10px;"
            f"border-left:3px solid #3b82f6;'>"
            f"<div style='font-size:11px;color:#60a5fa;font-weight:700;"
            f"text-transform:uppercase;letter-spacing:1px;"
            f"margin-bottom:6px;'>🧠 Scientific Reasoning</div>"
            f"<div style='font-size:13px;color:#cbd5e1;"
            f"line-height:1.7;'>{reasoning}</div></div>",
            unsafe_allow_html=True)
        st.markdown(
            f"<div style='background:#0f1f0f;border:1px solid #166534;"
            f"border-radius:10px;padding:14px;margin-bottom:8px;'>"
            f"<div style='font-size:11px;color:#4ade80;font-weight:700;"
            f"text-transform:uppercase;letter-spacing:1px;"
            f"margin-bottom:6px;'>🚀 Suggested Next Action</div>"
            f"<div style='font-size:14px;color:#bbf7d0;"
            f"line-height:1.7;'>{action}</div></div>",
            unsafe_allow_html=True)
        st.markdown(
            f"<div style='background:#111827;border-radius:8px;"
            f"padding:10px 14px;margin-bottom:4px;'>"
            f"<span style='font-size:11px;color:#475569;'>"
            f"📐 Evidence basis: {evidence_b}</span></div>",
            unsafe_allow_html=True)
        st.divider()

    # ── Tabs ──────────────────────────────────────────────────
    tab1,tab2,tab3,tab4,tab5,tab6,tab7 = st.tabs([
        "💡 Hypotheses",
        "🧬 Proteins & Evidence",
        "💊 Drugs",
        "⚠️ Risk Analysis",
        "🕸️ Network",
        "📡 Live Updates",
        "📄 Literature Review"
    ])

    # ── TAB 1: HYPOTHESES ────────────────────────────────────
    with tab1:
        # ── Decision Dashboard ────────────────────────────────
        st.markdown("### 🎯 Decision Dashboard")
        dash_cols = st.columns(len(data["hypotheses"]))
        for i, hyp in enumerate(data["hypotheses"]):
            with dash_cols[i]:
                rank   = int(hyp.get("rank",i+1))
                final  = float(hyp.get("final_score",0))
                gng    = hyp.get("go_no_go") or {}
                tti    = hyp.get("time_to_impact") or {}
                fp     = hyp.get("failure_prediction") or {}
                medals = {1:"🥇",2:"🥈",3:"🥉"}
                medal  = medals.get(rank,f"#{rank}")
                g_dec  = gng.get("decision","")
                g_col  = gng.get("decision_color","#64748b")
                g_em   = gng.get("decision_emoji","❓")
                sp_col = confidence_color(final)

                st.markdown(
                    f"<div style='background:#0f172a;"
                    f"border:1px solid #1e293b;"
                    f"border-radius:10px;padding:16px;"
                    f"text-align:center;'>"
                    f"<div style='font-size:28px;'>{medal}</div>"
                    f"<div style='color:{sp_col};font-weight:800;"
                    f"font-size:24px;margin:4px 0;'>{final:.0%}</div>"
                    f"<div style='color:{g_col};font-weight:700;"
                    f"font-size:16px;margin-bottom:8px;'>"
                    f"{g_em} {g_dec}</div>"
                    f"<div style='color:#94a3b8;font-size:11px;"
                    f"margin-bottom:6px;'>"
                    f"{', '.join(hyp.get('key_drugs',[]) or ['—'])}</div>"
                    f"<div style='background:{g_col}22;border-radius:6px;"
                    f"padding:4px;font-size:11px;color:{g_col};'>"
                    f"⏱️ {tti.get('years_range','?')} | "
                    f"🎯 {fp.get('success_probability',0):.0%} success"
                    f"</div></div>",
                    unsafe_allow_html=True
                )

        st.divider()
        st.markdown("### 📊 Hypothesis Comparison")
        render_comparison_table(data)
        st.divider()
        st.markdown("### 🔬 Detailed Analysis")
        for hyp in data["hypotheses"]:
            render_hypothesis_card(hyp, data, expanded=(hyp.get("rank")==1))

    # ── TAB 2: PROTEINS & EVIDENCE ───────────────────────────
    with tab2:
        st.markdown("### 🧬 Protein Targets")
        st.caption("OpenTargets association scores + AlphaFold pLDDT")
        for target in data["protein_targets"]:
            assoc  = float(target.get("association_score") or 0)
            plddt  = float(target.get("alphafold_plddt")   or 0)
            af_lbl = target.get("alphafold_label","Est.")
            af_col = target.get("alphafold_color","#64748b")
            a_col  = confidence_color(assoc)
            col1,col2,col3,col4 = st.columns([1,3,1,1])
            with col1:
                st.markdown(
                    f"<div style='background:#1e3a5f;color:#60a5fa;"
                    f"padding:10px;border-radius:8px;text-align:center;"
                    f"font-weight:700;font-size:18px;'>"
                    f"{target['gene_symbol']}</div>",
                    unsafe_allow_html=True)
            with col2:
                st.markdown(f"**{target['protein_name']}**")
                st.caption(target["function_description"][:150]+"...")
            with col3:
                st.markdown(
                    f"<div style='text-align:center;'>"
                    f"<div style='color:{a_col};font-size:20px;"
                    f"font-weight:700;'>{assoc:.2f}</div>"
                    f"<div style='color:#64748b;font-size:10px;'>"
                    f"Disease Assoc.</div></div>",
                    unsafe_allow_html=True)
            with col4:
                st.markdown(
                    f"<div style='text-align:center;background:#0f172a;"
                    f"border-radius:8px;padding:8px;'>"
                    f"<div style='color:{af_col};font-size:18px;"
                    f"font-weight:700;'>{plddt:.2f}</div>"
                    f"<div style='color:{af_col};font-size:10px;"
                    f"font-weight:600;'>{af_lbl}</div>"
                    f"<div style='color:#475569;font-size:9px;'>"
                    f"AlphaFold pLDDT</div></div>",
                    unsafe_allow_html=True)
            st.divider()

        st.markdown("### 📚 Research Papers")
        for paper in data["papers"]:
            src_col = "#3b82f6" if paper["source"]=="PubMed" else "#8b5cf6"
            col1,col2 = st.columns([5,1])
            with col1:
                st.markdown(f"**{paper['title']}**")
                s = paper.get("summary","")
                a = paper.get("abstract","")
                if s and s != "No summary available":
                    st.caption(s[:200])
                elif a and a != "No abstract available":
                    st.caption(a[:200]+"...")
            with col2:
                st.markdown(
                    f"<div style='text-align:center;'>"
                    f"<span style='background:{src_col}22;color:{src_col};"
                    f"padding:3px 8px;border-radius:10px;font-size:11px;'>"
                    f"{paper['source']}</span><br><br>"
                    f"<span style='color:#94a3b8;font-size:12px;'>"
                    f"{paper.get('year') or 'N/A'}</span></div>",
                    unsafe_allow_html=True)
                if paper.get("url"):
                    st.markdown(f"[🔗 View]({paper['url']})")
            st.divider()

    # ── TAB 3: DRUGS ─────────────────────────────────────────
    with tab3:
        st.markdown("### 💊 Drug-Protein Associations")
        for drug in data["drugs"]:
            phase    = drug.get("clinical_phase") or "N/A"
            fda_data = drug.get("fda_adverse_events") or []
            risk     = drug.get("risk_level","Unknown")
            risk_desc= drug.get("risk_description","")
            rs = {"High":("#2d0a0a","#ef4444","🔴"),
                  "Medium":("#2d1f02","#f59e0b","🟡"),
                  "Low":("#052e16","#22c55e","🟢"),
                  "Unknown":("#1a1f2e","#64748b","⚪")}
            r_bg,r_fg,r_em = rs.get(risk,rs["Unknown"])
            col1,col2,col3,col4,col5 = st.columns([2,2.5,2,2,2])
            with col1:
                st.markdown(f"**💊 {drug['drug_name']}**")
                st.caption(f"Type: {drug['drug_type']}")
                st.markdown(
                    f"<span style='background:#134e3a;color:#34d399;"
                    f"padding:3px 10px;border-radius:12px;font-size:12px;'>"
                    f"Phase {phase}</span>",
                    unsafe_allow_html=True)
            with col2:
                st.markdown(f"**Target:** `{drug['target_gene']}`")
                st.caption(f"Mechanism: {drug['mechanism'][:100]}")
            with col3:
                if fda_data:
                    top = fda_data[0]
                    st.markdown("**⚠️ Top FDA Signal**")
                    st.markdown(
                        f"<div style='background:#2d1b1b;color:#f87171;"
                        f"padding:8px 12px;border-radius:8px;font-size:13px;'>"
                        f"🚨 {top['reaction']}<br>"
                        f"<span style='color:#94a3b8;'>"
                        f"{top['count']:,} reports</span></div>",
                        unsafe_allow_html=True)
                else:
                    st.caption("No FDA signals found")
            with col4:
                st.markdown("**🛡️ Risk Level**")
                st.markdown(
                    f"<div style='background:{r_bg};border:1px solid {r_fg}55;"
                    f"border-radius:8px;padding:8px 12px;'>"
                    f"<div style='color:{r_fg};font-weight:700;"
                    f"font-size:15px;'>{r_em} {risk}</div>"
                    f"<div style='color:#94a3b8;font-size:11px;"
                    f"margin-top:4px;'>{risk_desc[:80]}...</div></div>",
                    unsafe_allow_html=True)
            with col5:
                comp = drug.get("competition_intel") or {}
                if comp:
                    st.markdown("**🏁 Competition**")
                    render_competition_badge(drug, compact=True)
                    n_sim = comp.get("num_similar_drugs",0)
                    opp   = comp.get("market_opportunity","")
                    opp_c = {"Strong":"#22c55e","Moderate":"#f59e0b",
                             "Crowded":"#ef4444"}.get(opp,"#64748b")
                    st.markdown(
                        f"<div style='font-size:11px;color:#64748b;"
                        f"margin-top:4px;'>{n_sim} similar drugs</div>"
                        f"<div style='color:{opp_c};font-size:11px;"
                        f"font-weight:600;'>{opp} opportunity</div>",
                        unsafe_allow_html=True
                    )
            st.divider()

    # ── TAB 4: RISK ANALYSIS ─────────────────────────────────
    with tab4:
        st.markdown("### ⚠️ FDA Risk Intelligence Summary")
        risk_counts = {"High":0,"Medium":0,"Low":0,"Unknown":0}
        for drug in data["drugs"]:
            lvl = drug.get("risk_level","Unknown")
            risk_counts[lvl] = risk_counts.get(lvl,0)+1
        r1,r2,r3,r4 = st.columns(4)
        r1.metric("🔴 High Risk",   risk_counts["High"])
        r2.metric("🟡 Medium Risk", risk_counts["Medium"])
        r3.metric("🟢 Low Risk",    risk_counts["Low"])
        r4.metric("⚪ Unknown",     risk_counts["Unknown"])
        st.divider()
        st.markdown("### 📋 Drug Risk Details")
        for drug in data["drugs"]:
            risk      = drug.get("risk_level","Unknown")
            risk_desc = drug.get("risk_description","")
            fda_data  = drug.get("fda_adverse_events") or []
            rs = {"High":("#2d0a0a","#ef4444","🔴"),
                  "Medium":("#2d1f02","#f59e0b","🟡"),
                  "Low":("#052e16","#22c55e","🟢"),
                  "Unknown":("#1a1f2e","#64748b","⚪")}
            r_bg,r_fg,r_em = rs.get(risk,rs["Unknown"])
            with st.expander(
                f"{r_em} {drug['drug_name']} — {risk} Risk "
                f"(Phase {drug.get('clinical_phase','N/A')}, "
                f"Target: {drug['target_gene']})"
            ):
                st.markdown(
                    f"<div style='background:{r_bg};"
                    f"border-left:4px solid {r_fg};"
                    f"padding:12px 16px;border-radius:0 8px 8px 0;"
                    f"margin-bottom:12px;'>"
                    f"<div style='color:{r_fg};font-weight:700;"
                    f"font-size:16px;'>{r_em} {risk} Risk</div>"
                    f"<div style='color:#94a3b8;margin-top:4px;'>"
                    f"{risk_desc}</div></div>",
                    unsafe_allow_html=True)
                # Competition Intelligence
                comp = drug.get("competition_intel") or {}
                if comp:
                    st.markdown("**🏁 Competitive Landscape**")
                    render_competition_badge(drug, compact=False)
                    st.divider()
                if fda_data:
                    st.markdown("**Top FDA Adverse Events:**")
                    for ae in fda_data[:5]:
                        pct = min(ae['count']/300,1.0)
                        ca,cb = st.columns([3,1])
                        with ca:
                            st.markdown(
                                f"<div style='font-size:13px;color:#e2e8f0;'>"
                                f"{ae['reaction']}</div>",
                                unsafe_allow_html=True)
                            st.progress(pct)
                        with cb:
                            st.markdown(
                                f"<div style='text-align:right;color:#94a3b8;"
                                f"font-size:13px;padding-top:4px;'>"
                                f"{ae['count']:,} reports</div>",
                                unsafe_allow_html=True)
                else:
                    st.info("No adverse event data in FDA FAERS")

    # ── TAB 5: NETWORK VISUALIZATION ─────────────────────────
    with tab5:
        st.markdown("### 🕸️ Protein-Drug Interaction Network")
        st.caption(
            "Interactive network showing proteins, drugs, pathways "
            "and their relationships"
        )

        # Build network from current data
        with st.spinner("Building interaction network..."):
            try:
                net_response = requests.post(
                    f"{API_BASE_URL}/network-data",
                    json={
                        "disease_name": data["disease_name"],
                        "max_targets":  max_targets,
                        "max_papers":   max_papers,
                        "max_drugs":    max_drugs
                    },
                    timeout=60
                )
                if net_response.status_code == 200:
                    net_data = net_response.json()
                    render_network_graph(
                        net_data.get("network",{}),
                        data["disease_name"]
                    )
                else:
                    st.error("Failed to load network data")
            except Exception as e:
                # Build network from existing data directly
                st.info(
                    "Building network from analysis data..."
                )
                # Simple fallback using available data
                from backend.services.network_service \
                    import build_network_data

                class QuickResult:
                    disease_name    = data["disease_name"]
                    protein_targets = []
                    drugs           = []
                    hypotheses      = []

                # Convert data dicts to simple objects
                for pt in data.get("protein_targets",[]):
                    class P:
                        pass
                    p = P()
                    p.gene_symbol      = pt["gene_symbol"]
                    p.protein_name     = pt["protein_name"]
                    p.association_score= pt["association_score"]
                    p.alphafold_plddt  = pt.get("alphafold_plddt",0.7)
                    QuickResult.protein_targets.append(p)

                net_data = build_network_data(QuickResult)
                render_network_graph(net_data, data["disease_name"])

    # ── TAB 6: LIVE UPDATES ──────────────────────────────────
    with tab6:
        st.markdown("### 📡 Real-Time Scientific Updates")
        st.caption(
            f"Latest PubMed papers for **{data['disease_name']}** "
            f"— auto-checked daily"
        )

        col_upd1, col_upd2 = st.columns([3, 1])
        with col_upd2:
            if st.button("🔄 Check Now", key="trigger_update"):
                with st.spinner("Checking PubMed..."):
                    try:
                        r = requests.post(
                            f"{API_BASE_URL}/trigger-update",
                            timeout=60
                        )
                        resp = r.json()
                        st.success(
                            f"✅ {resp.get('new_papers',0)} "
                            f"new papers found"
                        )
                    except Exception as e:
                        st.error(f"Update failed: {e}")

        with col_upd1:
            render_updates_panel(data["disease_name"])

        st.divider()
        st.markdown("### 🔭 Tracked Diseases")
        st.caption("Diseases being monitored for new publications")

        try:
            r   = requests.get(f"{API_BASE_URL}/latest-updates",
                               timeout=5)
            upd = r.json()
            tracked = upd.get("tracked_diseases",[])
            stats   = upd.get("stats",{})

            # Stats row
            s1,s2,s3 = st.columns(3)
            s1.metric("🔬 Tracked Diseases", len(tracked))
            s2.metric("📄 Total Updates",
                      stats.get("total_updates",0))
            s3.metric("🔄 Checks Run",
                      stats.get("check_count",0))

            # Tracked list
            if tracked:
                for disease in tracked:
                    count = stats.get(
                        "updates_per_disease",{}
                    ).get(disease, 0)
                    st.markdown(
                        f"<div style='background:#0f172a;"
                        f"border:1px solid #1e293b;"
                        f"border-radius:8px;padding:10px 14px;"
                        f"margin:4px 0;display:flex;"
                        f"justify-content:space-between;"
                        f"align-items:center;'>"
                        f"<span style='color:#e2e8f0;"
                        f"font-size:13px;'>🔬 {disease}</span>"
                        f"<span style='background:#1e3a5f;"
                        f"color:#60a5fa;padding:2px 10px;"
                        f"border-radius:10px;font-size:11px;'>"
                        f"{count} updates</span>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

            # Add new disease to track
            st.markdown("**➕ Track a New Disease**")
            new_disease = st.text_input(
                "Disease to track",
                placeholder="e.g. lung cancer",
                key="new_track_disease",
                label_visibility="collapsed"
            )
            if st.button("Add to Watchlist", key="add_track"):
                if new_disease.strip():
                    try:
                        r = requests.post(
                            f"{API_BASE_URL}/track-disease",
                            json={"disease_name": new_disease.strip()},
                            timeout=30
                        )
                        resp = r.json()
                        st.success(
                            f"✅ {resp.get('message','Added!')}"
                        )
                    except Exception as e:
                        st.error(f"Failed: {e}")

        except Exception as e:
            st.caption(f"Could not load tracked diseases: {e}")
        st.divider()
        st.markdown("### 🧠 Knowledge Graph Memory")
        st.caption("Accumulated intelligence from all past analyses")

        try:
            kg_r = requests.get(
                f"{API_BASE_URL}/knowledge-graph/insights",
                timeout=10
            )
            if kg_r.status_code == 200:
                kg   = kg_r.json()
                stats= kg.get("stats",{})
                cross= kg.get("cross_disease_proteins",[])
                drugs= kg.get("most_analyzed_drugs",[])

                kg1,kg2,kg3,kg4 = st.columns(4)
                kg1.metric("🔵 Total Nodes",
                           stats.get("node_count",0))
                kg2.metric("🔗 Total Edges",
                           stats.get("edge_count",0))
                kg3.metric("🔬 Analyses Run",
                           stats.get("total_analyses",0))
                kg4.metric("🧬 Proteins Tracked",
                           stats.get("total_proteins",0))

                if cross:
                    st.markdown("**🔁 Cross-Disease Proteins:**")
                    for p in cross[:5]:
                        diseases = ", ".join(p.get("diseases",[]))
                        st.markdown(
                            f"<div style='background:#1e3a5f22;"
                            f"border-left:3px solid #60a5fa;"
                            f"padding:6px 12px;margin:3px 0;"
                            f"border-radius:0 6px 6px 0;'>"
                            f"<span style='color:#60a5fa;font-weight:700;'>"
                            f"{p.get('gene_symbol','')}</span>"
                            f"<span style='color:#64748b;font-size:12px;"
                            f"margin-left:10px;'>Found in: {diseases}"
                            f"</span></div>",
                            unsafe_allow_html=True
                        )

                if drugs:
                    st.markdown("**💊 Most Analyzed Drugs:**")
                    for d in drugs[:5]:
                        phase = d.get("phase","?")
                        apps  = d.get("appearances",0)
                        st.markdown(
                            f"<div style='background:#1e3a2f22;"
                            f"border-left:3px solid #34d399;"
                            f"padding:6px 12px;margin:3px 0;"
                            f"border-radius:0 6px 6px 0;'>"
                            f"<span style='color:#34d399;font-weight:700;'>"
                            f"{d.get('drug_name',d.get('name',''))}</span>"
                            f"<span style='color:#64748b;font-size:12px;"
                            f"margin-left:10px;'>"
                            f"Phase {phase} | {apps} appearances</span>"
                            f"</div>",
                            unsafe_allow_html=True
                        )

                # Graph search
                st.markdown("**🔍 Search Knowledge Graph**")
                kg_query = st.text_input(
                    "Search", placeholder="e.g. PSEN1, LECANEMAB",
                    key="kg_search", label_visibility="collapsed"
                )
                if kg_query:
                    sr = requests.get(
                        f"{API_BASE_URL}/knowledge-graph/search",
                        params={"query": kg_query}, timeout=5
                    )
                    if sr.status_code == 200:
                        results = sr.json().get("results",{})
                        if results.get("proteins") or results.get("drugs"):
                            for node_dict in (results.get("proteins",[]) +
                                              results.get("drugs",[])):
                                for key, val in node_dict.items():
                                    st.json(val)
                        else:
                            st.caption(f"No results for '{kg_query}'")

        except Exception as e:
            st.caption(f"Knowledge graph unavailable: {e}")   

    # ── TAB 7: LITERATURE REVIEW ─────────────────────────────
    with tab7:
        st.markdown("### 📄 Auto-Generated Literature Review")
        st.caption(
            f"AI-generated research summary for **{data['disease_name']}** "
            f"based on retrieved evidence"
        )

        lr = data.get("literature_review") or {}
        if lr:
            gen_at = lr.get("generated_at","")
            if gen_at:
                st.caption(f"Generated: {gen_at}")

            sections = [
                ("🔬 Background",           "background"),
                ("📚 Current Research",      "current_research"),
                ("🔍 Research Gaps",         "research_gaps"),
                ("💡 Proposed Hypothesis",   "proposed_hypothesis"),
                ("📊 Supporting Evidence",   "supporting_evidence"),
                ("⚠️ Risks & Limitations",  "risks_limitations"),
                ("✅ Conclusion",            "conclusion"),
            ]

            section_colors = [
                "#3b82f6","#8b5cf6","#f59e0b",
                "#22c55e","#06b6d4","#ef4444","#22c55e"
            ]

            for (title, key), color in zip(sections, section_colors):
                content = lr.get(key,"")
                if content:
                    st.markdown(
                        f"<div style='background:#0f172a;"
                        f"border-left:4px solid {color};"
                        f"border-radius:0 8px 8px 0;"
                        f"padding:14px 16px;margin:8px 0;'>"
                        f"<div style='color:{color};font-weight:700;"
                        f"font-size:13px;text-transform:uppercase;"
                        f"letter-spacing:1px;margin-bottom:8px;'>"
                        f"{title}</div>"
                        f"<div style='color:#cbd5e1;font-size:14px;"
                        f"line-height:1.7;'>{content}</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

            # Export button
            if st.button("📥 Copy Full Report", key="copy_report"):
                report_text = f"LITERATURE REVIEW: {lr.get('disease_name','')}\n"
                report_text += f"Generated: {lr.get('generated_at','')}\n\n"
                for title, key in sections:
                    content = lr.get(key,"")
                    if content:
                        report_text += f"{title}\n{content}\n\n"
                st.code(report_text, language="")

        else:
            st.info(
                "Literature review will appear here after analysis. "
                "Run a disease analysis to generate a full report."
            ) 


# ── Empty states ──────────────────────────────────────────────
elif analyze_clicked and not disease_input.strip():
    st.warning("⚠️ Please enter a disease name first.")

elif not compare_clicked:
    st.markdown("""
    <div style='text-align:center;padding:40px;color:#475569;'>
        <div style='font-size:64px;'>🔬</div>
        <h3 style='color:#64748b;'>Enter a disease name above to begin</h3>
        <p>The AI analyzes protein targets, drug interactions,<br>
        research papers and generates novel biomedical hypotheses.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 💡 Try These Examples")
    ex_cols = st.columns(4)
    examples_info = [
        ("🧠","Alzheimer disease","Amyloid cascade, gamma-secretase"),
        ("🫀","Parkinson disease","Alpha-synuclein, dopamine pathway"),
        ("🎗️","breast cancer","HER2, BRCA1, hormone receptors"),
        ("🩸","type 2 diabetes","Insulin resistance, GLUT4 pathway"),
    ]
    for i,(emoji,name,desc) in enumerate(examples_info):
        with ex_cols[i]:
            st.markdown(
                f"<div style='background:#1a1f2e;border:1px solid #2d3561;"
                f"border-radius:10px;padding:16px;text-align:center;'>"
                f"<div style='font-size:28px;'>{emoji}</div>"
                f"<div style='color:#e2e8f0;font-weight:600;margin:8px 0;'>"
                f"{name}</div>"
                f"<div style='color:#64748b;font-size:12px;'>{desc}</div>"
                f"</div>",
                unsafe_allow_html=True)
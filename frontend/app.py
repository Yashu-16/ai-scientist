# frontend/app.py
# V5 — AI Scientist Decision Intelligence Platform
# Session-state-aware: PDF download works without page reset

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

# ── Session State Init ────────────────────────────────────────
if "last_analysis" not in st.session_state: st.session_state["last_analysis"] = None
if "last_disease" not in st.session_state: st.session_state["last_disease"] = ""
if "last_result" not in st.session_state: st.session_state["last_result"] = None
if "pdf_bytes" not in st.session_state: st.session_state["pdf_bytes"] = None
if "pdf_filename" not in st.session_state: st.session_state["pdf_filename"] = ""
if "pdf_disease" not in st.session_state: st.session_state["pdf_disease"] = ""
if "chat_history" not in st.session_state: st.session_state["chat_history"] = []
if "chat_disease" not in st.session_state: st.session_state["chat_disease"] = ""
if "show_trends" not in st.session_state: st.session_state["show_trends"] = False
if "repurpose_result" not in st.session_state: st.session_state["repurpose_result"] = None
if "repurpose_drug"   not in st.session_state: st.session_state["repurpose_drug"]   = ""

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


# ── Render Functions ──────────────────────────────────────────

def render_causal_analysis(ca: dict):
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
            f"<div style='background:{causal_color}22;border:1px solid {causal_color}55;"
            f"border-radius:10px;padding:14px;text-align:center;'>"
            f"<div style='font-size:24px;'>{ca_emoji}</div>"
            f"<div style='color:{causal_color};font-weight:800;font-size:16px;margin-top:6px;'>{causal_label}</div>"
            f"<div style='color:#64748b;font-size:12px;margin-top:4px;'>Score: {causal_score:.2f} | {total_hits} causal hits</div>"
            f"</div>", unsafe_allow_html=True)
    with col_ca2:
        st.markdown(
            f"<div style='background:#0f172a;border-radius:8px;padding:12px;font-size:13px;color:#94a3b8;line-height:1.6;'>{causal_note}</div>",
            unsafe_allow_html=True)
        if causal_verbs:
            st.markdown("**Causal verbs detected:** " + " ".join([f"`{v}`" for v in causal_verbs[:6]]))

    if causal_chain:
        st.markdown("**⛓️ Causal Chain**")
        chain_html = " → ".join([
            f"<span style='background:#1e293b;color:#e2e8f0;padding:4px 10px;border-radius:6px;font-size:12px;font-weight:600;'>{node}</span>"
            for node in causal_chain])
        st.markdown(f"<div style='padding:10px 0;'>{chain_html}</div>", unsafe_allow_html=True)

    if causal_evid:
        with st.expander(f"📄 View {len(causal_evid)} causal evidence snippets"):
            for ev in causal_evid[:3]:
                strength = ev.get("strength","")
                ev_color = ("#22c55e" if strength == "strong" else "#f59e0b" if strength == "moderate" else "#64748b")
                st.markdown(
                    f"<div style='background:#0f172a;border-left:3px solid {ev_color};padding:8px 12px;margin:4px 0;border-radius:0 6px 6px 0;'>"
                    f"<div style='color:{ev_color};font-size:10px;font-weight:700;text-transform:uppercase;margin-bottom:4px;'>{strength} signal — verb: '{ev.get('causal_verb','')}'</div>"
                    f"<div style='color:#cbd5e1;font-size:12px;line-height:1.5;'>\"{ev.get('text','')}\"</div>"
                    f"<div style='color:#475569;font-size:10px;margin-top:4px;'>Source: {ev.get('source','')}</div>"
                    f"</div>", unsafe_allow_html=True)


def render_validation_suggestion(vs: dict):
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
    type_emoji = {"In-vitro":"🧫","In-vivo":"🐭","Clinical":"🏥"}.get(v_type,"🔬")

    st.markdown("**🧪 Experimental Validation Suggestion**")
    st.markdown(
        f"<div style='background:{v_color}15;border:1px solid {v_color}44;border-radius:10px;padding:14px 16px;margin-bottom:8px;'>"
        f"<div><span style='background:{v_color};color:white;padding:3px 12px;border-radius:20px;font-size:12px;font-weight:700;'>{type_emoji} {v_type}</span>"
        f"<span style='margin-left:10px;background:{diff_col}22;color:{diff_col};padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;'>{diff} Difficulty</span>"
        f"<span style='margin-left:10px;color:#64748b;font-size:12px;'>⏱️ {timeline}</span></div>"
        f"<div style='margin-top:10px;font-size:14px;font-weight:600;color:#e2e8f0;'>{title}</div>"
        f"</div>", unsafe_allow_html=True)

    col_desc, col_tools = st.columns([3, 2])
    with col_desc:
        st.markdown(
            f"<div style='background:#0f172a;border-radius:8px;padding:12px;font-size:13px;color:#cbd5e1;line-height:1.7;'>"
            f"<div style='color:#94a3b8;font-size:10px;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;'>Protocol</div>{desc}</div>",
            unsafe_allow_html=True)
    with col_tools:
        if tools:
            tools_html = "".join([f"<div style='background:#1e293b;color:#94a3b8;padding:4px 10px;border-radius:6px;font-size:12px;margin-bottom:4px;'>🔧 {t}</div>" for t in tools[:4]])
            st.markdown(
                f"<div style='background:#0f172a;border-radius:8px;padding:12px;'>"
                f"<div style='color:#94a3b8;font-size:10px;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;'>Required Tools</div>{tools_html}</div>",
                unsafe_allow_html=True)
    if outcome:
        st.markdown(
            f"<div style='background:#0a1f0a;border:1px solid #166534;border-radius:8px;padding:10px 14px;margin-top:6px;'>"
            f"<span style='color:#4ade80;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;'>✅ Expected Outcome: </span>"
            f"<span style='color:#bbf7d0;font-size:13px;'>{outcome}</span></div>",
            unsafe_allow_html=True)


def render_hypothesis_critique(critique: dict):
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
    sev_emoji  = {"Minor":"🟢","Moderate":"🟡","Major":"🔴"}.get(severity,"🟡")

    st.markdown("**🔍 Critical Evaluation**")
    st.markdown(
        f"<div style='background:{sev_color}15;border:1px solid {sev_color}44;border-radius:10px;padding:14px 16px;margin-bottom:10px;'>"
        f"<span style='background:{sev_color}33;color:{sev_color};padding:3px 12px;border-radius:20px;font-size:12px;font-weight:700;'>{sev_emoji} {severity} Limitations</span>"
        f"<div style='font-size:13px;color:#cbd5e1;line-height:1.6;font-style:italic;margin-top:8px;'>\"{assessment}\"</div></div>",
        unsafe_allow_html=True)

    col_w, col_r = st.columns(2)
    with col_w:
        if weaknesses:
            st.markdown("<div style='color:#f87171;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;'>⚠️ Weaknesses</div>", unsafe_allow_html=True)
            for w in weaknesses:
                st.markdown(f"<div style='background:#1a0a0a;border-left:3px solid #ef444455;padding:8px 12px;margin:4px 0;border-radius:0 6px 6px 0;font-size:12px;color:#fca5a5;line-height:1.5;'>• {w}</div>", unsafe_allow_html=True)
        if contradictions:
            st.markdown("<div style='color:#fb923c;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin:10px 0 6px;'>🔄 Contradictory Evidence</div>", unsafe_allow_html=True)
            for c in contradictions:
                st.markdown(f"<div style='background:#1a0d05;border-left:3px solid #f97316;padding:8px 12px;margin:4px 0;border-radius:0 6px 6px 0;font-size:12px;color:#fdba74;line-height:1.5;'>• {c}</div>", unsafe_allow_html=True)
    with col_r:
        if risks:
            st.markdown("<div style='color:#fbbf24;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;'>🚨 Risks</div>", unsafe_allow_html=True)
            for r in risks:
                st.markdown(f"<div style='background:#1a1505;border-left:3px solid #f59e0b;padding:8px 12px;margin:4px 0;border-radius:0 6px 6px 0;font-size:12px;color:#fde68a;line-height:1.5;'>• {r}</div>", unsafe_allow_html=True)
        if conf_impact:
            st.markdown("<div style='color:#94a3b8;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin:10px 0 6px;'>📊 Confidence Impact</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='background:#0f172a;padding:8px 12px;border-radius:6px;font-size:12px;color:#94a3b8;line-height:1.5;'>{conf_impact}</div>", unsafe_allow_html=True)
    if salvage:
        st.markdown(
            f"<div style='background:#0f1f0f;border:1px solid #16653488;border-radius:8px;padding:12px 14px;margin-top:8px;'>"
            f"<div style='color:#4ade80;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;'>💡 How to Strengthen This Hypothesis</div>"
            f"<div style='font-size:13px;color:#bbf7d0;line-height:1.6;'>{salvage}</div></div>",
            unsafe_allow_html=True)


def render_uncertainty_indicator(uncertainty: dict, compact: bool = False):
    if not uncertainty:
        return
    score  = float(uncertainty.get("uncertainty_score") or 0)
    label  = str(uncertainty.get("uncertainty_label") or "Unknown")
    color  = str(uncertainty.get("uncertainty_color") or "#64748b")
    reason = str(uncertainty.get("uncertainty_reason") or "")
    note   = str(uncertainty.get("reliability_note") or "")
    factors= uncertainty.get("factors") or []
    emoji  = {"Low":"✅","Medium":"⚠️","High":"🔶","Very High":"❌"}.get(label,"❓")

    if compact:
        st.markdown(f"<span style='background:{color}22;color:{color};padding:3px 10px;border-radius:12px;font-size:12px;font-weight:700;'>{emoji} {label} Uncertainty</span>", unsafe_allow_html=True)
        return

    st.markdown("**📐 Uncertainty & Reliability**")
    col_u1, col_u2 = st.columns([1, 2])
    with col_u1:
        st.markdown(
            f"<div style='background:{color}15;border:2px solid {color}44;border-radius:12px;padding:16px;text-align:center;'>"
            f"<div style='font-size:28px;'>{emoji}</div>"
            f"<div style='color:{color};font-weight:800;font-size:18px;margin-top:6px;'>{label}</div>"
            f"<div style='color:#64748b;font-size:12px;margin-top:4px;'>Uncertainty</div>"
            f"<div style='color:{color};font-size:22px;font-weight:700;margin-top:6px;'>{score:.0%}</div></div>",
            unsafe_allow_html=True)
    with col_u2:
        st.markdown(f"<div style='background:#0f172a;border-radius:8px;padding:12px;font-size:13px;color:#cbd5e1;line-height:1.7;margin-bottom:8px;'>{reason}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='background:#0a1f0a;border:1px solid #166534;border-radius:8px;padding:10px;font-size:12px;color:#bbf7d0;'>💡 <strong>To reduce uncertainty:</strong> {note}</div>", unsafe_allow_html=True)

    if factors:
        st.markdown("**Contributing Factors:**")
        for factor in factors:
            f_impact = factor.get("impact","")
            f_color  = {"High":"#ef4444","Medium":"#f59e0b","Low":"#22c55e"}.get(f_impact,"#64748b")
            f_emoji  = {"High":"🔴","Medium":"🟡","Low":"🟢"}.get(f_impact,"⚪")
            st.markdown(
                f"<div style='background:#0f172a;border-left:3px solid {f_color};padding:6px 12px;margin:3px 0;border-radius:0 6px 6px 0;'>"
                f"<span style='color:{f_color};font-weight:700;font-size:12px;'>{f_emoji} {factor.get('factor','')}: {f_impact}</span>"
                f"<span style='color:#64748b;font-size:11px;margin-left:8px;'>{factor.get('description','')[:80]}</span></div>",
                unsafe_allow_html=True)

    flags_html = []
    for key, label_text in [("low_paper_count","🔴 Low paper count"),("weak_protein_assoc","🔴 Weak protein association"),
                              ("high_fda_risk","🔴 High FDA risk"),("no_causal_evidence","🟡 No causal evidence"),("limited_drug_data","🟡 Limited drug data")]:
        if uncertainty.get(key):
            flags_html.append(f"<span style='background:#1a1a2e;color:#94a3b8;padding:2px 8px;border-radius:8px;font-size:11px;margin:2px;display:inline-block;'>{label_text}</span>")
    if flags_html:
        st.markdown("<div style='margin-top:8px;'>" + "".join(flags_html) + "</div>", unsafe_allow_html=True)


def render_go_no_go_badge(gng: dict, size: str = "large"):
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
        st.markdown(f"<span style='background:{color};color:white;padding:4px 14px;border-radius:20px;font-size:13px;font-weight:800;letter-spacing:1px;'>{emoji} {decision}</span>", unsafe_allow_html=True)
        return

    bg_gradient = {"GO":"linear-gradient(135deg,#052e16,#0a3d1f)","NO-GO":"linear-gradient(135deg,#2d0a0a,#3d1010)","INVESTIGATE":"linear-gradient(135deg,#1c1202,#2d1f02)"}.get(decision,"linear-gradient(135deg,#0f172a,#1e293b)")
    st.markdown(
        f"<div style='background:{bg_gradient};border:2px solid {color}55;border-radius:14px;padding:20px 24px;margin:8px 0;'>"
        f"<div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;'>"
        f"<div style='display:flex;align-items:center;gap:12px;'><div style='font-size:36px;'>{emoji}</div>"
        f"<div><div style='font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:2px;font-weight:700;'>Final Decision</div>"
        f"<div style='font-size:28px;font-weight:900;color:{color};letter-spacing:2px;'>{decision}</div></div></div>"
        f"<div style='text-align:right;'><div style='color:#64748b;font-size:11px;'>Decision confidence</div>"
        f"<div style='color:{color};font-size:24px;font-weight:700;'>{conf:.0%}</div></div></div>"
        f"<div style='background:rgba(0,0,0,0.3);border-radius:8px;padding:12px;margin-bottom:12px;font-size:13px;color:#e2e8f0;line-height:1.6;'>"
        f"<strong style='color:{color};'>📋 Decision Basis: </strong>{primary}</div></div>",
        unsafe_allow_html=True)

    if supporting or blocking:
        col_s, col_b = st.columns(2)
        with col_s:
            if supporting:
                st.markdown("<div style='color:#22c55e;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;'>✅ Supporting Factors</div>", unsafe_allow_html=True)
                for s in supporting:
                    st.markdown(f"<div style='background:#052e1688;border-left:3px solid #22c55e;padding:6px 10px;margin:3px 0;border-radius:0 6px 6px 0;font-size:12px;color:#86efac;'>• {s}</div>", unsafe_allow_html=True)
        with col_b:
            if blocking:
                st.markdown("<div style='color:#ef4444;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;'>❌ Blocking Factors</div>", unsafe_allow_html=True)
                for b in blocking:
                    st.markdown(f"<div style='background:#2d0a0a88;border-left:3px solid #ef4444;padding:6px 10px;margin:3px 0;border-radius:0 6px 6px 0;font-size:12px;color:#fca5a5;'>• {b}</div>", unsafe_allow_html=True)

    if action:
        st.markdown(f"<div style='background:#0f1f0f;border:1px solid #16653488;border-radius:8px;padding:10px 14px;margin-top:8px;'><span style='color:#4ade80;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;'>🚀 Recommended Action: </span><span style='font-size:13px;color:#bbf7d0;'>{action}</span></div>", unsafe_allow_html=True)
    if flip:
        st.markdown(f"<div style='background:#111827;border-radius:8px;padding:8px 14px;margin-top:6px;'><span style='color:#64748b;font-size:11px;'>🔄 <em>{flip}</em></span></div>", unsafe_allow_html=True)


def render_failure_prediction(fp: dict):
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
    risk_emoji  = {"Low":"🟢","Medium":"🟡","High":"🔶","Very High":"🔴"}.get(risk_label,"❓")

    st.markdown("**⚠️ Failure Prediction Analysis**")
    col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
    with col_f1:
        st.markdown(f"<div style='background:{risk_color}15;border:2px solid {risk_color}44;border-radius:10px;padding:14px;text-align:center;'><div style='font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;'>Failure Risk</div><div style='font-size:24px;'>{risk_emoji}</div><div style='color:{risk_color};font-weight:800;font-size:16px;margin-top:4px;'>{risk_label}</div><div style='color:#64748b;font-size:13px;margin-top:2px;'>{risk_score:.0%}</div></div>", unsafe_allow_html=True)
    with col_f2:
        sp_color = confidence_color(success_p)
        st.markdown(f"<div style='background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:14px;text-align:center;'><div style='font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;'>Success Probability</div><div style='color:{sp_color};font-weight:800;font-size:28px;'>{success_p:.0%}</div><div style='color:#64748b;font-size:11px;'>estimated</div></div>", unsafe_allow_html=True)
    with col_f3:
        if top_reason:
            st.markdown(f"<div style='background:#1a0d0d;border-left:3px solid {risk_color};border-radius:0 8px 8px 0;padding:12px;'><div style='color:{risk_color};font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;'>Top Failure Mode</div><div style='color:#fca5a5;font-size:13px;line-height:1.5;'>{top_reason}</div></div>", unsafe_allow_html=True)
    if hist_ctx:
        st.markdown(f"<div style='background:#0f172a;border-radius:8px;padding:10px 14px;margin:8px 0;font-size:12px;color:#94a3b8;line-height:1.6;'><strong style='color:#60a5fa;'>📚 Historical Context: </strong>{hist_ctx}</div>", unsafe_allow_html=True)
    if reasons:
        st.markdown("**Predicted Failure Reasons:**")
        cat_colors = {"Safety":"#ef4444","Efficacy":"#f59e0b","Mechanism":"#8b5cf6","Trial Design":"#3b82f6","Market":"#10b981"}
        for r in reasons[:4]:
            cat = r.get("category",""); sev = r.get("severity","Medium")
            c_col = cat_colors.get(cat,"#64748b")
            sev_badge = {"High":"🔴 High","Medium":"🟡 Med","Low":"🟢 Low"}.get(sev,sev)
            with st.expander(f"[{cat}] {r.get('reason','')[:60]}... — {sev_badge}"):
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    st.markdown(f"<div style='font-size:12px;color:#94a3b8;margin-bottom:4px;'><strong style='color:{c_col};'>Evidence:</strong> {r.get('evidence','')}</div>", unsafe_allow_html=True)
                with col_r2:
                    st.markdown(f"<div style='font-size:12px;color:#86efac;'><strong>Mitigation:</strong> {r.get('mitigation','')}</div>", unsafe_allow_html=True)
    if safeguards:
        st.markdown("<div style='background:#0f1f0f;border:1px solid #166534;border-radius:8px;padding:12px 14px;margin-top:8px;'><div style='color:#4ade80;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;'>🛡️ Recommended Safeguards</div>" + "".join([f"<div style='color:#bbf7d0;font-size:12px;margin:3px 0;'>• {sg}</div>" for sg in safeguards[:4]]) + "</div>", unsafe_allow_html=True)


def _similar_drugs_html(similar: list) -> str:
    if not similar:
        return ""
    return f"<div style='font-size:11px;color:#64748b;'>Similar drugs: {', '.join(similar[:4])}</div>"


def render_competition_badge(drug: dict, compact: bool = False):
    comp = drug.get("competition_intel") or {}
    if not comp:
        return
    level      = str(comp.get("competition_level") or "Unknown")
    color      = str(comp.get("competition_color") or "#64748b")
    opp        = str(comp.get("market_opportunity") or "")
    note       = str(comp.get("strategic_note") or "")
    drug_class = str(comp.get("drug_class") or "")
    similar    = comp.get("similar_drug_names") or []
    opp_color  = {"Strong":"#22c55e","Moderate":"#f59e0b","Crowded":"#ef4444"}.get(opp,"#64748b")
    level_emoji= {"Low":"🟢","Medium":"🟡","High":"🔴"}.get(level,"⚪")
    opp_emoji  = {"Strong":"🌟","Moderate":"⚡","Crowded":"🏁"}.get(opp,"❓")

    if compact:
        st.markdown(f"<span style='background:{color}22;color:{color};padding:3px 8px;border-radius:8px;font-size:11px;font-weight:600;'>{level_emoji} {level} Competition</span>", unsafe_allow_html=True)
        return
    st.markdown(
        f"<div style='background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:14px;margin:6px 0;'>"
        f"<div style='display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;'>"
        f"<div><div style='font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;'>Drug Class</div>"
        f"<div style='color:#e2e8f0;font-size:13px;font-weight:600;'>{drug_class}</div></div>"
        f"<div style='display:flex;gap:8px;'>"
        f"<span style='background:{color}22;color:{color};padding:4px 10px;border-radius:8px;font-size:12px;font-weight:700;'>{level_emoji} {level} Competition</span>"
        f"<span style='background:{opp_color}22;color:{opp_color};padding:4px 10px;border-radius:8px;font-size:12px;font-weight:700;'>{opp_emoji} {opp}</span></div></div>"
        f"<div style='font-size:12px;color:#94a3b8;margin-bottom:8px;'>{note}</div>"
        f"{_similar_drugs_html(similar)}</div>",
        unsafe_allow_html=True)


def render_time_to_impact(tti: dict):
    if not tti:
        return
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
        st.markdown(f"<div style='background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:14px;text-align:center;'><div style='font-size:11px;color:#94a3b8;margin-bottom:4px;'>Estimated Timeline</div><div style='color:{color};font-size:24px;font-weight:800;'>{speed_emoji} {yr_rng}</div><div style='color:#64748b;font-size:11px;'>{speed} track</div></div>", unsafe_allow_html=True)
    with t2:
        sc_color = confidence_color(success)
        st.markdown(f"<div style='background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:14px;text-align:center;'><div style='font-size:11px;color:#94a3b8;margin-bottom:4px;'>Success Probability</div><div style='color:{sc_color};font-size:24px;font-weight:800;'>{success:.0%}</div><div style='color:#64748b;font-size:11px;'>to market</div></div>", unsafe_allow_html=True)
    with t3:
        next_truncated = next_m[:50] + "..." if len(next_m) > 50 else next_m
        st.markdown(f"<div style='background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:14px;'><div style='font-size:11px;color:#94a3b8;margin-bottom:4px;'>Current Stage</div><div style='color:#e2e8f0;font-size:12px;font-weight:600;'>{stage}</div><div style='color:#64748b;font-size:11px;margin-top:4px;'>Next: {next_truncated}</div></div>", unsafe_allow_html=True)

    if timeline:
        st.markdown("**📅 Timeline Breakdown:**")
        for i, step in enumerate(timeline, 1):
            st.markdown(f"<div style='background:#0f172a;border-left:3px solid {color};padding:6px 12px;margin:3px 0;border-radius:0 6px 6px 0;font-size:12px;color:#cbd5e1;'><strong style='color:{color};'>{i}.</strong> {step}</div>", unsafe_allow_html=True)
    if bottlenecks:
        st.markdown("<div style='background:#1a1105;border:1px solid #92400e44;border-radius:8px;padding:10px 14px;margin-top:6px;'><div style='color:#fbbf24;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;'>⚠️ Key Bottlenecks</div>" + "".join([f"<div style='color:#fde68a;font-size:12px;margin:2px 0;'>• {b}</div>" for b in bottlenecks]) + "</div>", unsafe_allow_html=True)


def render_executive_summary(es: dict):
    if not es:
        return
    headline = str(es.get("headline") or "")
    body     = str(es.get("body") or "")
    market   = str(es.get("market_opportunity") or "")
    bottom   = str(es.get("bottom_line") or "")
    st.markdown("**📋 Executive Summary**")
    st.markdown(
        f"<div style='background:linear-gradient(135deg,#0f1b2d,#1a2744);border:1px solid #2d4a7a;border-radius:10px;padding:16px;'>"
        f"<div style='color:#60a5fa;font-size:16px;font-weight:700;margin-bottom:10px;'>💼 {headline}</div>"
        f"<div style='color:#cbd5e1;font-size:13px;line-height:1.7;margin-bottom:10px;'>{body}</div>"
        f"<div style='background:#0a1628;border-radius:6px;padding:8px 12px;margin-bottom:8px;font-size:12px;color:#94a3b8;'>💰 {market}</div>"
        f"<div style='background:#0a1f0a;border-radius:6px;padding:8px 12px;font-size:13px;color:#4ade80;font-weight:600;'>✅ Bottom Line: {bottom}</div></div>",
        unsafe_allow_html=True)

SUGGESTED_QUESTIONS = [
    "Why is the top hypothesis risky?",
    "Explain the amyloidogenic pathway simply",
    "What are the main differences between the top 2 drugs?",
    "Which protein target is most promising and why?",
    "What would make this a GO instead of INVESTIGATE?",
    "What experiments should I run first?",
    "Summarize this analysis for a non-scientist",
    "What are the biggest uncertainties in this analysis?",
    "Why did the third hypothesis score lower?",
    "What is the FDA risk and how serious is it?",
]

def render_chat_tab(data: dict):
    """Render the AI chat interface tab."""

    disease_name = data.get("disease_name","")

    # Clear chat if disease changed
    if st.session_state.get("chat_disease") != disease_name:
        st.session_state["chat_history"] = []
        st.session_state["chat_disease"] = disease_name

    st.markdown("### 🤖 Ask Anything — AI Scientist Chat")
    st.caption(
        f"Ask questions about the **{disease_name}** analysis. "
        f"The AI has full context of proteins, drugs, hypotheses, and evidence."
    )

    # ── Suggested questions ───────────────────────────────────
    if not st.session_state["chat_history"]:
        st.markdown("**💡 Suggested Questions:**")
        # Show 6 questions in 2 rows of 3
        hyp_count = len(data.get("hypotheses", []))
        drug_count = len(data.get("drugs", []))

        # Pick relevant suggestions
        suggestions = SUGGESTED_QUESTIONS[:6]

        sq_cols = st.columns(3)
        for i, q in enumerate(suggestions):
            with sq_cols[i % 3]:
                if st.button(
                    q, key=f"sq_{i}",
                    use_container_width=True
                ):
                    st.session_state["chat_history"].append({
                        "role": "user", "content": q
                    })
                    # Get answer immediately
                    with st.spinner("🤖 Thinking..."):
                        resp = _ask_question_api(q, disease_name, data)
                        st.session_state["chat_history"].append({
                            "role": "assistant",
                            "content": resp["answer"],
                            "sources": resp.get("sources_used", [])
                        })
                    st.rerun()

        st.divider()

    # ── Chat history ──────────────────────────────────────────
    chat_container = st.container()
    with chat_container:
        for i, msg in enumerate(st.session_state["chat_history"]):
            if msg["role"] == "user":
                st.markdown(
                    f"<div style='background:#1e3a5f;border-radius:12px 12px 2px 12px;"
                    f"padding:12px 16px;margin:8px 0;margin-left:20%;'>"
                    f"<div style='font-size:11px;color:#60a5fa;font-weight:700;"
                    f"margin-bottom:4px;'>👤 You</div>"
                    f"<div style='color:#e2e8f0;font-size:14px;"
                    f"line-height:1.6;'>{msg['content']}</div></div>",
                    unsafe_allow_html=True
                )
            else:
                sources = msg.get("sources", [])
                sources_html = ""
                if sources:
                    src_badges = "".join([
                        f"<span style='background:#1e293b;color:#64748b;"
                        f"padding:2px 8px;border-radius:8px;font-size:10px;"
                        f"margin-right:4px;'>{s}</span>"
                        for s in sources
                    ])
                    sources_html = (
                        f"<div style='margin-top:8px;'>"
                        f"<span style='color:#64748b;font-size:10px;'>Sources: </span>"
                        f"{src_badges}</div>"
                    )

                st.markdown(
                    f"<div style='background:#0f172a;border:1px solid #1e293b;"
                    f"border-radius:2px 12px 12px 12px;"
                    f"padding:12px 16px;margin:8px 0;margin-right:10%;'>"
                    f"<div style='font-size:11px;color:#34d399;font-weight:700;"
                    f"margin-bottom:6px;'>🤖 AI Scientist</div>"
                    f"<div style='color:#cbd5e1;font-size:14px;"
                    f"line-height:1.7;white-space:pre-wrap;'>{msg['content']}</div>"
                    f"{sources_html}</div>",
                    unsafe_allow_html=True
                )

    # ── Input area ────────────────────────────────────────────
    st.markdown("---")
    col_inp, col_btn, col_clear = st.columns([5, 1, 1])

    with col_inp:
        user_input = st.text_input(
            "Ask a question",
            placeholder=f"e.g. Why is Lecanemab the top recommendation?",
            key="chat_input",
            label_visibility="collapsed"
        )
    with col_btn:
        send_clicked = st.button(
            "Send 💬", type="primary",
            use_container_width=True,
            key="chat_send"
        )
    with col_clear:
        if st.button("Clear 🗑️", use_container_width=True, key="chat_clear"):
            st.session_state["chat_history"] = []
            st.rerun()

    if send_clicked and user_input.strip():
        st.session_state["chat_history"].append({
            "role": "user", "content": user_input.strip()
        })
        with st.spinner("🤖 AI Scientist is thinking..."):
            resp = _ask_question_api(user_input.strip(), disease_name, data)
            st.session_state["chat_history"].append({
                "role":    "assistant",
                "content": resp["answer"],
                "sources": resp.get("sources_used", [])
            })
        st.rerun()

    # ── Stats ─────────────────────────────────────────────────
    if st.session_state["chat_history"]:
        n_q = sum(1 for m in st.session_state["chat_history"] if m["role"]=="user")
        st.caption(f"💬 {n_q} question{'s' if n_q != 1 else ''} asked in this session")

def render_trending_insights():
    """Render trending insights and emerging opportunities panel."""
    st.markdown("### 🔥 Emerging Opportunities & Trends")
    st.caption(
        "AI-detected trends from recent PubMed papers across all tracked diseases"
    )

    try:
        r = requests.get(
            f"{API_BASE_URL}/trending-insights",
            timeout=15
        )
        if r.status_code != 200:
            st.info("Trending insights unavailable. Run an analysis first.")
            return

        data   = r.json()
        trends = data.get("trends", {})
        total  = trends.get("total_papers_analyzed", 0)

        if total == 0:
            st.info(
                "📡 No papers analyzed yet. "
                "The system fetches papers on startup and daily. "
                "Click **🔄 Check Now** in the Live Updates tab to fetch papers."
            )
            return

        st.caption(f"Based on analysis of **{total} recent papers** across tracked diseases")

        # ── Emerging Opportunities ────────────────────────────
        opportunities = trends.get("emerging_opportunities", [])
        if opportunities:
            st.markdown("#### 💡 Emerging Drug Discovery Opportunities")
            for opp in opportunities:
                strength      = opp.get("strength","Moderate")
                strength_color= "#22c55e" if strength == "Strong" else "#f59e0b"
                strength_emoji= "🔥" if strength == "Strong" else "📈"

                st.markdown(
                    f"<div style='background:linear-gradient(135deg,#0f1b2d,#1a2744);"
                    f"border:1px solid #2d4a7a;border-radius:10px;"
                    f"padding:14px 18px;margin:8px 0;'>"
                    f"<div style='display:flex;justify-content:space-between;"
                    f"align-items:center;margin-bottom:8px;'>"
                    f"<div style='color:#60a5fa;font-weight:700;font-size:14px;'>"
                    f"{strength_emoji} {opp.get('signal','')}</div>"
                    f"<span style='background:{strength_color}22;color:{strength_color};"
                    f"padding:3px 10px;border-radius:12px;font-size:11px;"
                    f"font-weight:700;'>{strength} Signal</span>"
                    f"</div>"
                    f"<div style='color:#94a3b8;font-size:13px;"
                    f"line-height:1.6;'>{opp.get('description','')}</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )

        st.divider()

        # ── Trending proteins / mechanisms / diseases ─────────
        col_t1, col_t2, col_t3 = st.columns(3)

        with col_t1:
            st.markdown("#### 🧬 Trending Proteins")
            proteins = trends.get("trending_proteins", [])
            if proteins:
                for p in proteins[:6]:
                    trend_em = p.get("trend","")
                    mentions = p.get("mentions", 0)
                    freq     = p.get("frequency", 0)
                    bar_w    = min(int(freq * 200), 100)
                    color    = "#ef4444" if "Hot" in trend_em else "#f59e0b" if "Rising" in trend_em else "#60a5fa"
                    st.markdown(
                        f"<div style='background:#0f172a;border-radius:8px;"
                        f"padding:8px 12px;margin:4px 0;'>"
                        f"<div style='display:flex;justify-content:space-between;"
                        f"align-items:center;'>"
                        f"<span style='color:#e2e8f0;font-weight:600;"
                        f"font-size:13px;'>{p['name']}</span>"
                        f"<span style='color:{color};font-size:11px;'>"
                        f"{trend_em} ({mentions})</span></div>"
                        f"<div style='background:#1e293b;border-radius:4px;"
                        f"height:3px;margin-top:4px;'>"
                        f"<div style='background:{color};height:3px;"
                        f"border-radius:4px;width:{bar_w}%;'></div></div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
            else:
                st.caption("No protein trends detected yet")

        with col_t2:
            st.markdown("#### ⚗️ Trending Mechanisms")
            mechanisms = trends.get("trending_mechanisms", [])
            if mechanisms:
                for m in mechanisms[:6]:
                    trend_em = m.get("trend","")
                    mentions = m.get("mentions", 0)
                    freq     = m.get("frequency", 0)
                    bar_w    = min(int(freq * 200), 100)
                    color    = "#ef4444" if "Hot" in trend_em else "#f59e0b" if "Rising" in trend_em else "#8b5cf6"
                    st.markdown(
                        f"<div style='background:#0f172a;border-radius:8px;"
                        f"padding:8px 12px;margin:4px 0;'>"
                        f"<div style='display:flex;justify-content:space-between;"
                        f"align-items:center;'>"
                        f"<span style='color:#e2e8f0;font-weight:600;"
                        f"font-size:13px;'>{m['name']}</span>"
                        f"<span style='color:{color};font-size:11px;'>"
                        f"{trend_em} ({mentions})</span></div>"
                        f"<div style='background:#1e293b;border-radius:4px;"
                        f"height:3px;margin-top:4px;'>"
                        f"<div style='background:{color};height:3px;"
                        f"border-radius:4px;width:{bar_w}%;'></div></div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
            else:
                st.caption("No mechanism trends detected yet")

        with col_t3:
            st.markdown("#### 🏥 Trending Diseases")
            diseases = trends.get("trending_diseases", [])
            if diseases:
                for d in diseases[:6]:
                    trend_em = d.get("trend","")
                    mentions = d.get("mentions", 0)
                    freq     = d.get("frequency", 0)
                    bar_w    = min(int(freq * 200), 100)
                    color    = "#ef4444" if "Hot" in trend_em else "#f59e0b" if "Rising" in trend_em else "#34d399"
                    st.markdown(
                        f"<div style='background:#0f172a;border-radius:8px;"
                        f"padding:8px 12px;margin:4px 0;'>"
                        f"<div style='display:flex;justify-content:space-between;"
                        f"align-items:center;'>"
                        f"<span style='color:#e2e8f0;font-weight:600;"
                        f"font-size:13px;'>{d['name']}</span>"
                        f"<span style='color:{color};font-size:11px;'>"
                        f"{trend_em} ({mentions})</span></div>"
                        f"<div style='background:#1e293b;border-radius:4px;"
                        f"height:3px;margin-top:4px;'>"
                        f"<div style='background:{color};height:3px;"
                        f"border-radius:4px;width:{bar_w}%;'></div></div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
            else:
                st.caption("No disease trends detected yet")

        # ── Refresh button ────────────────────────────────────
        st.divider()
        if st.button("🔄 Refresh Trend Analysis", key="refresh_trends"):
            st.rerun()

        last_analyzed = trends.get("last_analyzed","")
        if last_analyzed:
            st.caption(f"Last analyzed: {last_analyzed[:19]}")

    except Exception as e:
        st.error(f"Could not load trending insights: {e}")
def render_repurposing_mode():
    """Render the drug repurposing analysis interface."""

    st.markdown("### 🔁 Drug Repurposing Mode")
    st.caption(
        "Enter a drug name to discover potential new disease indications "
        "based on mechanism of action and shared pathways."
    )

    # ── Quick-select known drugs ──────────────────────────────
    st.markdown("**Quick select a drug:**")
    quick_drugs = ["Lecanemab","Metformin","Nirogacestat",
                   "Rapamycin","Sildenafil","Aducanumab"]
    qd_cols = st.columns(len(quick_drugs))
    selected_drug = ""
    for i, drug in enumerate(quick_drugs):
        with qd_cols[i]:
            if st.button(drug, key=f"qd_{i}", use_container_width=True):
                st.session_state["repurpose_drug"] = drug

    # ── Drug input ────────────────────────────────────────────
    col_ri1, col_ri2 = st.columns([3, 1])
    with col_ri1:
        drug_input = st.text_input(
            "Drug name",
            value=st.session_state.get("repurpose_drug",""),
            placeholder="e.g. Lecanemab, Metformin, Rapamycin...",
            key="repurpose_input",
            label_visibility="collapsed"
        )
    with col_ri2:
        repurpose_clicked = st.button(
            "🔁 Analyze", type="primary",
            use_container_width=True,
            key="repurpose_btn"
        )

    if repurpose_clicked and drug_input.strip():
        with st.spinner(f"🔁 Analyzing repurposing potential for **{drug_input}**..."):
            try:
                r = requests.post(
                    f"{API_BASE_URL}/repurpose-drug",
                    json={"drug_name": drug_input.strip()},
                    timeout=60
                )
                if r.status_code == 200:
                    st.session_state["repurpose_result"] = r.json()
                    st.session_state["repurpose_drug"]   = drug_input.strip()
                else:
                    st.error(f"Analysis failed (status {r.status_code})")
            except Exception as e:
                st.error(f"Error: {e}")

    # ── Show results ──────────────────────────────────────────
    result = st.session_state.get("repurpose_result")
    if result and result.get("drug_name","").upper() == st.session_state.get("repurpose_drug","").upper():

        drug_name = result.get("drug_name","")
        primary   = result.get("primary_indication","")
        mechanism = result.get("mechanism_summary","")
        potential = result.get("overall_potential","Medium")
        rationale = result.get("repurposing_rationale","")
        candidates= result.get("repurposing_candidates",[])

        pot_color = {"High":"#22c55e","Medium":"#f59e0b","Low":"#ef4444"}.get(potential,"#64748b")
        pot_emoji = {"High":"🔥","Medium":"⚡","Low":"❄️"}.get(potential,"❓")

        # Header
        st.markdown(
            f"<div style='background:linear-gradient(135deg,#0f1b2d,#1a2744);"
            f"border:1px solid #2d4a7a;border-radius:12px;"
            f"padding:16px 20px;margin:12px 0;'>"
            f"<div style='display:flex;justify-content:space-between;"
            f"align-items:center;margin-bottom:10px;'>"
            f"<div>"
            f"<div style='font-size:11px;color:#60a5fa;text-transform:uppercase;"
            f"letter-spacing:1px;margin-bottom:4px;'>Drug Repurposing Analysis</div>"
            f"<div style='font-size:22px;font-weight:800;color:#e2e8f0;'>"
            f"💊 {drug_name}</div>"
            f"<div style='color:#64748b;font-size:13px;margin-top:4px;'>"
            f"Primary: {primary}</div>"
            f"</div>"
            f"<div style='text-align:center;'>"
            f"<div style='color:#64748b;font-size:11px;'>Repurposing Potential</div>"
            f"<div style='color:{pot_color};font-size:20px;font-weight:800;'>"
            f"{pot_emoji} {potential}</div>"
            f"</div></div>"
            f"<div style='background:rgba(0,0,0,0.2);border-radius:8px;"
            f"padding:10px;font-size:13px;color:#94a3b8;line-height:1.6;'>"
            f"<strong style='color:#60a5fa;'>Mechanism: </strong>{mechanism}</div>"
            f"</div>",
            unsafe_allow_html=True
        )

        if rationale:
            st.markdown(
                f"<div style='font-size:12px;color:#64748b;"
                f"padding:6px 0;'><em>{rationale}</em></div>",
                unsafe_allow_html=True
            )

        # Candidates
        st.markdown(f"### 🎯 {len(candidates)} Repurposing Candidates")

        conf_colors = {"High":"#22c55e","Medium":"#f59e0b","Low":"#ef4444"}
        ev_colors   = {
            "Phase 2":"#22c55e","Phase 1":"#84cc16",
            "Observational":"#f59e0b","Preclinical":"#f97316","Theoretical":"#64748b"
        }

        for i, cand in enumerate(candidates, 1):
            disease      = cand.get("disease","")
            rationale_c  = cand.get("rationale","")
            pathway      = cand.get("shared_pathway","")
            confidence   = cand.get("confidence","Medium")
            evidence     = cand.get("evidence_level","Preclinical")
            challenge    = cand.get("key_challenge","")
            next_step    = cand.get("next_step","")

            conf_col  = conf_colors.get(confidence,"#64748b")
            ev_col    = ev_colors.get(evidence,"#64748b")
            rank_emoji= {1:"🥇",2:"🥈",3:"🥉",4:"#4"}.get(i,f"#{i}")

            with st.expander(
                f"{rank_emoji} {disease} — {confidence} Confidence | {evidence}",
                expanded=(i == 1)
            ):
                col_c1, col_c2 = st.columns([3, 1])

                with col_c1:
                    st.markdown(
                        f"<div style='font-size:13px;color:#cbd5e1;"
                        f"line-height:1.7;margin-bottom:8px;'>{rationale_c}</div>",
                        unsafe_allow_html=True
                    )
                    if pathway:
                        st.markdown(
                            f"<div style='background:#0f172a;border-left:3px solid #8b5cf6;"
                            f"padding:6px 12px;border-radius:0 6px 6px 0;"
                            f"font-size:12px;color:#c4b5fd;margin-bottom:6px;'>"
                            f"🔗 Shared pathway: {pathway}</div>",
                            unsafe_allow_html=True
                        )
                    if challenge:
                        st.markdown(
                            f"<div style='background:#1a0d05;border-left:3px solid #f97316;"
                            f"padding:6px 12px;border-radius:0 6px 6px 0;"
                            f"font-size:12px;color:#fdba74;margin-bottom:6px;'>"
                            f"⚠️ Key challenge: {challenge}</div>",
                            unsafe_allow_html=True
                        )
                    if next_step:
                        st.markdown(
                            f"<div style='background:#0f1f0f;border:1px solid #166534;"
                            f"padding:8px 12px;border-radius:6px;font-size:12px;"
                            f"color:#bbf7d0;'>"
                            f"🚀 Next step: {next_step}</div>",
                            unsafe_allow_html=True
                        )

                with col_c2:
                    st.markdown(
                        f"<div style='background:#0f172a;border-radius:10px;"
                        f"padding:12px;text-align:center;'>"
                        f"<div style='color:#64748b;font-size:10px;"
                        f"text-transform:uppercase;letter-spacing:1px;"
                        f"margin-bottom:6px;'>Confidence</div>"
                        f"<div style='color:{conf_col};font-weight:800;"
                        f"font-size:18px;'>{confidence}</div>"
                        f"<div style='color:#64748b;font-size:10px;"
                        f"text-transform:uppercase;letter-spacing:1px;"
                        f"margin:8px 0 4px;'>Evidence</div>"
                        f"<div style='color:{ev_col};font-size:12px;"
                        f"font-weight:600;'>{evidence}</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

def _ask_question_api(question: str, disease_name: str, data: dict) -> dict:
    """Call the /ask-question API endpoint."""
    try:
        # Send only lightweight context (not full data to avoid payload size issues)
        context_data = {
            "protein_targets": [
                {"gene_symbol": p.get("gene_symbol",""),
                 "association_score": p.get("association_score",0),
                 "protein_name": p.get("protein_name","")}
                for p in data.get("protein_targets",[])[:5]
            ],
            "drugs": [
                {"drug_name":      d.get("drug_name",""),
                 "clinical_phase": d.get("clinical_phase"),
                 "risk_level":     d.get("risk_level",""),
                 "mechanism":      d.get("mechanism","")[:100],
                 "target_gene":    d.get("target_gene","")}
                for d in data.get("drugs",[])[:5]
            ],
            "hypotheses": [
                {"title":       h.get("title",""),
                 "final_score": h.get("final_score",0),
                 "key_proteins":h.get("key_proteins",[]),
                 "key_drugs":   h.get("key_drugs",[]),
                 "go_no_go":    {"decision": (h.get("go_no_go") or {}).get("decision","")},
                 "failure_prediction": {
                     "failure_risk_label": (h.get("failure_prediction") or {}).get("failure_risk_label",""),
                     "success_probability": (h.get("failure_prediction") or {}).get("success_probability",0)
                 }}
                for h in data.get("hypotheses",[])[:3]
            ],
            "evidence_strength": {
                "evidence_label": (data.get("evidence_strength") or {}).get("evidence_label",""),
                "total_papers":   (data.get("evidence_strength") or {}).get("total_papers",0)
            },
            "decision_summary": {
                "recommended_drug": (data.get("decision_summary") or {}).get("recommended_drug",""),
                "target_protein":   (data.get("decision_summary") or {}).get("target_protein",""),
                "go_no_go": {
                    "decision": ((data.get("decision_summary") or {}).get("go_no_go") or {}).get("decision",""),
                    "confidence_in_decision": ((data.get("decision_summary") or {}).get("go_no_go") or {}).get("confidence_in_decision",0)
                }
            },
            "papers": [
                {"title": p.get("title","")[:80]}
                for p in data.get("papers",[])[:3]
            ]
        }

        r = requests.post(
            f"{API_BASE_URL}/ask-question",
            json={
                "question":     question,
                "disease_name": disease_name,
                "context_data": context_data
            },
            timeout=30
        )

        if r.status_code == 200:
            return r.json()
        else:
            return {
                "answer": f"Sorry, I couldn't process that question (error {r.status_code}). Please try again.",
                "sources_used": []
            }

    except Exception as e:
        return {
            "answer": f"Connection error: {str(e)}. Make sure the backend is running.",
            "sources_used": []
        }


def render_network_graph(network_data: dict, disease_name: str):
    if not network_data:
        st.info("No network data available"); return
    nodes = network_data.get("nodes", [])
    edges = network_data.get("edges", [])
    stats = network_data.get("stats", {})
    if not nodes:
        st.info("No nodes to display"); return

    n1,n2,n3,n4 = st.columns(4)
    n1.metric("🔵 Total Nodes", stats.get("total_nodes",0))
    n2.metric("🧬 Proteins",    stats.get("proteins",0))
    n3.metric("💊 Drugs",       stats.get("drugs",0))
    n4.metric("🔮 Pathways",    stats.get("pathways",0))

    st.markdown("<div style='display:flex;gap:16px;flex-wrap:wrap;margin:8px 0 16px 0;'>" +
        "".join([f"<span style='display:flex;align-items:center;gap:6px;font-size:12px;color:#94a3b8;'><span style='width:12px;height:12px;border-radius:50%;background:{item['color']};display:inline-block;'></span>{item['label']}</span>"
        for item in [{"color":"#ef4444","label":"Disease"},{"color":"#3b82f6","label":"Protein"},{"color":"#10b981","label":"Drug (Low Risk)"},{"color":"#f59e0b","label":"Drug (Med Risk)"},{"color":"#8b5cf6","label":"Pathway"}]])
        + "</div>", unsafe_allow_html=True)

    nodes_json = json.dumps(nodes)
    edges_json = json.dumps(edges)
    html_content = f"""<!DOCTYPE html><html><head>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.js"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.css" rel="stylesheet">
        <style>body{{margin:0;padding:0;background-color:#0e1117;}} #network{{width:100%;height:520px;background-color:#0e1117;border:1px solid #1e293b;border-radius:10px;}}</style>
        </head><body><div id="network"></div>
        <script>
        var nodes=new vis.DataSet({nodes_json});
        var edges=new vis.DataSet({edges_json});
        var options={{nodes:{{shape:'dot',borderWidth:2,shadow:true,font:{{face:'monospace',size:13}}}},
            edges:{{smooth:{{type:'continuous',roundness:0.3}},font:{{size:10,color:'#64748b',align:'middle'}},shadow:false}},
            physics:{{enabled:true,forceAtlas2Based:{{gravitationalConstant:-50,centralGravity:0.01,springLength:120,springConstant:0.08,damping:0.4}},
            solver:'forceAtlas2Based',stabilization:{{enabled:true,iterations:200,fit:true}}}},
            interaction:{{hover:true,tooltipDelay:100,navigationButtons:true,keyboard:true}},layout:{{improvedLayout:true}}}};
        var network=new vis.Network(document.getElementById('network'),{{nodes:nodes,edges:edges}},options);
        network.once('stabilizationIterationsDone',function(){{network.fit({{animation:{{duration:500,easingFunction:'easeInOutQuad'}}}});}});
        </script></body></html>"""

    import streamlit.components.v1 as components
    components.html(html_content, height=560, scrolling=False)
    st.caption("💡 Click nodes to see details | Scroll to zoom | Drag to pan")


def render_updates_panel(disease_name: str):
    try:
        r = requests.get(f"{API_BASE_URL}/latest-updates", params={"disease": disease_name}, timeout=10)
        if r.status_code != 200:
            return
        data    = r.json()
        updates = data.get("updates", {})
        stats   = data.get("stats", {})
        papers  = updates.get(disease_name, [])
        if not papers:
            st.info(f"📡 No recent updates found for {disease_name}.")
            return
        last_check = stats.get('last_check','Never')
        last_check_str = last_check[:19] if last_check else 'Pending'
        st.markdown(f"<div style='background:#0f1b2d;border:1px solid #1e3a5f;border-radius:10px;padding:14px 18px;margin-bottom:12px;'><div style='color:#60a5fa;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;'>📡 Live Feed</div><div style='color:#e2e8f0;font-size:13px;margin-top:4px;'>{len(papers)} recent papers | Last check: {last_check_str}</div></div>", unsafe_allow_html=True)
        for paper in papers[:5]:
            is_new = paper.get("is_new", False)
            new_badge = "<span style='background:#22c55e;color:white;padding:1px 8px;border-radius:10px;font-size:10px;font-weight:700;margin-left:8px;'>NEW</span>" if is_new else ""
            st.markdown(f"<div style='background:#0f172a;border-left:3px solid #3b82f6;border-radius:0 8px 8px 0;padding:10px 14px;margin:6px 0;'><div style='font-size:13px;color:#e2e8f0;font-weight:500;'>{paper.get('title','')}{new_badge}</div><div style='font-size:11px;color:#64748b;margin-top:4px;'>📅 {paper.get('year','?')} | PubMed ID: {paper.get('pmid','')}</div></div>", unsafe_allow_html=True)
            if paper.get("url"):
                st.markdown(f"[🔗 Read paper]({paper['url']})")
    except Exception as e:
        st.caption(f"Updates unavailable: {str(e)}")


def render_comparison_table(data: dict):
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
                    drug_risk = d.get("risk_level","Unknown"); break
        ca         = hyp.get("causal_analysis") or {}
        causal_lbl = ca.get("causal_label","")
        causal_col = ca.get("causal_color","#64748b")
        medals     = {1:"🥇",2:"🥈",3:"🥉"}
        risk_ems   = {"High":"🔴","Medium":"🟡","Low":"🟢","Unknown":"⚪"}
        table_rows.append({"rank":rank,"medal":medals.get(rank,f"#{rank}"),"title":hyp["title"],
            "proteins":", ".join(hyp.get("key_proteins") or []),"drugs":", ".join(hyp.get("key_drugs") or []),
            "final":display,"color":confidence_color(display),"risk":drug_risk,"risk_emoji":risk_ems.get(drug_risk,"⚪"),
            "causal_label":causal_lbl,"causal_color":causal_col,"hyp_rank":rank})

    h1,h2,h3,h4,h5,h6,h7,h8,h9 = st.columns([0.5,2.5,1.0,1.0,0.8,1.0,0.8,1.0,1.0])
    for col,lbl in zip([h1,h2,h3,h4,h5,h6,h7,h8,h9],["Rank","Hypothesis","Proteins","Drugs","Score","Causal","Risk","Uncertainty","Decision"]):
        col.markdown(f"<div style='color:#64748b;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;'>{lbl}</div>", unsafe_allow_html=True)
    st.markdown("<hr style='border:none;border-top:1px solid #1e293b;margin:4px 0;'>", unsafe_allow_html=True)

    for row in table_rows:
        c1,c2,c3,c4,c5,c6,c7,c8,c9 = st.columns([0.5,2.5,1.0,1.0,0.8,1.0,0.8,1.0,1.0])
        with c1: st.markdown(f"<div style='font-size:22px;text-align:center;padding-top:6px;'>{row['medal']}</div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div style='font-size:13px;color:#e2e8f0;padding:6px 0;line-height:1.4;'>{row['title']}</div>", unsafe_allow_html=True)
        with c3:
            if row["proteins"]:
                st.markdown(" ".join([f"<span style='background:#1e3a5f;color:#60a5fa;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;margin:2px;display:inline-block;'>{p}</span>" for p in row["proteins"].split(", ")]), unsafe_allow_html=True)
        with c4:
            if row["drugs"]:
                st.markdown(" ".join([f"<span style='background:#1e3a2f;color:#34d399;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;margin:2px;display:inline-block;'>{d}</span>" for d in row["drugs"].split(", ")]), unsafe_allow_html=True)
            else:
                st.markdown("<span style='color:#475569;font-size:11px;'>—</span>", unsafe_allow_html=True)
        with c5:
            pct = row["final"]; color = row["color"]; bar_w = int(pct*60)
            st.markdown(f"<div style='padding-top:4px;'><div style='color:{color};font-weight:700;font-size:15px;'>{pct:.0%}</div><div style='background:#1e293b;border-radius:4px;height:4px;width:60px;margin-top:2px;'><div style='background:{color};height:4px;border-radius:4px;width:{bar_w}px;'></div></div></div>", unsafe_allow_html=True)
        with c6:
            if row["causal_label"]:
                cc = row["causal_color"]
                ca_em = "✅" if row["causal_label"] == "Likely Causal" else "⚠️" if row["causal_label"] == "Possibly Causal" else "ℹ️"
                st.markdown(f"<div style='background:{cc}22;color:{cc};padding:4px 8px;border-radius:8px;font-size:11px;font-weight:600;text-align:center;margin-top:4px;'>{ca_em} {row['causal_label']}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<span style='color:#475569;font-size:11px;'>—</span>", unsafe_allow_html=True)
        with c7:
            fg,bg = {"High":("#ef4444","#2d0a0a"),"Medium":("#f59e0b","#2d1f02"),"Low":("#22c55e","#052e16"),"Unknown":("#64748b","#1a1f2e")}.get(row["risk"],("#64748b","#1a1f2e"))
            st.markdown(f"<div style='background:{bg};color:{fg};padding:4px 10px;border-radius:8px;font-size:12px;font-weight:600;text-align:center;margin-top:4px;'>{row['risk_emoji']} {row['risk']}</div>", unsafe_allow_html=True)
        with c8:
            unc = {}
            for hyp_data in data["hypotheses"]:
                if hyp_data.get("rank") == row["rank"]:
                    unc = hyp_data.get("uncertainty") or {}; break
            if unc:
                u_label = unc.get("uncertainty_label",""); u_color = unc.get("uncertainty_color","#64748b")
                u_emoji = {"Low":"✅","Medium":"⚠️","High":"🔶","Very High":"❌"}.get(u_label,"❓")
                st.markdown(f"<div style='background:{u_color}22;color:{u_color};padding:4px 8px;border-radius:8px;font-size:11px;font-weight:600;text-align:center;margin-top:4px;'>{u_emoji} {u_label}</div>", unsafe_allow_html=True)
        with c9:
            gng = {}
            for hyp_data in data["hypotheses"]:
                if hyp_data.get("rank") == row["rank"]:
                    gng = hyp_data.get("go_no_go") or {}; break
            if gng:
                g_dec = gng.get("decision",""); g_color = gng.get("decision_color","#64748b"); g_emoji = gng.get("decision_emoji","❓")
                st.markdown(f"<div style='background:{g_color}22;color:{g_color};border:1px solid {g_color}55;padding:4px 8px;border-radius:8px;font-size:12px;font-weight:800;text-align:center;margin-top:4px;letter-spacing:1px;'>{g_emoji} {g_dec}</div>", unsafe_allow_html=True)
        st.markdown("<hr style='border:none;border-top:1px solid #0f172a;margin:2px 0;'>", unsafe_allow_html=True)
    st.caption("💡 Score = 0.4×protein + 0.3×drug_phase + 0.2×papers − 0.1×fda_risk")


def render_hypothesis_card(hyp: dict, data: dict, expanded: bool = False):
    rank    = int(hyp.get("rank") or 0) or 1
    final   = float(hyp.get("final_score") or 0.0)
    score   = float(hyp.get("confidence_score") or 0.0)
    p_score = float(hyp.get("protein_score") or 0.0)
    d_score = float(hyp.get("drug_score") or 0.0)
    pa_score= float(hyp.get("paper_score") or 0.0)
    r_pen   = float(hyp.get("risk_penalty") or 0.0)
    display = final if final > 0 else score
    medal   = {1:"🥇",2:"🥈",3:"🥉"}.get(rank,f"#{rank}")
    ca      = hyp.get("causal_analysis") or {}
    causal_lbl = ca.get("causal_label","")
    causal_tag = f" | {causal_lbl}" if causal_lbl else ""

    with st.expander(f"{medal} Rank {rank} | Score: {display:.0%}{causal_tag} | {hyp['title']}", expanded=expanded):
        gng = hyp.get("go_no_go") or {}
        if gng:
            render_go_no_go_badge(gng, size="large")
            st.markdown("---")

        st.markdown("**📊 Ranking Score Breakdown**")
        bc1,bc2,bc3,bc4,bc5 = st.columns(5)
        bc1.metric("🧬 Protein",    f"{p_score:.2f}", help="OpenTargets association (×0.4)")
        bc2.metric("💊 Drug Phase", f"{d_score:.2f}", help="Clinical trial phase (×0.3)")
        bc3.metric("📚 Papers",     f"{pa_score:.2f}", help="Paper support (×0.2)")
        bc4.metric("⚠️ Risk",       f"-{r_pen:.2f}", help="FDA penalty (×0.1)")
        bc5.metric("🎯 Final",      f"{final:.2%}" if final > 0 else f"{score:.2%}", help="Weighted composite score")
        if hyp.get("score_breakdown"):
            st.caption(f"📐 {hyp['score_breakdown']}")
        st.markdown("---")

        st.markdown("**LLM Confidence**")
        render_confidence_bar(score, hyp.get("confidence_label",""))

        ct1, ct2 = st.columns(2)
        with ct1:
            st.markdown("**🧬 Key Proteins**")
            proteins = hyp.get("key_proteins") or []
            if proteins:
                st.markdown(" ".join([f"<span class='protein-badge'>{p}</span>" for p in proteins]), unsafe_allow_html=True)
            else:
                st.caption("None tagged")
        with ct2:
            st.markdown("**💊 Key Drugs**")
            drugs = hyp.get("key_drugs") or []
            if drugs:
                st.markdown(" ".join([f"<span class='drug-badge'>{d}</span>" for d in drugs]), unsafe_allow_html=True)
            else:
                st.caption("None tagged")
        st.markdown("---")

        cs, ce = st.columns(2)
        with cs:
            st.markdown("**🔬 Scientific Explanation**")
            st.markdown(f"<div style='background:#0f172a;padding:14px;border-radius:8px;font-size:14px;line-height:1.7;color:#cbd5e1;'>{hyp.get('explanation','')}</div>", unsafe_allow_html=True)
        with ce:
            st.markdown("**🧒 Simple Explanation**")
            st.markdown(f"<div style='background:#0f172a;padding:14px;border-radius:8px;font-size:14px;line-height:1.7;color:#cbd5e1;'>{hyp.get('simple_explanation','')}</div>", unsafe_allow_html=True)

        if hyp.get("evidence_summary"):
            st.info(f"📌 {hyp['evidence_summary']}")

        steps = hyp.get("reasoning_steps") or []
        if steps:
            st.markdown("**🔗 Reasoning Chain**")
            for step in steps:
                st.markdown(f"<div style='background:#0f172a;border-left:3px solid #6366f1;padding:8px 14px;margin:4px 0;border-radius:0 6px 6px 0;font-size:13px;color:#c4b5fd;'>{step}</div>", unsafe_allow_html=True)

        render_causal_analysis(hyp.get("causal_analysis") or {})

        vs = hyp.get("validation_suggestion") or {}
        if vs:
            render_validation_suggestion(vs)

        cr = hyp.get("critique") or {}
        if cr:
            render_hypothesis_critique(cr)

        fp = hyp.get("failure_prediction") or {}
        if fp:
            render_failure_prediction(fp)

        tti = hyp.get("time_to_impact") or {}
        if tti:
            render_time_to_impact(tti)

        es = hyp.get("executive_summary") or {}
        if es:
            render_executive_summary(es)

        unc = hyp.get("uncertainty") or {}
        if unc:
            render_uncertainty_indicator(unc, compact=False)


def render_results(data: dict, max_targets: int, max_papers: int, max_drugs: int):
    """
    ── MASTER RENDER FUNCTION ──
    Renders ALL analysis results. Called for both fresh analyses
    and when restoring from session state (e.g. after PDF button click).
    This prevents the page-reset bug.
    """
    result = st.session_state.get("last_result") or {}

    st.success(f"✅ Analysis complete for **{data['disease_name']}** — {result.get('message','')}")

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
        bg_map   = {"green":("#052e16","#22c55e"),"yellow":("#1c1a02","#eab308"),"red":("#2d0a0a","#ef4444")}
        em_map   = {"green":"🟢","yellow":"🟡","red":"🔴"}
        bg,fg    = bg_map.get(ev_color, bg_map["yellow"])
        ev_em    = em_map.get(ev_color,"🟡")
        st.markdown(
            f"<div style='background:{bg};border:1px solid {fg}55;border-radius:10px;padding:14px 20px;margin:10px 0;'>"
            f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
            f"<div><div style='font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;'>Evidence Strength</div>"
            f"<div style='margin-top:2px;'><span style='font-size:20px;font-weight:800;color:{fg};'>{ev_em} {ev_label}</span>"
            f"<span style='color:#64748b;font-size:13px;margin-left:10px;'>Score: {ev_score:.2f}/1.00</span></div></div>"
            f"<div style='color:#64748b;font-size:12px;text-align:right;'>📄 {ev.get('total_papers',0)} papers | ⭐ {ev.get('high_citation_papers',0)} cited | 🕐 {ev.get('recent_papers',0)} recent</div></div>"
            f"<div style='margin-top:6px;font-size:11px;color:#475569;'>📐 {ev_bd}</div></div>",
            unsafe_allow_html=True)

    # Uncertainty banner
    au = data.get("analysis_uncertainty") or {}
    if au:
        au_score = float(au.get("uncertainty_score") or 0)
        au_label = str(au.get("uncertainty_label") or "Unknown")
        au_color = str(au.get("uncertainty_color") or "#64748b")
        au_reason= str(au.get("uncertainty_reason") or "")
        au_emoji = {"Low":"✅","Medium":"⚠️","High":"🔶","Very High":"❌"}.get(au_label,"❓")
        flag_items = []
        for key, lbl in [("low_paper_count","Low Paper Count"),("weak_protein_assoc","Weak Protein Assoc."),
                          ("high_fda_risk","High FDA Risk"),("no_causal_evidence","No Causal Evidence"),("limited_drug_data","Limited Drug Data")]:
            if au.get(key):
                flag_items.append(f"<span style='background:#2d1a1a;color:#f87171;padding:2px 8px;border-radius:8px;font-size:11px;margin:2px;display:inline-block;'>⚠️ {lbl}</span>")
        flags_html = "".join(flag_items) if flag_items else "<span style='color:#22c55e;font-size:11px;'>✅ No critical uncertainty flags</span>"
        st.markdown(
            f"<div style='background:{au_color}0d;border:1px solid {au_color}44;border-radius:10px;padding:14px 20px;margin:8px 0;'>"
            f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;'>"
            f"<div><span style='font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;'>Analysis Reliability</span>"
            f"<div style='margin-top:3px;'><span style='font-size:18px;font-weight:800;color:{au_color};'>{au_emoji} {au_label} Uncertainty</span>"
            f"<span style='color:#64748b;font-size:13px;margin-left:10px;'>Score: {au_score:.2f}/1.00</span></div></div></div>"
            f"<div style='font-size:12px;color:#94a3b8;margin-bottom:8px;'>{au_reason}</div>"
            f"<div>{flags_html}</div></div>",
            unsafe_allow_html=True)

    st.divider()

    # Decision Summary Panel
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
        risk_emoji = {"High":"🔴","Medium":"🟡","Low":"🟢","Unknown":"⚪"}.get(risk,"⚪")
        risk_col   = {"High":"#ef4444","Medium":"#f59e0b","Low":"#22c55e","Unknown":"#64748b"}.get(risk,"#64748b")

        st.markdown("<div style='font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:2px;font-weight:700;margin-bottom:8px;'>🎯 V4 DECISION INTELLIGENCE</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div style='background:linear-gradient(135deg,#0f1b2d,#1a2744);border:1px solid #2d4a7a;border-radius:12px;padding:16px 20px;margin-bottom:12px;'>"
            f"<div style='font-size:11px;color:#60a5fa;text-transform:uppercase;letter-spacing:2px;font-weight:700;margin-bottom:6px;'>✅ Best Recommendation for {data['disease_name']}</div>"
            f"<div style='font-size:15px;color:#e2e8f0;font-weight:500;line-height:1.5;'>{best_hyp}</div></div>",
            unsafe_allow_html=True)

        k1,k2,k3,k4 = st.columns(4)
        with k1: st.markdown(f"<div style='background:#0a1628;border:1px solid #1e3a5f;border-radius:10px;padding:16px;text-align:center;'><div style='font-size:11px;color:#60a5fa;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;'>💊 Recommended Drug</div><div style='font-size:22px;font-weight:800;color:#60a5fa;'>{drug}</div></div>", unsafe_allow_html=True)
        with k2: st.markdown(f"<div style='background:#0a1628;border:1px solid #2d1f5e;border-radius:10px;padding:16px;text-align:center;'><div style='font-size:11px;color:#a78bfa;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;'>🧬 Target Protein</div><div style='font-size:22px;font-weight:800;color:#a78bfa;'>{protein}</div></div>", unsafe_allow_html=True)
        with k3: st.markdown(f"<div style='background:#0a1628;border:1px solid #1e3a1e;border-radius:10px;padding:16px;text-align:center;'><div style='font-size:11px;color:{conf_color};text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;'>📊 Confidence</div><div style='font-size:22px;font-weight:800;color:{conf_color};'>{conf_emoji} {conf:.0%}</div><div style='font-size:11px;color:#64748b;margin-top:4px;'>{conf_label}</div></div>", unsafe_allow_html=True)
        with k4: st.markdown(f"<div style='background:#0a1628;border:1px solid #3a2000;border-radius:10px;padding:16px;text-align:center;'><div style='font-size:11px;color:{risk_col};text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;'>⚠️ Risk Level</div><div style='font-size:22px;font-weight:800;color:{risk_col};'>{risk_emoji} {risk}</div></div>", unsafe_allow_html=True)

        gng = ds.get("go_no_go") or {}
        if gng:
            render_go_no_go_badge(gng, size="large")
        st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
        st.markdown(f"<span style='background:#1e3a5f;color:#93c5fd;padding:5px 14px;border-radius:20px;font-size:12px;font-weight:600;'>🔬 Pathway: {pathway}</span>", unsafe_allow_html=True)
        st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='background:#070e1a;border-radius:8px;padding:14px;margin-bottom:10px;border-left:3px solid #3b82f6;'><div style='font-size:11px;color:#60a5fa;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;'>🧠 Scientific Reasoning</div><div style='font-size:13px;color:#cbd5e1;line-height:1.7;'>{reasoning}</div></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='background:#0f1f0f;border:1px solid #166534;border-radius:10px;padding:14px;margin-bottom:8px;'><div style='font-size:11px;color:#4ade80;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;'>🚀 Suggested Next Action</div><div style='font-size:14px;color:#bbf7d0;line-height:1.7;'>{action}</div></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='background:#111827;border-radius:8px;padding:10px 14px;margin-bottom:4px;'><span style='font-size:11px;color:#475569;'>📐 Evidence basis: {evidence_b}</span></div>", unsafe_allow_html=True)
        st.divider()

    # ── PDF Export Section ─────────────────────────────────────
    st.markdown("### 📥 Export Report")
    col_dl1, col_dl2, col_dl3 = st.columns([1, 2, 1])
    with col_dl2:
        if st.button("📄 Generate PDF Report", type="primary", use_container_width=True, key="gen_pdf"):
            with st.spinner("📄 Generating PDF report..."):
                try:
                    pdf_response = requests.post(
                        f"{API_BASE_URL}/generate-pdf-report",
                        json={"disease_name": data["disease_name"],
                              "max_targets": max_targets,
                              "max_papers":  max_papers,
                              "max_drugs":   max_drugs},
                        timeout=120
                    )
                    if pdf_response.status_code == 200:
                        st.session_state["pdf_bytes"]   = pdf_response.content
                        st.session_state["pdf_filename"] = f"AI_Scientist_{data['disease_name'].replace(' ','_')}.pdf"
                        st.session_state["pdf_disease"]  = data["disease_name"]
                        st.success(f"✅ Report ready! ({len(pdf_response.content)//1024}KB)")
                    else:
                        st.error(f"Failed to generate PDF (status {pdf_response.status_code})")
                except Exception as e:
                    st.error(f"PDF error: {e}")

        # Always show download button if PDF exists for this disease
        if (st.session_state.get("pdf_bytes") and
                st.session_state.get("pdf_disease") == data.get("disease_name")):
            st.download_button(
                label            = "⬇️ Download PDF Report",
                data             = st.session_state["pdf_bytes"],
                file_name        = st.session_state["pdf_filename"],
                mime             = "application/pdf",
                key              = "dl_pdf",
                use_container_width=True
            )
    st.divider()

    # ── Tabs ──────────────────────────────────────────────────
    tab1,tab2,tab3,tab4,tab5,tab6,tab7,tab8,tab9,tab10 = st.tabs([
        "💡 Hypotheses","🧬 Proteins & Evidence","💊 Drugs",
        "⚠️ Risk Analysis","🕸️ Network","📡 Live Updates",
        "📄 Literature Review","🤖 Ask AI","🔥 Trends","🔁 Repurpose"
    ])

    with tab1:
        # Decision Dashboard
        if data.get("hypotheses"):
            st.markdown("### 🎯 Decision Dashboard")
            dash_cols = st.columns(len(data["hypotheses"]))
            for i, hyp in enumerate(data["hypotheses"]):
                with dash_cols[i]:
                    rank   = int(hyp.get("rank",i+1))
                    final  = float(hyp.get("final_score",0))
                    gng    = hyp.get("go_no_go") or {}
                    tti    = hyp.get("time_to_impact") or {}
                    fp     = hyp.get("failure_prediction") or {}
                    medal  = {1:"🥇",2:"🥈",3:"🥉"}.get(rank,f"#{rank}")
                    g_dec  = gng.get("decision","")
                    g_col  = gng.get("decision_color","#64748b")
                    g_em   = gng.get("decision_emoji","❓")
                    sp_col = confidence_color(final)
                    drug_names = ", ".join(hyp.get("key_drugs",[]) or ["—"])
                    fp_sp  = float(fp.get("success_probability",0))
                    yr_rng = tti.get("years_range","?")
                    st.markdown(
                        f"<div style='background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:16px;text-align:center;'>"
                        f"<div style='font-size:28px;'>{medal}</div>"
                        f"<div style='color:{sp_col};font-weight:800;font-size:24px;margin:4px 0;'>{final:.0%}</div>"
                        f"<div style='color:{g_col};font-weight:700;font-size:16px;margin-bottom:8px;'>{g_em} {g_dec}</div>"
                        f"<div style='color:#94a3b8;font-size:11px;margin-bottom:6px;'>{drug_names}</div>"
                        f"<div style='background:{g_col}22;border-radius:6px;padding:4px;font-size:11px;color:{g_col};'>⏱️ {yr_rng} | 🎯 {fp_sp:.0%} success</div></div>",
                        unsafe_allow_html=True)
            st.divider()

        st.markdown("### 📊 Hypothesis Comparison")
        render_comparison_table(data)
        st.divider()
        st.markdown("### 🔬 Detailed Analysis")
        for hyp in data["hypotheses"]:
            render_hypothesis_card(hyp, data, expanded=(hyp.get("rank")==1))

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
            with col1: st.markdown(f"<div style='background:#1e3a5f;color:#60a5fa;padding:10px;border-radius:8px;text-align:center;font-weight:700;font-size:18px;'>{target['gene_symbol']}</div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"**{target['protein_name']}**")
                st.caption(target["function_description"][:150]+"...")
            with col3: st.markdown(f"<div style='text-align:center;'><div style='color:{a_col};font-size:20px;font-weight:700;'>{assoc:.2f}</div><div style='color:#64748b;font-size:10px;'>Disease Assoc.</div></div>", unsafe_allow_html=True)
            with col4: st.markdown(f"<div style='text-align:center;background:#0f172a;border-radius:8px;padding:8px;'><div style='color:{af_col};font-size:18px;font-weight:700;'>{plddt:.2f}</div><div style='color:{af_col};font-size:10px;font-weight:600;'>{af_lbl}</div><div style='color:#475569;font-size:9px;'>AlphaFold pLDDT</div></div>", unsafe_allow_html=True)
            st.divider()

        st.markdown("### 📚 Research Papers")
        for paper in data["papers"]:
            src_col = "#3b82f6" if paper["source"]=="PubMed" else "#8b5cf6"
            col1,col2 = st.columns([5,1])
            with col1:
                st.markdown(f"**{paper['title']}**")
                s = paper.get("summary",""); a = paper.get("abstract","")
                if s and s != "No summary available": st.caption(s[:200])
                elif a and a != "No abstract available": st.caption(a[:200]+"...")
            with col2:
                st.markdown(f"<div style='text-align:center;'><span style='background:{src_col}22;color:{src_col};padding:3px 8px;border-radius:10px;font-size:11px;'>{paper['source']}</span><br><br><span style='color:#94a3b8;font-size:12px;'>{paper.get('year') or 'N/A'}</span></div>", unsafe_allow_html=True)
                if paper.get("url"): st.markdown(f"[🔗 View]({paper['url']})")
            st.divider()

    with tab3:
        st.markdown("### 💊 Drug-Protein Associations")
        for drug in data["drugs"]:
            phase    = drug.get("clinical_phase") or "N/A"
            fda_data = drug.get("fda_adverse_events") or []
            risk     = drug.get("risk_level","Unknown")
            risk_desc= drug.get("risk_description","")
            r_bg,r_fg,r_em = {"High":("#2d0a0a","#ef4444","🔴"),"Medium":("#2d1f02","#f59e0b","🟡"),"Low":("#052e16","#22c55e","🟢"),"Unknown":("#1a1f2e","#64748b","⚪")}.get(risk,("#1a1f2e","#64748b","⚪"))
            col1,col2,col3,col4,col5 = st.columns([2,2.5,2,2,2])
            with col1:
                st.markdown(f"**💊 {drug['drug_name']}**"); st.caption(f"Type: {drug['drug_type']}")
                st.markdown(f"<span style='background:#134e3a;color:#34d399;padding:3px 10px;border-radius:12px;font-size:12px;'>Phase {phase}</span>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"**Target:** `{drug['target_gene']}`"); st.caption(f"Mechanism: {drug['mechanism'][:100]}")
            with col3:
                if fda_data:
                    top = fda_data[0]; st.markdown("**⚠️ Top FDA Signal**")
                    st.markdown(f"<div style='background:#2d1b1b;color:#f87171;padding:8px 12px;border-radius:8px;font-size:13px;'>🚨 {top['reaction']}<br><span style='color:#94a3b8;'>{top['count']:,} reports</span></div>", unsafe_allow_html=True)
                else: st.caption("No FDA signals found")
            with col4:
                st.markdown("**🛡️ Risk Level**")
                st.markdown(f"<div style='background:{r_bg};border:1px solid {r_fg}55;border-radius:8px;padding:8px 12px;'><div style='color:{r_fg};font-weight:700;font-size:15px;'>{r_em} {risk}</div><div style='color:#94a3b8;font-size:11px;margin-top:4px;'>{risk_desc[:80]}...</div></div>", unsafe_allow_html=True)
            with col5:
                comp = drug.get("competition_intel") or {}
                if comp:
                    st.markdown("**🏁 Competition**"); render_competition_badge(drug, compact=True)
                    n_sim = comp.get("num_similar_drugs",0); opp = comp.get("market_opportunity","")
                    opp_c = {"Strong":"#22c55e","Moderate":"#f59e0b","Crowded":"#ef4444"}.get(opp,"#64748b")
                    st.markdown(f"<div style='font-size:11px;color:#64748b;margin-top:4px;'>{n_sim} similar drugs</div><div style='color:{opp_c};font-size:11px;font-weight:600;'>{opp} opportunity</div>", unsafe_allow_html=True)
            st.divider()

    with tab4:
        st.markdown("### ⚠️ FDA Risk Intelligence Summary")
        risk_counts = {"High":0,"Medium":0,"Low":0,"Unknown":0}
        for drug in data["drugs"]:
            lvl = drug.get("risk_level","Unknown"); risk_counts[lvl] = risk_counts.get(lvl,0)+1
        r1,r2,r3,r4 = st.columns(4)
        r1.metric("🔴 High Risk",risk_counts["High"]); r2.metric("🟡 Medium Risk",risk_counts["Medium"])
        r3.metric("🟢 Low Risk",risk_counts["Low"]); r4.metric("⚪ Unknown",risk_counts["Unknown"])
        st.divider()
        st.markdown("### 📋 Drug Risk Details")
        for drug in data["drugs"]:
            risk = drug.get("risk_level","Unknown"); risk_desc = drug.get("risk_description",""); fda_data = drug.get("fda_adverse_events") or []
            r_bg,r_fg,r_em = {"High":("#2d0a0a","#ef4444","🔴"),"Medium":("#2d1f02","#f59e0b","🟡"),"Low":("#052e16","#22c55e","🟢"),"Unknown":("#1a1f2e","#64748b","⚪")}.get(risk,("#1a1f2e","#64748b","⚪"))
            with st.expander(f"{r_em} {drug['drug_name']} — {risk} Risk (Phase {drug.get('clinical_phase','N/A')}, Target: {drug['target_gene']})"):
                st.markdown(f"<div style='background:{r_bg};border-left:4px solid {r_fg};padding:12px 16px;border-radius:0 8px 8px 0;margin-bottom:12px;'><div style='color:{r_fg};font-weight:700;font-size:16px;'>{r_em} {risk} Risk</div><div style='color:#94a3b8;margin-top:4px;'>{risk_desc}</div></div>", unsafe_allow_html=True)
                comp = drug.get("competition_intel") or {}
                if comp:
                    st.markdown("**🏁 Competitive Landscape**"); render_competition_badge(drug, compact=False); st.divider()
                if fda_data:
                    st.markdown("**Top FDA Adverse Events:**")
                    for ae in fda_data[:5]:
                        pct = min(ae['count']/300,1.0)
                        ca,cb = st.columns([3,1])
                        with ca: st.markdown(f"<div style='font-size:13px;color:#e2e8f0;'>{ae['reaction']}</div>", unsafe_allow_html=True); st.progress(pct)
                        with cb: st.markdown(f"<div style='text-align:right;color:#94a3b8;font-size:13px;padding-top:4px;'>{ae['count']:,} reports</div>", unsafe_allow_html=True)
                else: st.info("No adverse event data in FDA FAERS")

    with tab5:
        st.markdown("### 🕸️ Protein-Drug Interaction Network")
        st.caption("Interactive network showing proteins, drugs, pathways and their relationships")
        with st.spinner("Building interaction network..."):
            try:
                net_response = requests.post(f"{API_BASE_URL}/network-data",
                    json={"disease_name":data["disease_name"],"max_targets":max_targets,"max_papers":max_papers,"max_drugs":max_drugs}, timeout=60)
                if net_response.status_code == 200:
                    render_network_graph(net_response.json().get("network",{}), data["disease_name"])
                else:
                    st.error("Failed to load network data")
            except Exception as e:
                st.info("Building network from analysis data...")

    with tab6:
        st.markdown("### 📡 Real-Time Scientific Updates")
        st.caption(f"Latest PubMed papers for **{data['disease_name']}** — auto-checked daily")
        col_upd1, col_upd2 = st.columns([3, 1])
        with col_upd2:
            if st.button("🔄 Check Now", key="trigger_update"):
                with st.spinner("Checking PubMed..."):
                    try:
                        r = requests.post(f"{API_BASE_URL}/trigger-update", timeout=60)
                        resp = r.json()
                        st.success(f"✅ {resp.get('new_papers',0)} new papers found")
                    except Exception as e:
                        st.error(f"Update failed: {e}")
        with col_upd1:
            render_updates_panel(data["disease_name"])

        st.divider()
        st.markdown("### 🔭 Tracked Diseases")
        try:
            r   = requests.get(f"{API_BASE_URL}/latest-updates", timeout=5)
            upd = r.json(); tracked = upd.get("tracked_diseases",[]); stats = upd.get("stats",{})
            s1,s2,s3 = st.columns(3)
            s1.metric("🔬 Tracked Diseases",len(tracked)); s2.metric("📄 Total Updates",stats.get("total_updates",0)); s3.metric("🔄 Checks Run",stats.get("check_count",0))
            if tracked:
                for disease in tracked:
                    count = stats.get("updates_per_disease",{}).get(disease,0)
                    st.markdown(f"<div style='background:#0f172a;border:1px solid #1e293b;border-radius:8px;padding:10px 14px;margin:4px 0;display:flex;justify-content:space-between;align-items:center;'><span style='color:#e2e8f0;font-size:13px;'>🔬 {disease}</span><span style='background:#1e3a5f;color:#60a5fa;padding:2px 10px;border-radius:10px;font-size:11px;'>{count} updates</span></div>", unsafe_allow_html=True)
            st.markdown("**➕ Track a New Disease**")
            new_disease = st.text_input("Disease to track", placeholder="e.g. lung cancer", key="new_track_disease", label_visibility="collapsed")
            if st.button("Add to Watchlist", key="add_track"):
                if new_disease.strip():
                    try:
                        r = requests.post(f"{API_BASE_URL}/track-disease", json={"disease_name":new_disease.strip()}, timeout=30)
                        st.success(f"✅ {r.json().get('message','Added!')}")
                    except Exception as e:
                        st.error(f"Failed: {e}")
        except Exception as e:
            st.caption(f"Could not load tracked diseases: {e}")

        st.divider()
        st.markdown("### 🧠 Knowledge Graph Memory")
        st.caption("Accumulated intelligence from all past analyses")
        try:
            kg_r = requests.get(f"{API_BASE_URL}/knowledge-graph/insights", timeout=10)
            if kg_r.status_code == 200:
                kg = kg_r.json(); stats = kg.get("stats",{}); cross = kg.get("cross_disease_proteins",[]); drugs = kg.get("most_analyzed_drugs",[])
                kg1,kg2,kg3,kg4 = st.columns(4)
                kg1.metric("🔵 Total Nodes",stats.get("node_count",0)); kg2.metric("🔗 Total Edges",stats.get("edge_count",0))
                kg3.metric("🔬 Analyses Run",stats.get("total_analyses",0)); kg4.metric("🧬 Proteins Tracked",stats.get("total_proteins",0))
                if cross:
                    st.markdown("**🔁 Cross-Disease Proteins:**")
                    for p in cross[:5]:
                        diseases_str = ", ".join(p.get("diseases",[]))
                        st.markdown(f"<div style='background:#1e3a5f22;border-left:3px solid #60a5fa;padding:6px 12px;margin:3px 0;border-radius:0 6px 6px 0;'><span style='color:#60a5fa;font-weight:700;'>{p.get('gene_symbol','')}</span><span style='color:#64748b;font-size:12px;margin-left:10px;'>Found in: {diseases_str}</span></div>", unsafe_allow_html=True)
                if drugs:
                    st.markdown("**💊 Most Analyzed Drugs:**")
                    for d in drugs[:5]:
                        dname = d.get("drug_name",d.get("name",""))
                        st.markdown(f"<div style='background:#1e3a2f22;border-left:3px solid #34d399;padding:6px 12px;margin:3px 0;border-radius:0 6px 6px 0;'><span style='color:#34d399;font-weight:700;'>{dname}</span><span style='color:#64748b;font-size:12px;margin-left:10px;'>Phase {d.get('phase','?')} | {d.get('appearances',0)} appearances</span></div>", unsafe_allow_html=True)
                st.markdown("**🔍 Search Knowledge Graph**")
                kg_query = st.text_input("Search KG", placeholder="e.g. PSEN1, LECANEMAB", key="kg_search", label_visibility="collapsed")
                if kg_query:
                    sr = requests.get(f"{API_BASE_URL}/knowledge-graph/search", params={"query":kg_query}, timeout=5)
                    if sr.status_code == 200:
                        results = sr.json().get("results",{})
                        if results.get("proteins") or results.get("drugs"):
                            for node_dict in (results.get("proteins",[]) + results.get("drugs",[])):
                                for key, val in node_dict.items(): st.json(val)
                        else: st.caption(f"No results for '{kg_query}'")
        except Exception as e:
            st.caption(f"Knowledge graph unavailable: {e}")

    with tab7:
        st.markdown("### 📄 Auto-Generated Literature Review")
        st.caption(f"AI-generated research summary for **{data['disease_name']}** based on retrieved evidence")
        lr = data.get("literature_review") or {}
        if lr:
            gen_at = lr.get("generated_at","")
            if gen_at: st.caption(f"Generated: {gen_at}")
            sections = [("🔬 Background","background"),("📚 Current Research","current_research"),("🔍 Research Gaps","research_gaps"),("💡 Proposed Hypothesis","proposed_hypothesis"),("📊 Supporting Evidence","supporting_evidence"),("⚠️ Risks & Limitations","risks_limitations"),("✅ Conclusion","conclusion")]
            section_colors = ["#3b82f6","#8b5cf6","#f59e0b","#22c55e","#06b6d4","#ef4444","#22c55e"]
            for (title, key), color in zip(sections, section_colors):
                content = lr.get(key,"")
                if content:
                    st.markdown(f"<div style='background:#0f172a;border-left:4px solid {color};border-radius:0 8px 8px 0;padding:14px 16px;margin:8px 0;'><div style='color:{color};font-weight:700;font-size:13px;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;'>{title}</div><div style='color:#cbd5e1;font-size:14px;line-height:1.7;'>{content}</div></div>", unsafe_allow_html=True)
            if st.button("📥 Copy Full Report", key="copy_report"):
                report_text = f"LITERATURE REVIEW: {lr.get('disease_name','')}\nGenerated: {lr.get('generated_at','')}\n\n"
                for title, key in sections:
                    content = lr.get(key,"")
                    if content: report_text += f"{title}\n{content}\n\n"
                st.code(report_text, language="")
        else:
            st.info("Literature review will appear here after analysis.")

    with tab8:
        render_chat_tab(data)

    with tab9:
        render_trending_insights()
        
    with tab10:
        render_repurposing_mode()


# ════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🧬 AI Scientist")
    st.markdown("*V5 Decision Intelligence Platform*")
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
    st.markdown(f"[📖 API Docs]({API_BASE_URL}/docs) | [🔑 Get Keys]({API_BASE_URL}/api/v1/keys)")

    st.divider()
    st.markdown("### 🔥 Quick Trends")
    if st.button("View Emerging Opportunities", key="sidebar_trends"):
        st.session_state["show_trends"] = True

# ════════════════════════════════════════════════════════════
# HEADER
# ════════════════════════════════════════════════════════════
st.markdown("""
<div style='text-align:center; padding:20px 0 10px 0;'>
    <h1 style='font-size:2.8em; font-weight:800;
               background:linear-gradient(90deg,#60a5fa,#a78bfa,#34d399);
               -webkit-background-clip:text; -webkit-text-fill-color:transparent;'>
        🧬 AI Scientist
    </h1>
    <p style='color:#94a3b8; font-size:1.1em; margin-top:-10px;'>
        V5 Decision & Risk Intelligence Platform for Drug Discovery
    </p>
</div>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# SEARCH MODE
# ════════════════════════════════════════════════════════════
examples = get_example_diseases()
search_mode = st.radio("Mode", ["🔬 Single Disease","🔀 Multi-Disease Comparison"], horizontal=True, label_visibility="collapsed")

if search_mode == "🔬 Single Disease":
    st.markdown("### 🔍 Enter a Disease to Analyze")
    col_input, col_button = st.columns([4, 1])
    with col_input:
        disease_input = st.text_input("Disease", placeholder="e.g. Alzheimer disease, breast cancer...", label_visibility="collapsed")
    with col_button:
        analyze_clicked = st.button("🔬 Analyze", type="primary", use_container_width=True)
    st.markdown("**Quick select:**")
    q_cols = st.columns(len(examples[:4]))
    for i, d in enumerate(examples[:4]):
        with q_cols[i]:
            if st.button(d, key=f"qs_{i}", use_container_width=True):
                disease_input = d; analyze_clicked = True
    multi_diseases = []; compare_clicked = False
else:
    st.markdown("### 🔀 Multi-Disease Comparison")
    st.caption("Select 2-4 diseases to compare shared proteins, drugs, and repurposing opportunities")
    all_diseases = examples or ["Alzheimer disease","Parkinson disease","breast cancer","type 2 diabetes","rheumatoid arthritis","lung cancer"]
    multi_diseases = st.multiselect("Select diseases to compare (2-4):", options=all_diseases, default=all_diseases[:2], max_selections=4)
    compare_clicked = st.button(f"🔀 Compare {len(multi_diseases)} Diseases", type="primary", disabled=(len(multi_diseases)<2))
    disease_input = ""; analyze_clicked = False

st.divider()


# ════════════════════════════════════════════════════════════
# MULTI-DISEASE COMPARISON
# ════════════════════════════════════════════════════════════
if compare_clicked and len(multi_diseases) >= 2:
    with st.spinner(f"🔀 Comparing {len(multi_diseases)} diseases — ~{len(multi_diseases)*40}s..."):
        pb = st.progress(0); stat = st.empty()
        stat.markdown(f"🚀 Running parallel pipelines for: **{', '.join(multi_diseases)}**")
        pb.progress(20)
        cmp_result = call_compare_api(multi_diseases, max_targets, max_papers, max_drugs)
        pb.progress(100); pb.empty(); stat.empty()

    if "error" in cmp_result:
        st.error(f"❌ {cmp_result['error']}"); st.stop()

    cmp = cmp_result.get("comparison",{}); individ = cmp_result.get("individual",{}); diseases = cmp.get("diseases_analyzed",[])
    st.success(f"✅ Compared **{len(diseases)} diseases** in {cmp_result.get('elapsed','?')}s — {cmp.get('total_shared_proteins',0)} shared proteins, {cmp.get('total_shared_drugs',0)} shared drugs")

    sm1,sm2,sm3,sm4 = st.columns(4)
    sm1.metric("🔬 Diseases",len(diseases)); sm2.metric("🧬 Shared Proteins",cmp.get("total_shared_proteins",0))
    sm3.metric("💊 Shared Drugs",cmp.get("total_shared_drugs",0)); sm4.metric("🔁 Repurposing",len(cmp.get("repurposing_opportunities",[])))

    repurp = cmp.get("repurposing_opportunities",[])
    if repurp:
        st.markdown("### 💡 Drug Repurposing Opportunities")
        for opp in repurp:
            st.markdown(f"<div style='background:#0f1f0f;border:1px solid #166534;border-radius:8px;padding:12px 16px;margin:6px 0;'><span style='color:#4ade80;font-size:13px;'>🔁 {opp}</span></div>", unsafe_allow_html=True)

    st.divider(); st.markdown("### 💊 Drug Comparison Across Diseases")
    drug_rows = cmp.get("drug_comparison",[]); n_diseases = len(diseases)
    if drug_rows:
        header_cols = st.columns([2,1.5]+[1.5]*n_diseases+[1,1])
        for col,lbl in zip(header_cols, ["Drug","Target"]+[d[:12]+"..." for d in diseases]+["Avg","Overlap"]):
            col.markdown(f"<div style='color:#64748b;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;'>{lbl}</div>", unsafe_allow_html=True)
        st.markdown("<hr style='border:none;border-top:1px solid #1e293b;margin:4px 0;'>", unsafe_allow_html=True)
        for row in drug_rows[:10]:
            row_cols = st.columns([2,1.5]+[1.5]*n_diseases+[1,1])
            appears = row.get("appears_in",1); badge_col = "#22c55e" if appears >= 2 else "#60a5fa"
            with row_cols[0]: st.markdown(f"<div style='padding:4px 0;'><div style='color:#e2e8f0;font-weight:600;font-size:13px;'>{row['drug_name']}</div><span style='background:{badge_col}22;color:{badge_col};padding:1px 6px;border-radius:8px;font-size:10px;'>{'🔁 Multi-disease' if appears>=2 else '1 disease'}</span></div>", unsafe_allow_html=True)
            with row_cols[1]: st.markdown(f"<div style='color:#a78bfa;font-size:12px;padding-top:4px;font-weight:600;'>{row.get('target_protein','—')}</div>", unsafe_allow_html=True)
            disease_entries = {e["disease_name"]:e for e in row.get("diseases",[])}
            for i, d in enumerate(diseases):
                with row_cols[2+i]:
                    entry = disease_entries.get(d)
                    if entry and entry.get("final_score",0) > 0:
                        sc = entry["final_score"]; sc_col = confidence_color(sc); risk = entry.get("risk_level","Unknown")
                        r_em = {"High":"🔴","Medium":"🟡","Low":"🟢","Unknown":"⚪"}.get(risk,"⚪")
                        st.markdown(f"<div style='text-align:center;'><div style='color:{sc_col};font-weight:700;font-size:14px;'>{sc:.0%}</div><div style='font-size:10px;color:#64748b;'>{r_em} {risk}</div></div>", unsafe_allow_html=True)
                    else: st.markdown("<div style='text-align:center;color:#374151;font-size:18px;padding-top:4px;'>—</div>", unsafe_allow_html=True)
            with row_cols[-2]:
                avg = row.get("avg_score",0)
                if avg > 0: st.markdown(f"<div style='text-align:center;color:{confidence_color(avg)};font-weight:700;font-size:14px;padding-top:4px;'>{avg:.0%}</div>", unsafe_allow_html=True)
                else: st.markdown("<div style='text-align:center;color:#374151;'>—</div>", unsafe_allow_html=True)
            with row_cols[-1]:
                ov = row.get("overlap_score",0)
                st.markdown(f"<div style='text-align:center;color:{confidence_color(ov)};font-weight:700;font-size:14px;padding-top:4px;'>{ov:.0%}</div>", unsafe_allow_html=True)
            st.markdown("<hr style='border:none;border-top:1px solid #0f172a;margin:2px 0;'>", unsafe_allow_html=True)

    shared = cmp.get("shared_proteins",[])
    if shared:
        st.divider(); st.markdown("### 🧬 Shared Protein Targets")
        for sp in shared:
            avg_assoc = sp.get("avg_association",0); sp_color = confidence_color(avg_assoc); d_list = ", ".join(sp.get("diseases",[]))
            col1,col2,col3 = st.columns([1,4,1])
            with col1: st.markdown(f"<div style='background:#1e3a5f;color:#60a5fa;padding:10px;border-radius:8px;text-align:center;font-weight:700;font-size:18px;'>{sp['gene_symbol']}</div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"**{sp.get('protein_name','')}**"); st.caption(f"Found in: {d_list}")
                st.markdown(f"<span style='background:#22c55e22;color:#22c55e;padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600;'>🔁 Appears in {sp.get('appears_in',1)} diseases</span>", unsafe_allow_html=True)
            with col3: st.markdown(f"<div style='text-align:center;'><div style='color:{sp_color};font-size:20px;font-weight:700;'>{avg_assoc:.2f}</div><div style='color:#64748b;font-size:10px;'>Avg Assoc.</div></div>", unsafe_allow_html=True)
            st.divider()

    if individ:
        st.markdown("### 🎯 Individual Disease Recommendations")
        ind_cols = st.columns(len(individ))
        for i,(dname,ddata) in enumerate(individ.items()):
            with ind_cols[i]:
                ds = ddata.get("decision_summary") or {}; drug = ds.get("recommended_drug","—"); prot = ds.get("target_protein","—")
                conf = float(ds.get("confidence_score") or 0); risk = ds.get("risk_level","Unknown")
                risk_em = {"High":"🔴","Medium":"🟡","Low":"🟢","Unknown":"⚪"}.get(risk,"⚪"); conf_col = confidence_color(conf)
                st.markdown(f"<div style='background:#0f1b2d;border:1px solid #2d4a7a;border-radius:10px;padding:16px;'><div style='font-size:11px;color:#60a5fa;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;font-weight:700;'>🎯 {dname}</div><div style='color:#60a5fa;font-size:16px;font-weight:700;margin-bottom:4px;'>💊 {drug}</div><div style='color:#a78bfa;font-size:13px;margin-bottom:8px;'>🧬 {prot}</div><div style='color:{conf_col};font-weight:700;font-size:18px;'>{conf:.0%}</div><div style='color:#64748b;font-size:11px;'>confidence</div><div style='margin-top:8px;'><span style='font-size:13px;'>{risk_em} {risk} Risk</span></div></div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# SINGLE DISEASE — RUN ANALYSIS
# ════════════════════════════════════════════════════════════
elif analyze_clicked and disease_input.strip():
    # If new disease, clear PDF cache
    if st.session_state.get("last_disease") != disease_input.strip():
        st.session_state["pdf_bytes"]   = None
        st.session_state["pdf_filename"]= ""
        st.session_state["pdf_disease"] = ""
        st.session_state["last_disease"]= disease_input.strip()

    with st.spinner(f"🔬 Analyzing **{disease_input}** — ~60 seconds..."):
        pb = st.progress(0); stat = st.empty()
        stat.markdown("📡 **Stage 1/4** — Fetching protein targets...")
        pb.progress(10); time.sleep(0.3)
        stat.markdown("💊 **Stage 2/4** — Mapping drugs + FDA signals...")
        pb.progress(25)
        result = call_api(disease_input.strip(), max_targets, max_papers, max_drugs)
        pb.progress(75)
        stat.markdown("📚 **Stage 3/4** — Retrieving papers...")
        time.sleep(0.2); pb.progress(90)
        stat.markdown("🤖 **Stage 4/4** — Generating hypotheses...")
        time.sleep(0.2); pb.progress(100); stat.empty(); pb.empty()

    if "error" in result:
        st.error(f"❌ {result['error']}"); st.stop()
    if not result.get("success"):
        st.error(f"❌ {result.get('message','Unknown error')}"); st.stop()

    # ── Store in session state ────────────────────────────────
    st.session_state["last_analysis"] = result["data"]
    st.session_state["last_result"]   = result
    st.session_state["last_disease"]  = disease_input.strip()

    # ── Render results ────────────────────────────────────────
    render_results(result["data"], max_targets, max_papers, max_drugs)


# ════════════════════════════════════════════════════════════
# RESTORE PREVIOUS ANALYSIS (handles button clicks that rerun)
# ════════════════════════════════════════════════════════════
elif st.session_state.get("last_analysis"):
    render_results(st.session_state["last_analysis"], max_targets, max_papers, max_drugs)


# ════════════════════════════════════════════════════════════
# EMPTY STATE
# ════════════════════════════════════════════════════════════
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
                f"<div style='background:#1a1f2e;border:1px solid #2d3561;border-radius:10px;padding:16px;text-align:center;'>"
                f"<div style='font-size:28px;'>{emoji}</div>"
                f"<div style='color:#e2e8f0;font-weight:600;margin:8px 0;'>{name}</div>"
                f"<div style='color:#64748b;font-size:12px;'>{desc}</div></div>",
                unsafe_allow_html=True)
# frontend/app.py
# Purpose: Streamlit frontend for the AI Scientist platform.
# Calls the FastAPI backend and displays results in a clean UI.
#
# Run with: streamlit run frontend/app.py

import streamlit as st
import requests
import time

# ── Page Configuration ───────────────────────────────────────
st.set_page_config(
    page_title = "AI Scientist — Hypothesis Generator",
    page_icon  = "🧬",
    layout     = "wide",
    initial_sidebar_state = "expanded"
)

# ── Backend URL ──────────────────────────────────────────────
API_BASE_URL = "https://ai-scientist-api.onrender.com"

# ── Custom CSS ───────────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #0e1117; }

    /* Hypothesis card */
    .hypothesis-card {
        background: linear-gradient(135deg, #1a1f2e, #16213e);
        border: 1px solid #2d3561;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
    }

    /* Protein badge */
    .protein-badge {
        background-color: #1e3a5f;
        color: #60a5fa;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        margin-right: 6px;
        display: inline-block;
    }

    /* Drug badge */
    .drug-badge {
        background-color: #1e3a2f;
        color: #34d399;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        margin-right: 6px;
        display: inline-block;
    }

    /* Confidence bar wrapper */
    .confidence-wrapper {
        background-color: #1a1f2e;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 10px 0;
    }

    /* Section header */
    .section-header {
        color: #94a3b8;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 8px;
    }

    /* Evidence card */
    .evidence-card {
        background-color: #151b27;
        border-left: 3px solid #3b82f6;
        border-radius: 0 8px 8px 0;
        padding: 12px 16px;
        margin-bottom: 10px;
    }

    /* Drug row */
    .drug-row {
        background-color: #151b27;
        border-left: 3px solid #10b981;
        border-radius: 0 8px 8px 0;
        padding: 12px 16px;
        margin-bottom: 10px;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ── Helper Functions ─────────────────────────────────────────

def confidence_color(score: float) -> str:
    """Return color hex based on confidence score."""
    if score >= 0.8:   return "#22c55e"   # green
    elif score >= 0.6: return "#84cc16"   # lime
    elif score >= 0.4: return "#f59e0b"   # amber
    else:              return "#ef4444"   # red


def confidence_emoji(score: float) -> str:
    if score >= 0.8:   return "🟢"
    elif score >= 0.6: return "🟡"
    elif score >= 0.4: return "🟠"
    else:              return "🔴"


def render_confidence_bar(score: float, label: str):
    """Render a visual confidence bar using Streamlit progress."""
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


def call_api(disease_name: str, max_targets: int, max_papers: int, max_drugs: int) -> dict:
    """Call the FastAPI backend and return the response."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/analyze-disease",
            json={
                "disease_name": disease_name,
                "max_targets" : max_targets,
                "max_papers"  : max_papers,
                "max_drugs"   : max_drugs
            },
            timeout=180   # 3 min timeout for full pipeline
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to backend. Make sure the FastAPI server is running:\n`uvicorn backend.main:app --reload --port 8000`"}
    except requests.exceptions.Timeout:
        return {"error": "Request timed out. The pipeline takes ~60s — please try again."}
    except requests.exceptions.HTTPError as e:
        return {"error": f"API error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def get_example_diseases() -> list:
    """Fetch example diseases from API."""
    try:
        r = requests.get(f"{API_BASE_URL}/diseases/examples", timeout=5)
        return r.json().get("examples", [])
    except:
        return ["Alzheimer disease", "Parkinson disease", "breast cancer", "type 2 diabetes"]


# ── Sidebar ──────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🧬 AI Scientist")
    st.markdown("*Evidence-Based Hypothesis Generator*")
    st.divider()

    st.markdown("### ⚙️ Analysis Settings")

    max_targets = st.slider(
        "Protein Targets",
        min_value=3, max_value=10, value=5,
        help="Number of protein targets to fetch from OpenTargets"
    )
    max_drugs = st.slider(
        "Drugs per Protein",
        min_value=1, max_value=5, value=3,
        help="Maximum drugs to map per protein target"
    )
    max_papers = st.slider(
        "Research Papers",
        min_value=3, max_value=10, value=5,
        help="Number of papers to retrieve per source"
    )

    st.divider()
    st.markdown("### 📡 Data Sources")
    st.markdown("""
    - 🧬 **OpenTargets** — Protein targets
    - 💊 **FDA FAERS** — Adverse events
    - 📚 **PubMed** — Research papers
    - 📖 **Semantic Scholar** — Paper summaries
    - 🤖 **GPT-4o-mini** — Hypothesis generation
    """)

    st.divider()
    st.markdown("### ⚠️ Disclaimer")
    st.caption(
        "This tool generates AI-assisted research hypotheses for "
        "exploratory purposes only. Not for clinical use."
    )


# ── Main Page ────────────────────────────────────────────────

# Header
st.markdown("""
<div style='text-align:center; padding: 20px 0 10px 0;'>
    <h1 style='font-size:2.8em; font-weight:800; 
               background: linear-gradient(90deg, #60a5fa, #a78bfa, #34d399);
               -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
        🧬 AI Scientist
    </h1>
    <p style='color:#94a3b8; font-size:1.1em; margin-top:-10px;'>
        Evidence-Based Biomedical Hypothesis Generation Platform
    </p>
</div>
""", unsafe_allow_html=True)

# ── Search Box ───────────────────────────────────────────────
st.markdown("### 🔍 Enter a Disease to Analyze")

examples = get_example_diseases()

col_input, col_button = st.columns([4, 1])

with col_input:
    disease_input = st.text_input(
        label       = "Disease Name",
        placeholder = "e.g. Alzheimer disease, breast cancer, Parkinson disease...",
        label_visibility = "collapsed"
    )

with col_button:
    analyze_clicked = st.button("🔬 Analyze", type="primary", use_container_width=True)

# Quick-select example chips
st.markdown("**Quick select:**")
cols = st.columns(len(examples[:4]))
for i, disease in enumerate(examples[:4]):
    with cols[i]:
        if st.button(disease, key=f"ex_{i}", use_container_width=True):
            disease_input = disease
            analyze_clicked = True

st.divider()

# ── Run Analysis ─────────────────────────────────────────────
if analyze_clicked and disease_input.strip():

    with st.spinner(f"🔬 Analyzing **{disease_input}** — this takes ~60 seconds..."):

        # Show live progress steps
        progress_bar = st.progress(0)
        status_text  = st.empty()

        status_text.markdown("📡 **Stage 1/4** — Fetching protein targets from OpenTargets...")
        progress_bar.progress(10)
        time.sleep(0.5)

        status_text.markdown("💊 **Stage 2/4** — Mapping drugs + FDA adverse event signals...")
        progress_bar.progress(25)

        # Make API call
        result = call_api(disease_input.strip(), max_targets, max_papers, max_drugs)

        progress_bar.progress(75)
        status_text.markdown("📚 **Stage 3/4** — Retrieving research papers...")
        time.sleep(0.3)

        progress_bar.progress(90)
        status_text.markdown("🤖 **Stage 4/4** — GPT generating hypotheses...")
        time.sleep(0.3)

        progress_bar.progress(100)
        status_text.empty()
        progress_bar.empty()

    # ── Error Handling ────────────────────────────────────────
    if "error" in result:
        st.error(f"❌ {result['error']}")
        st.stop()

    if not result.get("success"):
        st.error(f"❌ Analysis failed: {result.get('message', 'Unknown error')}")
        st.stop()

    data = result["data"]

    # ── Success Banner ────────────────────────────────────────
    st.success(f"✅ Analysis complete for **{data['disease_name']}** — {result['message']}")

    # ── Summary Metrics ───────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🧬 Protein Targets", len(data["protein_targets"]))
    m2.metric("💊 Drug Associations", len(data["drugs"]))
    m3.metric("📚 Research Papers", len(data["papers"]))
    m4.metric("💡 Hypotheses", len(data["hypotheses"]))

    st.divider()

    # ════════════════════════════════════════════════════════
    # SECTION 1: HYPOTHESES
    # ════════════════════════════════════════════════════════
    st.markdown("## 💡 Generated Hypotheses")
    st.caption("AI-generated, evidence-backed biomedical hypotheses ranked by confidence score")

    for i, hyp in enumerate(data["hypotheses"], 1):
        score = hyp["confidence_score"]
        color = confidence_color(score)

        with st.expander(
            f"Hypothesis {i}: {hyp['title']}",
            expanded=(i == 1)   # Auto-expand first hypothesis
        ):
            # Confidence bar
            st.markdown("**Confidence Score**")
            render_confidence_bar(score, hyp["confidence_label"])

            # Protein + Drug tags
            col_tags1, col_tags2 = st.columns(2)
            with col_tags1:
                st.markdown("**🧬 Key Proteins**")
                if hyp["key_proteins"]:
                    tags = " ".join([
                        f"<span class='protein-badge'>{p}</span>"
                        for p in hyp["key_proteins"]
                    ])
                    st.markdown(tags, unsafe_allow_html=True)
                else:
                    st.caption("No specific proteins tagged")

            with col_tags2:
                st.markdown("**💊 Key Drugs**")
                if hyp["key_drugs"]:
                    tags = " ".join([
                        f"<span class='drug-badge'>{d}</span>"
                        for d in hyp["key_drugs"]
                    ])
                    st.markdown(tags, unsafe_allow_html=True)
                else:
                    st.caption("No specific drugs tagged")

            st.markdown("---")

            # Explanations side by side
            col_sci, col_simple = st.columns(2)

            with col_sci:
                st.markdown("**🔬 Scientific Explanation**")
                st.markdown(
                    f"<div style='background:#0f172a; padding:16px; "
                    f"border-radius:8px; font-size:14px; line-height:1.7; color:#cbd5e1;'>"
                    f"{hyp['explanation']}</div>",
                    unsafe_allow_html=True
                )

            with col_simple:
                st.markdown("**🧒 Simple Explanation**")
                st.markdown(
                    f"<div style='background:#0f172a; padding:16px; "
                    f"border-radius:8px; font-size:14px; line-height:1.7; color:#cbd5e1;'>"
                    f"{hyp['simple_explanation']}</div>",
                    unsafe_allow_html=True
                )

            # Evidence summary
            if hyp.get("evidence_summary"):
                st.markdown("**📚 Evidence Summary**")
                st.info(f"📌 {hyp['evidence_summary']}")

    st.divider()

    # ════════════════════════════════════════════════════════
    # SECTION 2: PROTEIN TARGETS
    # ════════════════════════════════════════════════════════
    st.markdown("## 🧬 Protein Targets")
    st.caption(f"Top proteins associated with {data['disease_name']} from OpenTargets")

    for target in data["protein_targets"]:
        score = target["association_score"]
        col1, col2, col3 = st.columns([1, 3, 1])

        with col1:
            st.markdown(
                f"<div style='background:#1e3a5f; color:#60a5fa; padding:10px; "
                f"border-radius:8px; text-align:center; font-weight:700; font-size:18px;'>"
                f"{target['gene_symbol']}</div>",
                unsafe_allow_html=True
            )
        with col2:
            st.markdown(f"**{target['protein_name']}**")
            st.caption(target["function_description"][:150] + "...")
        with col3:
            color = confidence_color(score)
            st.markdown(
                f"<div style='text-align:center;'>"
                f"<div style='color:{color}; font-size:22px; font-weight:700;'>{score:.2f}</div>"
                f"<div style='color:#64748b; font-size:11px;'>Association Score</div>"
                f"</div>",
                unsafe_allow_html=True
            )
        st.divider()

    # ════════════════════════════════════════════════════════
    # SECTION 3: DRUGS + FDA SIGNALS
    # ════════════════════════════════════════════════════════
    st.markdown("## 💊 Drug-Protein Associations + FDA Signals")
    st.caption("Known drugs targeting identified proteins, with FDA adverse event data")

    for drug in data["drugs"]:
        phase    = drug.get("clinical_phase") or "N/A"
        fda_data = drug.get("fda_adverse_events", [])

        col1, col2, col3 = st.columns([2, 3, 2])

        with col1:
            st.markdown(f"**💊 {drug['drug_name']}**")
            st.caption(f"Type: {drug['drug_type']}")
            st.markdown(
                f"<span style='background:#134e3a; color:#34d399; padding:3px 10px; "
                f"border-radius:12px; font-size:12px;'>Phase {phase}</span>",
                unsafe_allow_html=True
            )

        with col2:
            st.markdown(f"**Target:** `{drug['target_gene']}`")
            st.caption(f"Mechanism: {drug['mechanism'][:100]}")

        with col3:
            if fda_data:
                st.markdown("**⚠️ Top FDA Signal**")
                top = fda_data[0]
                st.markdown(
                    f"<div style='background:#2d1b1b; color:#f87171; padding:8px 12px; "
                    f"border-radius:8px; font-size:13px;'>"
                    f"🚨 {top['reaction']}<br>"
                    f"<span style='color:#94a3b8;'>{top['count']:,} reports</span></div>",
                    unsafe_allow_html=True
                )
            else:
                st.caption("No FDA signals found")

        st.divider()

    # ════════════════════════════════════════════════════════
    # SECTION 4: RESEARCH PAPERS
    # ════════════════════════════════════════════════════════
    st.markdown("## 📚 Supporting Research Papers")
    st.caption("Retrieved from PubMed and Semantic Scholar")

    for paper in data["papers"]:
        source_color = "#3b82f6" if paper["source"] == "PubMed" else "#8b5cf6"
        source_label = paper["source"]

        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"**{paper['title']}**")
            if paper.get("summary") and paper["summary"] != "No summary available":
                st.caption(paper["summary"][:200])
            elif paper.get("abstract") and paper["abstract"] != "No abstract available":
                st.caption(paper["abstract"][:200] + "...")
        with col2:
            st.markdown(
                f"<div style='text-align:center;'>"
                f"<span style='background:{source_color}22; color:{source_color}; "
                f"padding:4px 10px; border-radius:12px; font-size:12px;'>{source_label}</span>"
                f"<br><br>"
                f"<span style='color:#94a3b8; font-size:12px;'>{paper.get('year') or 'N/A'}</span>"
                f"</div>",
                unsafe_allow_html=True
            )
            if paper.get("url"):
                st.markdown(f"[🔗 View]({paper['url']})")

        st.divider()

elif analyze_clicked and not disease_input.strip():
    st.warning("⚠️ Please enter a disease name before clicking Analyze.")

else:
    # ── Landing State ─────────────────────────────────────────
    st.markdown("""
    <div style='text-align:center; padding:40px; color:#475569;'>
        <div style='font-size:64px;'>🔬</div>
        <h3 style='color:#64748b;'>Enter a disease name above to begin</h3>
        <p>The AI will analyze protein targets, drug interactions,<br>
        research papers and generate novel biomedical hypotheses.</p>
    </div>
    """, unsafe_allow_html=True)

    # Show example cards
    st.markdown("### 💡 Try These Examples")
    ex_cols = st.columns(4)
    examples_info = [
        ("🧠", "Alzheimer disease",   "Amyloid cascade, gamma-secretase"),
        ("🫀", "Parkinson disease",   "Alpha-synuclein, dopamine pathway"),
        ("🎗️", "breast cancer",       "HER2, BRCA1, hormone receptors"),
        ("🩸", "type 2 diabetes",     "Insulin resistance, GLUT4 pathway"),
    ]
    for i, (emoji, name, desc) in enumerate(examples_info):
        with ex_cols[i]:
            st.markdown(
                f"<div style='background:#1a1f2e; border:1px solid #2d3561; "
                f"border-radius:10px; padding:16px; text-align:center;'>"
                f"<div style='font-size:28px;'>{emoji}</div>"
                f"<div style='color:#e2e8f0; font-weight:600; margin:8px 0;'>{name}</div>"
                f"<div style='color:#64748b; font-size:12px;'>{desc}</div>"
                f"</div>",
                unsafe_allow_html=True
            )
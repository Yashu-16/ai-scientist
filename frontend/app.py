# frontend/app.py
# Purpose: Streamlit frontend for the AI Scientist platform V2
# Features: Ranking display, Evidence Strength banner, Score breakdown

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
API_BASE_URL = "http://localhost:8000"

# ── Custom CSS ───────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }

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

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ── Helper Functions ─────────────────────────────────────────

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

def call_api(disease_name: str, max_targets: int,
             max_papers: int, max_drugs: int) -> dict:
    try:
        response = requests.post(
            f"{API_BASE_URL}/analyze-disease",
            json={
                "disease_name": disease_name,
                "max_targets" : max_targets,
                "max_papers"  : max_papers,
                "max_drugs"   : max_drugs
            },
            timeout=180
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to backend. Make sure FastAPI is running."}
    except requests.exceptions.Timeout:
        return {"error": "Request timed out (~60s). Please try again."}
    except requests.exceptions.HTTPError as e:
        return {"error": f"API error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

def get_example_diseases() -> list:
    try:
        r = requests.get(f"{API_BASE_URL}/diseases/examples", timeout=5)
        return r.json().get("examples", [])
    except:
        return ["Alzheimer disease", "Parkinson disease",
                "breast cancer", "type 2 diabetes"]


# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧬 AI Scientist")
    st.markdown("*Evidence-Based Hypothesis Generator*")
    st.divider()

    st.markdown("### ⚙️ Analysis Settings")
    max_targets = st.slider("Protein Targets",  3, 10, 5)
    max_drugs   = st.slider("Drugs per Protein", 1,  5, 3)
    max_papers  = st.slider("Research Papers",   3, 10, 5)

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
        "AI-assisted hypotheses for exploratory purposes only. "
        "Not for clinical use."
    )


# ── Main Page ────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center; padding:20px 0 10px 0;'>
    <h1 style='font-size:2.8em; font-weight:800;
               background:linear-gradient(90deg,#60a5fa,#a78bfa,#34d399);
               -webkit-background-clip:text; -webkit-text-fill-color:transparent;'>
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
        label            = "Disease Name",
        placeholder      = "e.g. Alzheimer disease, breast cancer...",
        label_visibility = "collapsed"
    )
with col_button:
    analyze_clicked = st.button(
        "🔬 Analyze", type="primary", use_container_width=True
    )

st.markdown("**Quick select:**")
cols = st.columns(len(examples[:4]))
for i, disease in enumerate(examples[:4]):
    with cols[i]:
        if st.button(disease, key=f"ex_{i}", use_container_width=True):
            disease_input   = disease
            analyze_clicked = True

st.divider()

# ── Run Analysis ─────────────────────────────────────────────
if analyze_clicked and disease_input.strip():

    with st.spinner(f"🔬 Analyzing **{disease_input}** — ~60 seconds..."):
        progress_bar = st.progress(0)
        status_text  = st.empty()

        status_text.markdown("📡 **Stage 1/4** — Fetching protein targets...")
        progress_bar.progress(10)
        time.sleep(0.5)

        status_text.markdown("💊 **Stage 2/4** — Mapping drugs + FDA signals...")
        progress_bar.progress(25)

        result = call_api(
            disease_input.strip(), max_targets, max_papers, max_drugs
        )

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
        st.error(f"❌ {result.get('message', 'Unknown error')}")
        st.stop()

    data = result["data"]

    st.success(
        f"✅ Analysis complete for **{data['disease_name']}** "
        f"— {result['message']}"
    )

    # ── Summary Metrics ───────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🧬 Protein Targets",  len(data["protein_targets"]))
    m2.metric("💊 Drug Associations", len(data["drugs"]))
    m3.metric("📚 Research Papers",  len(data["papers"]))
    m4.metric("💡 Hypotheses",       len(data["hypotheses"]))

    # ── Evidence Strength Banner ──────────────────────────────
    ev = data.get("evidence_strength") or {}
    if ev:
        ev_score     = float(ev.get("evidence_score") or 0)
        ev_label     = str(ev.get("evidence_label")   or "Unknown")
        ev_color     = str(ev.get("evidence_color")   or "yellow")
        ev_breakdown = str(ev.get("evidence_breakdown") or "")
        bg_map   = {
            "green":  ("#052e16", "#22c55e"),
            "yellow": ("#1c1a02", "#eab308"),
            "red":    ("#2d0a0a", "#ef4444")
        }
        emoji_map = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
        bg, fg    = bg_map.get(ev_color, bg_map["yellow"])
        ev_emoji  = emoji_map.get(ev_color, "🟡")
        st.markdown(
            f"""<div style='background:{bg}; border:1px solid {fg}55;
                    border-radius:10px; padding:14px 20px; margin:10px 0;'>
              <div style='display:flex; justify-content:space-between;
                          align-items:center;'>
                <div>
                  <div style='font-size:11px; color:#94a3b8;
                              text-transform:uppercase; letter-spacing:1px;'>
                    Evidence Strength</div>
                  <div style='margin-top:2px;'>
                    <span style='font-size:20px; font-weight:800;
                                  color:{fg};'>{ev_emoji} {ev_label}</span>
                    <span style='color:#64748b; font-size:13px;
                                  margin-left:10px;'>
                      Score: {ev_score:.2f} / 1.00</span>
                  </div>
                </div>
                <div style='color:#64748b; font-size:12px; text-align:right;'>
                  📄 {ev.get('total_papers',0)} papers &nbsp;|&nbsp;
                  ⭐ {ev.get('high_citation_papers',0)} highly cited
                  &nbsp;|&nbsp;
                  🕐 {ev.get('recent_papers',0)} recent
                </div>
              </div>
              <div style='margin-top:6px; font-size:11px; color:#475569;'>
                📐 {ev_breakdown}</div>
            </div>""",
            unsafe_allow_html=True
        )

    st.divider()

    # ════════════════════════════════════════════════════════
    # TABBED LAYOUT — Feature 7
    # ════════════════════════════════════════════════════════
    tab1, tab2, tab3, tab4 = st.tabs([
        "💡 Hypotheses",
        "🧬 Proteins & Evidence",
        "💊 Drugs",
        "⚠️ Risk Analysis"
    ])

    # ════════════════════════════════════════════════════════
    # TAB 1: HYPOTHESES
    # ════════════════════════════════════════════════════════
    with tab1:
        st.markdown("### 📊 Hypothesis Comparison")

        # Build table rows
        table_rows = []
        for hyp in data["hypotheses"]:
            rank    = int(hyp.get("rank") or 0) or 1
            final   = float(hyp.get("final_score") or 0.0)
            score   = float(hyp.get("confidence_score") or 0.0)
            display = final if final > 0 else score
            drugs   = hyp.get("key_drugs", [])

            drug_risk = "Unknown"
            if drugs:
                drug_name = drugs[0].upper()
                for d in data["drugs"]:
                    if d["drug_name"].upper() == drug_name:
                        drug_risk = d.get("risk_level", "Unknown")
                        break

            medals    = {1: "🥇", 2: "🥈", 3: "🥉"}
            risk_emoji= {"High":"🔴","Medium":"🟡","Low":"🟢","Unknown":"⚪"}
            table_rows.append({
                "rank": rank, "medal": medals.get(rank, f"#{rank}"),
                "title": hyp["title"],
                "proteins": ", ".join(hyp.get("key_proteins") or []),
                "drugs": ", ".join(hyp.get("key_drugs") or []),
                "final": display, "llm": score,
                "risk": drug_risk,
                "risk_emoji": risk_emoji.get(drug_risk, "⚪"),
                "color": confidence_color(display)
            })

        # Header
        h1,h2,h3,h4,h5,h6 = st.columns([0.5,3.5,1.2,1.2,1.0,1.0])
        for col, label in zip(
            [h1,h2,h3,h4,h5,h6],
            ["Rank","Hypothesis","Proteins","Drugs","Score","Risk"]
        ):
            col.markdown(
                f"<div style='color:#64748b; font-size:11px; "
                f"font-weight:700; text-transform:uppercase; "
                f"letter-spacing:1px;'>{label}</div>",
                unsafe_allow_html=True
            )
        st.markdown(
            "<hr style='border:none; border-top:1px solid #1e293b; "
            "margin:4px 0;'>",
            unsafe_allow_html=True
        )

        for row in table_rows:
            c1,c2,c3,c4,c5,c6 = st.columns([0.5,3.5,1.2,1.2,1.0,1.0])
            with c1:
                st.markdown(
                    f"<div style='font-size:22px; text-align:center; "
                    f"padding-top:6px;'>{row['medal']}</div>",
                    unsafe_allow_html=True
                )
            with c2:
                st.markdown(
                    f"<div style='font-size:13px; color:#e2e8f0; "
                    f"padding:6px 0;'>{row['title']}</div>",
                    unsafe_allow_html=True
                )
            with c3:
                if row["proteins"]:
                    st.markdown(
                        " ".join([
                            f"<span style='background:#1e3a5f;color:#60a5fa;"
                            f"padding:2px 8px;border-radius:10px;font-size:11px;"
                            f"font-weight:600;margin:2px;display:inline-block;'>"
                            f"{p}</span>"
                            for p in row["proteins"].split(", ")
                        ]),
                        unsafe_allow_html=True
                    )
            with c4:
                if row["drugs"]:
                    st.markdown(
                        " ".join([
                            f"<span style='background:#1e3a2f;color:#34d399;"
                            f"padding:2px 8px;border-radius:10px;font-size:11px;"
                            f"font-weight:600;margin:2px;display:inline-block;'>"
                            f"{d}</span>"
                            for d in row["drugs"].split(", ")
                        ]),
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        "<span style='color:#475569;font-size:11px;'>—</span>",
                        unsafe_allow_html=True
                    )
            with c5:
                pct   = row["final"]
                color = row["color"]
                bar_w = int(pct * 60)
                st.markdown(
                    f"<div style='padding-top:4px;'>"
                    f"<div style='color:{color};font-weight:700;"
                    f"font-size:15px;'>{pct:.0%}</div>"
                    f"<div style='background:#1e293b;border-radius:4px;"
                    f"height:4px;width:60px;margin-top:2px;'>"
                    f"<div style='background:{color};height:4px;"
                    f"border-radius:4px;width:{bar_w}px;'></div>"
                    f"</div></div>",
                    unsafe_allow_html=True
                )
            with c6:
                risk_colors = {
                    "High":    ("#ef4444","#2d0a0a"),
                    "Medium":  ("#f59e0b","#2d1f02"),
                    "Low":     ("#22c55e","#052e16"),
                    "Unknown": ("#64748b","#1a1f2e")
                }
                fg,bg = risk_colors.get(row["risk"], risk_colors["Unknown"])
                st.markdown(
                    f"<div style='background:{bg};color:{fg};"
                    f"padding:4px 10px;border-radius:8px;font-size:12px;"
                    f"font-weight:600;text-align:center;margin-top:4px;'>"
                    f"{row['risk_emoji']} {row['risk']}</div>",
                    unsafe_allow_html=True
                )
            st.markdown(
                "<hr style='border:none;border-top:1px solid #0f172a;"
                "margin:2px 0;'>",
                unsafe_allow_html=True
            )

        st.caption(
            "💡 Score = 0.4×protein + 0.3×drug_phase + "
            "0.2×papers − 0.1×fda_risk"
        )
        st.divider()
        st.markdown("### 🔬 Detailed Analysis")

        for hyp in data["hypotheses"]:
            rank    = int(hyp.get("rank") or 0) or 1
            final   = float(hyp.get("final_score") or 0.0)
            score   = float(hyp.get("confidence_score") or 0.0)
            p_score = float(hyp.get("protein_score") or 0.0)
            d_score = float(hyp.get("drug_score") or 0.0)
            pa_score= float(hyp.get("paper_score") or 0.0)
            r_pen   = float(hyp.get("risk_penalty") or 0.0)
            display = final if final > 0 else score
            medals  = {1:"🥇",2:"🥈",3:"🥉"}
            medal   = medals.get(rank, f"#{rank}")

            with st.expander(
                f"{medal} Rank {rank} | Score: {display:.0%} | {hyp['title']}",
                expanded=(rank == 1)
            ):
                bc1,bc2,bc3,bc4,bc5 = st.columns(5)
                bc1.metric("🧬 Protein",   f"{p_score:.2f}")
                bc2.metric("💊 Drug Phase", f"{d_score:.2f}")
                bc3.metric("📚 Papers",    f"{pa_score:.2f}")
                bc4.metric("⚠️ Risk",      f"-{r_pen:.2f}")
                bc5.metric("🎯 Final",
                           f"{final:.2%}" if final > 0 else f"{score:.2%}")

                if hyp.get("score_breakdown"):
                    st.caption(f"📐 {hyp['score_breakdown']}")
                st.markdown("---")

                st.markdown("**LLM Confidence**")
                render_confidence_bar(score, hyp.get("confidence_label",""))

                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    st.markdown("**🧬 Key Proteins**")
                    proteins = hyp.get("key_proteins") or []
                    if proteins:
                        st.markdown(
                            " ".join([
                                f"<span class='protein-badge'>{p}</span>"
                                for p in proteins
                            ]),
                            unsafe_allow_html=True
                        )
                    else:
                        st.caption("None tagged")
                with col_t2:
                    st.markdown("**💊 Key Drugs**")
                    drugs = hyp.get("key_drugs") or []
                    if drugs:
                        st.markdown(
                            " ".join([
                                f"<span class='drug-badge'>{d}</span>"
                                for d in drugs
                            ]),
                            unsafe_allow_html=True
                        )
                    else:
                        st.caption("None tagged")

                st.markdown("---")
                col_s, col_e = st.columns(2)
                with col_s:
                    st.markdown("**🔬 Scientific Explanation**")
                    st.markdown(
                        f"<div style='background:#0f172a;padding:14px;"
                        f"border-radius:8px;font-size:14px;"
                        f"line-height:1.7;color:#cbd5e1;'>"
                        f"{hyp.get('explanation','')}</div>",
                        unsafe_allow_html=True
                    )
                with col_e:
                    st.markdown("**🧒 Simple Explanation**")
                    st.markdown(
                        f"<div style='background:#0f172a;padding:14px;"
                        f"border-radius:8px;font-size:14px;"
                        f"line-height:1.7;color:#cbd5e1;'>"
                        f"{hyp.get('simple_explanation','')}</div>",
                        unsafe_allow_html=True
                    )

                if hyp.get("evidence_summary"):
                    st.info(f"📌 {hyp['evidence_summary']}")

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
                            unsafe_allow_html=True
                        )

    # ════════════════════════════════════════════════════════
    # TAB 2: PROTEINS & EVIDENCE
    # ════════════════════════════════════════════════════════
    with tab2:
        st.markdown("### 🧬 Protein Targets")
        st.caption(
            f"Top proteins for {data['disease_name']} "
            f"— OpenTargets association scores + AlphaFold structural confidence"
        )

        for target in data["protein_targets"]:
            assoc  = float(target.get("association_score") or 0)
            plddt  = float(target.get("alphafold_plddt")   or 0)
            af_lbl = target.get("alphafold_label", "Est.")
            af_col = target.get("alphafold_color", "#64748b")
            a_col  = confidence_color(assoc)

            col1,col2,col3,col4 = st.columns([1,3,1,1])
            with col1:
                st.markdown(
                    f"<div style='background:#1e3a5f;color:#60a5fa;"
                    f"padding:10px;border-radius:8px;text-align:center;"
                    f"font-weight:700;font-size:18px;'>"
                    f"{target['gene_symbol']}</div>",
                    unsafe_allow_html=True
                )
            with col2:
                st.markdown(f"**{target['protein_name']}**")
                st.caption(target["function_description"][:150] + "...")
            with col3:
                st.markdown(
                    f"<div style='text-align:center;'>"
                    f"<div style='color:{a_col};font-size:20px;"
                    f"font-weight:700;'>{assoc:.2f}</div>"
                    f"<div style='color:#64748b;font-size:10px;'>"
                    f"Disease Assoc.</div></div>",
                    unsafe_allow_html=True
                )
            with col4:
                st.markdown(
                    f"<div style='text-align:center;"
                    f"background:#0f172a;border-radius:8px;padding:8px;'>"
                    f"<div style='color:{af_col};font-size:18px;"
                    f"font-weight:700;'>{plddt:.2f}</div>"
                    f"<div style='color:{af_col};font-size:10px;"
                    f"font-weight:600;'>{af_lbl}</div>"
                    f"<div style='color:#475569;font-size:9px;'>"
                    f"AlphaFold pLDDT</div></div>",
                    unsafe_allow_html=True
                )
            st.divider()

        st.markdown("### 📚 Research Papers")
        st.caption("Retrieved from PubMed and Semantic Scholar")

        for paper in data["papers"]:
            src_color = "#3b82f6" if paper["source"] == "PubMed" else "#8b5cf6"
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"**{paper['title']}**")
                summary  = paper.get("summary","")
                abstract = paper.get("abstract","")
                if summary and summary != "No summary available":
                    st.caption(summary[:200])
                elif abstract and abstract != "No abstract available":
                    st.caption(abstract[:200] + "...")
            with col2:
                st.markdown(
                    f"<div style='text-align:center;'>"
                    f"<span style='background:{src_color}22;"
                    f"color:{src_color};padding:3px 8px;"
                    f"border-radius:10px;font-size:11px;'>"
                    f"{paper['source']}</span><br><br>"
                    f"<span style='color:#94a3b8;font-size:12px;'>"
                    f"{paper.get('year') or 'N/A'}</span></div>",
                    unsafe_allow_html=True
                )
                if paper.get("url"):
                    st.markdown(f"[🔗 View]({paper['url']})")
            st.divider()

    # ════════════════════════════════════════════════════════
    # TAB 3: DRUGS
    # ════════════════════════════════════════════════════════
    with tab3:
        st.markdown("### 💊 Drug-Protein Associations")
        st.caption("Known drugs with mechanisms, clinical phases, and FDA signals")

        for drug in data["drugs"]:
            phase    = drug.get("clinical_phase") or "N/A"
            fda_data = drug.get("fda_adverse_events") or []
            risk     = drug.get("risk_level", "Unknown")
            risk_desc= drug.get("risk_description", "")

            risk_styles = {
                "High":    ("#2d0a0a","#ef4444","🔴"),
                "Medium":  ("#2d1f02","#f59e0b","🟡"),
                "Low":     ("#052e16","#22c55e","🟢"),
                "Unknown": ("#1a1f2e","#64748b","⚪"),
            }
            r_bg,r_fg,r_emoji = risk_styles.get(risk, risk_styles["Unknown"])

            col1,col2,col3,col4 = st.columns([2,3,2,2])
            with col1:
                st.markdown(f"**💊 {drug['drug_name']}**")
                st.caption(f"Type: {drug['drug_type']}")
                st.markdown(
                    f"<span style='background:#134e3a;color:#34d399;"
                    f"padding:3px 10px;border-radius:12px;font-size:12px;'>"
                    f"Phase {phase}</span>",
                    unsafe_allow_html=True
                )
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
                        unsafe_allow_html=True
                    )
                else:
                    st.caption("No FDA signals found")
            with col4:
                st.markdown("**🛡️ Risk Level**")
                st.markdown(
                    f"<div style='background:{r_bg};border:1px solid {r_fg}55;"
                    f"border-radius:8px;padding:8px 12px;'>"
                    f"<div style='color:{r_fg};font-weight:700;"
                    f"font-size:15px;'>{r_emoji} {risk}</div>"
                    f"<div style='color:#94a3b8;font-size:11px;"
                    f"margin-top:4px;'>{risk_desc[:80]}...</div></div>",
                    unsafe_allow_html=True
                )
            st.divider()

    # ════════════════════════════════════════════════════════
    # TAB 4: RISK ANALYSIS
    # ════════════════════════════════════════════════════════
    with tab4:
        st.markdown("### ⚠️ FDA Risk Intelligence Summary")
        st.caption(
            "Risk classification based on FDA FAERS adverse event reports"
        )

        # Risk summary counts
        risk_counts = {"High": 0, "Medium": 0, "Low": 0, "Unknown": 0}
        for drug in data["drugs"]:
            lvl = drug.get("risk_level", "Unknown")
            risk_counts[lvl] = risk_counts.get(lvl, 0) + 1

        r1,r2,r3,r4 = st.columns(4)
        r1.metric("🔴 High Risk",    risk_counts["High"],
                  help=">200 adverse event reports")
        r2.metric("🟡 Medium Risk",  risk_counts["Medium"],
                  help="50-200 adverse event reports")
        r3.metric("🟢 Low Risk",     risk_counts["Low"],
                  help="<50 adverse event reports")
        r4.metric("⚪ Unknown",      risk_counts["Unknown"],
                  help="No FDA FAERS data available")

        st.divider()
        st.markdown("### 📋 Drug Risk Details")

        for drug in data["drugs"]:
            risk      = drug.get("risk_level", "Unknown")
            risk_desc = drug.get("risk_description", "")
            fda_data  = drug.get("fda_adverse_events") or []

            risk_styles = {
                "High":    ("#2d0a0a","#ef4444","🔴"),
                "Medium":  ("#2d1f02","#f59e0b","🟡"),
                "Low":     ("#052e16","#22c55e","🟢"),
                "Unknown": ("#1a1f2e","#64748b","⚪"),
            }
            r_bg,r_fg,r_emoji = risk_styles.get(risk, risk_styles["Unknown"])

            with st.expander(
                f"{r_emoji} {drug['drug_name']} — {risk} Risk "
                f"(Phase {drug.get('clinical_phase','N/A')}, "
                f"Target: {drug['target_gene']})"
            ):
                st.markdown(
                    f"<div style='background:{r_bg};border-left:4px solid {r_fg};"
                    f"padding:12px 16px;border-radius:0 8px 8px 0;"
                    f"margin-bottom:12px;'>"
                    f"<div style='color:{r_fg};font-weight:700;"
                    f"font-size:16px;'>{r_emoji} {risk} Risk</div>"
                    f"<div style='color:#94a3b8;margin-top:4px;'>"
                    f"{risk_desc}</div></div>",
                    unsafe_allow_html=True
                )

                if fda_data:
                    st.markdown("**Top FDA Adverse Events:**")
                    for ae in fda_data[:5]:
                        pct = min(ae['count'] / 300, 1.0)
                        col_a, col_b = st.columns([3,1])
                        with col_a:
                            st.markdown(
                                f"<div style='font-size:13px;"
                                f"color:#e2e8f0;'>{ae['reaction']}</div>",
                                unsafe_allow_html=True
                            )
                            st.progress(pct)
                        with col_b:
                            st.markdown(
                                f"<div style='text-align:right;"
                                f"color:#94a3b8;font-size:13px;"
                                f"padding-top:4px;'>"
                                f"{ae['count']:,} reports</div>",
                                unsafe_allow_html=True
                            )
                else:
                    st.info("No adverse event data in FDA FAERS")

elif analyze_clicked and not disease_input.strip():
    st.warning("⚠️ Please enter a disease name first.")

else:
    # ── Landing State ─────────────────────────────────────────
    st.markdown("""
    <div style='text-align:center; padding:40px; color:#475569;'>
        <div style='font-size:64px;'>🔬</div>
        <h3 style='color:#64748b;'>Enter a disease name above to begin</h3>
        <p>The AI analyzes protein targets, drug interactions,<br>
        research papers and generates novel biomedical hypotheses.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 💡 Try These Examples")
    ex_cols = st.columns(4)
    examples_info = [
        ("🧠", "Alzheimer disease",  "Amyloid cascade, gamma-secretase"),
        ("🫀", "Parkinson disease",  "Alpha-synuclein, dopamine pathway"),
        ("🎗️", "breast cancer",      "HER2, BRCA1, hormone receptors"),
        ("🩸", "type 2 diabetes",    "Insulin resistance, GLUT4 pathway"),
    ]
    for i, (emoji, name, desc) in enumerate(examples_info):
        with ex_cols[i]:
            st.markdown(
                f"<div style='background:#1a1f2e; border:1px solid #2d3561; "
                f"border-radius:10px; padding:16px; text-align:center;'>"
                f"<div style='font-size:28px;'>{emoji}</div>"
                f"<div style='color:#e2e8f0; font-weight:600; margin:8px 0;'>"
                f"{name}</div>"
                f"<div style='color:#64748b; font-size:12px;'>{desc}</div>"
                f"</div>",
                unsafe_allow_html=True
            )
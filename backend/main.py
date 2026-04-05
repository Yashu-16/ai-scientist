# backend/main.py
# Purpose: FastAPI backend — exposes the full AI Scientist pipeline
# as clean REST API endpoints.
#
# Endpoints:
#   GET  /                    → health check
#   GET  /health              → detailed status
#   POST /analyze-disease     → full pipeline + hypothesis generation
#   GET  /diseases/examples   → example disease names for UI

import time
import json  # ← make sure this is at the top of main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.models.schemas import (
    AnalysisRequest,
    AnalysisResponse,
    DiseaseAnalysisResult,
    MultiDiseaseRequest,
    MultiDiseaseComparison,
    DrugComparisonRow,
    DiseaseComparisonEntry,
    SharedProtein
)
from backend.services.pipeline_service   import run_data_pipeline
from backend.services.hypothesis_service import generate_hypotheses
from backend.services.updates_service    import (
    updates_store,
    run_update_check,
    setup_scheduler
)
from backend.api_security import (
    get_api_key,
    optional_api_key,
    usage_tracker,
    VALID_API_KEYS
)
from backend.services.knowledge_graph import knowledge_graph
from fastapi.responses import Response


# ── App Lifecycle ────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n🧬 AI Scientist API starting up...")
    print("   Endpoints ready at http://localhost:8000")
    print("   API docs at     http://localhost:8000/docs\n")

    # Load knowledge graph
    print("📊 Loading knowledge graph...")
    stats = knowledge_graph.get_stats()
    print(f"   Graph: {stats['node_count']} nodes, "
          f"{stats['edge_count']} edges, "
          f"{stats['total_analyses']} analyses")

    # Start scheduler
    scheduler = setup_scheduler(app)
    app.state.scheduler = scheduler

    print("🔄 Running initial scientific update check...")
    try:
        run_update_check()
    except Exception as e:
        print(f"⚠️  Initial update check failed: {e}")

    yield

    if hasattr(app.state,'scheduler') and app.state.scheduler:
        app.state.scheduler.shutdown()
    print("\n🛑 AI Scientist API shutting down...")


# ── FastAPI App ──────────────────────────────────────────────
app = FastAPI(
    title       = "AI Scientist — Hypothesis Generation API",
    description = """
    Generate evidence-backed biomedical hypotheses by combining:
    - **Protein targets** from OpenTargets
    - **Drug mappings** from OpenTargets + FDA FAERS
    - **Research papers** from PubMed + Semantic Scholar
    - **LLM reasoning** from GPT-4o-mini / Llama3
    """,
    version     = "1.0.0",
    lifespan    = lifespan
)

# ── CORS Middleware ──────────────────────────────────────────
# Allows the Streamlit frontend (different port) to call this API
import os

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8501",
    "https://*.vercel.app",
    os.getenv("FRONTEND_URL", ""),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Keep * for now, restrict after deploy
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ───────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    """Root endpoint — confirms API is running."""
    return {
        "status" : "running",
        "name"   : "AI Scientist Hypothesis Generation API",
        "version": "1.0.0",
        "docs"   : "/docs"
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Detailed health check — confirms all services are importable."""
    return {
        "status"  : "healthy",
        "services": {
            "protein_service" : "ready",
            "drug_service"    : "ready",
            "paper_service"   : "ready",
            "hypothesis_service": "ready"
        }
    }


@app.get("/diseases/examples", tags=["Utility"])
def get_example_diseases():
    """Returns example disease names to populate the UI search box."""
    return {
        "examples": [
            "Alzheimer disease",
            "Parkinson disease",
            "breast cancer",
            "type 2 diabetes",
            "rheumatoid arthritis",
            "lung cancer",
            "multiple sclerosis",
            "colorectal cancer"
        ]
    }

@app.get("/cache/stats", tags=["Utility"])
def cache_stats():
    """Returns current cache statistics."""
    from backend.services.pipeline_service import pipeline_cache
    return {
        "cache": pipeline_cache.stats(),
        "message": "Results are cached for 60 minutes"
    }


@app.delete("/cache/clear", tags=["Utility"])
def clear_cache():
    """Clears all cached pipeline results."""
    from backend.services.pipeline_service import pipeline_cache
    count = pipeline_cache.clear()
    return {
        "cleared": count,
        "message": f"Cleared {count} cached entries"
    }

@app.get("/latest-updates", tags=["Updates"])
def get_latest_updates(disease: str = None):
    """
    Get latest scientific paper updates for tracked diseases.

    Optional query param: ?disease=Alzheimer+disease
    Returns recent PubMed papers found in last 7 days.
    """
    updates = updates_store.get_updates(disease)
    stats   = updates_store.get_stats()

    return {
        "success":          True,
        "stats":            stats,
        "updates":          updates,
        "tracked_diseases": stats["tracked_diseases"]
    }


@app.post("/track-disease", tags=["Updates"])
def track_disease(request: dict):
    """
    Add a disease to the monitoring list.
    Body: {"disease_name": "breast cancer"}
    """
    disease_name = request.get("disease_name","").strip()
    if not disease_name:
        raise HTTPException(status_code=422,
                            detail="disease_name is required")

    updates_store.add_tracked_disease(disease_name)

    # Fetch initial papers for this disease
    from backend.services.updates_service import fetch_recent_papers
    papers = fetch_recent_papers(disease_name, days_back=30,
                                 max_results=3)
    if papers:
        updates_store.store_updates(disease_name, papers)

    return {
        "success":      True,
        "disease_name": disease_name,
        "papers_found": len(papers),
        "message":      f"Now tracking '{disease_name}'. "
                        f"Found {len(papers)} recent papers."
    }


@app.post("/trigger-update", tags=["Updates"])
def trigger_manual_update():
    """
    Manually trigger a scientific update check.
    Useful for testing without waiting for daily schedule.
    """
    total_new = run_update_check()
    stats     = updates_store.get_stats()

    return {
        "success":    True,
        "new_papers": total_new,
        "stats":      stats,
        "message":    f"Update complete. Found {total_new} new papers."
    }
@app.get("/trending-insights", tags=["Updates"])
def get_trending_insights():
    """
    Analyze stored paper updates to detect trending proteins,
    mechanisms, and emerging drug discovery opportunities.

    Returns keyword frequency analysis across all tracked diseases.
    """
    from backend.services.updates_service import analyze_trends

    try:
        trends = analyze_trends()
        return {
            "success": True,
            "trends":  trends
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Trend analysis failed: {str(e)}"
        )

@app.post("/repurpose-drug", tags=["Drug Repurposing"])
def repurpose_drug(request: dict):
    """
    Drug Repurposing Mode — find new disease indications for an existing drug.

    Input:
        drug_name    : str  — Name of the drug to repurpose
        current_use  : str  — Optional known indication

    Returns:
        repurposing_candidates: list of disease candidates with reasoning
        mechanism_summary:      str
        confidence:             str
    """
    from backend.services.hypothesis_service import client, LLM_MODEL, LLM_PROVIDER

    drug_name   = str(request.get("drug_name","")).strip()
    current_use = str(request.get("current_use","")).strip()

    if not drug_name:
        raise HTTPException(status_code=422, detail="drug_name is required")

    # ── Known drug mechanisms database (lightweight) ──────────
    KNOWN_DRUGS = {
        "LECANEMAB": {
            "mechanism": "Anti-amyloid beta antibody — binds and clears Aβ aggregates",
            "primary":   "Alzheimer disease (Phase 4)",
            "targets":   ["APP","amyloid-beta"]
        },
        "METFORMIN": {
            "mechanism": "AMPK activator — reduces hepatic glucose production",
            "primary":   "Type 2 diabetes",
            "targets":   ["AMPK","mTOR","FOXO1"]
        },
        "NIROGACESTAT": {
            "mechanism": "Gamma-secretase inhibitor — blocks PSEN1/PSEN2 cleavage activity",
            "primary":   "Desmoid tumors (Phase 4)",
            "targets":   ["PSEN1","PSEN2","Notch"]
        },
        "SEMAGACESTAT": {
            "mechanism": "Gamma-secretase inhibitor — reduces Aβ production",
            "primary":   "Alzheimer disease (discontinued)",
            "targets":   ["PSEN1","gamma-secretase"]
        },
        "ADUCANUMAB": {
            "mechanism": "Anti-amyloid antibody targeting Aβ plaques",
            "primary":   "Alzheimer disease (FDA approved)",
            "targets":   ["APP","amyloid-beta"]
        },
        "SILDENAFIL": {
            "mechanism": "PDE5 inhibitor — increases cGMP, causes vasodilation",
            "primary":   "Erectile dysfunction, Pulmonary hypertension",
            "targets":   ["PDE5A","cGMP"]
        },
        "RAPAMYCIN": {
            "mechanism": "mTOR inhibitor — suppresses mTORC1 signaling",
            "primary":   "Organ transplant rejection",
            "targets":   ["MTOR","FKBP12"]
        },
    }

    drug_upper = drug_name.upper()
    drug_info  = KNOWN_DRUGS.get(drug_upper, {
        "mechanism": f"Mechanism of {drug_name} (from general knowledge)",
        "primary":   current_use or "Unknown",
        "targets":   []
    })

    if LLM_PROVIDER == "mock" or client is None:
        return {
            "success": True,
            "drug_name": drug_name,
            "mechanism_summary": drug_info["mechanism"],
            "repurposing_candidates": [
                {
                    "disease":     "Parkinson disease",
                    "rationale":   "Shared pathway with current indication",
                    "confidence":  "Medium",
                    "evidence":    "Preclinical models show promise",
                    "next_step":   "Phase 2 trial design"
                }
            ],
            "confidence": "Mock"
        }

    prompt = f"""You are a drug repurposing expert with deep knowledge of disease mechanisms, drug targets, and clinical translation.

DRUG TO REPURPOSE: {drug_name}
PRIMARY INDICATION: {drug_info['primary']}
MECHANISM: {drug_info['mechanism']}
KNOWN TARGETS: {', '.join(drug_info['targets']) if drug_info['targets'] else 'Unknown'}

Your task: Identify 3-4 compelling disease indications where {drug_name} might be repurposed.

Consider:
1. Shared molecular pathways with the drug's known mechanism
2. Diseases where the drug's targets are implicated
3. Historical repurposing precedents for similar drug classes
4. Current clinical evidence or trials for alternative indications
5. Mechanistic plausibility (not just association)

Return ONLY a JSON object:
{{
  "mechanism_summary": "2-sentence explanation of the drug's mechanism relevant to repurposing",
  "repurposing_candidates": [
    {{
      "disease": "Disease name",
      "rationale": "2-3 sentences: WHY this drug might work for this disease mechanistically",
      "shared_pathway": "The molecular pathway linking the drug to this disease",
      "confidence": "High / Medium / Low",
      "evidence_level": "Preclinical / Phase 1 / Phase 2 / Observational / Theoretical",
      "key_challenge": "Main obstacle to this repurposing",
      "next_step": "Specific recommended next step (concrete experiment or trial)"
    }}
  ],
  "overall_repurposing_potential": "High / Medium / Low",
  "repurposing_rationale": "1-2 sentences on why this drug class is/isn't generally good for repurposing"
}}

Rank candidates by confidence (highest first). Return ONLY valid JSON.
"""

    try:
        response = client.chat.completions.create(
            model   = LLM_MODEL,
            messages= [
                {"role": "system", "content": "Drug repurposing expert. Return only valid JSON."},
                {"role": "user",   "content": prompt}
            ],
            temperature = 0.3,
            max_tokens  = 1500,
        )

        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw   = "\n".join(lines[1:-1])

        result = json.loads(raw)

        return {
            "success":                   True,
            "drug_name":                 drug_name,
            "primary_indication":        drug_info["primary"],
            "mechanism_summary":         result.get("mechanism_summary",""),
            "repurposing_candidates":    result.get("repurposing_candidates",[]),
            "overall_potential":         result.get("overall_repurposing_potential","Medium"),
            "repurposing_rationale":     result.get("repurposing_rationale",""),
            "confidence":                "AI-generated"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Repurposing analysis failed: {str(e)}"
        )

@app.post("/generate-pdf-report", tags=["Reports"])
def generate_pdf_report_endpoint(request: AnalysisRequest):
    """
    Generate a downloadable PDF research report for a disease analysis.
    Uses cached pipeline result if available.
    Returns PDF bytes as application/pdf.
    """
    from backend.services.pipeline_service   import run_data_pipeline
    from backend.services.hypothesis_service import generate_hypotheses
    from backend.services.hypothesis_service import generate_literature_review
    from backend.services.report_service     import generate_pdf_report

    # Run pipeline (uses cache)
    pipeline = run_data_pipeline(
        disease_name = request.disease_name,
        max_targets  = request.max_targets,
        max_papers   = request.max_papers,
        max_drugs    = request.max_drugs
    )

    if pipeline.analysis_status == "error":
        raise HTTPException(status_code=422, detail=pipeline.error_message)

    # Generate hypotheses if not cached
    if not pipeline.hypotheses:
        pipeline.hypotheses = generate_hypotheses(pipeline, 3)

    if not pipeline.literature_review:
        pipeline.literature_review = generate_literature_review(pipeline)

    # Serialize to dict for report
    try:
        data = pipeline.model_dump()
    except Exception:
        data = pipeline.dict()

    # Generate PDF
    try:
        pdf_bytes = generate_pdf_report(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    filename = f"AI_Scientist_{request.disease_name.replace(' ','_')}.pdf"

    return Response(
        content     = pdf_bytes,
        media_type  = "application/pdf",
        headers     = {
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )

@app.post("/ask-question", tags=["Chat"])
def ask_question(request: dict):
    """
    AI Scientist Chat — Ask anything about a disease analysis.

    Input:
        question     : str  — The user's question
        disease_name : str  — Optional disease context
        context_data : dict — Optional pipeline data for richer answers

    Returns:
        answer       : str
        sources_used : list
        confidence   : str
    """
    from backend.services.hypothesis_service import client, LLM_MODEL, LLM_PROVIDER

    question     = str(request.get("question","")).strip()
    disease_name = str(request.get("disease_name","")).strip()
    context_data = request.get("context_data") or {}

    if not question:
        raise HTTPException(status_code=422, detail="question is required")

    if LLM_PROVIDER == "mock" or client is None:
        return {
            "success": True,
            "answer": (
                f"Mock answer for: '{question}'\n\n"
                "To get real AI answers, configure your OPENAI_API_KEY in .env"
            ),
            "sources_used": ["Mock mode"],
            "confidence": "N/A"
        }

    # ── Build rich context from pipeline data ─────────────────
    context_parts = []

    if disease_name:
        context_parts.append(f"Disease being analyzed: {disease_name}")

    if context_data:
        # Proteins
        proteins = context_data.get("protein_targets", [])
        if proteins:
            prot_str = ", ".join([
                f"{p.get('gene_symbol','')} (score: {p.get('association_score',0):.2f})"
                for p in proteins[:5]
            ])
            context_parts.append(f"Key protein targets: {prot_str}")

        # Drugs
        drugs = context_data.get("drugs", [])
        if drugs:
            drug_str = ", ".join([
                f"{d.get('drug_name','')} (Phase {d.get('clinical_phase','?')}, "
                f"Risk: {d.get('risk_level','?')})"
                for d in drugs[:5]
            ])
            context_parts.append(f"Available drugs: {drug_str}")

        # Hypotheses
        hypotheses = context_data.get("hypotheses", [])
        if hypotheses:
            best = hypotheses[0] if hypotheses else {}
            context_parts.append(
                f"Top hypothesis: {best.get('title','')} "
                f"(Score: {best.get('final_score',0):.0%})"
            )
            if len(hypotheses) > 1:
                context_parts.append(
                    f"Other hypotheses: " +
                    "; ".join([h.get("title","") for h in hypotheses[1:3]])
                )

        # Evidence
        ev = context_data.get("evidence_strength") or {}
        if ev:
            context_parts.append(
                f"Evidence strength: {ev.get('evidence_label','')} "
                f"({ev.get('total_papers',0)} papers)"
            )

        # Decision
        ds = context_data.get("decision_summary") or {}
        if ds:
            gng = ds.get("go_no_go") or {}
            context_parts.append(
                f"Overall decision: {gng.get('decision','Unknown')} "
                f"({gng.get('confidence_in_decision',0):.0%} confident) — "
                f"Recommended: {ds.get('recommended_drug','')} → {ds.get('target_protein','')}"
            )

        # Papers
        papers = context_data.get("papers", [])
        if papers:
            paper_titles = "; ".join([p.get("title","")[:60] for p in papers[:3]])
            context_parts.append(f"Recent papers: {paper_titles}")

    context_str = "\n".join(context_parts) if context_parts else "No analysis context available."

    # ── System prompt ─────────────────────────────────────────
    system_prompt = f"""You are AI Scientist, an expert biomedical research assistant specializing in drug discovery and translational medicine.

You have access to a real analysis of {disease_name or 'a disease'} performed using OpenTargets, FDA FAERS, PubMed, and AlphaFold data.

CURRENT ANALYSIS CONTEXT:
{context_str}

YOUR ROLE:
- Answer questions about the disease, proteins, drugs, pathways, and hypotheses shown above
- Provide scientifically accurate, evidence-based answers
- Reference specific proteins, drugs, and scores from the context when relevant
- Be concise but comprehensive (3-5 sentences typical)
- If asked to compare, use specific data from the context
- If asked about risk, reference FDA signals and risk levels
- If asked to explain simply, use analogies
- If the question is outside your context, say so clearly and answer from general knowledge

STYLE:
- Professional but accessible
- Always ground answers in the analysis data when possible
- Use specific numbers (scores, phases, counts) when relevant
- Structure longer answers with clear paragraphs"""

    try:
        response = client.chat.completions.create(
            model   = LLM_MODEL,
            messages= [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": question}
            ],
            temperature = 0.4,
            max_tokens  = 600,
        )

        answer = response.choices[0].message.content.strip()

        # Determine what sources were used
        sources = []
        if context_data.get("protein_targets"): sources.append("OpenTargets protein data")
        if context_data.get("drugs"):           sources.append("FDA FAERS drug data")
        if context_data.get("papers"):          sources.append("PubMed literature")
        if context_data.get("hypotheses"):      sources.append("Generated hypotheses")
        if not sources:                         sources.append("General biomedical knowledge")

        return {
            "success":     True,
            "answer":      answer,
            "sources_used":sources,
            "confidence":  "High" if context_data else "Medium",
            "question":    question,
            "disease":     disease_name
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")

# ════════════════════════════════════════════════════════════
# PRODUCTIZED API ENDPOINTS
# ════════════════════════════════════════════════════════════

@app.post("/api/v1/generate-hypothesis", tags=["Product API"])
def api_generate_hypothesis(
    request:  AnalysisRequest,
    key_info: dict = Depends(optional_api_key)
):
    """
    **Product API**: Generate ranked biomedical hypotheses.

    Returns top 3 ranked hypotheses with:
    - Composite scoring breakdown
    - Causal analysis (Likely Causal / Correlational)
    - Experimental validation suggestions
    - Critical evaluation

    **Authentication**: Add header `X-API-Key: demo-key-free-001`

    **Rate limits**:
    - Free tier: 10 requests/day
    - Pro tier: 100 requests/day
    """
    from backend.services.pipeline_service   import run_data_pipeline
    from backend.services.hypothesis_service import generate_hypotheses
    from backend.services.pipeline_service   import compute_decision_summary

    start = time.time()

    pipeline = run_data_pipeline(
        disease_name = request.disease_name,
        max_targets  = request.max_targets,
        max_papers   = request.max_papers,
        max_drugs    = request.max_drugs
    )

    if pipeline.analysis_status == "error":
        raise HTTPException(status_code=422,
                            detail=pipeline.error_message)

    hypotheses             = generate_hypotheses(pipeline, 3)
    pipeline.hypotheses    = hypotheses
    pipeline.decision_summary = compute_decision_summary(pipeline)

    elapsed = round(time.time() - start, 2)

    return {
        "success":      True,
        "disease":      pipeline.disease_name,
        "elapsed_s":    elapsed,
        "api_tier":     key_info.get("tier","anonymous"),
        "hypotheses": [
            {
                "rank":            h.rank,
                "title":           h.title,
                "final_score":     h.final_score,
                "confidence":      h.confidence_score,
                "key_proteins":    h.key_proteins,
                "key_drugs":       h.key_drugs,
                "causal_label":    h.causal_analysis.causal_label
                                   if h.causal_analysis else "Unknown",
                "causal_score":    h.causal_analysis.causal_score
                                   if h.causal_analysis else 0.0,
                "validation_type": h.validation_suggestion.validation_type
                                   if h.validation_suggestion else "Unknown",
                "critique_severity": h.critique.critique_severity
                                     if h.critique else "Unknown",
                "evidence_summary":h.evidence_summary,
                "reasoning_steps": h.reasoning_steps
            }
            for h in hypotheses
        ],
        "decision": {
            "recommended_drug":  pipeline.decision_summary.recommended_drug
                                 if pipeline.decision_summary else "",
            "target_protein":    pipeline.decision_summary.target_protein
                                 if pipeline.decision_summary else "",
            "confidence":        pipeline.decision_summary.confidence_score
                                 if pipeline.decision_summary else 0.0,
            "risk_level":        pipeline.decision_summary.risk_level
                                 if pipeline.decision_summary else "",
            "suggested_action":  pipeline.decision_summary.suggested_action
                                 if pipeline.decision_summary else ""
        }
    }


@app.post("/api/v1/rank-drugs", tags=["Product API"])
def api_rank_drugs(
    request:  AnalysisRequest,
    key_info: dict = Depends(optional_api_key)
):
    """
    **Product API**: Rank drugs for a disease by evidence strength.

    Returns drugs sorted by:
    - Clinical phase
    - Target protein association score
    - FDA risk level

    **Authentication**: Add header `X-API-Key: demo-key-free-001`
    """
    from backend.services.pipeline_service import run_data_pipeline

    pipeline = run_data_pipeline(
        disease_name = request.disease_name,
        max_targets  = request.max_targets,
        max_papers   = request.max_papers,
        max_drugs    = request.max_drugs
    )

    if pipeline.analysis_status == "error":
        raise HTTPException(status_code=422,
                            detail=pipeline.error_message)

    # Score and rank drugs
    PHASE_SCORES = {4: 1.0, 3: 0.75, 2: 0.5, 1: 0.25}
    RISK_PENALTY = {"High": 0.3, "Medium": 0.1,
                    "Low": 0.0, "Unknown": 0.05}

    protein_scores = {
        pt.gene_symbol: pt.association_score
        for pt in pipeline.protein_targets
    }

    ranked_drugs = []
    for drug in pipeline.drugs:
        phase        = drug.clinical_phase or 0
        phase_score  = PHASE_SCORES.get(phase, 0.1)
        protein_score= protein_scores.get(drug.target_gene, 0.5)
        risk_penalty = RISK_PENALTY.get(drug.risk_level, 0.05)
        drug_score   = round(
            0.5 * phase_score +
            0.4 * protein_score -
            0.1 * risk_penalty, 4
        )

        ranked_drugs.append({
            "drug_name":     drug.drug_name,
            "target_gene":   drug.target_gene,
            "clinical_phase":drug.clinical_phase,
            "mechanism":     drug.mechanism,
            "risk_level":    drug.risk_level,
            "drug_score":    drug_score,
            "phase_score":   phase_score,
            "protein_score": protein_score,
            "risk_penalty":  risk_penalty
        })

    ranked_drugs.sort(key=lambda x: x["drug_score"], reverse=True)
    for i, d in enumerate(ranked_drugs, 1):
        d["rank"] = i

    return {
        "success":      True,
        "disease":      pipeline.disease_name,
        "api_tier":     key_info.get("tier","anonymous"),
        "total_drugs":  len(ranked_drugs),
        "ranked_drugs": ranked_drugs
    }


@app.post("/api/v1/analyze-risk", tags=["Product API"])
def api_analyze_risk(
    request:  AnalysisRequest,
    key_info: dict = Depends(optional_api_key)
):
    """
    **Product API**: FDA risk analysis for disease-related drugs.

    Returns:
    - Risk classification per drug (High/Medium/Low)
    - Top adverse events from FDA FAERS
    - Risk summary statistics
    - Recommended monitoring protocols

    **Authentication**: Add header `X-API-Key: demo-key-free-001`
    """
    from backend.services.pipeline_service import run_data_pipeline

    pipeline = run_data_pipeline(
        disease_name = request.disease_name,
        max_targets  = request.max_targets,
        max_papers   = request.max_papers,
        max_drugs    = request.max_drugs
    )

    if pipeline.analysis_status == "error":
        raise HTTPException(status_code=422,
                            detail=pipeline.error_message)

    risk_summary = {"High": 0, "Medium": 0,
                    "Low": 0, "Unknown": 0}

    drug_risks = []
    for drug in pipeline.drugs:
        risk = drug.risk_level
        risk_summary[risk] = risk_summary.get(risk, 0) + 1

        top_ae = None
        if drug.fda_adverse_events:
            ae     = drug.fda_adverse_events[0]
            top_ae = {"reaction": ae.reaction, "count": ae.count}

        monitoring = {
            "High":    "Monthly safety monitoring required. "
                       "Review benefit-risk before prescribing.",
            "Medium":  "Standard clinical monitoring. "
                       "Report adverse events.",
            "Low":     "Routine monitoring sufficient.",
            "Unknown": "Insufficient data. Monitor closely."
        }.get(risk, "Monitor as per clinical guidelines.")

        drug_risks.append({
            "drug_name":      drug.drug_name,
            "target_gene":    drug.target_gene,
            "clinical_phase": drug.clinical_phase,
            "risk_level":     risk,
            "risk_description":drug.risk_description[:100],
            "top_fda_signal": top_ae,
            "monitoring_protocol": monitoring
        })

    # Overall risk assessment
    if risk_summary["High"] > 0:
        overall = "High — multiple high-risk agents identified"
    elif risk_summary["Medium"] >= 2:
        overall = "Medium — several moderate-risk agents present"
    else:
        overall = "Low-Medium — manageable risk profile"

    return {
        "success":          True,
        "disease":          pipeline.disease_name,
        "api_tier":         key_info.get("tier","anonymous"),
        "overall_risk":     overall,
        "risk_summary":     risk_summary,
        "drug_risks":       drug_risks,
        "recommendation":   (
            "Prioritize drugs with Low/Medium risk and Phase 3+ "
            "clinical evidence. Avoid High risk agents unless "
            "benefit clearly outweighs risk."
        )
    }


@app.get("/api/v1/decision-summary/{disease_name}",
         tags=["Product API"])
def api_decision_summary(
    disease_name: str,
    key_info:     dict = Depends(optional_api_key)
):
    """
    **Product API**: Get the top decision recommendation for a disease.

    Returns the single best drug-protein hypothesis with:
    - Recommended drug and target
    - Confidence score
    - Risk level
    - Suggested next action

    **Authentication**: Add header `X-API-Key: demo-key-free-001`

    **Example**: GET /api/v1/decision-summary/Alzheimer%20disease
    """
    from backend.services.pipeline_service   import (
        run_data_pipeline, compute_decision_summary
    )
    from backend.services.hypothesis_service import generate_hypotheses

    pipeline = run_data_pipeline(
        disease_name = disease_name,
        max_targets  = 5,
        max_papers   = 4,
        max_drugs    = 3
    )

    if pipeline.analysis_status == "error":
        raise HTTPException(status_code=422,
                            detail=pipeline.error_message)

    hypotheses          = generate_hypotheses(pipeline, 3)
    pipeline.hypotheses = hypotheses
    ds = compute_decision_summary(pipeline)

    return {
        "success":          True,
        "disease":          disease_name,
        "api_tier":         key_info.get("tier","anonymous"),
        "recommendation": {
            "best_hypothesis":   ds.best_hypothesis,
            "recommended_drug":  ds.recommended_drug,
            "target_protein":    ds.target_protein,
            "pathway":           ds.target_pathway,
            "confidence_score":  ds.confidence_score,
            "confidence_label":  ds.confidence_label,
            "risk_level":        ds.risk_level,
            "reasoning":         ds.reasoning_summary,
            "suggested_action":  ds.suggested_action,
            "evidence_basis":    ds.evidence_basis
        }
    }


@app.get("/api/v1/usage", tags=["Product API"])
def api_usage_stats(
    key_info: dict = Depends(optional_api_key)
):
    """
    **Product API**: Get your API usage statistics.

    **Authentication**: Add header `X-API-Key: demo-key-free-001`
    """
    api_key  = key_info.get("api_key","")
    stats    = usage_tracker.get_stats(api_key) if api_key else \
               usage_tracker.get_stats()

    return {
        "success":    True,
        "tier":       key_info.get("tier","anonymous"),
        "usage":      stats,
        "limits": {
            "requests_per_day": key_info.get("requests_per_day",0),
            "features":         key_info.get("features",[])
        }
    }


@app.get("/api/v1/keys", tags=["Product API"])
def api_available_keys():
    """
    **Product API**: List available demo API keys for testing.
    In production this would be replaced by a key management system.
    """
    return {
        "demo_keys": [
            {
                "key":         k,
                "name":        v["name"],
                "tier":        v["tier"],
                "daily_limit": v["requests_per_day"],
                "description": v["description"]
            }
            for k, v in VALID_API_KEYS.items()
            if k != "internal-dev-key"  # Hide internal key
        ],
        "usage_instructions": {
            "header":  "X-API-Key",
            "example": "curl -H 'X-API-Key: demo-key-free-001' ...",
            "docs":    "http://localhost:8000/docs"
        }
    }

@app.post("/network-data", tags=["Visualization"])
def get_network_data(request: AnalysisRequest):
    """
    Generate protein-drug interaction network data.
    Returns nodes and edges for frontend visualization.
    Uses cached pipeline result if available.
    """
    from backend.services.pipeline_service   import run_data_pipeline
    from backend.services.hypothesis_service import generate_hypotheses
    from backend.services.network_service    import build_network_data

    # Run pipeline (uses cache if available)
    pipeline_result = run_data_pipeline(
        disease_name = request.disease_name,
        max_targets  = request.max_targets,
        max_papers   = request.max_papers,
        max_drugs    = request.max_drugs
    )

    if pipeline_result.analysis_status == "error":
        raise HTTPException(status_code=422,
                            detail=pipeline_result.error_message)

    # Generate hypotheses for pathway data
    if not pipeline_result.hypotheses:
        pipeline_result.hypotheses = generate_hypotheses(
            pipeline_result, num_hypotheses=3
        )

    # Build network
    network_data = build_network_data(pipeline_result)

    return {
        "success":      True,
        "disease_name": pipeline_result.disease_name,
        "network":      network_data
    }


@app.post("/analyze-disease", response_model=AnalysisResponse, tags=["Analysis"])
def analyze_disease(request: AnalysisRequest):
    """
    MAIN ENDPOINT — Full pipeline:
    disease → proteins → drugs → papers → hypotheses → decision
    """
    start_time = time.time()
    print(f"\n📥 Request received: '{request.disease_name}'")

    try:
        # ── Stage 1-3: Data Pipeline ──────────────────────────
        pipeline_result = run_data_pipeline(
            disease_name = request.disease_name,
            max_targets  = request.max_targets,
            max_papers   = request.max_papers,
            max_drugs    = request.max_drugs
        )
        # Auto-track this disease for future updates
        updates_store.add_tracked_disease(request.disease_name)

        if pipeline_result.analysis_status == "error":
            raise HTTPException(
                status_code = 422,
                detail      = f"Pipeline error: {pipeline_result.error_message}"
            )

        if not pipeline_result.protein_targets:
            raise HTTPException(
                status_code = 404,
                detail      = f"No protein targets found for '{request.disease_name}'."
            )

        # ── Stage 4: Hypothesis Generation ───────────────────
        hypotheses = generate_hypotheses(pipeline_result, num_hypotheses=3)
        pipeline_result.hypotheses = hypotheses

        # ── Stage 5: Decision Summary ─────────────────────────
        # Must run AFTER hypotheses are populated
        from backend.services.pipeline_service import compute_decision_summary
        pipeline_result.decision_summary = compute_decision_summary(pipeline_result)

        # ── V4: GO/NO-GO for overall analysis ────────────────
        from backend.services.decision_service import \
            compute_analysis_go_no_go
        if pipeline_result.decision_summary:
            pipeline_result.decision_summary.go_no_go = \
                compute_analysis_go_no_go(pipeline_result)
            gng = pipeline_result.decision_summary.go_no_go
            print(f"\n🚦 Overall Decision: "
                  f"{gng.decision_emoji} {gng.decision} "
                  f"({gng.confidence_in_decision:.0%} confident)")
            # ── V4: Literature review ─────────────────────────────
        from backend.services.hypothesis_service import \
            generate_literature_review
        pipeline_result.literature_review = \
            generate_literature_review(pipeline_result)
        print("📄 Literature review generated")

        # ── Ingest into knowledge graph ───────────────────────
        try:
            added = knowledge_graph.ingest_pipeline_result(pipeline_result)
            print(f"📊 Knowledge graph updated: "
                  f"+{added['proteins']} proteins, "
                  f"+{added['drugs']} drugs, "
                  f"+{added['edges']} edges")
        except Exception as e:
            print(f"⚠️  Knowledge graph ingest error: {e}")

        ds = pipeline_result.decision_summary
        print(f"\n🎯 Decision Summary:")
        print(f"   Drug       : {ds.recommended_drug}")
        print(f"   Protein    : {ds.target_protein}")
        print(f"   Confidence : {ds.confidence_score:.0%}")
        print(f"   Risk       : {ds.risk_level}")

        elapsed = round(time.time() - start_time, 2)
        print(f"\n✅ Analysis complete in {elapsed}s")
        print(f"   Proteins   : {len(pipeline_result.protein_targets)}")
        print(f"   Drugs      : {len(pipeline_result.drugs)}")
        print(f"   Papers     : {len(pipeline_result.papers)}")
        print(f"   Hypotheses : {len(hypotheses)}")

        return AnalysisResponse(
            success = True,
            data    = pipeline_result,
            message = f"Analysis complete in {elapsed}s"
        )

    except HTTPException:
        raise

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        raise HTTPException(
            status_code = 500,
            detail      = f"Internal server error: {str(e)}"
        )

        # ── V4: Ingest into knowledge graph ──────────────────
        added = knowledge_graph.ingest_pipeline_result(pipeline_result)
        print(f"📊 Knowledge graph updated: "
              f"+{added['proteins']} proteins, "
              f"+{added['drugs']} drugs, "
              f"+{added['edges']} edges")

@app.post("/compare-diseases", tags=["Analysis"])
def compare_diseases(request: MultiDiseaseRequest):
    """
    MULTI-DISEASE COMPARISON ENDPOINT

    Runs full pipeline for each disease in parallel,
    then identifies:
    - Shared protein targets across diseases
    - Drugs appearing in multiple diseases
    - Cross-disease scoring for drug repurposing

    Example request:
    {
        "diseases": ["Alzheimer disease", "Parkinson disease"],
        "max_targets": 5,
        "max_papers": 4,
        "max_drugs": 3
    }
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from backend.services.pipeline_service  import run_data_pipeline
    from backend.services.hypothesis_service import generate_hypotheses
    from backend.services.pipeline_service  import compute_decision_summary

    start_time = time.time()

    # Limit to 4 diseases max to keep runtime reasonable
    diseases = request.diseases[:4]
    print(f"\n📥 Multi-disease comparison: {diseases}")

    # ── Run all disease pipelines in parallel ─────────────────
    disease_results: dict[str, DiseaseAnalysisResult] = {}

    def run_single(disease_name: str) -> tuple:
        print(f"  [Thread] Starting: {disease_name}")
        try:
            pipeline = run_data_pipeline(
                disease_name = disease_name,
                max_targets  = request.max_targets,
                max_papers   = request.max_papers,
                max_drugs    = request.max_drugs
            )
            if pipeline.analysis_status == "complete":
                hyps = generate_hypotheses(pipeline, num_hypotheses=3)
                pipeline.hypotheses      = hyps
                pipeline.decision_summary= compute_decision_summary(pipeline)
            return (disease_name, pipeline)
        except Exception as e:
            print(f"  [Thread] Error for {disease_name}: {e}")
            return (disease_name, None)

    with ThreadPoolExecutor(max_workers=len(diseases)) as executor:
        futures = {executor.submit(run_single, d): d for d in diseases}
        for future in as_completed(futures):
            name, result = future.result()
            if result:
                disease_results[name] = result
                print(f"  ✅ Completed: {name}")

    if not disease_results:
        raise HTTPException(status_code=500,
                            detail="All disease pipelines failed")

    # ── Find shared proteins ──────────────────────────────────
    protein_map: dict[str, dict] = {}

    for disease_name, result in disease_results.items():
        for pt in result.protein_targets:
            sym = pt.gene_symbol
            if sym not in protein_map:
                protein_map[sym] = {
                    "gene_symbol":     sym,
                    "protein_name":    pt.protein_name,
                    "diseases":        [],
                    "scores":          []
                }
            protein_map[sym]["diseases"].append(disease_name)
            protein_map[sym]["scores"].append(pt.association_score)

    shared_proteins = []
    for sym, info in protein_map.items():
        if len(info["diseases"]) >= 2:   # Appears in 2+ diseases
            avg = round(sum(info["scores"]) / len(info["scores"]), 4)
            shared_proteins.append(SharedProtein(
                gene_symbol      = sym,
                protein_name     = info["protein_name"],
                diseases         = info["diseases"],
                avg_association  = avg,
                appears_in       = len(info["diseases"])
            ))

    # Sort by appears_in then avg_association
    shared_proteins.sort(
        key=lambda x: (x.appears_in, x.avg_association), reverse=True
    )

    # ── Build drug comparison table ───────────────────────────
    drug_map: dict[str, dict] = {}

    for disease_name, result in disease_results.items():
        # Get best hypothesis per drug for this disease
        hyp_by_drug = {}
        for hyp in result.hypotheses:
            for drug_name in hyp.key_drugs:
                key = drug_name.upper()
                if key not in hyp_by_drug or hyp.final_score > hyp_by_drug[key]["score"]:
                    hyp_by_drug[key] = {
                        "score":  hyp.final_score,
                        "conf":   hyp.confidence_score,
                        "title":  hyp.title
                    }

        for drug in result.drugs:
            key       = drug.drug_name.upper()
            hyp_data  = hyp_by_drug.get(key, {})

            if key not in drug_map:
                drug_map[key] = {
                    "drug_name":      drug.drug_name,
                    "target_protein": drug.target_gene,
                    "mechanism":      drug.mechanism[:80],
                    "entries":        []
                }

            drug_map[key]["entries"].append(DiseaseComparisonEntry(
                disease_name     = disease_name,
                final_score      = hyp_data.get("score", 0.0),
                confidence       = hyp_data.get("conf",  0.0),
                risk_level       = drug.risk_level,
                hypothesis_title = hyp_data.get("title", "")[:60]
            ))

    drug_rows = []
    for key, info in drug_map.items():
        entries    = info["entries"]
        scores     = [e.final_score for e in entries if e.final_score > 0]
        avg_score  = round(sum(scores) / len(scores), 4) if scores else 0.0

        # Overlap score: consistency across diseases (std dev penalty)
        if len(scores) >= 2:
            mean   = avg_score
            stddev = (sum((s - mean)**2 for s in scores) / len(scores)) ** 0.5
            overlap= round(max(0.0, 1.0 - stddev), 4)
        else:
            overlap = 0.5  # Single disease

        drug_rows.append(DrugComparisonRow(
            drug_name      = info["drug_name"],
            target_protein = info["target_protein"],
            mechanism      = info["mechanism"],
            diseases       = entries,
            overlap_score  = overlap,
            avg_score      = avg_score,
            appears_in     = len(entries)
        ))

    # Sort by: appears_in (more diseases = better), then avg_score
    drug_rows.sort(
        key=lambda x: (x.appears_in, x.avg_score), reverse=True
    )

    # ── Identify repurposing opportunities ────────────────────
    repurposing = []
    for row in drug_rows:
        if row.appears_in >= 2:
            diseases_str = " and ".join([e.disease_name for e in row.diseases])
            repurposing.append(
                f"{row.drug_name} targets {row.target_protein} "
                f"in both {diseases_str} "
                f"(avg score: {row.avg_score:.0%}, "
                f"consistency: {row.overlap_score:.0%})"
            )

    comparison = MultiDiseaseComparison(
        diseases_analyzed         = list(disease_results.keys()),
        shared_proteins           = shared_proteins[:10],
        drug_comparison           = drug_rows[:15],
        total_shared_proteins     = len(shared_proteins),
        total_shared_drugs        = sum(1 for r in drug_rows if r.appears_in >= 2),
        repurposing_opportunities = repurposing[:5]
    )

    elapsed = round(time.time() - start_time, 2)
    print(f"\n✅ Multi-disease comparison complete in {elapsed}s")
    print(f"   Diseases        : {len(disease_results)}")
    print(f"   Shared proteins : {len(shared_proteins)}")
    print(f"   Shared drugs    : {comparison.total_shared_drugs}")

    return {
        "success":    True,
        "elapsed":    elapsed,
        "comparison": comparison.model_dump(),
        "individual": {
            name: {
                "disease_name":    r.disease_name,
                "protein_targets": [p.model_dump() for p in r.protein_targets],
                "drugs":           [d.model_dump() for d in r.drugs],
                "hypotheses":      [h.model_dump() for h in r.hypotheses],
                "decision_summary":r.decision_summary.model_dump()
                                   if r.decision_summary else None
            }
            for name, r in disease_results.items()
        },
        "message": f"Compared {len(disease_results)} diseases in {elapsed}s"
    }

@app.get("/knowledge-graph/stats", tags=["Knowledge Graph"])
def kg_stats():
    """Get knowledge graph statistics."""
    return {
        "success": True,
        "stats":   knowledge_graph.get_stats()
    }


@app.get("/knowledge-graph/insights", tags=["Knowledge Graph"])
def kg_insights():
    """Get cross-disease insights from knowledge graph."""
    return {
        "success":               True,
        "cross_disease_proteins":knowledge_graph.get_cross_disease_proteins(),
        "most_analyzed_drugs":   knowledge_graph.get_most_analyzed_drugs(5),
        "stats":                 knowledge_graph.get_stats()
    }


@app.get("/knowledge-graph/search", tags=["Knowledge Graph"])
def kg_search(query: str):
    """Search the knowledge graph."""
    return {
        "success": True,
        "query":   query,
        "results": knowledge_graph.search(query)
    }
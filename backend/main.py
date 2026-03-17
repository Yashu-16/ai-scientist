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
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.models.schemas import (
    AnalysisRequest,
    AnalysisResponse,
    DiseaseAnalysisResult
)
from backend.services.pipeline_service   import run_data_pipeline
from backend.services.hypothesis_service import generate_hypotheses


# ── App Lifecycle ────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs on startup and shutdown."""
    print("\n🧬 AI Scientist API starting up...")
    print("   Endpoints ready at http://localhost:8000")
    print("   API docs at     http://localhost:8000/docs\n")
    yield
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
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],   # In production: restrict to your domain
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
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


@app.post("/analyze-disease", response_model=AnalysisResponse, tags=["Analysis"])
def analyze_disease(request: AnalysisRequest):
    """
    MAIN ENDPOINT — Full pipeline: disease → proteins → drugs → papers → hypotheses.

    Takes a disease name and returns:
    - Protein targets with association scores
    - Drug-protein mappings with FDA adverse event signals
    - Supporting research papers
    - AI-generated hypotheses with confidence scores

    Example request body:
    {
        "disease_name": "Alzheimer disease",
        "max_targets": 5,
        "max_papers": 5,
        "max_drugs": 3
    }
    """

    start_time = time.time()

    print(f"\n📥 Request received: '{request.disease_name}'")

    try:
        # ── Stage 1-3: Data Pipeline ─────────────────────────
        pipeline_result = run_data_pipeline(
            disease_name = request.disease_name,
            max_targets  = request.max_targets,
            max_papers   = request.max_papers,
            max_drugs    = request.max_drugs
        )

        # Check pipeline succeeded
        if pipeline_result.analysis_status == "error":
            raise HTTPException(
                status_code = 422,
                detail      = f"Pipeline error: {pipeline_result.error_message}"
            )

        # Check we have enough data to generate hypotheses
        if not pipeline_result.protein_targets:
            raise HTTPException(
                status_code = 404,
                detail      = f"No protein targets found for '{request.disease_name}'. "
                              f"Try a more specific disease name."
            )

        # ── Stage 4: Hypothesis Generation ───────────────────
        hypotheses = generate_hypotheses(pipeline_result, num_hypotheses=3)
        pipeline_result.hypotheses = hypotheses

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
        raise  # Re-raise HTTP exceptions as-is

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        raise HTTPException(
            status_code = 500,
            detail      = f"Internal server error: {str(e)}"
        )
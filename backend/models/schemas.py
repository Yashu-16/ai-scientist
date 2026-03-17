# backend/models/schemas.py
# Purpose: Define all data structures used across the application.
# Pydantic models give us automatic validation, serialization,
# and clean documentation for our FastAPI endpoints.

from pydantic import BaseModel, Field
from typing import List, Optional


# ── Protein Target ───────────────────────────────────────────
class ProteinTarget(BaseModel):
    gene_symbol:        str
    protein_name:       str
    ensembl_id:         str
    biotype:            str
    association_score:  float
    function_description: str


# ── Drug ────────────────────────────────────────────────────
class FDAAdverseEvent(BaseModel):
    reaction: str
    count:    int


class Drug(BaseModel):
    drug_name:          str
    drug_type:          str
    clinical_phase:     Optional[int]   = None
    mechanism:          str
    description:        str             = ""
    target_gene:        str
    fda_adverse_events: List[FDAAdverseEvent] = []


# ── Research Paper ───────────────────────────────────────────
class ResearchPaper(BaseModel):
    source:         str                   # "PubMed" or "Semantic Scholar"
    title:          str
    abstract:       str
    summary:        str
    authors:        List[str]             = []
    year:           Optional[int]         = None
    citation_count: int                   = 0
    paper_id:       str                   = ""
    url:            str                   = ""


# ── Hypothesis ───────────────────────────────────────────────
class Hypothesis(BaseModel):
    title:            str        # One-line hypothesis statement
    explanation:      str        # Detailed scientific explanation
    simple_explanation: str      # ELI5 version
    confidence_score: float      # 0.0 to 1.0
    confidence_label: str        # "High" / "Medium" / "Low"
    key_proteins:     List[str]  = []
    key_drugs:        List[str]  = []
    evidence_summary: str        = ""


# ── Full Analysis Result ─────────────────────────────────────
class DiseaseAnalysisResult(BaseModel):
    disease_name:    str
    disease_id:      str                  = ""
    protein_targets: List[ProteinTarget]  = []
    drugs:           List[Drug]           = []
    papers:          List[ResearchPaper]  = []
    hypotheses:      List[Hypothesis]     = []
    analysis_status: str                  = "pending"  # pending | complete | error
    error_message:   str                  = ""


# ── API Request / Response ───────────────────────────────────
class AnalysisRequest(BaseModel):
    disease_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        example="Alzheimer disease"
    )
    max_targets:  int = Field(default=5,  ge=1, le=10)
    max_papers:   int = Field(default=5,  ge=1, le=10)
    max_drugs:    int = Field(default=3,  ge=1, le=5)


class AnalysisResponse(BaseModel):
    success:  bool
    data:     Optional[DiseaseAnalysisResult] = None
    message:  str = ""
# backend/models/schemas.py
# V2 — includes Evidence Strength, Risk fields, Ranking fields

from pydantic import BaseModel, Field
from typing import List, Optional


# ── Protein Target ────────────────────────────────────────────
class ProteinTarget(BaseModel):
    gene_symbol:          str
    protein_name:         str
    ensembl_id:           str
    biotype:              str
    association_score:    float
    function_description: str
    # ── Feature 6: AlphaFold fields ──────────────────────────
    alphafold_plddt:   float = 0.0    # Structural confidence 0.0-1.0
    alphafold_label:   str   = ""     # V.High / High / Medium / Low
    alphafold_color:   str   = ""     # Hex color for UI
    alphafold_source:  str   = ""     # "AlphaFold API" or "curated"


# ── Drug ─────────────────────────────────────────────────────
class FDAAdverseEvent(BaseModel):
    reaction: str
    count:    int


class Drug(BaseModel):
    drug_name:          str
    drug_type:          str
    clinical_phase:     Optional[int]         = None
    mechanism:          str
    description:        str                   = ""
    target_gene:        str
    fda_adverse_events: List[FDAAdverseEvent] = []
    risk_level:         str                   = "Unknown"
    risk_description:   str                   = ""


# ── Research Paper ────────────────────────────────────────────
class ResearchPaper(BaseModel):
    source:         str
    title:          str
    abstract:       str
    summary:        str
    authors:        List[str]     = []
    year:           Optional[int] = None
    citation_count: int           = 0
    paper_id:       str           = ""
    url:            str           = ""


# ── Evidence Strength ─────────────────────────────────────────
class EvidenceStrength(BaseModel):
    evidence_score:       float = 0.0
    evidence_label:       str   = ""
    evidence_color:       str   = ""
    total_papers:         int   = 0
    high_citation_papers: int   = 0
    recent_papers:        int   = 0
    avg_citations:        float = 0.0
    evidence_breakdown:   str   = ""


# ── Hypothesis ────────────────────────────────────────────────
class Hypothesis(BaseModel):
    title:              str
    explanation:        str
    simple_explanation: str
    confidence_score:   float
    confidence_label:   str

    # Ranking fields (Feature 1)
    rank:            int   = 0
    final_score:     float = 0.0
    protein_score:   float = 0.0
    drug_score:      float = 0.0
    paper_score:     float = 0.0
    risk_penalty:    float = 0.0
    score_breakdown: str   = ""

    key_proteins:    List[str] = []
    key_drugs:       List[str] = []
    evidence_summary: str      = ""
    reasoning_steps:  List[str] = []


# ── Full Analysis Result ──────────────────────────────────────
class DiseaseAnalysisResult(BaseModel):
    disease_name:      str
    disease_id:        str                        = ""
    protein_targets:   List[ProteinTarget]        = []
    drugs:             List[Drug]                 = []
    papers:            List[ResearchPaper]        = []
    hypotheses:        List[Hypothesis]           = []
    evidence_strength: Optional[EvidenceStrength] = None
    analysis_status:   str                        = "pending"
    error_message:     str                        = ""


# ── API Request / Response ────────────────────────────────────
class AnalysisRequest(BaseModel):
    disease_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        example="Alzheimer disease"
    )
    max_targets: int = Field(default=5, ge=1, le=10)
    max_papers:  int = Field(default=5, ge=1, le=10)
    max_drugs:   int = Field(default=3, ge=1, le=5)


class AnalysisResponse(BaseModel):
    success: bool
    data:    Optional[DiseaseAnalysisResult] = None
    message: str = ""
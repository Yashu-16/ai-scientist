// types/index.ts
// Complete type definitions matching the FastAPI backend responses exactly

export interface ProteinTarget {
  gene_symbol: string
  protein_name: string
  association_score: number
  alphafold_plddt: number
  alphafold_label: string
  alphafold_color: string
  function_description: string
}

export interface FDAAdverseEvent {
  reaction: string
  count: number
}

export interface CompetitionIntel {
  competition_level: string
  competition_color: string
  market_opportunity: string
  num_similar_drugs: number
  similar_drug_names: string[]
  strategic_note: string
  drug_class: string
}

export interface Drug {
  drug_name: string
  drug_type: string
  clinical_phase: number | string
  mechanism: string
  description?: string
  target_gene: string
  risk_level: "High" | "Medium" | "Low" | "Unknown"
  risk_description: string
  risk_color?: string
  fda_adverse_events: FDAAdverseEvent[]
  competition_intel?: CompetitionIntel
}

export interface Paper {
  title: string
  year: number | null
  source: string
  url?: string
  summary?: string
  abstract?: string
  citation_count?: number
  pmid?: string
}

export interface CausalEvidence {
  text: string
  causal_verb: string
  strength: string
  source: string
}

export interface CausalAnalysis {
  causal_score: number
  causal_label: string
  causal_color: string
  correlation_note: string
  causal_chain: string[]
  causal_verbs_found: string[]
  total_causal_hits: number
  total_papers_scanned?: number
  causal_evidence: CausalEvidence[]
}

export interface ValidationSuggestion {
  validation_type: string
  validation_color: string
  experiment_title: string
  experiment_description: string
  required_tools: string[]
  expected_outcome: string
  estimated_timeline: string
  difficulty: string
  difficulty_color: string
}

export interface HypothesisCritique {
  overall_assessment: string
  weaknesses: string[]
  contradictory_evidence: string[]
  risks: string[]
  confidence_impact: string
  salvage_suggestion: string
  critique_severity: string
  severity_color: string
}

export interface FailureReason {
  category: string
  reason: string
  severity: string
  evidence: string
  mitigation: string
}

export interface FailurePrediction {
  failure_risk_score: number
  failure_risk_label: string
  failure_risk_color: string
  top_failure_reason: string
  historical_context: string
  success_probability: number
  failure_reasons: FailureReason[]
  recommended_safeguards: string[]
}

export interface TimeToImpact {
  years_to_market?: number
  years_range: string
  current_stage: string
  next_milestone: string
  success_probability: number
  speed_category: string
  speed_color: string
  timeline_breakdown: string[]
  key_bottlenecks: string[]
}

export interface ExecutiveSummary {
  headline: string
  body: string
  market_opportunity: string
  bottom_line: string
  audience_level?: string
}

export interface UncertaintyFactor {
  factor: string
  impact: string
  description: string
}

export interface Uncertainty {
  uncertainty_score: number
  uncertainty_label: string
  uncertainty_color: string
  uncertainty_reason: string
  reliability_note: string
  low_paper_count: boolean
  weak_protein_assoc: boolean
  high_fda_risk: boolean
  no_causal_evidence: boolean
  limited_drug_data: boolean
  factors: UncertaintyFactor[]
}

export interface GoNoGo {
  decision: "GO" | "NO-GO" | "INVESTIGATE"
  decision_color: string
  decision_emoji: string
  confidence_in_decision: number
  composite_score?: number
  uncertainty_score?: number
  risk_level?: string
  evidence_label?: string
  primary_reason: string
  supporting_reasons: string[]
  blocking_reasons: string[]
  recommended_action: string
  conditions_to_flip: string
}

export interface Hypothesis {
  rank: number
  title: string
  explanation: string
  simple_explanation: string
  confidence_score: number
  confidence_label: string
  key_proteins: string[]
  key_drugs: string[]
  evidence_summary?: string
  final_score: number
  protein_score?: number
  drug_score?: number
  paper_score?: number
  risk_penalty?: number
  score_breakdown?: string
  reasoning_steps: string[]
  causal_analysis?: CausalAnalysis
  validation_suggestion?: ValidationSuggestion
  critique?: HypothesisCritique
  failure_prediction?: FailurePrediction
  time_to_impact?: TimeToImpact
  executive_summary?: ExecutiveSummary
  uncertainty?: Uncertainty
  go_no_go?: GoNoGo
}

export interface DecisionSummary {
  best_hypothesis: string
  recommended_drug: string
  target_protein: string
  target_pathway: string
  confidence_score: number
  confidence_label: string
  risk_level: string
  risk_color?: string
  reasoning_summary: string
  suggested_action: string
  evidence_basis: string
  go_no_go: GoNoGo
}

export interface EvidenceStrength {
  evidence_label: string
  evidence_score: number
  evidence_color: string
  total_papers: number
  high_citation_papers: number
  recent_papers: number
  evidence_breakdown: string
}

export interface AnalysisUncertainty {
  uncertainty_label: string
  uncertainty_score: number
  uncertainty_color: string
  uncertainty_reason: string
  reliability_note?: string
  low_paper_count?: boolean
  weak_protein_assoc?: boolean
  high_fda_risk?: boolean
  no_causal_evidence?: boolean
  limited_drug_data?: boolean
  factors?: UncertaintyFactor[]
}

export interface LiteratureReview {
  disease_name?: string
  background?: string
  current_research?: string
  research_gaps?: string
  proposed_hypothesis?: string
  supporting_evidence?: string
  risks_limitations?: string
  conclusion?: string
  generated_at?: string
}

export interface NetworkNode {
  id: string | number
  label: string
  color?: string
  size?: number
  title?: string
  [key: string]: unknown
}

export interface NetworkEdge {
  from: string | number
  to: string | number
  label?: string
  [key: string]: unknown
}

export interface NetworkData {
  nodes: NetworkNode[]
  edges: NetworkEdge[]
  stats: {
    total_nodes: number
    proteins: number
    drugs: number
    pathways: number
  }
}

export interface AnalysisResult {
  disease_name: string
  analysis_status: string
  protein_targets: ProteinTarget[]
  drugs: Drug[]
  papers: Paper[]
  hypotheses: Hypothesis[]
  decision_summary: DecisionSummary
  evidence_strength: EvidenceStrength
  analysis_uncertainty: AnalysisUncertainty
  literature_review?: LiteratureReview
}

export interface TrendItem {
  name: string
  mentions: number
  frequency: number
  trend: string
}

export interface EmergingOpportunity {
  signal: string
  description: string
  strength: string
  protein?: string
  mechanism?: string
}

export interface TrendData {
  trending_proteins: TrendItem[]
  trending_mechanisms: TrendItem[]
  trending_diseases: TrendItem[]
  emerging_opportunities: EmergingOpportunity[]
  total_papers_analyzed: number
  last_analyzed: string
}

export interface RepurposeCandidate {
  disease: string
  rationale: string
  shared_pathway: string
  confidence: string
  evidence_level: string
  key_challenge: string
  next_step: string
}

export interface RepurposeResult {
  success: boolean
  drug_name: string
  primary_indication: string
  mechanism_summary: string
  overall_potential: string
  repurposing_rationale: string
  repurposing_candidates: RepurposeCandidate[]
}

export interface PaperUpdate {
  title: string
  year: number
  pmid: string
  url: string
  is_new?: boolean
}

export interface UpdatesResponse {
  updates: Record<string, PaperUpdate[]>
  tracked_diseases: string[]
  stats: {
    last_check: string
    total_updates: number
    check_count: number
    updates_per_disease: Record<string, number>
  }
}

export interface KGInsights {
  stats: {
    node_count: number
    edge_count: number
    total_analyses: number
    total_proteins: number
  }
  cross_disease_proteins: {
    gene_symbol: string
    diseases: string[]
    avg_association?: number
  }[]
  most_analyzed_drugs: {
    drug_name?: string
    name?: string
    phase: string | number
    appearances: number
  }[]
}

export interface ChatMessage {
  role: "user" | "assistant"
  content: string
  sources?: string[]
}
from backend.services.hypothesis_service import add_causal_analysis
from backend.services.paper_service import extract_causal_evidence

print("✅ Both functions importable")

# Quick test of causal extraction
mock_papers = [{
    'abstract': 'NIROGACESTAT inhibits PSEN1 and reduces amyloid-beta production. This activates clearance pathways and promotes neuronal survival.',
    'summary': '',
    'title': 'Test paper',
    'citation_count': 0,
    'year': 2024
}]

result = extract_causal_evidence(mock_papers, ['PSEN1'], ['NIROGACESTAT'])

print(f"Causal score: {result['causal_score']}")
print(f"Causal label: {result['causal_label']}")
print(f"Verbs found : {result['causal_verbs_found']}")
print(f"Total hits  : {result['total_causal_hits']}")
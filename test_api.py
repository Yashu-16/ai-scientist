# test_api.py — verify scores + evidence strength
import requests
import json

response = requests.post(
    "http://localhost:8000/analyze-disease",
    json={
        "disease_name": "Alzheimer disease",
        "max_targets": 3,
        "max_papers":  3,
        "max_drugs":   2
    },
    timeout=180
)

data = response.json()

# Check hypothesis score fields
print("=" * 50)
print("HYPOTHESIS SCORE FIELDS:")
print("=" * 50)
for h in data["data"]["hypotheses"]:
    print(f"\nTitle        : {h['title'][:55]}")
    print(f"rank         : {h.get('rank')}")
    print(f"final_score  : {h.get('final_score')}")
    print(f"protein_score: {h.get('protein_score')}")
    print(f"drug_score   : {h.get('drug_score')}")
    print(f"paper_score  : {h.get('paper_score')}")
    print(f"risk_penalty : {h.get('risk_penalty')}")

# Check evidence strength
print("\n" + "=" * 50)
print("EVIDENCE STRENGTH:")
print("=" * 50)
print(json.dumps(data["data"].get("evidence_strength"), indent=2))
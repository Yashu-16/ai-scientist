import requests, json

BASE = "http://localhost:8000"

# Test available keys
print("\n" + "="*50)
print("AVAILABLE API KEYS:")
r = requests.get(f"{BASE}/api/v1/keys")
print(json.dumps(r.json(), indent=2)[:500])

# Test with free key
headers = {"X-API-Key": "demo-key-free-001"}

print("\n" + "="*50)
print("RANK DRUGS (with API key):")
r = requests.post(
    f"{BASE}/api/v1/rank-drugs",
    json={"disease_name":"Alzheimer disease",
          "max_targets":3,"max_papers":3,"max_drugs":2},
    headers=headers, timeout=120
)
data = r.json()
print(f"Status: {r.status_code}")
print(f"Tier: {data.get('api_tier')}")
for d in data.get("ranked_drugs",[])[:3]:
    print(f"  #{d['rank']} {d['drug_name']} "
          f"score={d['drug_score']} risk={d['risk_level']}")

print("\n" + "="*50)
print("DECISION SUMMARY (GET endpoint):")
r = requests.get(
    f"{BASE}/api/v1/decision-summary/Alzheimer%20disease",
    headers=headers, timeout=120
)
data = r.json()
print(f"Status: {r.status_code}")
rec = data.get("recommendation",{})
print(f"Drug: {rec.get('recommended_drug')}")
print(f"Conf: {rec.get('confidence_score'):.0%}")
print(f"Risk: {rec.get('risk_level')}")
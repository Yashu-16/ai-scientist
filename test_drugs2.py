import requests

# Test 1: Check what fields Target type has for drugs
q1 = """
query {
  target(ensemblId: "ENSG00000113924") {
    approvedSymbol
    knownDrugs(size: 3) {
      rows {
        drug { name }
      }
    }
  }
}
"""

# Test 2: Try associatedDiseases approach
q2 = """
query {
  disease(efoId: "MONDO:0008753") {
    id
    name
    knownDrugs(size: 5) {
      rows {
        drug { name maximumClinicalTrialPhase }
        target { approvedSymbol }
        mechanismOfAction
      }
    }
  }
}
"""

# Test 3: Try drug search by disease
q3 = """
query {
  drugs(chemblIds: []) {
    count
  }
}
"""

for i, q in enumerate([q1, q2, q3], 1):
    r = requests.post(
        "https://api.platform.opentargets.org/api/v4/graphql",
        json={"query": q},
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    print(f"\nTest {i}: {r.status_code}")
    print(r.text[:300])

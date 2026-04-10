import requests

# Test 1: Disease evidences without mechanismOfAction
q1 = """
query {
  disease(efoId: "MONDO_0008753") {
    id
    name
    evidences(ensemblIds: ["ENSG00000113924",
                           "ENSG00000158104",
                           "ENSG00000197594"]) {
      rows {
        drug {
          id
          name
          maximumClinicalStage
          drugType
          description
          mechanismsOfAction {
            rows {
              mechanismOfAction
              targets { approvedSymbol }
            }
          }
        }
        clinicalStage
        target { approvedSymbol }
      }
    }
  }
}
"""

# Test 2: Simpler - just drug name and phase
q2 = """
query {
  disease(efoId: "MONDO_0008753") {
    id
    name
    evidences(ensemblIds: ["ENSG00000113924",
                           "ENSG00000158104",
                           "ENSG00000197594"]) {
      rows {
        drug {
          id
          name
          maximumClinicalStage
          drugType
        }
        clinicalStage
        target { approvedSymbol }
      }
    }
  }
}
"""

for i, q in enumerate([q1, q2], 1):
    r = requests.post(
        "https://api.platform.opentargets.org/api/v4/graphql",
        json={"query": q},
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    print(f"\nTest {i}: {r.status_code}")
    print(r.text[:800])

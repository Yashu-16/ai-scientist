import requests

# Test 1: Use MONDO_0008753 (underscore) for disease
q1 = """
query {
  disease(efoId: "MONDO_0008753") {
    id
    name
  }
}
"""

# Test 2: Try evidences field for drug-disease links
q2 = """
query {
  disease(efoId: "MONDO_0008753") {
    id
    name
    evidences(ensemblIds: ["ENSG00000113924"], 
              enableIndirect: true,
              datasourceIds: ["chembl"],
              page: {index: 0, size: 5}) {
      rows {
        drug {
          id
          name
          maximumClinicalStage
          drugType
        }
        clinicalPhase
        clinicalStatus
        mechanismOfAction
        target { approvedSymbol }
      }
    }
  }
}
"""

# Test 3: Try drug field directly on target with evidences
q3 = """
query {
  target(ensemblId: "ENSG00000113924") {
    approvedSymbol
    evidences(efoIds: ["MONDO_0008753"],
              enableIndirect: true,
              datasourceIds: ["chembl"],
              page: {index: 0, size: 5}) {
      rows {
        drug {
          id
          name
          maximumClinicalStage
        }
        clinicalPhase
        mechanismOfAction
      }
    }
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
    print(r.text[:600])

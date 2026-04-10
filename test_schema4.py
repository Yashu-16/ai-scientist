import requests

# Test 1: Disease evidences with correct fields
q1 = """
query {
  disease(efoId: "MONDO_0008753") {
    id
    name
    evidences(ensemblIds: ["ENSG00000113924"],
              enableIndirect: true,
              datasourceIds: ["chembl"]) {
      rows {
        drug {
          id
          name
          maximumClinicalStage
          drugType
        }
        clinicalStage
        mechanismOfAction
        target { approvedSymbol }
      }
    }
  }
}
"""

# Test 2: Without datasource filter - get all evidence types
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
          description
        }
        clinicalStage
        mechanismOfAction
        target { approvedSymbol }
      }
    }
  }
}
"""

# Test 3: Target evidences with correct fields
q3 = """
query {
  target(ensemblId: "ENSG00000113924") {
    approvedSymbol
    evidences(efoIds: ["MONDO_0008753"]) {
      rows {
        drug {
          id
          name
          maximumClinicalStage
        }
        clinicalStage
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
    print(r.text[:800])

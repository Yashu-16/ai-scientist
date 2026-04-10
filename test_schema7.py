import requests

# Test 1: Get nitisinone with correct indication fields
q1 = """
query {
  drug(chemblId: "CHEMBL1337") {
    id
    name
    maximumClinicalStage
    drugType
    description
    indications {
      rows {
        disease { name id }
        indicationId
      }
    }
    mechanismsOfAction {
      rows {
        mechanismOfAction
        targets { approvedSymbol }
      }
    }
  }
}
"""

# Test 2: Search drugs for a common disease to understand the pattern
q2 = """
query {
  search(queryString: "parkinson",
         entityNames: ["drug"],
         page: {index: 0, size: 5}) {
    hits {
      id
      name
      object {
        ... on Drug {
          name
          maximumClinicalStage
          drugType
          description
        }
      }
    }
  }
}
"""

# Test 3: Get disease and find drugs via indications
q3 = """
query {
  disease(efoId: "MONDO_0008753") {
    id
    name
    evidences(ensemblIds: ["ENSG00000113924"],
              datasourceIds: ["chembl"]) {
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

for i, q in enumerate([q1, q2, q3], 1):
    r = requests.post(
        "https://api.platform.opentargets.org/api/v4/graphql",
        json={"query": q},
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    print(f"\nTest {i}: {r.status_code}")
    print(r.text[:800])

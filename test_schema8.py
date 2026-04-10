import requests

# Test 1: Search drugs for alkaptonuria by name
q1 = """
query {
  search(queryString: "alkaptonuria",
         entityNames: ["drug"],
         page: {index: 0, size: 10}) {
    hits {
      id
      name
      object {
        ... on Drug {
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
      }
    }
  }
}
"""

# Test 2: Get nitisinone indications with correct field name
q2 = """
query {
  drug(chemblId: "CHEMBL1337") {
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
    indications {
      rows {
        disease { name id }
        phases
      }
    }
  }
}
"""

# Test 3: Search Alzheimer drugs to confirm pattern works
q3 = """
query {
  search(queryString: "Alzheimer disease",
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

for i, q in enumerate([q1, q2, q3], 1):
    r = requests.post(
        "https://api.platform.opentargets.org/api/v4/graphql",
        json={"query": q},
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    print(f"\nTest {i}: {r.status_code}")
    print(r.text[:1000])

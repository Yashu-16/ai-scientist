import requests

# Test 1: Search for drugs related to alkaptonuria directly
q1 = """
query {
  search(queryString: "alkaptonuria", 
         entityNames: ["drug"], 
         page: {index: 0, size: 5}) {
    hits {
      id
      name
      entity
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

# Test 2: Search for nitisinone (known drug for alkaptonuria)
q2 = """
query {
  search(queryString: "nitisinone",
         entityNames: ["drug"],
         page: {index: 0, size: 3}) {
    hits {
      id
      name
      entity
      object {
        ... on Drug {
          name
          maximumClinicalStage
          drugType
          description
          indications {
            rows {
              disease { name id }
              maxPhaseForIndication
            }
          }
        }
      }
    }
  }
}
"""

# Test 3: Get drug by ChEMBL ID directly
q3 = """
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
        maxPhaseForIndication
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

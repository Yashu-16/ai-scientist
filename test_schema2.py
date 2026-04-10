import requests

# Test 1: Fix pharmacogenomics with correct field name
q1 = """
query {
  target(ensemblId: "ENSG00000113924") {
    approvedSymbol
    pharmacogenomics {
      drugs {
        drug {
          name
          maximumClinicalStage
        }
      }
    }
  }
}
"""

# Test 2: Try correct disease ID format
# Alkaptonuria EFO ID
q2 = """
query {
  disease(efoId: "EFO_0004229") {
    id name
  }
}
"""

# Test 3: Search for disease to find correct ID
q3 = """
query {
  search(queryString: "Alkaptonuria", entityNames: ["disease"], page: {index: 0, size: 3}) {
    hits {
      id
      name
      entity
    }
  }
}
"""

# Test 4: Try indicationsByEnsgId or similar
q4 = """
query {
  target(ensemblId: "ENSG00000113924") {
    approvedSymbol
    tractability {
      label
      modality
      value
    }
  }
}
"""

for i, q in enumerate([q1, q2, q3, q4], 1):
    r = requests.post(
        "https://api.platform.opentargets.org/api/v4/graphql",
        json={"query": q},
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    print(f"\nTest {i}: {r.status_code}")
    print(r.text[:500])

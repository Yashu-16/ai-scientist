import requests

# Check actual OpenTargets v4 schema for drug-related fields
q1 = """
query {
  target(ensemblId: "ENSG00000113924") {
    approvedSymbol
    approvedName
  }
}
"""

# Try the correct v4 field name for drugs
q2 = """
query {
  target(ensemblId: "ENSG00000113924") {
    approvedSymbol
    pharmacogenomics {
      drugs {
        drug {
          name
          maximumClinicalTrialPhase
        }
      }
    }
  }
}
"""

# Try interaction field
q3 = """
query {
  target(ensemblId: "ENSG00000113924") {
    approvedSymbol
    interactions(page: {index: 0, size: 3}) {
      rows {
        targetB {
          approvedSymbol
        }
      }
    }
  }
}
"""

# Try drug warnings via disease
q4 = """
query {
  disease(efoId: "MONDO:0008753") {
    id
    name
    therapeuticAreas {
      id
      name
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
    print(r.text[:400])

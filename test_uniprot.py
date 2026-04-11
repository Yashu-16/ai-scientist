import requests

# Test if proteinAnnotations field exists
query = """
query {
  disease(efoId: "MONDO_0004975") {
    associatedTargets(page: {index: 0, size: 3}) {
      rows {
        target {
          approvedSymbol
          proteinAnnotations {
            uniprot
          }
        }
        score
      }
    }
  }
}
"""
r = requests.post(
    "https://api.platform.opentargets.org/api/v4/graphql",
    json={"query": query},
    headers={"Content-Type": "application/json"},
    timeout=30
)
print(r.status_code)
print(r.text[:800])

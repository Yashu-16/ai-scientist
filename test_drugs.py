import requests

query = """
query {
  disease(efoId: "MONDO:0008753") {
    id name
    associatedTargets(page: { index: 0, size: 5 }) {
      rows {
        target {
          approvedSymbol
          knownDrugs(size: 3) {
            rows {
              drug { name maximumClinicalTrialPhase }
              mechanismOfAction
            }
          }
        }
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
print(r.text[:1000])

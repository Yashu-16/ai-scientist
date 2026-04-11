import requests

# Test different UniProt field names in OpenTargets v4
queries = {
    "proteinIds": """
query {
  target(ensemblId: "ENSG00000142192") {
    approvedSymbol
    proteinIds { id source }
  }
}""",
    "dbXrefs": """
query {
  target(ensemblId: "ENSG00000142192") {
    approvedSymbol
    dbXrefs { id source }
  }
}""",
    "alternativeGenes": """
query {
  target(ensemblId: "ENSG00000142192") {
    approvedSymbol
    alternativeGenes
  }
}""",
    "synonyms": """
query {
  target(ensemblId: "ENSG00000142192") {
    approvedSymbol
    synonyms { label source }
  }
}"""
}

for name, q in queries.items():
    r = requests.post(
        "https://api.platform.opentargets.org/api/v4/graphql",
        json={"query": q},
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    print(f"\n{name}: {r.status_code}")
    print(r.text[:300])

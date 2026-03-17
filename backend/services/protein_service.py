# backend/services/protein_service.py
# Purpose: Fetch protein/gene targets associated with a disease
# using the OpenTargets GraphQL API (free, no API key needed)

import requests
import json

# OpenTargets GraphQL endpoint
OPENTARGETS_API = "https://api.platform.opentargets.org/api/v4/graphql"


def search_disease_id(disease_name: str) -> dict:
    """
    Step 1: Convert a disease name (e.g., 'Alzheimer') 
    into an OpenTargets disease ID (e.g., 'MONDO_0004975')
    """
    
    query = """
    query SearchDisease($name: String!) {
      search(queryString: $name, entityNames: ["disease"], page: {index: 0, size: 1}) {
        hits {
          id
          name
          entity
        }
      }
    }
    """
    
    variables = {"name": disease_name}
    
    try:
        response = requests.post(
            OPENTARGETS_API,
            json={"query": query, "variables": variables},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        hits = data.get("data", {}).get("search", {}).get("hits", [])
        
        if not hits:
            return {"error": f"No disease found for: {disease_name}"}
        
        # Return the top match
        top_hit = hits[0]
        return {
            "disease_id": top_hit["id"],
            "disease_name": top_hit["name"]
        }
        
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}


def fetch_protein_targets(disease_name: str, max_targets: int = 10) -> dict:
    """
    Main function: Given a disease name, return top associated protein targets.
    
    Returns a list of proteins with:
    - gene symbol (e.g., APOE, APP)
    - protein name
    - evidence score (0.0 to 1.0)
    - biological function description
    """
    
    # First, get the disease ID
    disease_info = search_disease_id(disease_name)
    
    if "error" in disease_info:
        return disease_info
    
    disease_id = disease_info["disease_id"]
    resolved_name = disease_info["disease_name"]
    
    print(f"  → Found disease: {resolved_name} (ID: {disease_id})")
    
    # Now fetch associated targets
    query = """
    query DiseaseTargets($diseaseId: String!, $size: Int!) {
      disease(efoId: $diseaseId) {
        id
        name
        associatedTargets(page: {index: 0, size: $size}) {
          rows {
            target {
              id
              approvedSymbol
              approvedName
              biotype
              functionDescriptions
            }
            score
          }
        }
      }
    }
    """
    
    variables = {
        "diseaseId": disease_id,
        "size": max_targets
    }
    
    try:
        response = requests.post(
            OPENTARGETS_API,
            json={"query": query, "variables": variables},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        disease_data = data.get("data", {}).get("disease", {})
        
        if not disease_data:
            return {"error": "No data returned from OpenTargets"}
        
        rows = disease_data.get("associatedTargets", {}).get("rows", [])
        
        # Clean and structure the results
        targets = []
        for row in rows:
            target = row.get("target", {})
            score = row.get("score", 0)
            
            # Get the first function description if available
            descriptions = target.get("functionDescriptions", [])
            description = descriptions[0] if descriptions else "No description available"
            
            targets.append({
                "gene_symbol": target.get("approvedSymbol", "Unknown"),
                "protein_name": target.get("approvedName", "Unknown"),
                "ensembl_id": target.get("id", ""),
                "biotype": target.get("biotype", "Unknown"),
                "association_score": round(score, 4),
                "function_description": description[:300]  # Limit length
            })
        
        return {
            "disease_name": resolved_name,
            "disease_id": disease_id,
            "total_targets": len(targets),
            "targets": targets
        }
        
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}


# ── Quick test ──────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing OpenTargets API...")
    print("=" * 50)
    
    test_disease = "Alzheimer disease"
    print(f"Fetching protein targets for: {test_disease}\n")
    
    result = fetch_protein_targets(test_disease, max_targets=5)
    
    if "error" in result:
        print(f"ERROR: {result['error']}")
    else:
        print(f"Disease: {result['disease_name']}")
        print(f"Total targets found: {result['total_targets']}")
        print("\nTop Protein Targets:")
        print("-" * 50)
        for i, target in enumerate(result["targets"], 1):
            print(f"{i}. {target['gene_symbol']} — {target['protein_name']}")
            print(f"   Score: {target['association_score']}")
            print(f"   Type:  {target['biotype']}")
            print(f"   Func:  {target['function_description'][:100]}...")
            print()
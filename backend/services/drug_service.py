# backend/services/drug_service.py
# Purpose: Two things:
#   1. Map proteins → known drugs (using OpenTargets drug evidence)
#   2. Fetch FDA adverse event signals for those drugs (FDA FAERS API)
# Note: Some proteins (like APOE) are risk factors, not direct drug targets.
#       We use a fallback mock dataset for those cases.

import requests

OPENTARGETS_API = "https://api.platform.opentargets.org/api/v4/graphql"
FDA_FAERS_API   = "https://api.fda.gov/drug/event.json"

# ── Fallback mock drug data for well-known disease areas ────
# Used when OpenTargets returns no drugs for a protein
MOCK_DRUG_DATA = {
    "APOE": [
        {
            "drug_name": "Bexarotene",
            "drug_type": "Small molecule",
            "clinical_phase": 2,
            "mechanism": "APOE expression modulator — increases APOE-mediated amyloid clearance",
            "description": "Retinoid X receptor agonist investigated for Alzheimer's via APOE pathway",
            "target_gene": "APOE"
        }
    ],
    "APP": [
        {
            "drug_name": "Lecanemab",
            "drug_type": "Antibody",
            "clinical_phase": 4,
            "mechanism": "Amyloid beta aggregation inhibitor targeting APP cleavage products",
            "description": "FDA-approved monoclonal antibody targeting amyloid-beta protofibrils",
            "target_gene": "APP"
        }
    ],
    "PSEN1": [
        {
            "drug_name": "Semagacestat",
            "drug_type": "Small molecule",
            "clinical_phase": 3,
            "mechanism": "Gamma-secretase inhibitor — blocks PSEN1-mediated APP cleavage",
            "description": "Investigated gamma-secretase inhibitor targeting PSEN1 in Alzheimer's",
            "target_gene": "PSEN1"
        }
    ],
    "GRIN1": [
        {
            "drug_name": "Memantine",
            "drug_type": "Small molecule",
            "clinical_phase": 4,
            "mechanism": "NMDA receptor antagonist — modulates GRIN1-containing receptor activity",
            "description": "FDA-approved NMDA receptor antagonist for moderate-to-severe Alzheimer's",
            "target_gene": "GRIN1"
        }
    ],
    "BACE1": [
        {
            "drug_name": "Verubecestat",
            "drug_type": "Small molecule",
            "clinical_phase": 3,
            "mechanism": "BACE1 inhibitor — reduces amyloid-beta production",
            "description": "BACE1 inhibitor investigated in Alzheimer's disease clinical trials",
            "target_gene": "BACE1"
        }
    ]
}


def fetch_drugs_for_protein(ensembl_id: str, gene_symbol: str, max_drugs: int = 5) -> list:
    """
    Given a protein (Ensembl ID), fetch known drugs that target it
    using OpenTargets. Falls back to mock data if none found.
    """

    query = """
    query ProteinDrugs($targetId: String!, $size: Int!) {
      target(ensemblId: $targetId) {
        id
        approvedSymbol
        knownDrugs(size: $size) {
          rows {
            drug {
              id
              name
              drugType
              maximumClinicalTrialPhase
              description
            }
            mechanismOfAction
            disease {
              name
            }
          }
        }
      }
    }
    """

    variables = {"targetId": ensembl_id, "size": max_drugs}

    try:
        response = requests.post(
            OPENTARGETS_API,
            json={"query": query, "variables": variables},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        target_data = data.get("data", {}).get("target", {})
        rows = target_data.get("knownDrugs", {}).get("rows", []) if target_data else []

        drugs = []
        seen_drugs = set()

        for row in rows:
            drug      = row.get("drug", {})
            drug_name = drug.get("name", "Unknown")

            if drug_name in seen_drugs:
                continue
            seen_drugs.add(drug_name)

            drugs.append({
                "drug_name":     drug_name,
                "drug_id":       drug.get("id", ""),
                "drug_type":     drug.get("drugType", "Unknown"),
                "clinical_phase": drug.get("maximumClinicalTrialPhase"),
                "mechanism":     row.get("mechanismOfAction", "Unknown mechanism"),
                "description":   (drug.get("description") or "")[:200],
                "target_gene":   gene_symbol
            })

        # ── Fallback: if API returned nothing, use mock data ──
        if not drugs and gene_symbol in MOCK_DRUG_DATA:
            print(f"     ℹ️  No API drugs found for {gene_symbol} — using curated fallback data")
            drugs = MOCK_DRUG_DATA[gene_symbol]

        return drugs

    except requests.exceptions.RequestException as e:
        print(f"  Drug fetch error for {gene_symbol}: {e}")
        # Return mock data on error too
        return MOCK_DRUG_DATA.get(gene_symbol, [])


def fetch_fda_adverse_events(drug_name: str, max_results: int = 3) -> list:
    """
    Fetch top adverse event signals from FDA FAERS for a given drug.
    """

    params = {
        "search": f'patient.drug.medicinalproduct:"{drug_name}"',
        "count":  "patient.reaction.reactionmeddrapt.exact",
        "limit":  max_results
    }

    try:
        response = requests.get(FDA_FAERS_API, params=params, timeout=30)

        if response.status_code == 404:
            return []  # No reports found — not an error

        response.raise_for_status()
        data = response.json()

        return [
            {
                "reaction": item.get("term", "Unknown"),
                "count":    item.get("count", 0)
            }
            for item in data.get("results", [])
        ]

    except requests.exceptions.RequestException as e:
        print(f"  FDA FAERS error for {drug_name}: {e}")
        return []


def fetch_drug_data_for_disease(protein_targets: list, max_drugs_per_protein: int = 3) -> dict:
    """
    Master function: Given protein targets, fetch drugs + FDA signals.
    Processes top 3 proteins only to keep API calls manageable.
    """

    all_drug_data = []

    for target in protein_targets[:3]:
        gene_symbol = target.get("gene_symbol", "")
        ensembl_id  = target.get("ensembl_id", "")

        if not ensembl_id:
            continue

        print(f"  → Fetching drugs for: {gene_symbol} ({ensembl_id})")
        drugs = fetch_drugs_for_protein(ensembl_id, gene_symbol, max_drugs_per_protein)

        for drug in drugs:
            drug_name = drug["drug_name"]
            print(f"     → FDA signals for: {drug_name}")
            fda_signals = fetch_fda_adverse_events(drug_name, max_results=3)

            all_drug_data.append({
                **drug,
                "fda_adverse_events": fda_signals
            })

    return {
        "total_drugs": len(all_drug_data),
        "drug_data":   all_drug_data
    }


# ── Quick test ───────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing Drug + FDA API...")
    print("=" * 50)

    # Test with top Alzheimer's proteins — these have real drug data
    test_targets = [
        {"gene_symbol": "PSEN1", "ensembl_id": "ENSG00000080815", "protein_name": "Presenilin 1"},
        {"gene_symbol": "APP",   "ensembl_id": "ENSG00000142192", "protein_name": "Amyloid Precursor Protein"},
        {"gene_symbol": "APOE",  "ensembl_id": "ENSG00000130203", "protein_name": "Apolipoprotein E"},
    ]

    result = fetch_drug_data_for_disease(test_targets, max_drugs_per_protein=3)

    print(f"\nTotal drugs found: {result['total_drugs']}")
    print("\nDrug-Protein Mappings:")
    print("-" * 50)

    for drug in result["drug_data"]:
        print(f"💊 {drug['drug_name']} → 🧬 {drug['target_gene']}")
        print(f"   Type:      {drug['drug_type']}")
        print(f"   Phase:     Phase {drug['clinical_phase']}")
        print(f"   Mechanism: {drug['mechanism'][:80]}")
        if drug.get("fda_adverse_events"):
            top_ae = drug["fda_adverse_events"][0]
            print(f"   FDA Signal: {top_ae['reaction']} ({top_ae['count']} reports)")
        print()
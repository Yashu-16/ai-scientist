# backend/services/drug_service.py
# V2 — Feature 3: FDA Risk Intelligence Layer
# Adds risk_level + risk_description to every drug
# based on adverse event report counts from FDA FAERS

import requests

OPENTARGETS_API = "https://api.platform.opentargets.org/api/v4/graphql"
FDA_FAERS_API   = "https://api.fda.gov/drug/event.json"

# ── Risk Classification Rules ─────────────────────────────────
# Based on total adverse event reports for the top reaction
RISK_TIERS = [
    (200, "High",    "#ef4444",
     "High volume of adverse event reports. Significant safety signals detected in FDA FAERS. "
     "Requires careful benefit-risk evaluation before therapeutic consideration."),
    (50,  "Medium",  "#f59e0b",
     "Moderate adverse event reporting. Safety signals present but within manageable range. "
     "Standard clinical monitoring protocols recommended."),
    (0,   "Low",     "#22c55e",
     "Low adverse event signal. Limited safety concerns detected in FDA FAERS database. "
     "Favorable safety profile for further investigation."),
]

# Fallback mock data for proteins without direct drug targets
MOCK_DRUG_DATA = {
    "APOE": [{
        "drug_name":     "Bexarotene",
        "drug_type":     "Small molecule",
        "clinical_phase": 2,
        "mechanism":     "APOE expression modulator — increases APOE-mediated amyloid clearance",
        "description":   "Retinoid X receptor agonist investigated for Alzheimer's via APOE pathway",
        "target_gene":   "APOE"
    }],
    "APP": [{
        "drug_name":     "Lecanemab",
        "drug_type":     "Antibody",
        "clinical_phase": 4,
        "mechanism":     "Amyloid beta aggregation inhibitor targeting APP cleavage products",
        "description":   "FDA-approved monoclonal antibody targeting amyloid-beta protofibrils",
        "target_gene":   "APP"
    }],
    "PSEN1": [{
        "drug_name":     "Semagacestat",
        "drug_type":     "Small molecule",
        "clinical_phase": 3,
        "mechanism":     "Gamma-secretase inhibitor — blocks PSEN1-mediated APP cleavage",
        "description":   "Investigated gamma-secretase inhibitor targeting PSEN1",
        "target_gene":   "PSEN1"
    }],
    "GRIN1": [{
        "drug_name":     "Memantine",
        "drug_type":     "Small molecule",
        "clinical_phase": 4,
        "mechanism":     "NMDA receptor antagonist — modulates GRIN1-containing receptor activity",
        "description":   "FDA-approved NMDA receptor antagonist for Alzheimer's",
        "target_gene":   "GRIN1"
    }],
    "BACE1": [{
        "drug_name":     "Verubecestat",
        "drug_type":     "Small molecule",
        "clinical_phase": 3,
        "mechanism":     "BACE1 inhibitor — reduces amyloid-beta production",
        "description":   "BACE1 inhibitor investigated in Alzheimer's clinical trials",
        "target_gene":   "BACE1"
    }]
}

# ── Drug Class Competition Database ──────────────────────────
# Curated competitive landscape for major drug classes
# Used for market intelligence without requiring additional APIs

DRUG_CLASS_COMPETITION = {
    # Gamma-secretase inhibitors/modulators
    "gamma-secretase inhibitor": {
        "class":        "Gamma-secretase inhibitor",
        "similar_drugs":["Semagacestat","Avagacestat","BMS-708163",
                         "LY-450139","MK-0752","PF-3084014"],
        "level":        "High",
        "opportunity":  "Crowded",
        "note":         "Highly competitive class; multiple Phase 3 failures. Differentiation required."
    },
    "gamma-secretase modulator": {
        "class":        "Gamma-secretase modulator",
        "similar_drugs":["Tarenflurbil","CHF-5074","NIC5-15"],
        "level":        "Medium",
        "opportunity":  "Moderate",
        "note":         "Modulator class less crowded than inhibitors; better safety profile sought."
    },
    # Amyloid-beta antibodies
    "amyloid-beta": {
        "class":        "Amyloid-beta antibody",
        "similar_drugs":["Aducanumab","Lecanemab","Donanemab",
                         "Gantenerumab","Solanezumab","Crenezumab"],
        "level":        "High",
        "opportunity":  "Crowded",
        "note":         "Highly competitive; FDA approvals exist. Strong clinical precedent but crowded."
    },
    "amyloid beta": {
        "class":        "Amyloid-beta targeting agent",
        "similar_drugs":["Aducanumab","Lecanemab","Donanemab","Gantenerumab"],
        "level":        "High",
        "opportunity":  "Crowded",
        "note":         "Major pharma companies active. Requires significant differentiation."
    },
    # BACE inhibitors
    "bace": {
        "class":        "BACE inhibitor",
        "similar_drugs":["Verubecestat","Atabecestat","Lanabecestat",
                         "Elenbecestat","CNP520"],
        "level":        "Medium",
        "opportunity":  "Moderate",
        "note":         "Multiple Phase 3 failures. Space less crowded now; selective inhibitors sought."
    },
    # NMDA antagonists
    "nmda": {
        "class":        "NMDA receptor antagonist",
        "similar_drugs":["Memantine","Ketamine","Esketamine",
                         "Nitromemantine","NitroSynapsin"],
        "level":        "Medium",
        "opportunity":  "Moderate",
        "note":         "Established class with marketed drugs. Novel mechanisms needed."
    },
    # LRRK2 inhibitors (Parkinson's)
    "lrrk2": {
        "class":        "LRRK2 kinase inhibitor",
        "similar_drugs":["DNL201","DNL151","BIIB122","PF-06685360"],
        "level":        "Medium",
        "opportunity":  "Moderate",
        "note":         "Active clinical development. First-in-class advantage still possible."
    },
    # Alpha-synuclein antibodies
    "alpha-synuclein": {
        "class":        "Alpha-synuclein antibody",
        "similar_drugs":["Prasinezumab","Cinpanemab","Buntanetap",
                         "MEDI1341","Lu AF82422"],
        "level":        "Medium",
        "opportunity":  "Moderate",
        "note":         "Multiple Phase 2 programs active. Target validation still ongoing."
    },
    # HER2 targeting (cancer)
    "her2": {
        "class":        "HER2-targeting agent",
        "similar_drugs":["Trastuzumab","Pertuzumab","Lapatinib",
                         "Neratinib","Tucatinib","T-DM1","T-DXd"],
        "level":        "High",
        "opportunity":  "Crowded",
        "note":         "Extremely competitive class. Multiple approved agents. Combination strategies needed."
    },
    # CDK4/6 inhibitors
    "cdk": {
        "class":        "CDK inhibitor",
        "similar_drugs":["Palbociclib","Ribociclib","Abemaciclib",
                         "Trilaciclib","Lerociclib"],
        "level":        "High",
        "opportunity":  "Crowded",
        "note":         "3 approved CDK4/6 inhibitors dominate breast cancer. Differentiation critical."
    },
    # GLP-1 agonists (diabetes)
    "glp": {
        "class":        "GLP-1 receptor agonist",
        "similar_drugs":["Semaglutide","Liraglutide","Dulaglutide",
                         "Exenatide","Tirzepatide"],
        "level":        "High",
        "opportunity":  "Crowded",
        "note":         "Blockbuster class. Semaglutide dominates. Differentiation through delivery or combo needed."
    },
    # Default for unknown
    "default": {
        "class":        "Unknown drug class",
        "similar_drugs":[],
        "level":        "Low",
        "opportunity":  "Strong",
        "note":         "Limited competition data available. Potentially novel mechanism."
    }
}

COMPETITION_COLORS = {
    "Low":    "#22c55e",
    "Medium": "#f59e0b",
    "High":   "#ef4444"
}

OPPORTUNITY_COLORS = {
    "Strong":   "#22c55e",
    "Moderate": "#f59e0b",
    "Crowded":  "#ef4444"
}


def classify_competition(
    drug_name:  str,
    mechanism:  str,
    drug_type:  str
) -> "CompetitionIntel":
    """
    Classify competitive landscape for a drug based on mechanism.

    Args:
        drug_name : Name of the drug
        mechanism : Mechanism of action string
        drug_type : Drug type (Small molecule / Antibody / etc.)

    Returns:
        CompetitionIntel object
    """
    from backend.models.schemas import CompetitionIntel

    mechanism_lower = mechanism.lower()
    drug_lower      = drug_name.lower()

    # Match against competition database
    matched = None
    for keyword, data in DRUG_CLASS_COMPETITION.items():
        if keyword == "default":
            continue
        if keyword in mechanism_lower or keyword in drug_lower:
            matched = data
            break

    if not matched:
        matched = DRUG_CLASS_COMPETITION["default"]

    # Remove the drug itself from similar drugs list
    similar = [d for d in matched["similar_drugs"]
               if d.lower() != drug_lower][:5]

    level = matched["level"]
    color = COMPETITION_COLORS.get(level, "#64748b")

    return CompetitionIntel(
        competition_level  = level,
        competition_color  = color,
        num_similar_drugs  = len(similar),
        similar_drug_names = similar,
        market_opportunity = matched["opportunity"],
        strategic_note     = matched["note"],
        drug_class         = matched["class"]
    )


def classify_fda_risk(adverse_events: list) -> tuple:
    """
    Classify drug risk level based on FDA adverse event counts.

    Args:
        adverse_events: list of {reaction, count} dicts

    Returns:
        (risk_level, risk_description, risk_color) tuple

    Risk Tiers:
        High   → top reaction >200 reports
        Medium → top reaction 50–200 reports
        Low    → top reaction <50 reports
        None   → no adverse event data found
    """
    if not adverse_events:
        return (
            "Unknown",
            "No adverse event data found in FDA FAERS. "
            "Insufficient safety signal data for risk classification.",
            "#64748b"
        )

    top_count = adverse_events[0].get("count", 0)

    for threshold, level, color, description in RISK_TIERS:
        if top_count > threshold:
            return (level, description, color)

    return ("Low", RISK_TIERS[2][3], "#22c55e")


def fetch_drugs_for_protein(
    ensembl_id:  str,
    gene_symbol: str,
    max_drugs:   int = 5
) -> list:
    """
    Fetch known drugs for a protein from OpenTargets.
    Falls back to mock data if API returns nothing.
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

        drugs      = []
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

        if not drugs and gene_symbol in MOCK_DRUG_DATA:
            print(f"     ℹ️  No API drugs for {gene_symbol} — using fallback")
            drugs = MOCK_DRUG_DATA[gene_symbol]

        return drugs

    except requests.exceptions.RequestException as e:
        print(f"  Drug fetch error for {gene_symbol}: {e}")
        return MOCK_DRUG_DATA.get(gene_symbol, [])


def fetch_fda_adverse_events(drug_name: str, max_results: int = 5) -> list:
    """
    Fetch top adverse event reactions from FDA FAERS for a drug.
    Returns sorted list of {reaction, count} dicts.
    """
    params = {
        "search": f'patient.drug.medicinalproduct:"{drug_name}"',
        "count":  "patient.reaction.reactionmeddrapt.exact",
        "limit":  max_results
    }

    try:
        response = requests.get(FDA_FAERS_API, params=params, timeout=30)
        if response.status_code == 404:
            return []
        response.raise_for_status()
        data = response.json()

        return [
            {"reaction": item.get("term", "Unknown"),
             "count":    item.get("count", 0)}
            for item in data.get("results", [])
        ]

    except requests.exceptions.RequestException as e:
        print(f"  FDA FAERS error for {drug_name}: {e}")
        return []


def fetch_drug_data_for_disease(
    protein_targets:       list,
    max_drugs_per_protein: int = 3
) -> dict:
    """
    Master function: fetch drugs + FDA signals + risk classification
    for the top 3 protein targets.

    Returns structured drug data with risk intelligence fields.
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

            # Get adverse events
            fda_events = fetch_fda_adverse_events(drug_name, max_results=5)

            # ── Classify Risk ─────────────────────────────────
            risk_level, risk_description, risk_color = classify_fda_risk(fda_events)

            # ── Competition Intelligence ──────────────────────
            comp_intel = classify_competition(
                drug_name = drug_name,
                mechanism = drug.get("mechanism",""),
                drug_type = drug.get("drug_type","")
            )

            print(
                f"        Competition: {comp_intel.competition_level} "
                f"({comp_intel.num_similar_drugs} similar drugs)"
            )

            all_drug_data.append({
                **drug,
                "fda_adverse_events": fda_events,
                "risk_level":         risk_level,
                "risk_description":   risk_description,
                "risk_color":         risk_color,
                # V4 Feature 4
                "competition_level":    comp_intel.competition_level,
                "competition_color":    comp_intel.competition_color,
                "num_similar_drugs":    comp_intel.num_similar_drugs,
                "similar_drug_names":   comp_intel.similar_drug_names,
                "market_opportunity":   comp_intel.market_opportunity,
                "strategic_note":       comp_intel.strategic_note,
                "drug_class":           comp_intel.drug_class
            })

            print(
                f"        Risk: {risk_level} "
                f"({'top AE: ' + str(fda_events[0]['count']) + ' reports' if fda_events else 'no data'})"
            )

    return {
        "total_drugs": len(all_drug_data),
        "drug_data":   all_drug_data
    }


# ── Quick test ────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing Drug Service V2 — Risk Intelligence Layer")
    print("=" * 55)

    test_targets = [
        {"gene_symbol": "PSEN1", "ensembl_id": "ENSG00000080815"},
        {"gene_symbol": "APP",   "ensembl_id": "ENSG00000142192"},
        {"gene_symbol": "APOE",  "ensembl_id": "ENSG00000130203"},
    ]

    result = fetch_drug_data_for_disease(test_targets, max_drugs_per_protein=3)

    print(f"\nTotal drugs: {result['total_drugs']}")
    print("\nDrug Risk Intelligence:")
    print("-" * 55)

    for drug in result["drug_data"]:
        risk  = drug["risk_level"]
        emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(risk, "⚪")
        print(f"\n💊 {drug['drug_name']} → {drug['target_gene']}")
        print(f"   Phase  : {drug['clinical_phase']}")
        print(f"   Risk   : {emoji} {risk}")
        print(f"   Reason : {drug['risk_description'][:80]}...")
        if drug["fda_adverse_events"]:
            top = drug["fda_adverse_events"][0]
            print(f"   Top AE : {top['reaction']} ({top['count']:,} reports)")
# backend/services/drug_service.py
# V4 — Real drug data using verified OpenTargets v4 API
# Strategy: search drugs by disease name → get mechanisms → FDA risk

import requests

OPENTARGETS_API = "https://api.platform.opentargets.org/api/v4/graphql"
FDA_FAERS_API   = "https://api.fda.gov/drug/event.json"

# ── Clinical Stage Mapping ────────────────────────────────────
STAGE_TO_PHASE = {
    "APPROVAL":   4,
    "PHASE4":     4,
    "PHASE3":     3,
    "PHASE2":     2,
    "PHASE1":     1,
    "PRECLINICAL":0,
    "UNKNOWN":    0,
}

# ── Risk Classification ───────────────────────────────────────
RISK_TIERS = [
    (200, "High",   "#ef4444",
     "High volume of adverse event reports. Significant safety signals detected in FDA FAERS. "
     "Requires careful benefit-risk evaluation before therapeutic consideration."),
    (50,  "Medium", "#f59e0b",
     "Moderate adverse event reporting. Safety signals present but within manageable range. "
     "Standard clinical monitoring protocols recommended."),
    (0,   "Low",    "#22c55e",
     "Low adverse event signal. Limited safety concerns detected in FDA FAERS database. "
     "Favorable safety profile for further investigation."),
]

# ── Competition Database ──────────────────────────────────────
DRUG_CLASS_COMPETITION = {
    "gamma-secretase inhibitor": {
        "class": "Gamma-secretase inhibitor",
        "similar_drugs": ["Semagacestat","Avagacestat","BMS-708163","LY-450139","MK-0752"],
        "level": "Medium", "opportunity": "Moderate",
        "note": "Multiple Phase 3 failures. Differentiation required."
    },
    "amyloid-beta": {
        "class": "Amyloid-beta antibody",
        "similar_drugs": ["Aducanumab","Lecanemab","Donanemab","Gantenerumab","Solanezumab"],
        "level": "High", "opportunity": "Crowded",
        "note": "Highly competitive. FDA approvals exist."
    },
    "bace": {
        "class": "BACE inhibitor",
        "similar_drugs": ["Verubecestat","Atabecestat","Lanabecestat","Elenbecestat"],
        "level": "Medium", "opportunity": "Moderate",
        "note": "Multiple Phase 3 failures."
    },
    "nmda": {
        "class": "NMDA receptor antagonist",
        "similar_drugs": ["Memantine","Ketamine","Esketamine","Nitromemantine"],
        "level": "Medium", "opportunity": "Moderate",
        "note": "Established class. Novel mechanisms needed."
    },
    "lrrk2": {
        "class": "LRRK2 kinase inhibitor",
        "similar_drugs": ["DNL201","DNL151","BIIB122","PF-06685360"],
        "level": "Medium", "opportunity": "Moderate",
        "note": "Active clinical development."
    },
    "alpha-synuclein": {
        "class": "Alpha-synuclein antibody",
        "similar_drugs": ["Prasinezumab","Cinpanemab","Buntanetap","MEDI1341"],
        "level": "Medium", "opportunity": "Moderate",
        "note": "Multiple Phase 2 programs active."
    },
    "her2": {
        "class": "HER2-targeting agent",
        "similar_drugs": ["Trastuzumab","Pertuzumab","Lapatinib","Neratinib","Tucatinib"],
        "level": "High", "opportunity": "Crowded",
        "note": "Extremely competitive class."
    },
    "cdk": {
        "class": "CDK inhibitor",
        "similar_drugs": ["Palbociclib","Ribociclib","Abemaciclib","Trilaciclib"],
        "level": "High", "opportunity": "Crowded",
        "note": "3 approved CDK4/6 inhibitors dominate."
    },
    "glp": {
        "class": "GLP-1 receptor agonist",
        "similar_drugs": ["Semaglutide","Liraglutide","Dulaglutide","Tirzepatide"],
        "level": "High", "opportunity": "Crowded",
        "note": "Blockbuster class. Semaglutide dominates."
    },
    "hppd": {
        "class": "HPPD inhibitor",
        "similar_drugs": ["Nitisinone","NTBC"],
        "level": "Low", "opportunity": "Strong",
        "note": "Limited competition. Nitisinone is only approved drug."
    },
    "dopamine": {
        "class": "Dopamine modulator",
        "similar_drugs": ["Levodopa","Pramipexole","Ropinirole","Rotigotine"],
        "level": "High", "opportunity": "Crowded",
        "note": "Well-established class for Parkinson's."
    },
    "tyrosine": {
        "class": "Tyrosine metabolism modulator",
        "similar_drugs": ["Nitisinone","Orfadin"],
        "level": "Low", "opportunity": "Strong",
        "note": "Rare disease space — limited competition."
    },
    "insulin": {
        "class": "Insulin sensitizer / secretagogue",
        "similar_drugs": ["Metformin","Sitagliptin","Empagliflozin","Liraglutide"],
        "level": "High", "opportunity": "Crowded",
        "note": "Extremely competitive diabetes space."
    },
    "default": {
        "class": "Unknown drug class",
        "similar_drugs": [],
        "level": "Low", "opportunity": "Strong",
        "note": "Limited competition data. Potentially novel mechanism."
    }
}

COMPETITION_COLORS = {"Low": "#22c55e", "Medium": "#f59e0b", "High": "#ef4444"}
OPPORTUNITY_COLORS = {"Strong": "#22c55e", "Moderate": "#f59e0b", "Crowded": "#ef4444"}


def classify_competition(drug_name: str, mechanism: str, drug_type: str):
    """Classify competitive landscape for a drug."""
    from backend.models.schemas import CompetitionIntel
    mechanism_lower = mechanism.lower()
    drug_lower      = drug_name.lower()
    matched = None
    for keyword, data in DRUG_CLASS_COMPETITION.items():
        if keyword == "default":
            continue
        if keyword in mechanism_lower or keyword in drug_lower:
            matched = data
            break
    if not matched:
        matched = DRUG_CLASS_COMPETITION["default"]
    similar = [d for d in matched["similar_drugs"] if d.lower() != drug_lower][:5]
    level   = matched["level"]
    color   = COMPETITION_COLORS.get(level, "#64748b")
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
    """Classify drug risk from FDA adverse event counts."""
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


def parse_clinical_stage(stage_str: str) -> int:
    """Convert OpenTargets stage string to numeric phase."""
    if not stage_str:
        return 0
    return STAGE_TO_PHASE.get(stage_str.upper().replace(" ", ""), 0)


def fetch_drugs_by_disease_name(disease_name: str, max_drugs: int = 10) -> list:
    """
    PRIMARY: Search OpenTargets for drugs by disease name.
    Uses verified search API that returns real drug data.
    """
    query = """
    query SearchDrugs($disease: String!, $size: Int!) {
      search(queryString: $disease,
             entityNames: ["drug"],
             page: {index: 0, size: $size}) {
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
    try:
        response = requests.post(
            OPENTARGETS_API,
            json={"query": query, "variables": {"disease": disease_name, "size": max_drugs}},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        hits = data.get("data", {}).get("search", {}).get("hits", [])

        drugs      = []
        seen_drugs = set()

        for hit in hits:
            obj = hit.get("object", {})
            if not obj:
                continue

            drug_name   = obj.get("name", "")
            if not drug_name or drug_name.upper() in seen_drugs:
                continue

            # Filter: only include drugs whose description mentions the disease
            description   = obj.get("description", "").lower()
            disease_lower = disease_name.lower()
            disease_words = [w for w in disease_lower.split() if len(w) > 4]

            # For small result sets accept all; for large sets filter by relevance
            if len(hits) > 3:
                if disease_lower not in description:
                    if not any(w in description for w in disease_words):
                        continue

            seen_drugs.add(drug_name.upper())

            # Get mechanism and target gene
            mechanism   = "Unknown mechanism"
            target_gene = ""
            moa_rows    = obj.get("mechanismsOfAction", {}).get("rows", [])
            if moa_rows:
                mechanism = moa_rows[0].get("mechanismOfAction", "Unknown mechanism")
                targets   = moa_rows[0].get("targets", [])
                if targets:
                    target_gene = targets[0].get("approvedSymbol", "")

            phase = parse_clinical_stage(obj.get("maximumClinicalStage", ""))

            drugs.append({
                "drug_name":      drug_name.title(),
                "drug_id":        hit.get("id", ""),
                "drug_type":      obj.get("drugType", "Unknown"),
                "clinical_phase": phase,
                "mechanism":      mechanism,
                "description":    obj.get("description", "")[:200],
                "target_gene":    target_gene,
                "status":         obj.get("maximumClinicalStage", ""),
            })

        print(f"  Disease drug search '{disease_name}': {len(drugs)} drugs found")
        return drugs

    except Exception as e:
        print(f"  Drug search error for {disease_name}: {e}")
        return []


def fetch_drugs_for_protein_targets(
    protein_targets: list,
    disease_name:    str,
    max_drugs:       int = 5
) -> list:
    """
    FALLBACK: Search drugs for each protein target individually.
    """
    query = """
    query SearchProteinDrug($term: String!, $size: Int!) {
      search(queryString: $term,
             entityNames: ["drug"],
             page: {index: 0, size: $size}) {
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
    drugs      = []
    seen_drugs = set()

    for target in protein_targets[:3]:
        gene_symbol = target.get("gene_symbol", "")
        if not gene_symbol:
            continue

        search_term = f"{gene_symbol} {disease_name}"
        print(f"  → Protein drug search: {search_term}")

        try:
            response = requests.post(
                OPENTARGETS_API,
                json={"query": query, "variables": {"term": search_term, "size": max_drugs}},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            hits = data.get("data", {}).get("search", {}).get("hits", [])

            for hit in hits:
                obj       = hit.get("object", {})
                drug_name = obj.get("name", "")
                if not drug_name or drug_name.upper() in seen_drugs:
                    continue
                seen_drugs.add(drug_name.upper())

                mechanism   = "Unknown mechanism"
                target_gene = gene_symbol
                moa_rows    = obj.get("mechanismsOfAction", {}).get("rows", [])
                if moa_rows:
                    mechanism = moa_rows[0].get("mechanismOfAction", "Unknown mechanism")
                    targets   = moa_rows[0].get("targets", [])
                    if targets:
                        target_gene = targets[0].get("approvedSymbol", gene_symbol)

                phase = parse_clinical_stage(obj.get("maximumClinicalStage", ""))

                drugs.append({
                    "drug_name":      drug_name.title(),
                    "drug_id":        hit.get("id", ""),
                    "drug_type":      obj.get("drugType", "Unknown"),
                    "clinical_phase": phase,
                    "mechanism":      mechanism,
                    "description":    obj.get("description", "")[:200],
                    "target_gene":    target_gene,
                    "status":         obj.get("maximumClinicalStage", ""),
                })

        except Exception as e:
            print(f"  Protein drug search error ({gene_symbol}): {e}")
            continue

    print(f"  Protein-level drug search: {len(drugs)} drugs found")
    return drugs


def fetch_fda_adverse_events(drug_name: str, max_results: int = 5) -> list:
    """Fetch top adverse event reactions from FDA FAERS."""
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
            {"reaction": item.get("term", "Unknown"), "count": item.get("count", 0)}
            for item in data.get("results", [])
        ]
    except Exception as e:
        print(f"  FDA FAERS error for {drug_name}: {e}")
        return []


def fetch_drug_data_for_disease(
    protein_targets:       list,
    max_drugs_per_protein: int = 3,
    disease_id:            str = "",
    disease_name:          str = ""
) -> dict:
    """
    Master function: fetch real drugs + FDA signals + risk + competition.
    Strategy:
    1. Search by disease name (primary — most comprehensive)
    2. Fall back to protein-level search if nothing found
    3. Enrich each drug with FDA + risk + competition data
    """
    all_drug_data   = []
    seen_drug_names = set()

    # ── Step 1: Disease-level search ──────────────────────────
    if disease_name:
        print(f"\n  🔍 Searching drugs for: {disease_name}")
        disease_drugs = fetch_drugs_by_disease_name(disease_name, max_drugs=10)

        for drug in disease_drugs:
            drug_name = drug["drug_name"]
            if drug_name.upper() in seen_drug_names:
                continue
            seen_drug_names.add(drug_name.upper())

            print(f"     → FDA signals for: {drug_name}")
            fda_events   = fetch_fda_adverse_events(drug_name)
            risk_level, risk_description, risk_color = classify_fda_risk(fda_events)
            comp_intel   = classify_competition(
                drug_name = drug_name,
                mechanism = drug.get("mechanism", ""),
                drug_type = drug.get("drug_type", "")
            )

            all_drug_data.append({
                **drug,
                "fda_adverse_events":  fda_events,
                "risk_level":          risk_level,
                "risk_description":    risk_description,
                "risk_color":          risk_color,
                "competition_level":   comp_intel.competition_level,
                "competition_color":   comp_intel.competition_color,
                "num_similar_drugs":   comp_intel.num_similar_drugs,
                "similar_drug_names":  comp_intel.similar_drug_names,
                "market_opportunity":  comp_intel.market_opportunity,
                "strategic_note":      comp_intel.strategic_note,
                "drug_class":          comp_intel.drug_class
            })
            print(f"        Phase: {drug['clinical_phase']} | Risk: {risk_level}")

    # ── Step 2: Protein-level fallback ─────────────────────────
    if not all_drug_data and protein_targets:
        print(f"  ⚠️  No disease drugs found — trying protein-level search")
        protein_drugs = fetch_drugs_for_protein_targets(
            protein_targets, disease_name, max_drugs_per_protein
        )

        for drug in protein_drugs:
            drug_name = drug["drug_name"]
            if drug_name.upper() in seen_drug_names:
                continue
            seen_drug_names.add(drug_name.upper())

            print(f"     → FDA signals for: {drug_name}")
            fda_events   = fetch_fda_adverse_events(drug_name)
            risk_level, risk_description, risk_color = classify_fda_risk(fda_events)
            comp_intel   = classify_competition(
                drug_name = drug_name,
                mechanism = drug.get("mechanism", ""),
                drug_type = drug.get("drug_type", "")
            )

            all_drug_data.append({
                **drug,
                "fda_adverse_events":  fda_events,
                "risk_level":          risk_level,
                "risk_description":    risk_description,
                "risk_color":          risk_color,
                "competition_level":   comp_intel.competition_level,
                "competition_color":   comp_intel.competition_color,
                "num_similar_drugs":   comp_intel.num_similar_drugs,
                "similar_drug_names":  comp_intel.similar_drug_names,
                "market_opportunity":  comp_intel.market_opportunity,
                "strategic_note":      comp_intel.strategic_note,
                "drug_class":          comp_intel.drug_class
            })

    print(f"\n  ✅ Total drugs fetched: {len(all_drug_data)}")
    return {
        "total_drugs": len(all_drug_data),
        "drug_data":   all_drug_data
    }


# ── Quick test ────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing Drug Service V4 — Real Data")
    print("=" * 55)

    test_cases = [
        {"disease_name": "Alkaptonuria",     "disease_id": "MONDO_0008753"},
        {"disease_name": "Alzheimer disease","disease_id": "MONDO_0004975"},
        {"disease_name": "Parkinson disease","disease_id": "MONDO_0005180"},
        {"disease_name": "type 2 diabetes",  "disease_id": "MONDO_0005148"},
    ]

    for case in test_cases:
        print(f"\n{'='*55}")
        print(f"Disease: {case['disease_name']}")
        result = fetch_drug_data_for_disease(
            protein_targets = [],
            disease_name    = case["disease_name"],
            disease_id      = case["disease_id"]
        )
        print(f"Total drugs: {result['total_drugs']}")
        for drug in result["drug_data"]:
            print(f"  💊 {drug['drug_name']} | Phase {drug['clinical_phase']} | "
                  f"Risk: {drug['risk_level']} | Target: {drug['target_gene']} | "
                  f"Mechanism: {drug['mechanism'][:50]}")
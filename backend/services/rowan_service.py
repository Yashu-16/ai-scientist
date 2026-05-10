# backend/services/rowan_service.py
# Rowan Phase 1 Integration — Molecular Validation for Drug Repurposing
# Requires: py -3.11 -m pip install rowan-python stjames httpx
# API docs: https://docs.rowansci.com/api/python/v3/

import os
import asyncio
import httpx
from typing import Optional

ROWAN_API_KEY = os.getenv("ROWAN_API_KEY", "")
PUBCHEM_BASE  = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

# ── Known biologics — not suitable for small-molecule ADMET ──────────────────
KNOWN_BIOLOGICS = {
    "LECANEMAB","ADUCANUMAB","DONANEMAB","GANTENERUMAB",
    "CRENEZUMAB","SOLANEZUMAB","NIVOLUMAB","PEMBROLIZUMAB",
    "ATEZOLIZUMAB","DURVALUMAB","TRASTUZUMAB","BEVACIZUMAB",
    "RITUXIMAB","ADALIMUMAB","INFLIXIMAB","ETANERCEPT",
    "OMALIZUMAB","DUPILUMAB","SECUKINUMAB","USTEKINUMAB",
    "TOCILIZUMAB","SARILUMAB","IXEKIZUMAB","GUSELKUMAB",
}

def is_biologic(drug_name: str) -> bool:
    if drug_name.upper() in KNOWN_BIOLOGICS:
        return True
    biologic_suffixes = ["mab","zumab","mumab","umab","ximab","cept","kine","fermin","tropin"]
    return any(drug_name.lower().endswith(s) for s in biologic_suffixes)


# ── PubChem SMILES lookup ─────────────────────────────────────────────────────
async def get_smiles_from_pubchem(drug_name: str) -> Optional[str]:
    if is_biologic(drug_name):
        print(f"ℹ️  {drug_name} is a biologic — skipping SMILES lookup")
        return None
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            for prop in ["IsomericSMILES", "CanonicalSMILES", "ConnectivitySMILES"]:
                try:
                    url = f"{PUBCHEM_BASE}/compound/name/{drug_name}/property/{prop}/JSON"
                    res = await client.get(url)
                    if res.status_code == 200:
                        props = res.json().get("PropertyTable", {}).get("Properties", [])
                        if props:
                            row = props[0]
                            smiles = (
                                row.get("IsomericSMILES") or
                                row.get("CanonicalSMILES") or
                                row.get("ConnectivitySMILES")
                            )
                            if smiles:
                                print(f"✅ PubChem SMILES for {drug_name}: {smiles[:50]}...")
                                return smiles
                except Exception:
                    continue

            # Fallback: CID → SMILES
            cid_res = await client.get(f"{PUBCHEM_BASE}/compound/name/{drug_name}/cids/JSON")
            if cid_res.status_code == 200:
                cids = cid_res.json().get("IdentifierList", {}).get("CID", [])
                if cids:
                    cid = cids[0]
                    s_res = await client.get(
                        f"{PUBCHEM_BASE}/compound/cid/{cid}/property/IsomericSMILES/JSON"
                    )
                    if s_res.status_code == 200:
                        props = s_res.json().get("PropertyTable", {}).get("Properties", [])
                        if props:
                            smiles = props[0].get("IsomericSMILES") or props[0].get("CanonicalSMILES")
                            if smiles:
                                print(f"✅ PubChem CID→SMILES for {drug_name}: {smiles[:50]}...")
                                return smiles
    except Exception as e:
        print(f"⚠️  PubChem lookup failed for {drug_name}: {e}")
    print(f"❌ No SMILES found for {drug_name}")
    return None


# ── Rowan SDK init ────────────────────────────────────────────────────────────
def _init_rowan():
    try:
        import rowan
        rowan.api_key = ROWAN_API_KEY
        return rowan
    except ImportError:
        print("⚠️  rowan-python not installed. Run: pip install rowan-python")
        return None


# ── Parse ADMET results ───────────────────────────────────────────────────────
def _parse_admet(properties: dict) -> dict:
    """
    Parse Rowan's 49 ADMET properties into human-readable format.
    All probability values 0-1 where higher = more likely.
    """
    def pct(v): return f"{round(v * 100)}%" if v is not None else "N/A"
    def prob_label(v, threshold=0.5): return "Yes" if v and v >= threshold else "No"

    bbb   = properties.get("BBB_Martins")
    herg  = properties.get("hERG")
    dili  = properties.get("DILI")
    hia   = properties.get("HIA_Hou")
    sol   = properties.get("Solubility_AqSolDB")
    bio   = properties.get("Bioavailability_Ma")
    clintox = properties.get("ClinTox")
    ames  = properties.get("AMES")
    logp  = properties.get("logP") or properties.get("Lipophilicity_AstraZeneca")
    tpsa  = properties.get("tpsa")
    mw    = properties.get("molecular_weight")
    lipinski = properties.get("Lipinski")
    pgp   = properties.get("Pgp_Broccatelli")
    caco2 = properties.get("Caco2_Wang")
    pampa = properties.get("PAMPA_NCATS")

    # Solubility class from LogS
    sol_class = "Unknown"
    if sol is not None:
        if sol >= -1:   sol_class = "Highly soluble"
        elif sol >= -3: sol_class = "Soluble"
        elif sol >= -5: sol_class = "Moderately soluble"
        else:           sol_class = "Poorly soluble"

    # BBB class
    bbb_class = "Unknown"
    if bbb is not None:
        if bbb >= 0.7:   bbb_class = "High BBB penetration"
        elif bbb >= 0.4: bbb_class = "Moderate BBB penetration"
        else:            bbb_class = "Low BBB penetration"

    return {
        # Absorption
        "oral_absorption":     pct(hia),
        "bioavailability":     pct(bio),
        "caco2_permeability":  f"{round(caco2, 2)} cm/s" if caco2 else "N/A",
        "pampa_permeability":  pct(pampa),
        # Distribution
        "bbb_permeability":    bbb_class,
        "bbb_score":           round(bbb, 3) if bbb is not None else None,
        "pgp_substrate":       prob_label(pgp),
        "logp":                round(logp, 2) if logp else None,
        "tpsa":                round(tpsa, 1) if tpsa else None,
        # Toxicity
        "herg_inhibition":     f"Low ({pct(herg)})" if herg and herg < 0.3 else f"High ({pct(herg)})" if herg else "N/A",
        "herg_score":          round(herg, 3) if herg is not None else None,
        "hepatotoxicity":      f"Low ({pct(dili)})" if dili and dili < 0.3 else f"High ({pct(dili)})" if dili else "N/A",
        "dili_score":          round(dili, 3) if dili is not None else None,
        "ames_mutagenicity":   prob_label(ames),
        "clinical_toxicity":   pct(clintox),
        # Solubility
        "solubility_class":    sol_class,
        "log_s":               round(sol, 2) if sol is not None else None,
        # Drug-likeness
        "molecular_weight":    round(mw, 1) if mw else None,
        "lipinski_violations": int(4 - lipinski) if lipinski is not None else None,
        # Raw all 49 properties
        "raw":                 properties,
    }


# ── ADMET workflow ────────────────────────────────────────────────────────────
def _run_admet_sync(rowan, smiles: str) -> Optional[dict]:
    try:
        workflow = rowan.submit_admet_workflow(
            initial_smiles=smiles,
            name="causyn_admet",
        )
        print(f"  ADMET submitted: {workflow.uuid}")

        # Poll until done
        import time
        for _ in range(40):  # max 200s
            time.sleep(5)
            workflow.fetch_latest()
            if workflow.status.value in (2, 3, 4):  # completed/failed/stopped
                break

        # Get full data via retrieve
        full = rowan.retrieve_workflow(workflow.uuid)
        if full.data and isinstance(full.data, dict):
            props = full.data.get("properties", {})
            if props:
                print(f"  ✅ ADMET: {len(props)} properties retrieved")
                return _parse_admet(props)
    except Exception as e:
        print(f"⚠️  ADMET sync error: {e}")
    return None


async def run_admet(smiles: str) -> Optional[dict]:
    try:
        rowan = _init_rowan()
        if not rowan:
            return None
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: _run_admet_sync(rowan, smiles))
    except Exception as e:
        print(f"⚠️  Rowan ADMET error: {e}")
        return None


# ── pKa workflow ──────────────────────────────────────────────────────────────
def _run_pka_sync(rowan, smiles: str) -> Optional[dict]:
    try:
        from stjames import Molecule
        mol = Molecule.from_smiles(smiles)
        workflow = rowan.submit_pka_workflow(
            initial_molecule=mol,
            name="causyn_pka",
        )
        print(f"  pKa submitted: {workflow.uuid}")

        import time
        for _ in range(40):
            time.sleep(5)
            workflow.fetch_latest()
            if workflow.status.value in (2, 3, 4):
                break

        full = rowan.retrieve_workflow(workflow.uuid)
        if full.data and isinstance(full.data, dict):
            structures      = full.data.get("structures") or []
            conjugate_acids = full.data.get("conjugate_acids") or []
            conjugate_bases = full.data.get("conjugate_bases") or []
            pka_range       = full.data.get("pka_range", [2, 12])

            all_pkas = []

            # Extract pKa values from structures
            for s in structures:
                if isinstance(s, dict):
                    pka_val = s.get("pka") or s.get("pKa")
                    if pka_val and isinstance(pka_val, (int, float)):
                        all_pkas.append(round(pka_val, 2))

            # Also check conjugate acids/bases
            for item in (conjugate_acids + conjugate_bases):
                if isinstance(item, dict):
                    pka_val = item.get("pka") or item.get("pKa")
                    if pka_val and isinstance(pka_val, (int, float)):
                        all_pkas.append(round(pka_val, 2))

            # Assess activity at physiological pH 7.4
            active = "Unknown"
            # No pKa in range 2-12 means drug is neutral at physiological pH
            if not all_pkas:
                active = f"Neutral at physiological pH (no ionizable groups in pKa range {pka_range[0]}-{pka_range[1]})"
                # Neutral drugs are generally active at physiological pH
                active = "Yes — drug is neutral at physiological pH (no ionization)"
            else:
                for pka_val in all_pkas:
                    if 5.5 <= pka_val <= 9.0:
                        active = f"Yes — pKa {pka_val} near physiological pH"
                        break
                else:
                    active = f"Check ionization — pKa values: {all_pkas}"

            print(f"  ✅ pKa: {len(all_pkas)} values, status: {active[:50]}")
            return {
                "pka_values":                 all_pkas,
                "pka_range_tested":           pka_range,
                "active_at_physiological_ph": active,
                "raw":                        full.data,
            }
    except Exception as e:
        print(f"⚠️  pKa sync error: {e}")
    return None


async def run_pka(smiles: str) -> Optional[dict]:
    try:
        rowan = _init_rowan()
        if not rowan:
            return None
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: _run_pka_sync(rowan, smiles))
    except Exception as e:
        print(f"⚠️  pKa error: {e}")
        return None


# ── Solubility workflow ───────────────────────────────────────────────────────
def _run_solubility_sync(rowan, smiles: str) -> Optional[dict]:
    try:
        workflow = rowan.submit_solubility_workflow(
            initial_smiles=smiles,
            name="causyn_solubility",
        )
        print(f"  Solubility submitted: {workflow.uuid}")

        import time
        for _ in range(40):
            time.sleep(5)
            workflow.fetch_latest()
            if workflow.status.value in (2, 3, 4):
                break

        full = rowan.retrieve_workflow(workflow.uuid)
        if full.data and isinstance(full.data, dict):
            log_s = None

            # Rowan fastsolv returns solubilities per solvent at multiple temps
            # Use ethanol (CCO) at 298.15K (index 1) as proxy for aqueous
            # Water SMILES not directly available — use lowest solubility solvent
            solubilities = full.data.get("solubilities", {})
            temps = full.data.get("temperatures", [298.15])

            # Find index closest to 298.15K (room temp / physiological)
            try:
                temp_idx = min(range(len(temps)), key=lambda i: abs(temps[i] - 298.15))
            except Exception:
                temp_idx = 1

            # Try ethanol (CCO) first — closest to aqueous behavior
            # Then pick the solvent with highest solubility (best case)
            if "CCO" in solubilities:
                vals = solubilities["CCO"].get("solubilities", [])
                if vals and temp_idx < len(vals):
                    log_s = vals[temp_idx]
            elif solubilities:
                # Take average across solvents at target temp
                all_vals = []
                for sol_data in solubilities.values():
                    vals = sol_data.get("solubilities", [])
                    if vals and temp_idx < len(vals):
                        all_vals.append(vals[temp_idx])
                if all_vals:
                    log_s = sum(all_vals) / len(all_vals)

            sol_class = "Unknown"
            if log_s is not None and isinstance(log_s, (int, float)):
                if log_s >= -1:   sol_class = "Highly soluble"
                elif log_s >= -3: sol_class = "Soluble"
                elif log_s >= -5: sol_class = "Moderately soluble"
                else:             sol_class = "Poorly soluble"

            print(f"  ✅ Solubility: LogS={round(log_s, 2) if log_s else None} ({sol_class})")
            return {
                "log_s":            round(log_s, 2) if log_s is not None else None,
                "solubility_class": sol_class,
                "solvents_tested":  list(solubilities.keys()),
                "raw":              full.data,
            }
    except Exception as e:
        print(f"⚠️  Solubility sync error: {e}")
    return None


async def run_solubility(smiles: str) -> Optional[dict]:
    try:
        rowan = _init_rowan()
        if not rowan:
            return None
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: _run_solubility_sync(rowan, smiles))
    except Exception as e:
        print(f"⚠️  Solubility error: {e}")
        return None


# ── Full Molecular Validation ─────────────────────────────────────────────────
async def validate_drug_molecularly(
    drug_name: str,
    target_proteins: list = None,
    pdb_ids: list = None,
) -> dict:
    print(f"\n🔬 Rowan Phase 1 validation: {drug_name}")

    # Check biologic
    if is_biologic(drug_name):
        return {
            "available":     False,
            "drug_name":     drug_name,
            "is_biologic":   True,
            "error":         None,
            "biologic_note": (
                f"{drug_name} is a biologic (monoclonal antibody or protein therapeutic). "
                "Traditional small-molecule ADMET and docking validation does not apply. "
                "For biologics, validation requires immunogenicity assays, "
                "epitope mapping, and cryo-EM structural analysis."
            ),
        }

    # No API key — return mock
    if not ROWAN_API_KEY:
        print("⚠️  ROWAN_API_KEY not set — returning mock data")
        return _mock_validation(drug_name)

    # Get SMILES
    smiles = await get_smiles_from_pubchem(drug_name)
    if not smiles:
        return {
            "available":   False,
            "drug_name":   drug_name,
            "is_biologic": False,
            "error":       f"Could not retrieve molecular structure for {drug_name} from PubChem.",
        }

    # Run ADMET + pKa in parallel (solubility already included in ADMET)
    print(f"🧪 Running ADMET + pKa for {drug_name}...")
    admet_task = asyncio.create_task(run_admet(smiles))
    pka_task   = asyncio.create_task(run_pka(smiles))

    admet_result, pka_result = await asyncio.gather(
        admet_task, pka_task,
        return_exceptions=True
    )

    if isinstance(admet_result, Exception): admet_result = None
    if isinstance(pka_result, Exception):   pka_result   = None

    # Extract solubility from ADMET result (already computed there)
    solubility_result = None
    if admet_result:
        solubility_result = {
            "log_s":            admet_result.get("log_s"),
            "solubility_class": admet_result.get("solubility_class"),
            "source":           "ADMET-AI (from ADMET workflow)",
        }

    mol_score = _compute_molecular_score(admet_result, pka_result, solubility_result, [])

    return {
        "available":         True,
        "drug_name":         drug_name,
        "is_biologic":       False,
        "smiles":            smiles[:80] + "..." if len(smiles) > 80 else smiles,
        "admet":             admet_result,
        "pka":               pka_result,
        "solubility":        solubility_result,
        "docking":           [],
        "molecular_score":   mol_score["score"],
        "molecular_grade":   mol_score["grade"],
        "molecular_summary": mol_score["summary"],
        "rowan_powered":     True,
    }


# ── Scoring ───────────────────────────────────────────────────────────────────
def _compute_molecular_score(admet, pka, solubility, docking) -> dict:
    score   = 50
    reasons = []

    if admet:
        # hERG — cardiac safety (score 0-1, lower is safer)
        herg_score = admet.get("herg_score")
        if herg_score is not None:
            if herg_score < 0.3:
                score += 10; reasons.append(f"✅ Low hERG risk ({round(herg_score*100)}%)")
            elif herg_score > 0.7:
                score -= 15; reasons.append(f"⚠️ High hERG risk ({round(herg_score*100)}%)")

        # DILI — liver toxicity (lower is safer)
        dili_score = admet.get("dili_score")
        if dili_score is not None:
            if dili_score < 0.3:
                score += 8; reasons.append(f"✅ Low hepatotoxicity ({round(dili_score*100)}%)")
            elif dili_score > 0.7:
                score -= 12; reasons.append(f"⚠️ Hepatotoxicity concern ({round(dili_score*100)}%)")

        # BBB penetration
        bbb = admet.get("bbb_score")
        if bbb is not None:
            if bbb >= 0.6:
                score += 8; reasons.append(f"✅ Good BBB penetration ({round(bbb*100)}%)")
            elif bbb < 0.3:
                reasons.append(f"ℹ️ Low BBB penetration ({round(bbb*100)}%)")

        # Oral absorption
        oral = admet.get("oral_absorption", "")
        if oral and "%" in str(oral):
            val = float(str(oral).replace("%", ""))
            if val >= 80:
                score += 7; reasons.append(f"✅ High oral absorption ({oral})")

        # Bioavailability
        bio = admet.get("bioavailability", "")
        if bio and "%" in str(bio):
            val = float(str(bio).replace("%", ""))
            if val >= 70:
                score += 5; reasons.append(f"✅ Good bioavailability ({bio})")

        # Solubility from ADMET
        sol_class = admet.get("solubility_class", "")
        if "highly" in str(sol_class).lower():
            score += 8; reasons.append(f"✅ Highly soluble")
        elif "poorly" in str(sol_class).lower():
            score -= 5; reasons.append(f"⚠️ Poor solubility")

    # pKa
    if pka:
        active = str(pka.get("active_at_physiological_ph", "")).lower()
        if "yes" in active or "neutral" in active:
            score += 5; reasons.append("✅ Active at pH 7.4")

    # Docking
    for dock in (docking or []):
        affinity = dock.get("binding_affinity_kcal_mol")
        if affinity and isinstance(affinity, (int, float)):
            if affinity <= -9:   score += 15; reasons.append(f"✅ Excellent docking ({affinity:.1f})")
            elif affinity <= -7: score += 10; reasons.append(f"✅ Strong docking ({affinity:.1f})")
            elif affinity <= -5: score += 5;  reasons.append(f"🔶 Moderate docking ({affinity:.1f})")
            else:                score -= 5;  reasons.append(f"⚠️ Weak docking ({affinity:.1f})")

    score = max(0, min(100, score))
    if score >= 75:   grade = "A — Strong molecular candidate"
    elif score >= 60: grade = "B — Promising candidate"
    elif score >= 45: grade = "C — Moderate candidate"
    else:             grade = "D — Weak molecular fit"

    return {
        "score":   score,
        "grade":   grade,
        "summary": " · ".join(reasons) if reasons else "Molecular validation completed",
    }


# ── Mock fallback ─────────────────────────────────────────────────────────────
def _mock_validation(drug_name: str) -> dict:
    return {
        "available":     True,
        "drug_name":     drug_name,
        "is_biologic":   False,
        "smiles":        "CN(C)C(=N)N=C(N)N (mock)",
        "rowan_powered": False,
        "mock":          True,
        "admet": {
            "oral_absorption":     "94%",
            "bioavailability":     "77%",
            "bbb_permeability":    "Moderate BBB penetration",
            "bbb_score":          0.57,
            "herg_inhibition":     "Low (7%)",
            "herg_score":          0.068,
            "hepatotoxicity":      "Low (9%)",
            "dili_score":          0.087,
            "solubility_class":    "Highly soluble",
            "log_s":               -0.6,
            "molecular_weight":    129.2,
            "lipinski_violations": 0,
        },
        "pka": {
            "pka_values":                 [11.5, 13.0],
            "active_at_physiological_ph": "Check — pKa 11.5 vs pH 7.4",
        },
        "solubility": {
            "log_s":            -0.6,
            "solubility_class": "Highly soluble",
        },
        "docking":           [],
        "molecular_score":   78,
        "molecular_grade":   "B — Promising candidate",
        "molecular_summary": "Mock data — set ROWAN_API_KEY to enable real validation",
    }
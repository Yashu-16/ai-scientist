# backend/services/rowan_service.py
# Rowan Phase 1 — Pure REST API implementation (no SDK required)
# Works on any Python version (3.10, 3.11, 3.14+)
# API: https://api.rowansci.com with X-API-Key header

import os
import asyncio
import httpx
from typing import Optional

ROWAN_API_KEY = os.getenv("ROWAN_API_KEY", "")
ROWAN_BASE    = "https://api.rowansci.com"
PUBCHEM_BASE  = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

# ── Known biologics ───────────────────────────────────────────────────────────
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
    suffixes = ["mab","zumab","mumab","umab","ximab","cept","kine","fermin","tropin"]
    return any(drug_name.lower().endswith(s) for s in suffixes)


# ── Rowan REST helpers ────────────────────────────────────────────────────────
def _rowan_headers() -> dict:
    return {"X-API-Key": ROWAN_API_KEY, "Content-Type": "application/json"}


async def _submit_workflow(workflow_type: str, workflow_data: dict, name: str, smiles: str) -> Optional[str]:
    """Submit a Rowan workflow via REST API. Returns UUID."""
    payload = {
        "name":          name,
        "folder_uuid":   None,
        "workflow_type": workflow_type,
        "workflow_data": workflow_data,
        "initial_smiles": smiles,
        "max_credits":   None,
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.post(
                f"{ROWAN_BASE}/workflow",
                headers=_rowan_headers(),
                json=payload,
            )
            if res.status_code == 200:
                data = res.json()
                uuid = data.get("uuid")
                print(f"  ✅ Submitted {workflow_type}: {uuid}")
                return uuid
            else:
                print(f"  ⚠️  Submit {workflow_type} failed: {res.status_code} {res.text[:200]}")
    except Exception as e:
        print(f"  ⚠️  Submit {workflow_type} error: {e}")
    return None


async def _poll_workflow(uuid: str, max_wait: int = 300) -> Optional[dict]:
    """Poll Rowan workflow until complete. Returns full workflow dict."""
    import time as _time
    start = _time.time()
    DONE = {"completed_ok", "completed", "failed", "stopped", "error"}

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        while _time.time() - start < max_wait:
            try:
                res = await client.get(
                    f"{ROWAN_BASE}/workflow/{uuid}/",
                    headers=_rowan_headers(),
                )
                if res.status_code == 200:
                    data = res.json()
                    # Rowan returns status as object_status (int) or status string
                    status_int = data.get("object_status")
                    status_str = str(data.get("status", "")).lower()
                    elapsed = round(_time.time() - start)
                    print(f"  [{elapsed}s] {uuid[:8]}... status_int={status_int} status_str={status_str}")
                    # Status 2=completed_ok, 3=failed, 4=stopped
                    if status_int in (2, 3, 4) or any(s in status_str for s in DONE):
                        return data
                else:
                    print(f"  ⚠️  Poll error: {res.status_code}")
            except Exception as e:
                print(f"  ⚠️  Poll exception: {e}")
            await asyncio.sleep(6)

    print(f"  ⏱️  Workflow {uuid} timed out after {max_wait}s")
    return None


# ── PubChem SMILES ────────────────────────────────────────────────────────────
async def get_smiles_from_pubchem(drug_name: str) -> Optional[str]:
    if is_biologic(drug_name):
        print(f"  ℹ️  {drug_name} is a biologic — skipping SMILES")
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
                            smiles = (
                                props[0].get("IsomericSMILES") or
                                props[0].get("CanonicalSMILES") or
                                props[0].get("ConnectivitySMILES")
                            )
                            if smiles:
                                print(f"  ✅ PubChem SMILES: {smiles[:50]}...")
                                return smiles
                except Exception:
                    continue
            # CID fallback
            r = await client.get(f"{PUBCHEM_BASE}/compound/name/{drug_name}/cids/JSON")
            if r.status_code == 200:
                cids = r.json().get("IdentifierList", {}).get("CID", [])
                if cids:
                    r2 = await client.get(
                        f"{PUBCHEM_BASE}/compound/cid/{cids[0]}/property/IsomericSMILES/JSON"
                    )
                    if r2.status_code == 200:
                        props = r2.json().get("PropertyTable", {}).get("Properties", [])
                        if props:
                            smiles = props[0].get("IsomericSMILES") or props[0].get("CanonicalSMILES")
                            if smiles:
                                print(f"  ✅ PubChem CID SMILES: {smiles[:50]}...")
                                return smiles
    except Exception as e:
        print(f"  ⚠️  PubChem error: {e}")
    print(f"  ❌ No SMILES for {drug_name}")
    return None


# ── ADMET ─────────────────────────────────────────────────────────────────────
async def run_admet(smiles: str) -> Optional[dict]:
    """Run ADMET-AI prediction via Rowan REST API."""
    print(f"  🧪 Submitting ADMET...")
    uuid = await _submit_workflow(
        workflow_type="admet",
        workflow_data={"messages": [], "mode": "rapid", "initial_smiles": smiles},
        name="causyn_admet",
        smiles=smiles,
    )
    if not uuid:
        return None

    result = await _poll_workflow(uuid, max_wait=300)
    if not result:
        return None

    data = result.get("object_data") or {}
    props = data.get("properties", {})
    if props:
        print(f"  ✅ ADMET: {len(props)} properties")
        return _parse_admet(props)

    print(f"  ⚠️  ADMET data keys: {list(data.keys())}")
    return None

def _parse_admet(properties: dict) -> dict:
    """Parse Rowan's 49 ADMET properties into human-readable format."""
    def pct(v): return f"{round(v * 100)}%" if v is not None else "N/A"
    def prob_label(v, t=0.5): return "Yes" if v and v >= t else "No"

    bbb    = properties.get("BBB_Martins")
    herg   = properties.get("hERG")
    dili   = properties.get("DILI")
    hia    = properties.get("HIA_Hou")
    sol    = properties.get("Solubility_AqSolDB")
    bio    = properties.get("Bioavailability_Ma")
    clintox= properties.get("ClinTox")
    ames   = properties.get("AMES")
    logp   = properties.get("Lipophilicity_AstraZeneca") or properties.get("logP")
    tpsa   = properties.get("tpsa")
    mw     = properties.get("molecular_weight")
    lipinski = properties.get("Lipinski")
    pgp    = properties.get("Pgp_Broccatelli")
    caco2  = properties.get("Caco2_Wang")
    pampa  = properties.get("PAMPA_NCATS")

    sol_class = "Unknown"
    if sol is not None:
        if sol >= -1:   sol_class = "Highly soluble"
        elif sol >= -3: sol_class = "Soluble"
        elif sol >= -5: sol_class = "Moderately soluble"
        else:           sol_class = "Poorly soluble"

    bbb_class = "Unknown"
    if bbb is not None:
        if bbb >= 0.7:   bbb_class = "High BBB penetration"
        elif bbb >= 0.4: bbb_class = "Moderate BBB penetration"
        else:            bbb_class = "Low BBB penetration"

    return {
        "oral_absorption":      pct(hia),
        "bioavailability":      pct(bio),
        "caco2_permeability":   f"{round(caco2, 2)} cm/s" if caco2 else "N/A",
        "pampa_permeability":   pct(pampa),
        "bbb_permeability":     bbb_class,
        "bbb_score":            round(bbb, 3) if bbb is not None else None,
        "pgp_substrate":        prob_label(pgp),
        "logp":                 round(logp, 2) if logp else None,
        "tpsa":                 round(tpsa, 1) if tpsa else None,
        "herg_inhibition":      f"Low ({pct(herg)})" if herg and herg < 0.3 else f"High ({pct(herg)})" if herg else "N/A",
        "herg_score":           round(herg, 3) if herg is not None else None,
        "hepatotoxicity":       f"Low ({pct(dili)})" if dili and dili < 0.3 else f"High ({pct(dili)})" if dili else "N/A",
        "dili_score":           round(dili, 3) if dili is not None else None,
        "ames_mutagenicity":    prob_label(ames),
        "clinical_toxicity":    pct(clintox),
        "solubility_class":     sol_class,
        "log_s":                round(sol, 2) if sol is not None else None,
        "molecular_weight":     round(mw, 1) if mw else None,
        "lipinski_violations":  int(4 - lipinski) if lipinski is not None else None,
        "raw":                  properties,
    }


# ── pKa ──────────────────────────────────────────────────────────────────────
async def run_pka(smiles: str) -> Optional[dict]:
    """Run pKa prediction via Rowan REST API."""
    print(f"  🧪 Submitting pKa...")
    uuid = await _submit_workflow(
        workflow_type="pka",
        workflow_data={
            "messages": [], "mode": "careful",
            "initial_smiles": smiles,
            "microscopic_pka_method": "aimnet2_wagen2024",
            "solvent": "water",
            "pka_range": [2.0, 12.0],
            "deprotonate_elements": [7, 8, 16],
            "deprotonate_atoms": [],
            "protonate_elements": [7],
            "protonate_atoms": [],
            "reasonableness_buffer": 5.0,
            "structures": [],
            "conjugate_acids": [],
            "conjugate_bases": [],
        },
        name="causyn_pka",
        smiles=smiles,
    )
    if not uuid:
        return None

    result = await _poll_workflow(uuid, max_wait=300)
    if not result:
        return None

    data = result.get("object_data") or {}
    structures = data.get("structures") or []
    pka_range  = data.get("pka_range", [2, 12])
    all_pkas   = []

    for s in structures:
        if isinstance(s, dict):
            val = s.get("pka") or s.get("pKa")
            if val and isinstance(val, (int, float)):
                all_pkas.append(round(val, 2))

    active = "Unknown"
    if not all_pkas:
        active = "Yes — drug is neutral at physiological pH (no ionization in pKa 2-12)"
    else:
        for v in all_pkas:
            if 5.5 <= v <= 9.0:
                active = f"Yes — pKa {v} near physiological pH"
                break
        else:
            active = f"Check ionization — pKa: {all_pkas}"

    print(f"  ✅ pKa: {len(all_pkas)} values, {active[:50]}")
    return {
        "pka_values":                 all_pkas,
        "pka_range_tested":           pka_range,
        "active_at_physiological_ph": active,
    }


# ── Full validation ───────────────────────────────────────────────────────────
async def validate_drug_molecularly(
    drug_name: str,
    target_proteins: list = None,
    pdb_ids: list = None,
) -> dict:
    print(f"\n🔬 Rowan REST validation: {drug_name}")

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

    if not ROWAN_API_KEY:
        print("  ⚠️  ROWAN_API_KEY not set — returning mock")
        return _mock_validation(drug_name)

    smiles = await get_smiles_from_pubchem(drug_name)
    if not smiles:
        return {
            "available":   False,
            "drug_name":   drug_name,
            "is_biologic": False,
            "error":       f"Could not retrieve SMILES for {drug_name} from PubChem.",
        }

    # Run ADMET + pKa in parallel
    print(f"  🧬 Running ADMET + pKa in parallel...")
    admet_task = asyncio.create_task(run_admet(smiles))
    pka_task   = asyncio.create_task(run_pka(smiles))

    admet_result, pka_result = await asyncio.gather(
        admet_task, pka_task, return_exceptions=True
    )

    if isinstance(admet_result, Exception):
        print(f"  ⚠️  ADMET exception: {admet_result}")
        admet_result = None
    if isinstance(pka_result, Exception):
        print(f"  ⚠️  pKa exception: {pka_result}")
        pka_result = None

    # Extract solubility from ADMET
    solubility_result = None
    if admet_result:
        solubility_result = {
            "log_s":            admet_result.get("log_s"),
            "solubility_class": admet_result.get("solubility_class"),
            "source":           "ADMET-AI",
        }

    mol_score = _compute_molecular_score(admet_result, pka_result)

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


def _compute_molecular_score(admet, pka) -> dict:
    score, reasons = 50, []

    if admet:
        herg = admet.get("herg_score")
        if herg is not None:
            if herg < 0.3:  score += 10; reasons.append(f"✅ Low hERG ({round(herg*100)}%)")
            elif herg > 0.7: score -= 15; reasons.append(f"⚠️ High hERG ({round(herg*100)}%)")

        dili = admet.get("dili_score")
        if dili is not None:
            if dili < 0.3:  score += 8; reasons.append(f"✅ Low hepatotoxicity ({round(dili*100)}%)")
            elif dili > 0.7: score -= 12; reasons.append(f"⚠️ Hepatotoxicity ({round(dili*100)}%)")

        bbb = admet.get("bbb_score")
        if bbb is not None:
            if bbb >= 0.6: score += 8; reasons.append(f"✅ Good BBB ({round(bbb*100)}%)")

        oral = admet.get("oral_absorption", "")
        if "%" in str(oral) and float(str(oral).replace("%","")) >= 80:
            score += 7; reasons.append(f"✅ High oral absorption ({oral})")

        bio = admet.get("bioavailability", "")
        if "%" in str(bio) and float(str(bio).replace("%","")) >= 70:
            score += 5; reasons.append(f"✅ Good bioavailability ({bio})")

        sol = str(admet.get("solubility_class","")).lower()
        if "highly" in sol: score += 8; reasons.append("✅ Highly soluble")
        elif "poorly" in sol: score -= 5; reasons.append("⚠️ Poor solubility")

    if pka:
        active = str(pka.get("active_at_physiological_ph","")).lower()
        if "yes" in active or "neutral" in active:
            score += 5; reasons.append("✅ Active at pH 7.4")

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


def _mock_validation(drug_name: str) -> dict:
    return {
        "available":     True,
        "drug_name":     drug_name,
        "is_biologic":   False,
        "smiles":        "CN(C)C(=N)N=C(N)N (mock)",
        "rowan_powered": False,
        "mock":          True,
        "admet": {
            "oral_absorption":  "94%", "bioavailability": "76%",
            "bbb_permeability": "Moderate BBB penetration", "bbb_score": 0.57,
            "herg_inhibition":  "Low (7%)", "herg_score": 0.068,
            "hepatotoxicity":   "Low (9%)", "dili_score": 0.087,
            "solubility_class": "Highly soluble", "log_s": -0.6,
            "molecular_weight": 129.2, "lipinski_violations": 0,
        },
        "pka": {
            "pka_values": [],
            "active_at_physiological_ph": "Yes — drug is neutral at physiological pH",
        },
        "solubility":        {"log_s": -0.6, "solubility_class": "Highly soluble"},
        "docking":           [],
        "molecular_score":   78,
        "molecular_grade":   "B — Promising candidate",
        "molecular_summary": "Mock — set ROWAN_API_KEY to enable real validation",
    }
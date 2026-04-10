# backend/services/clinical_trials_service.py
# Real clinical trial data from ClinicalTrials.gov API v2
# Free API — no key required

import requests

CLINICAL_TRIALS_API = "https://clinicaltrials.gov/api/v2/studies"

# ── Status display mapping ────────────────────────────────────
STATUS_DISPLAY = {
    "RECRUITING":              {"label": "Recruiting",        "color": "#22c55e"},
    "ACTIVE_NOT_RECRUITING":   {"label": "Active",            "color": "#3b82f6"},
    "COMPLETED":               {"label": "Completed",         "color": "#64748b"},
    "NOT_YET_RECRUITING":      {"label": "Not Yet Recruiting","color": "#f59e0b"},
    "TERMINATED":              {"label": "Terminated",        "color": "#ef4444"},
    "WITHDRAWN":               {"label": "Withdrawn",         "color": "#ef4444"},
    "SUSPENDED":               {"label": "Suspended",         "color": "#f97316"},
    "UNKNOWN":                 {"label": "Unknown",           "color": "#94a3b8"},
}

PHASE_DISPLAY = {
    "PHASE1":    "Phase 1",
    "PHASE2":    "Phase 2",
    "PHASE3":    "Phase 3",
    "PHASE4":    "Phase 4",
    "EARLY_PHASE1": "Early Phase 1",
    "NA":        "N/A",
}


def parse_trial(study: dict) -> dict:
    """Parse a single ClinicalTrials.gov study into clean format."""
    protocol = study.get("protocolSection", {})

    # Identification
    id_module     = protocol.get("identificationModule", {})
    nct_id        = id_module.get("nctId", "")
    title         = id_module.get("briefTitle", "")

    # Status
    status_module = protocol.get("statusModule", {})
    status_raw    = status_module.get("overallStatus", "UNKNOWN")
    start_date    = status_module.get("startDateStruct", {}).get("date", "")
    completion    = status_module.get("completionDateStruct", {}).get("date", "")

    # Sponsor
    sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
    sponsor        = sponsor_module.get("leadSponsor", {}).get("name", "")

    # Conditions
    conditions_module = protocol.get("conditionsModule", {})
    conditions        = conditions_module.get("conditions", [])

    # Phase
    design_module = protocol.get("designModule", {})
    phases        = design_module.get("phases", [])
    phase_raw     = phases[0] if phases else "NA"
    phase_display = PHASE_DISPLAY.get(phase_raw, phase_raw)

    # Interventions
    interventions_module = protocol.get("armsInterventionsModule", {})
    interventions        = interventions_module.get("interventions", [])
    drug_names           = [
        i.get("name", "")
        for i in interventions
        if i.get("type", "").upper() == "DRUG"
    ]

    # Status display
    status_info = STATUS_DISPLAY.get(status_raw, STATUS_DISPLAY["UNKNOWN"])

    return {
        "nct_id":       nct_id,
        "title":        title,
        "status":       status_raw,
        "status_label": status_info["label"],
        "status_color": status_info["color"],
        "phase":        phase_display,
        "phase_raw":    phase_raw,
        "sponsor":      sponsor,
        "start_date":   start_date,
        "completion_date": completion,
        "conditions":   conditions,
        "drug_names":   drug_names,
        "url":          f"https://clinicaltrials.gov/study/{nct_id}",
    }


def fetch_trials_for_drug(
    drug_name:    str,
    disease_name: str = "",
    max_results:  int = 5
) -> list:
    """
    Fetch clinical trials for a specific drug.
    Optionally filter by disease name.
    Returns list of trial dicts.
    """
    params = {
        "query.intr": drug_name,
        "fields":     "NCTId,BriefTitle,OverallStatus,Phase,"
                      "LeadSponsorName,StartDate,CompletionDate,"
                      "Condition,InterventionName,InterventionType",
        "pageSize":   max_results,
    }

    # Add disease filter if provided
    if disease_name:
        params["query.cond"] = disease_name

    try:
        response = requests.get(
            CLINICAL_TRIALS_API,
            params=params,
            timeout=30
        )
        response.raise_for_status()
        data    = response.json()
        studies = data.get("studies", [])

        trials = [parse_trial(s) for s in studies]
        print(f"     🔬 Trials for {drug_name}: {len(trials)} found")
        return trials

    except Exception as e:
        print(f"     ⚠️  Trials fetch error for {drug_name}: {e}")
        return []


def fetch_trials_for_disease(
    disease_name: str,
    max_results:  int = 10,
    status_filter: list = None
) -> list:
    """
    Fetch all clinical trials for a disease.
    Returns list of trial dicts sorted by status (recruiting first).
    """
    params = {
        "query.cond": disease_name,
        "fields":     "NCTId,BriefTitle,OverallStatus,Phase,"
                      "LeadSponsorName,StartDate,CompletionDate,"
                      "Condition,InterventionName,InterventionType",
        "pageSize":   max_results,
    }

    # Filter by status if provided
    if status_filter:
        params["filter.overallStatus"] = ",".join(status_filter)

    try:
        response = requests.get(
            CLINICAL_TRIALS_API,
            params=params,
            timeout=30
        )
        response.raise_for_status()
        data    = response.json()
        studies = data.get("studies", [])

        trials = [parse_trial(s) for s in studies]

        # Sort: Recruiting first, then Active, then Completed
        status_order = {
            "RECRUITING":            0,
            "ACTIVE_NOT_RECRUITING": 1,
            "NOT_YET_RECRUITING":    2,
            "COMPLETED":             3,
            "UNKNOWN":               4,
            "TERMINATED":            5,
            "WITHDRAWN":             6,
        }
        trials.sort(key=lambda t: status_order.get(t["status"], 99))

        print(f"  🔬 Disease trials for {disease_name}: {len(trials)} found")
        return trials

    except Exception as e:
        print(f"  ⚠️  Disease trials fetch error: {e}")
        return []


def enrich_drugs_with_trials(
    drugs:        list,
    disease_name: str,
    max_per_drug: int = 3
) -> list:
    """
    Add clinical trial data to each drug in the drugs list.
    Returns enriched drugs list.
    """
    print(f"\n  🔬 Fetching clinical trials for {len(drugs)} drugs...")

    for drug in drugs:
        drug_name = drug.get("drug_name", "")
        if not drug_name:
            continue

        trials = fetch_trials_for_drug(
            drug_name    = drug_name,
            disease_name = disease_name,
            max_results  = max_per_drug
        )

        # Add trial summary to drug
        drug["clinical_trials"]       = trials
        drug["trial_count"]           = len(trials)
        drug["active_trial_count"]    = sum(
            1 for t in trials
            if t["status"] in ("RECRUITING", "ACTIVE_NOT_RECRUITING")
        )
        drug["completed_trial_count"] = sum(
            1 for t in trials
            if t["status"] == "COMPLETED"
        )

        # Update clinical phase from trials if more accurate
        if trials:
            # Find highest phase from real trials
            phase_map = {"Phase 4":4,"Phase 3":3,"Phase 2":2,"Phase 1":1}
            trial_phases = [
                phase_map.get(t["phase"], 0)
                for t in trials
            ]
            if trial_phases:
                max_trial_phase = max(trial_phases)
                # Only update if trial phase is higher than current
                current_phase = drug.get("clinical_phase") or 0
                if max_trial_phase > current_phase:
                    drug["clinical_phase"] = max_trial_phase
                    print(f"     📈 Updated {drug_name} phase: "
                          f"{current_phase} → {max_trial_phase}")

    return drugs


def get_trial_summary(trials: list) -> dict:
    """
    Generate a summary of trial activity from a list of trials.
    """
    if not trials:
        return {
            "total":     0,
            "active":    0,
            "completed": 0,
            "recruiting":0,
            "summary":   "No clinical trials found"
        }

    total     = len(trials)
    recruiting = sum(1 for t in trials if t["status"] == "RECRUITING")
    active     = sum(1 for t in trials
                     if t["status"] == "ACTIVE_NOT_RECRUITING")
    completed  = sum(1 for t in trials if t["status"] == "COMPLETED")

    if recruiting > 0:
        summary = f"{recruiting} trial(s) currently recruiting"
    elif active > 0:
        summary = f"{active} active trial(s) in progress"
    elif completed > 0:
        summary = f"{completed} completed trial(s)"
    else:
        summary = f"{total} trial(s) found"

    return {
        "total":      total,
        "recruiting": recruiting,
        "active":     active,
        "completed":  completed,
        "summary":    summary
    }


# ── Quick test ────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing ClinicalTrials.gov Service")
    print("=" * 55)

    # Test 1: Alkaptonuria disease trials
    print("\n1. Disease trials — Alkaptonuria:")
    trials = fetch_trials_for_disease("Alkaptonuria", max_results=5)
    for t in trials:
        print(f"   {t['status_label']:15} | {t['phase']:8} | "
              f"{t['nct_id']} | {t['title'][:50]}")

    # Test 2: Drug trials — Nitisinone
    print("\n2. Drug trials — Nitisinone + Alkaptonuria:")
    trials = fetch_trials_for_drug("Nitisinone", "Alkaptonuria", max_results=5)
    for t in trials:
        print(f"   {t['status_label']:15} | {t['phase']:8} | "
              f"{t['nct_id']} | {t['title'][:50]}")

    # Test 3: Alzheimer + Donepezil
    print("\n3. Drug trials — Donepezil + Alzheimer disease:")
    trials = fetch_trials_for_drug("Donepezil", "Alzheimer disease", max_results=3)
    for t in trials:
        print(f"   {t['status_label']:15} | {t['phase']:8} | "
              f"{t['nct_id']} | {t['title'][:50]}")

    # Test 4: Enrich drugs list
    print("\n4. Enrich drugs with trials:")
    test_drugs = [
        {"drug_name": "Nitisinone",  "clinical_phase": 4},
        {"drug_name": "Levodopa",    "clinical_phase": 4},
    ]
    enriched = enrich_drugs_with_trials(test_drugs, "Alkaptonuria", max_per_drug=3)
    for d in enriched:
        print(f"   💊 {d['drug_name']}: "
              f"{d['trial_count']} trials "
              f"({d['active_trial_count']} active, "
              f"{d['completed_trial_count']} completed)")
import requests

# Test 1: Search trials for Alkaptonuria
r1 = requests.get(
    "https://clinicaltrials.gov/api/v2/studies",
    params={
        "query.cond": "Alkaptonuria",
        "filter.overallStatus": "RECRUITING,ACTIVE_NOT_RECRUITING,COMPLETED",
        "fields": "NCTId,BriefTitle,OverallStatus,Phase,LeadSponsorName,StartDate,Condition",
        "pageSize": 5
    },
    timeout=30
)
print("Test 1 - Alkaptonuria trials:", r1.status_code)
print(r1.text[:800])

# Test 2: Search trials for a drug
r2 = requests.get(
    "https://clinicaltrials.gov/api/v2/studies",
    params={
        "query.intr": "Nitisinone",
        "query.cond": "Alkaptonuria",
        "fields": "NCTId,BriefTitle,OverallStatus,Phase,LeadSponsorName,StartDate",
        "pageSize": 5
    },
    timeout=30
)
print("\nTest 2 - Nitisinone trials:", r2.status_code)
print(r2.text[:800])

# Test 3: Search trials for Alzheimer + Donepezil
r3 = requests.get(
    "https://clinicaltrials.gov/api/v2/studies",
    params={
        "query.intr": "Donepezil",
        "query.cond": "Alzheimer",
        "fields": "NCTId,BriefTitle,OverallStatus,Phase",
        "pageSize": 3
    },
    timeout=30
)
print("\nTest 3 - Donepezil Alzheimer trials:", r3.status_code)
print(r3.text[:800])

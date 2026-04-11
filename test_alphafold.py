import requests

# Check what AlphaFold API actually returns for APP (P05067)
r = requests.get(
    "https://alphafold.ebi.ac.uk/api/prediction/P05067",
    timeout=10
)
print("Status:", r.status_code)
print("Response:", r.text[:500])

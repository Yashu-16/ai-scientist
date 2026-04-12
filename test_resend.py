import requests
import os

API_KEY = "re_AkJEMzba_FMQLLMkidvfZJzYs5AT88Mwq"  # paste your actual key

r = requests.post(
    "https://api.resend.com/emails",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "from": "onboarding@resend.dev",
        "to": "yash.randhe164@gmail.com",  # paste your own email
        "subject": "AI Scientist - Invite Test",
        "html": "<h1>Test invite email</h1><p>If you see this, Resend is working!</p>"
    }
)
print("Status:", r.status_code)
print("Response:", r.text)

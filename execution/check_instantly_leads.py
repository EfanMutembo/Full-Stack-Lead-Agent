"""
Quick script to check what lead data is actually in Instantly campaign.
"""
import os
import sys
import json
import requests
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

api_key = os.getenv("INSTANTLY_API_KEY")
campaign_id = "9c02e553-62d8-43d8-a3c3-87fc1da8c398"

# Try to get leads from campaign
api_url = f"https://api.instantly.ai/api/v2/campaigns/{campaign_id}/leads"

headers = {
    "Authorization": f"Bearer {api_key}",
    "x-api-key": api_key,
    "Content-Type": "application/json"
}

print(f"🔍 Fetching leads from campaign: {campaign_id}\n")

try:
    response = requests.get(api_url, headers=headers, timeout=30)

    if response.status_code == 200:
        data = response.json()
        leads = data.get("leads", []) if isinstance(data, dict) else data

        if leads and len(leads) > 0:
            # Show first lead
            first_lead = leads[0]
            print("✅ First lead in campaign:")
            print(json.dumps(first_lead, indent=2))

            # Check for name fields
            print("\n📊 Name field analysis:")
            print(f"   first_name: '{first_lead.get('first_name', 'NOT FOUND')}'")
            print(f"   last_name: '{first_lead.get('last_name', 'NOT FOUND')}'")
            print(f"   full_name: '{first_lead.get('full_name', 'NOT FOUND')}'")
            print(f"   name: '{first_lead.get('name', 'NOT FOUND')}'")
            print(f"   email: '{first_lead.get('email', 'NOT FOUND')}'")
            print(f"   company_name: '{first_lead.get('company_name', 'NOT FOUND')}'")

        else:
            print("⚠️  No leads found in campaign")
    else:
        print(f"❌ API Error: {response.status_code}")
        print(f"Response: {response.text}")

except Exception as e:
    print(f"❌ Error: {str(e)}")

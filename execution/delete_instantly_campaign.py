"""
Delete an Instantly campaign.
"""
import os
import sys
import requests
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

api_key = os.getenv("INSTANTLY_API_KEY")
campaign_id = "66a51a64-d5a3-41d6-9c8f-966f73c1be78"

api_url = f"https://api.instantly.ai/api/v2/campaigns/{campaign_id}"

headers = {
    "Authorization": f"Bearer {api_key}",
    "x-api-key": api_key
}

print(f"🗑️  Deleting campaign: {campaign_id}\n")

try:
    response = requests.delete(api_url, headers=headers, timeout=30)

    if response.status_code in [200, 204]:
        print("✅ Campaign deleted successfully")
    else:
        print(f"⚠️  API Response: {response.status_code}")
        print(f"   {response.text}")

except Exception as e:
    print(f"❌ Error: {str(e)}")

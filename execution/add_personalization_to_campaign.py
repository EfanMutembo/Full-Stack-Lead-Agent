"""
Add personalization data to leads in an Instantly campaign.

Instead of delete/re-add, this just adds the leads with personalization.
Instantly will update existing leads when you add them again with the same email.

Usage:
    python add_personalization_to_campaign.py --input .tmp/csv_leads_personalized.json --campaign-id "9c02e553-62d8-43d8-a3c3-87fc1da8c398"
"""

import os
import sys
import json
import argparse
import requests
import time
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()


def add_personalized_leads_to_campaign(input_file, campaign_id):
    """
    Add personalized leads to Instantly campaign.

    Args:
        input_file (str): Path to JSON file with personalized leads
        campaign_id (str): Instantly campaign ID

    Returns:
        dict: Results with upload statistics
    """

    # Get API key
    api_key = os.getenv("INSTANTLY_API_KEY")
    if not api_key:
        return {
            "status": "error",
            "message": "INSTANTLY_API_KEY not found in .env file"
        }

    # Load personalized leads
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            leads = json.load(f)
    except FileNotFoundError:
        return {
            "status": "error",
            "message": f"Input file not found: {input_file}"
        }
    except json.JSONDecodeError:
        return {
            "status": "error",
            "message": f"Invalid JSON in file: {input_file}"
        }

    if not leads:
        return {
            "status": "error",
            "message": "No leads found in input file"
        }

    # Filter to only leads with personalization
    personalized_leads = [lead for lead in leads if lead.get('personalization')]

    if not personalized_leads:
        return {
            "status": "error",
            "message": f"No leads with personalization found in input file (0/{len(leads)})"
        }

    print(f"📊 Adding personalized leads to Instantly campaign...")
    print(f"   Campaign ID: {campaign_id}")
    print(f"   Total leads in file: {len(leads)}")
    print(f"   Leads with personalization: {len(personalized_leads)}")

    # Use V2 API endpoint for adding leads
    api_url = "https://api.instantly.ai/api/v2/leads/add"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }

    # Process in batches
    batch_size = 100
    batches = [personalized_leads[i:i + batch_size] for i in range(0, len(personalized_leads), batch_size)]

    total_uploaded = 0
    total_failed = 0

    print(f"\n📤 Uploading {len(batches)} batch(es)...")

    for batch_num, batch in enumerate(batches, 1):
        # Format leads for Instantly API
        formatted_leads = []
        for lead in batch:
            instantly_lead = {
                "email": lead.get("email", ""),
                "first_name": lead.get("first_name", ""),
                "last_name": lead.get("last_name", ""),
                "company_name": lead.get("company_name_normalized") or lead.get("company_name", ""),
                "website": lead.get("company_website", ""),
                "personalization": lead.get("personalization", "")
            }

            # Remove empty fields
            instantly_lead = {k: v for k, v in instantly_lead.items() if v}
            formatted_leads.append(instantly_lead)

        request_data = {
            "campaign_id": campaign_id,
            "leads": formatted_leads
        }

        try:
            response = requests.post(api_url, json=request_data, headers=headers, timeout=60)

            if response.status_code == 200:
                result = response.json()
                uploaded = result.get("leads_uploaded", len(formatted_leads))
                total_uploaded += uploaded
                print(f"   ✅ Batch {batch_num}/{len(batches)}: {uploaded} leads uploaded")
            else:
                print(f"   ❌ Batch {batch_num}/{len(batches)} failed: {response.status_code} - {response.text[:200]}")
                total_failed += len(formatted_leads)

        except Exception as e:
            print(f"   ❌ Batch {batch_num}/{len(batches)} failed: {str(e)}")
            total_failed += len(formatted_leads)

        # Rate limiting
        if batch_num < len(batches):
            time.sleep(1)

    return {
        "status": "success" if total_failed == 0 else "partial",
        "campaign_id": campaign_id,
        "total_leads_in_file": len(leads),
        "leads_with_personalization": len(personalized_leads),
        "uploaded": total_uploaded,
        "failed": total_failed,
        "message": f"Successfully uploaded {total_uploaded} leads with personalization"
    }


def main():
    parser = argparse.ArgumentParser(description='Add personalized leads to Instantly campaign')
    parser.add_argument('--input', required=True, help='Input JSON file with personalized leads')
    parser.add_argument('--campaign-id', required=True, help='Instantly campaign ID')

    args = parser.parse_args()

    # Add personalized leads
    result = add_personalized_leads_to_campaign(args.input, args.campaign_id)

    # Print results
    print("\n" + "="*60)
    if result['status'] in ['success', 'partial']:
        print(f"✅ {result['message']}")
        print(f"   Campaign ID: {result['campaign_id']}")
        print(f"   Total leads in file: {result['total_leads_in_file']}")
        print(f"   Leads with personalization: {result['leads_with_personalization']}")
        print(f"   Uploaded: {result['uploaded']}")
        print(f"   Failed: {result['failed']}")
    else:
        print(f"❌ {result['message']}")
        sys.exit(1)

    print("="*60)

    # Output JSON result
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

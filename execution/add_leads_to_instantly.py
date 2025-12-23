"""
Add leads to Instantly.ai campaigns via API.

Usage:
    python add_leads_to_instantly.py --leads full_leads.json --campaigns campaign_ids.json --output upload_report.json
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


def is_valid_email(email):
    """Basic email validation."""
    if not email or '@' not in email:
        return False
    return True


def add_leads_to_campaign(leads, campaign_id, campaign_name, api_key, batch_size=100):
    """
    Add leads to a single Instantly campaign using the correct V2 endpoint.

    Args:
        leads (list): List of lead dictionaries
        campaign_id (str): Instantly campaign ID
        campaign_name (str): Campaign name for logging
        api_key (str): Instantly API key
        batch_size (int): Number of leads per batch (max 1000)

    Returns:
        dict: Upload result
    """

    # Correct V2 API endpoint: POST /api/v2/leads/add
    api_url = "https://api.instantly.ai/api/v2/leads/add"

    # API V2 uses Bearer token in headers
    # Instantly requires BOTH Authorization and x-api-key headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }

    print(f"\n📤 Adding leads to campaign: {campaign_name}")
    print(f"   Campaign ID: {campaign_id}")
    print(f"   Total leads: {len(leads)}")

    # Filter leads with valid emails
    valid_leads = []
    for lead in leads:
        email = lead.get("email") or lead.get("contact_email")
        if is_valid_email(email):
            valid_leads.append(lead)

    if len(valid_leads) < len(leads):
        print(f"   ⚠️  Filtered out {len(leads) - len(valid_leads)} leads without valid emails")

    if not valid_leads:
        return {
            "status": "error",
            "message": "No leads with valid email addresses",
            "campaign_id": campaign_id,
            "campaign_name": campaign_name
        }

    # Process in batches
    total_uploaded = 0
    total_failed = 0
    batches = [valid_leads[i:i + batch_size] for i in range(0, len(valid_leads), batch_size)]

    print(f"   Processing {len(batches)} batch(es)...")

    for batch_num, batch in enumerate(batches, 1):
        # Prepare leads array for Instantly API
        formatted_leads = []
        for lead in batch:
            # Extract fields with fallbacks
            email = lead.get("email") or lead.get("contact_email")
            first_name = lead.get("first_name") or lead.get("firstName") or ""
            last_name = lead.get("last_name") or lead.get("lastName") or ""
            # Use normalized company name if available
            company_name = lead.get("company_name_normalized") or lead.get("company_name") or lead.get("companyName") or ""
            website = lead.get("company_website") or lead.get("website") or ""

            # Build lead object for Instantly V2 API
            # Use snake_case for field names (API accepts both)
            # Email copy uses camelCase variables like {{firstName}}
            instantly_lead = {
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "company_name": company_name,
                "website": website,
                "personalization": company_name
            }

            # Remove empty fields to avoid API issues
            instantly_lead = {k: v for k, v in instantly_lead.items() if v}

            formatted_leads.append(instantly_lead)

        # Make API request with correct format
        request_data = {
            "campaign_id": campaign_id,
            "leads": formatted_leads  # Array of lead objects
        }

        try:
            response = requests.post(api_url, json=request_data, headers=headers, timeout=60)

            if response.status_code == 200:
                result = response.json()
                uploaded = result.get("leads_uploaded", len(formatted_leads))
                total_uploaded += uploaded
                print(f"   ✅ Batch {batch_num}/{len(batches)}: {uploaded} leads uploaded")
            else:
                error_msg = f"API returned status {response.status_code}: {response.text[:200]}"
                print(f"   ❌ Batch {batch_num}/{len(batches)} failed: {error_msg}")
                total_failed += len(formatted_leads)

        except requests.exceptions.RequestException as e:
            error_msg = f"Request error: {str(e)}"
            print(f"   ❌ Batch {batch_num}/{len(batches)} failed: {error_msg}")
            total_failed += len(formatted_leads)

        # Rate limiting: wait 1 second between batches
        if batch_num < len(batches):
            time.sleep(1)

    print(f"   📊 Upload complete: {total_uploaded} successful, {total_failed} failed")

    return {
        "status": "success" if total_failed == 0 else "partial",
        "campaign_id": campaign_id,
        "campaign_name": campaign_name,
        "total_leads": len(leads),
        "valid_leads": len(valid_leads),
        "uploaded": total_uploaded,
        "failed": total_failed
    }


def add_leads_to_campaigns(leads_file, campaigns_file, output_file="upload_report.json"):
    """
    Add leads to multiple Instantly campaigns.

    Args:
        leads_file (str): Path to leads JSON file
        campaigns_file (str): Path to campaign IDs JSON file
        output_file (str): Output file for upload report

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

    # Use API key as-is (no decoding for V2)
    # V2 API keys should be used directly without base64 decoding

    # Load leads
    try:
        with open(leads_file, 'r', encoding='utf-8') as f:
            leads = json.load(f)
    except FileNotFoundError:
        return {
            "status": "error",
            "message": f"Leads file not found: {leads_file}"
        }
    except json.JSONDecodeError:
        return {
            "status": "error",
            "message": f"Invalid JSON in leads file: {leads_file}"
        }

    # Load campaign IDs
    try:
        with open(campaigns_file, 'r', encoding='utf-8') as f:
            campaigns_data = json.load(f)
    except FileNotFoundError:
        return {
            "status": "error",
            "message": f"Campaigns file not found: {campaigns_file}"
        }
    except json.JSONDecodeError:
        return {
            "status": "error",
            "message": f"Invalid JSON in campaigns file: {campaigns_file}"
        }

    campaigns = campaigns_data.get("campaigns", [])
    successful_campaigns = [c for c in campaigns if c.get("status") == "success"]

    if not successful_campaigns:
        return {
            "status": "error",
            "message": "No successful campaigns found in campaigns file"
        }

    print(f"🚀 Adding {len(leads)} leads to {len(successful_campaigns)} campaign(s)...")

    results = []
    total_uploaded = 0
    total_failed = 0

    for campaign in successful_campaigns:
        campaign_id = campaign.get("campaign_id")
        campaign_name = campaign.get("campaign_name", "Unknown")

        result = add_leads_to_campaign(
            leads=leads,
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            api_key=api_key
        )

        results.append(result)
        total_uploaded += result.get("uploaded", 0)
        total_failed += result.get("failed", 0)

        # Wait between campaigns
        if len(successful_campaigns) > 1:
            time.sleep(3)

    print(f"\n" + "="*50)
    print(f"📊 Upload Summary:")
    print(f"   Campaigns: {len(successful_campaigns)}")
    print(f"   Total leads uploaded: {total_uploaded}")
    print(f"   Total failed: {total_failed}")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".tmp", exist_ok=True)

    # Save results
    output_data = {
        "results": results,
        "summary": {
            "campaigns": len(successful_campaigns),
            "total_leads": len(leads),
            "total_uploaded": total_uploaded,
            "total_failed": total_failed
        }
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"💾 Saved upload report to: {output_file}")

    return {
        "status": "success" if total_failed == 0 else "partial",
        "campaigns": len(successful_campaigns),
        "total_uploaded": total_uploaded,
        "total_failed": total_failed,
        "file": output_file
    }


def main():
    parser = argparse.ArgumentParser(description="Add leads to Instantly campaigns")
    parser.add_argument("--leads", required=True, help="Path to leads JSON file")
    parser.add_argument("--campaigns", required=True, help="Path to campaign IDs JSON file")
    parser.add_argument("--output", default=".tmp/upload_report.json", help="Output file path")

    args = parser.parse_args()

    result = add_leads_to_campaigns(
        leads_file=args.leads,
        campaigns_file=args.campaigns,
        output_file=args.output
    )

    # Print result
    print("\n" + "="*50)
    if result["status"] == "success":
        print(f"✅ ALL LEADS UPLOADED SUCCESSFULLY!")
        print(f"   Campaigns: {result['campaigns']}")
        print(f"   Total uploaded: {result['total_uploaded']}")
    elif result["status"] == "partial":
        print(f"⚠️  PARTIAL SUCCESS")
        print(f"   Uploaded: {result['total_uploaded']}")
        print(f"   Failed: {result['total_failed']}")
    else:
        print(f"❌ FAILED: {result.get('message', 'Unknown error')}")

    print("\n" + json.dumps(result, indent=2))

    # Exit with appropriate code
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()

"""
Create Instantly.ai campaigns via API.

Usage:
    python create_instantly_campaigns.py --campaign-copy campaign_copy_product.json --output campaign_ids.json
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


def create_instantly_campaign(campaign_copy, api_key):
    """
    Create a single Instantly campaign via API.

    Args:
        campaign_copy (dict): Campaign copy with name, subject lines, and emails
        api_key (str): Instantly API key (may be base64 encoded)

    Returns:
        dict: Campaign creation result with ID and status
    """

    # Use API key as-is (no decoding for V2)
    # V2 API keys should be used directly without base64 decoding

    # API endpoint (V2 uses different format)
    api_url = "https://api.instantly.ai/api/v2/campaigns"

    # Prepare campaign data
    # Build email sequence - V2 API uses nested steps structure
    sequences = []
    steps = []
    for email in campaign_copy["emails"]:
        steps.append({
            "type": "email",
            "delay": 2 if email["step"] > 1 else 1,  # Days to wait
            "variants": [{
                "subject": email["subject"],
                "body": email["body"]
            }]
        })

    sequences.append({"steps": steps})

    # Prepare campaign schedule (required for V2 API)
    campaign_schedule = {
        "schedules": [
            {
                "name": "Business Hours",
                "timing": {
                    "from": "09:00",
                    "to": "17:00"
                },
                "days": {
                    "1": True,  # Monday
                    "2": True,  # Tuesday
                    "3": True,  # Wednesday
                    "4": True,  # Thursday
                    "5": True   # Friday
                },
                "timezone": "Atlantic/Canary"  # Use valid timezone from Instantly
            }
        ],
        "start_date": "2025-12-08"
    }

    campaign_data = {
        "name": campaign_copy["campaign_name"],
        "campaign_schedule": campaign_schedule,
        "sequences": sequences
    }

    # API V2 uses Bearer token in headers, not in body
    # Instantly requires BOTH Authorization and x-api-key headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }

    print(f"\n📤 Creating campaign: {campaign_copy['campaign_name']}")
    print(f"   Emails in sequence: {len(sequences)}")

    try:
        response = requests.post(api_url, json=campaign_data, headers=headers, timeout=30)

        # Check response
        if response.status_code == 200:
            result = response.json()
            campaign_id = result.get("id") or result.get("campaign_id")

            print(f"✅ Campaign created successfully")
            print(f"   Campaign ID: {campaign_id}")

            return {
                "status": "success",
                "campaign_id": campaign_id,
                "campaign_name": campaign_copy["campaign_name"],
                "offer": campaign_copy.get("offer", "Unknown"),
                "emails_count": len(sequences)
            }
        else:
            error_msg = f"API returned status {response.status_code}: {response.text}"
            print(f"❌ {error_msg}")
            return {
                "status": "error",
                "message": error_msg,
                "campaign_name": campaign_copy["campaign_name"]
            }

    except requests.exceptions.RequestException as e:
        error_msg = f"Request error: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "status": "error",
            "message": error_msg,
            "campaign_name": campaign_copy["campaign_name"]
        }


def create_campaigns(campaign_copy_files, output_file="campaign_ids.json"):
    """
    Create multiple Instantly campaigns from campaign copy files.

    Args:
        campaign_copy_files (list): List of paths to campaign copy JSON files
        output_file (str): Output file for campaign IDs

    Returns:
        dict: Results with campaign IDs
    """

    # Get API key
    api_key = os.getenv("INSTANTLY_API_KEY")
    if not api_key:
        return {
            "status": "error",
            "message": "INSTANTLY_API_KEY not found in .env file"
        }

    print(f"🚀 Creating {len(campaign_copy_files)} Instantly campaigns...")

    results = []
    successful = 0
    failed = 0

    for copy_file in campaign_copy_files:
        # Load campaign copy
        try:
            with open(copy_file, 'r', encoding='utf-8') as f:
                campaign_copy = json.load(f)
        except FileNotFoundError:
            print(f"❌ File not found: {copy_file}")
            failed += 1
            continue
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON in file: {copy_file}")
            failed += 1
            continue

        # Create campaign
        result = create_instantly_campaign(campaign_copy, api_key)
        results.append(result)

        if result["status"] == "success":
            successful += 1
        else:
            failed += 1

        # Rate limiting: wait 1 second between API calls
        if len(campaign_copy_files) > 1:
            time.sleep(1)

    print(f"\n" + "="*50)
    print(f"📊 Campaign Creation Summary:")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".tmp", exist_ok=True)

    # Save results
    output_data = {
        "campaigns": results,
        "summary": {
            "total": len(campaign_copy_files),
            "successful": successful,
            "failed": failed
        }
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"💾 Saved campaign IDs to: {output_file}")

    return {
        "status": "success" if failed == 0 else "partial",
        "total": len(campaign_copy_files),
        "successful": successful,
        "failed": failed,
        "file": output_file
    }


def main():
    parser = argparse.ArgumentParser(description="Create Instantly campaigns from campaign copy files")
    parser.add_argument("--campaign-copy", nargs='+', required=True, help="Path(s) to campaign copy JSON file(s)")
    parser.add_argument("--output", default=".tmp/campaign_ids.json", help="Output file path")

    args = parser.parse_args()

    result = create_campaigns(
        campaign_copy_files=args.campaign_copy,
        output_file=args.output
    )

    # Print result
    print("\n" + "="*50)
    if result["status"] == "success":
        print(f"✅ ALL CAMPAIGNS CREATED SUCCESSFULLY!")
        print(f"   Total: {result['successful']}/{result['total']}")
    elif result["status"] == "partial":
        print(f"⚠️  PARTIAL SUCCESS")
        print(f"   Successful: {result['successful']}/{result['total']}")
        print(f"   Failed: {result['failed']}/{result['total']}")
    else:
        print(f"❌ FAILED: {result.get('message', 'Unknown error')}")

    print("\n" + json.dumps(result, indent=2))

    # Exit with appropriate code
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()

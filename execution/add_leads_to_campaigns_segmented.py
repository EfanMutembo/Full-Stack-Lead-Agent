"""
Add leads to Instantly.ai campaigns with segment matching.

Each campaign receives ONLY the leads from its matching segment based on campaign name.
Campaign name should include segment name (e.g., "Product A - Executive Leadership - HVAC").

Usage:
    python add_leads_to_campaigns_segmented.py --campaigns .tmp/campaign_ids.json --segments .tmp/segment_mapping.json --leads-dir .tmp --output .tmp/upload_report.json
"""

import os
import sys
import json
import argparse
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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


def upload_single_batch(batch_num, batch, campaign_id, api_key, total_batches):
    """
    Upload a single batch of leads to Instantly (for parallel processing).

    Args:
        batch_num (int): Batch number for logging
        batch (list): List of lead dictionaries
        campaign_id (str): Instantly campaign ID
        api_key (str): Instantly API key
        total_batches (int): Total number of batches for logging

    Returns:
        dict: Upload result with uploaded/failed counts
    """
    # V2 API endpoint
    api_url = "https://api.instantly.ai/api/v2/leads/add"

    # Instantly requires BOTH Authorization and x-api-key headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }

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

        # Build lead object for Instantly V2 API (snake_case field names)
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

    # Make API request
    request_data = {
        "campaign_id": campaign_id,
        "leads": formatted_leads
    }

    try:
        response = requests.post(api_url, json=request_data, headers=headers, timeout=60)

        if response.status_code == 200:
            result = response.json()
            uploaded = result.get("leads_uploaded", len(formatted_leads))
            print(f"   ✅ Batch {batch_num}/{total_batches}: {uploaded} leads uploaded")
            return {"uploaded": uploaded, "failed": 0}
        else:
            error_msg = f"API returned status {response.status_code}: {response.text[:200]}"
            print(f"   ❌ Batch {batch_num}/{total_batches} failed: {error_msg}")
            return {"uploaded": 0, "failed": len(formatted_leads)}

    except requests.exceptions.RequestException as e:
        error_msg = f"Request error: {str(e)}"
        print(f"   ❌ Batch {batch_num}/{total_batches} failed: {error_msg}")
        return {"uploaded": 0, "failed": len(formatted_leads)}


def add_leads_to_campaign(leads, campaign_id, campaign_name, api_key, batch_size=100):
    """
    Add leads to a single Instantly campaign using the V2 API with parallel batch uploads.

    Args:
        leads (list): List of lead dictionaries
        campaign_id (str): Instantly campaign ID
        campaign_name (str): Campaign name for logging
        api_key (str): Instantly API key
        batch_size (int): Number of leads per batch (max 100)

    Returns:
        dict: Upload result
    """

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
    batches = [valid_leads[i:i + batch_size] for i in range(0, len(valid_leads), batch_size)]

    print(f"   Processing {len(batches)} batch(es) in parallel...")

    total_uploaded = 0
    total_failed = 0

    # Upload batches in parallel using ThreadPoolExecutor
    # Use up to 5 concurrent uploads to avoid overwhelming the API
    max_workers = min(5, len(batches))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all batch upload tasks
        future_to_batch = {
            executor.submit(upload_single_batch, batch_num, batch, campaign_id, api_key, len(batches)): batch_num
            for batch_num, batch in enumerate(batches, 1)
        }

        # Collect results as they complete
        for future in as_completed(future_to_batch):
            result = future.result()
            total_uploaded += result["uploaded"]
            total_failed += result["failed"]

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


def extract_segment_from_campaign_name(campaign_name, segment_mapping):
    """
    Extract segment_id from campaign name by matching segment name.

    Campaign name format: "Product A - Executive Leadership - Industry"
    Looks for segment name in campaign name.

    Args:
        campaign_name (str): Campaign name
        segment_mapping (dict): Segment mapping data with segments array

    Returns:
        str: segment_id or None if no match
    """
    segments = segment_mapping.get('segments', [])

    for segment in segments:
        segment_id = segment['segment_id']
        segment_name = segment['segment_name']

        # Check if segment name appears in campaign name
        if segment_name in campaign_name:
            return segment_id

    return None


def add_leads_to_campaigns_segmented(campaigns_file, segments_file, leads_dir, output_file):
    """
    Upload leads to campaigns with segment matching.

    Each campaign receives only leads from its matching segment.

    Args:
        campaigns_file (str): Path to campaign IDs JSON file
        segments_file (str): Path to segment mapping JSON file
        leads_dir (str): Directory containing segment lead files
        output_file (str): Path to upload report output file

    Returns:
        dict: Upload results with statistics
    """

    # Get API key
    api_key = os.getenv("INSTANTLY_API_KEY")
    if not api_key:
        return {
            "status": "error",
            "message": "INSTANTLY_API_KEY not found in .env file"
        }

    # Load campaigns
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

    campaigns = campaigns_data.get('campaigns', [])
    successful_campaigns = [c for c in campaigns if c.get('status') == 'success']

    if not successful_campaigns:
        return {
            "status": "error",
            "message": "No successful campaigns found in campaigns file"
        }

    # Load segment mapping
    try:
        with open(segments_file, 'r', encoding='utf-8') as f:
            segment_mapping = json.load(f)
    except FileNotFoundError:
        return {
            "status": "error",
            "message": f"Segment mapping file not found: {segments_file}"
        }
    except json.JSONDecodeError:
        return {
            "status": "error",
            "message": f"Invalid JSON in segments file: {segments_file}"
        }

    print(f"🚀 Adding segment-specific leads to {len(successful_campaigns)} campaign(s)...")
    print(f"   Segments available: {len(segment_mapping.get('segments', []))}")

    results = []
    total_uploaded = 0
    total_failed = 0
    total_skipped = 0

    for campaign in successful_campaigns:
        campaign_name = campaign.get('campaign_name', 'Unknown')
        campaign_id = campaign.get('campaign_id')

        # Extract segment from campaign name
        segment_id = extract_segment_from_campaign_name(campaign_name, segment_mapping)

        if not segment_id:
            print(f"\n⚠️  Could not identify segment for campaign: '{campaign_name}'")
            print(f"   Skipping this campaign")
            results.append({
                "campaign_name": campaign_name,
                "campaign_id": campaign_id,
                "status": "skipped",
                "reason": "Could not identify segment from campaign name"
            })
            total_skipped += 1
            continue

        # Load segment leads
        segment_file = os.path.join(leads_dir, f"segment_{segment_id}_leads.json")

        if not os.path.exists(segment_file):
            print(f"\n❌ Segment file not found: {segment_file}")
            results.append({
                "campaign_name": campaign_name,
                "campaign_id": campaign_id,
                "status": "error",
                "reason": f"Segment file not found: {segment_file}"
            })
            total_failed += 1
            continue

        try:
            with open(segment_file, 'r', encoding='utf-8') as f:
                segment_leads = json.load(f)
        except json.JSONDecodeError:
            print(f"\n❌ Invalid JSON in segment file: {segment_file}")
            results.append({
                "campaign_name": campaign_name,
                "campaign_id": campaign_id,
                "status": "error",
                "reason": f"Invalid JSON in segment file"
            })
            total_failed += 1
            continue

        if not segment_leads:
            print(f"\n⚠️  No leads in segment file: {segment_file}")
            results.append({
                "campaign_name": campaign_name,
                "campaign_id": campaign_id,
                "status": "skipped",
                "reason": "No leads in segment"
            })
            total_skipped += 1
            continue

        # Upload leads to campaign
        result = add_leads_to_campaign(
            leads=segment_leads,
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            api_key=api_key
        )

        results.append(result)
        total_uploaded += result.get('uploaded', 0)
        total_failed += result.get('failed', 0)

        # Wait between campaigns
        if len(successful_campaigns) > 1:
            time.sleep(2)

    # Print summary
    print("\n" + "="*50)
    print(f"📊 Upload Summary:")
    print(f"   Campaigns processed: {len(successful_campaigns)}")
    print(f"   Total leads uploaded: {total_uploaded}")
    print(f"   Total failed: {total_failed}")
    print(f"   Campaigns skipped: {total_skipped}")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".tmp", exist_ok=True)

    # Save results
    output_data = {
        "status": "success" if total_failed == 0 and total_skipped == 0 else "partial",
        "results": results,
        "summary": {
            "campaigns_processed": len(successful_campaigns),
            "total_uploaded": total_uploaded,
            "total_failed": total_failed,
            "campaigns_skipped": total_skipped
        }
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"💾 Saved upload report to: {output_file}")

    return {
        "status": output_data["status"],
        "campaigns_processed": len(successful_campaigns),
        "total_uploaded": total_uploaded,
        "total_failed": total_failed,
        "campaigns_skipped": total_skipped,
        "file": output_file
    }


def main():
    parser = argparse.ArgumentParser(description="Add leads to Instantly campaigns with segment matching")
    parser.add_argument("--campaigns", required=True, help="Path to campaign IDs JSON file")
    parser.add_argument("--segments", required=True, help="Path to segment mapping JSON file")
    parser.add_argument("--leads-dir", default=".tmp", help="Directory containing segment lead files")
    parser.add_argument("--output", default=".tmp/upload_report.json", help="Output file path")

    args = parser.parse_args()

    result = add_leads_to_campaigns_segmented(
        campaigns_file=args.campaigns,
        segments_file=args.segments,
        leads_dir=args.leads_dir,
        output_file=args.output
    )

    # Print result
    print("\n" + "="*50)
    if result["status"] == "success":
        print(f"✅ ALL LEADS UPLOADED SUCCESSFULLY!")
        print(f"   Campaigns: {result['campaigns_processed']}")
        print(f"   Total uploaded: {result['total_uploaded']}")
    elif result["status"] == "partial":
        print(f"⚠️  PARTIAL SUCCESS")
        print(f"   Uploaded: {result['total_uploaded']}")
        print(f"   Failed: {result['total_failed']}")
        print(f"   Skipped: {result['campaigns_skipped']}")
    else:
        print(f"❌ FAILED: {result.get('message', 'Unknown error')}")

    print("\n" + json.dumps(result, indent=2))

    # Exit with appropriate code
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()

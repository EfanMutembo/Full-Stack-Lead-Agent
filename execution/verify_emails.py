"""
Verify email addresses using AnyMailFinder API.

This script reads leads from a JSON file, verifies their email addresses,
and outputs only leads with valid/verified emails.

Usage:
    python verify_emails.py --input .tmp/full_leads_normalized.json --output .tmp/full_leads_verified.json --report .tmp/verification_report.json

API Documentation:
    https://anymailfinder.com/email-finder-api/docs/verify-email
"""

import os
import sys
import json
import argparse
import requests
import time
import re
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()


def is_valid_email_format(email):
    """
    Pre-validate email format before API call.

    Args:
        email (str): Email address to validate

    Returns:
        bool: True if email format is valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False

    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    # Check format
    if not re.match(pattern, email):
        return False

    # Additional checks for obviously invalid patterns
    invalid_patterns = [
        r'@example\.com$',
        r'@test\.com$',
        r'noreply@',
        r'no-reply@',
        r'^test@',
        r'^admin@.*\.local$',
        r'@localhost$'
    ]

    for invalid in invalid_patterns:
        if re.search(invalid, email, re.IGNORECASE):
            return False

    return True


def verify_email(email, api_key, max_retries=3, session=None):
    """
    Verify a single email address using AnyMailFinder API.

    Args:
        email (str): Email address to verify
        api_key (str): AnyMailFinder API key
        max_retries (int): Maximum number of retry attempts
        session (requests.Session): Optional session for connection pooling

    Returns:
        dict: Verification result with status and details
    """
    if not email:
        return {
            "email": email,
            "status": "invalid",
            "reason": "No email provided"
        }

    # Use session if provided, otherwise create a new request
    http_client = session if session else requests

    url = "https://api.anymailfinder.com/v5.1/verify-email"
    headers = {
        "Content-Type": "application/json",
        "Authorization": api_key
    }
    payload = {"email": email}

    for attempt in range(max_retries):
        try:
            response = http_client.post(url, headers=headers, json=payload, timeout=180)

            if response.status_code == 200:
                result = response.json()
                email_status = result.get("email_status", "unknown")

                return {
                    "email": email,
                    "status": email_status,
                    "reason": f"Verification result: {email_status}",
                    "raw_response": result
                }
            elif response.status_code == 401:
                return {
                    "email": email,
                    "status": "error",
                    "reason": "Invalid API key or authentication failed"
                }
            elif response.status_code == 429:
                # Rate limited - wait and retry
                wait_time = (2 ** attempt) * 2  # Exponential backoff: 2s, 4s, 8s
                print(f"   ⏳ Rate limited, waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
            else:
                return {
                    "email": email,
                    "status": "error",
                    "reason": f"API returned status {response.status_code}: {response.text[:100]}"
                }

        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                print(f"   ⏳ Timeout for {email}, retrying...")
                continue
            return {
                "email": email,
                "status": "error",
                "reason": "Request timed out after 180 seconds"
            }
        except requests.exceptions.RequestException as e:
            return {
                "email": email,
                "status": "error",
                "reason": f"Request error: {str(e)[:100]}"
            }

    return {
        "email": email,
        "status": "error",
        "reason": f"Failed after {max_retries} attempts"
    }


def verify_leads(input_file, output_file, report_file, keep_risky=False, batch_size=5):
    """
    Verify all email addresses in a leads file.

    Args:
        input_file (str): Path to input JSON file with leads
        output_file (str): Path to output JSON file with verified leads
        report_file (str): Path to verification report JSON file
        keep_risky (bool): Whether to keep leads with "risky" email status
        batch_size (int): Number of concurrent verification requests

    Returns:
        dict: Verification summary with statistics
    """
    # Check API key
    api_key = os.getenv("ANYMAILFINDER_API_KEY")
    if not api_key:
        return {
            "status": "error",
            "message": "ANYMAILFINDER_API_KEY not found in .env file"
        }

    # Load leads
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

    print(f"🔍 Verifying emails for {len(leads)} leads...")
    print(f"   Batch size: {batch_size} concurrent requests")
    print(f"   Keep risky emails: {'✅ Yes' if keep_risky else '❌ No'}")
    print()

    # Verify emails in parallel
    verified_leads = []
    verification_details = []
    stats = {
        "total": len(leads),
        "valid": 0,
        "risky": 0,
        "invalid": 0,
        "error": 0,
        "no_email": 0
    }

    # Create session for connection pooling
    session = requests.Session()

    # Use ThreadPoolExecutor for parallel verification
    with ThreadPoolExecutor(max_workers=batch_size) as executor:
        # Submit all verification tasks
        future_to_lead = {}
        for lead in leads:
            email = lead.get("email") or lead.get("personal_email") or ""
            if not email:
                stats["no_email"] += 1
                verification_details.append({
                    "email": None,
                    "status": "no_email",
                    "reason": "No email in lead data",
                    "lead": lead
                })
                continue

            # Pre-filter: check email format before API call
            if not is_valid_email_format(email):
                stats["invalid"] += 1
                verification_details.append({
                    "email": email,
                    "status": "invalid",
                    "reason": "Invalid email format (pre-filtered)",
                    "kept": False,
                    "lead": lead
                })
                print(f"   ❌ [pre-filter] {email}: Invalid format (skipped API call)")
                continue

            future = executor.submit(verify_email, email, api_key, session=session)
            future_to_lead[future] = lead

        # Process results as they complete
        for i, future in enumerate(as_completed(future_to_lead), 1):
            lead = future_to_lead[future]
            result = future.result()

            status = result["status"]
            email = result["email"]

            # Update stats
            if status in stats:
                stats[status] += 1
            else:
                stats["error"] += 1

            # Determine if lead should be kept
            keep_lead = False
            if status == "valid":
                keep_lead = True
                icon = "✅"
            elif status == "risky" and keep_risky:
                keep_lead = True
                icon = "⚠️"
            elif status == "risky":
                icon = "⚠️"
            elif status == "invalid":
                icon = "❌"
            else:
                icon = "⚠️"

            # Add to verified leads if keeping
            if keep_lead:
                verified_leads.append(lead)

            # Store verification details
            verification_details.append({
                **result,
                "kept": keep_lead,
                "lead": lead
            })

            print(f"   {icon} [{i}/{len(future_to_lead)}] {email}: {result['reason']}")

    # Close session
    session.close()

    # Calculate percentages
    total_verified = stats["valid"] + stats["risky"] + stats["invalid"]
    valid_percentage = (stats["valid"] / total_verified * 100) if total_verified > 0 else 0
    kept_count = len(verified_leads)
    kept_percentage = (kept_count / len(leads) * 100) if len(leads) > 0 else 0

    # Create report
    report = {
        "status": "success",
        "statistics": {
            **stats,
            "kept": kept_count,
            "removed": len(leads) - kept_count,
            "valid_percentage": round(valid_percentage, 1),
            "kept_percentage": round(kept_percentage, 1)
        },
        "settings": {
            "keep_risky": keep_risky,
            "batch_size": batch_size
        },
        "verification_details": verification_details
    }

    # Save verified leads
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".tmp", exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(verified_leads, f, indent=2, ensure_ascii=False)

    # Save report
    os.makedirs(os.path.dirname(report_file) if os.path.dirname(report_file) else ".tmp", exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "="*60)
    print(f"📊 Email Verification Summary:")
    print(f"   Total leads: {stats['total']}")
    print(f"   ✅ Valid: {stats['valid']} ({valid_percentage:.1f}%)")
    print(f"   ⚠️  Risky: {stats['risky']}")
    print(f"   ❌ Invalid: {stats['invalid']}")
    print(f"   ⚠️  Errors: {stats['error']}")
    print(f"   ⚠️  No email: {stats['no_email']}")
    print(f"\n   Leads kept: {kept_count} ({kept_percentage:.1f}%)")
    print(f"   Leads removed: {len(leads) - kept_count}")
    print(f"\n   Verified leads saved to: {output_file}")
    print(f"   Report saved to: {report_file}")

    return report


def main():
    parser = argparse.ArgumentParser(description="Verify email addresses using AnyMailFinder API")
    parser.add_argument("--input", required=True, help="Input JSON file with leads")
    parser.add_argument("--output", required=True, help="Output JSON file for verified leads")
    parser.add_argument("--report", default=".tmp/verification_report.json", help="Verification report output file")
    parser.add_argument("--keep-risky", action="store_true", help="Keep leads with 'risky' email status (default: remove)")
    parser.add_argument("--batch-size", type=int, default=10, help="Number of concurrent verification requests (default: 10)")

    args = parser.parse_args()

    result = verify_leads(
        input_file=args.input,
        output_file=args.output,
        report_file=args.report,
        keep_risky=args.keep_risky,
        batch_size=args.batch_size
    )

    # Print result as JSON
    print("\n" + "="*60)
    print(json.dumps({k: v for k, v in result.items() if k != "verification_details"}, indent=2))

    # Exit with appropriate code
    sys.exit(0 if result.get("status") == "success" else 1)


if __name__ == "__main__":
    main()

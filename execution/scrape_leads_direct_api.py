"""
Scrape leads using direct Apify API endpoint for code_crafter/leads-finder.

Usage:
    python scrape_leads_direct_api.py --query "Solar PV installers UK" --limit 25 --output test_leads.json
"""

import os
import sys
import json
import argparse
import requests
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()


def scrape_leads_direct(query, limit=25, location=None, employee_count=None, revenue_range=None,
                         industries=None, excluded_industries=None, excluded_job_titles=None, output_file="leads.json"):
    """
    Scrape leads using direct Apify API endpoint.

    Args:
        query (str): Search query
        limit (int): Number of leads to scrape
        location (str): Geographic filter
        employee_count (str or list): Employee count filter (e.g., "51-100" or ["1-10", "11-20"])
        revenue_range (str): Revenue range filter (e.g., "$25M-$50M")
        output_file (str): Output JSON file path

    Returns:
        dict: Results with status and file path
    """

    # Get API token
    api_token = os.getenv("APIFY_API_TOKEN")
    if not api_token:
        return {
            "status": "error",
            "message": "APIFY_API_TOKEN not found in .env file"
        }

    # API endpoint
    api_url = f"https://api.apify.com/v2/acts/code_crafter~leads-finder/run-sync-get-dataset-items?token={api_token}"

    # Handle employee_count - convert to list if it's a string or already a list
    employee_sizes = []
    if employee_count:
        if isinstance(employee_count, list):
            employee_sizes = employee_count
        else:
            employee_sizes = [employee_count]

    # Configure actor input with CORRECT field names from Apify API
    actor_input = {
        "fetch_count": limit,  # CRITICAL: This is the correct field for limiting leads
        "company_keywords": query.split() if query else [],  # Split query into keywords
        "contact_location": [location.lower()] if location else [],  # Must be lowercase
        "size": employee_sizes,  # Can be multiple size ranges
        "company_industry": industries if industries else [],
        "company_not_industry": excluded_industries if excluded_industries else [],
        "contact_not_job_title": excluded_job_titles if excluded_job_titles else [],
        "company_domain": [],
        "contact_city": [],
        "contact_job_title": [],
        "contact_not_city": [],
        "contact_not_location": [],
        "email_status": [],
        "functional_level": [],
        "seniority_level": [],
        "funding": []
    }

    # Add revenue filters only if provided
    if revenue_range:
        parts = revenue_range.replace('$', '').split('-')
        if len(parts) >= 1:
            actor_input["min_revenue"] = parts[0].strip()  # e.g., "25M"
        if len(parts) >= 2:
            actor_input["max_revenue"] = parts[1].strip()  # e.g., "50M"

    print(f"🔍 Starting direct API lead scrape...")
    print(f"   Company Keywords: {query}")
    print(f"   Location: {location or 'Not specified'}")
    print(f"   Company Size: {employee_count or 'Not specified'}")
    print(f"   Revenue Range: {revenue_range or 'Not specified'}")
    print(f"   Fetch Count (EXACT LIMIT): {limit}")
    print(f"   API: code_crafter/leads-finder")

    try:
        # Make POST request to run actor synchronously
        print(f"\n⏳ Sending request to Apify API...")

        response = requests.post(
            api_url,
            json=actor_input,
            headers={
                "Content-Type": "application/json"
            },
            timeout=300  # 5 minute timeout
        )

        # Check for HTTP errors (200 and 201 are both success)
        if response.status_code not in [200, 201]:
            error_msg = f"API returned status {response.status_code}: {response.text}"
            print(f"❌ {error_msg}")
            return {
                "status": "error",
                "message": error_msg
            }

        # Parse response
        results = response.json()

        # Check if results is a list
        if not isinstance(results, list):
            print(f"⚠️  Unexpected response format: {type(results)}")
            results = [results] if results else []

        # CRITICAL: Limit to exactly the requested amount
        if len(results) > limit:
            print(f"⚠️  API returned {len(results)} leads, limiting to exactly {limit}")
            results = results[:limit]

        print(f"✅ Retrieved exactly {len(results)} leads")

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".tmp", exist_ok=True)

        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"💾 Saved results to: {output_file}")

        return {
            "status": "success",
            "count": len(results),
            "file": output_file
        }

    except requests.exceptions.Timeout:
        error_msg = "Request timed out after 5 minutes"
        print(f"❌ {error_msg}")
        return {
            "status": "error",
            "message": error_msg
        }

    except requests.exceptions.RequestException as e:
        error_msg = f"Request error: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "status": "error",
            "message": error_msg
        }

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "status": "error",
            "message": error_msg
        }


def main():
    parser = argparse.ArgumentParser(description="Scrape leads using direct Apify API")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--limit", type=int, default=25, help="Number of leads to scrape")
    parser.add_argument("--location", help="Geographic filter")
    parser.add_argument("--employees", help="Employee count filter (e.g., '51-100')")
    parser.add_argument("--revenue", help="Revenue range filter (e.g., '$25M-$50M')")
    parser.add_argument("--industries", help="Comma-separated list of industries")
    parser.add_argument("--exclude-industries", help="Comma-separated list of industries to exclude")
    parser.add_argument("--exclude-titles", help="Comma-separated list of job titles to exclude")
    parser.add_argument("--output", default=".tmp/leads.json", help="Output file path")

    args = parser.parse_args()

    result = scrape_leads_direct(
        query=args.query,
        limit=args.limit,
        location=args.location,
        employee_count=args.employees.split(',') if args.employees else None,
        revenue_range=args.revenue,
        industries=args.industries.split(',') if args.industries else None,
        excluded_industries=args.exclude_industries.split(',') if args.exclude_industries else None,
        excluded_job_titles=args.exclude_titles.split(',') if args.exclude_titles else None,
        output_file=args.output
    )

    # Print result as JSON for easy parsing
    print("\n" + "="*50)
    print(json.dumps(result, indent=2))

    # Exit with appropriate code
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()

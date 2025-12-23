"""
Validate lead quality using AI to check if leads match target ICP (Ideal Customer Profile).

This validates against ALL ICP criteria:
- Industry/niche
- Location/geography
- Company size (employee count)
- Revenue range
- Any other firmographic data

Optionally fetches company websites to enrich validation data.

Usage:
    python validate_lead_quality.py --input test_leads.json --icp-industry "HVAC companies" --icp-location "UK" --icp-employees "10-50" --threshold 80 --output validation_report.json

    # With website enrichment:
    python validate_lead_quality.py --input test_leads.json --icp-industry "HVAC companies" --enrich-web --threshold 80 --output validation_report.json
"""

import os
import sys
import json
import argparse
import requests
from dotenv import load_dotenv
from anthropic import Anthropic

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()


def fetch_website_summary(url, timeout=10):
    """
    Fetch and summarize a company website for validation enrichment.

    Args:
        url (str): Company website URL
        timeout (int): Request timeout in seconds

    Returns:
        str: Summary of website content or error message
    """
    try:
        if not url or not url.startswith('http'):
            return "No valid website URL provided"

        # Fetch homepage
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)

        if response.status_code == 200:
            # Get first 3000 characters of text content
            text = response.text[:3000]
            return f"Website accessible. Preview: {text[:500]}"
        else:
            return f"Website returned status {response.status_code}"

    except requests.exceptions.Timeout:
        return "Website request timed out"
    except requests.exceptions.RequestException as e:
        return f"Could not fetch website: {str(e)[:100]}"
    except Exception as e:
        return f"Error: {str(e)[:100]}"


def validate_leads(input_file, icp_criteria, threshold=85, output_file="validation_report.json", enrich_web=False, offer_name=None, match_threshold=75):
    """
    Validate that scraped leads match the target ICP using Claude AI percentage matching.

    Args:
        input_file (str): Path to JSON file with leads
        icp_criteria (dict): ICP criteria including industry, location, employees, revenue, etc.
        threshold (int): Minimum percentage of valid leads to pass (default: 85)
        output_file (str): Output file for validation report
        enrich_web (bool): Whether to fetch company websites for enrichment
        offer_name (str, optional): Name of offer/product being sold (helps AI understand fit)
        match_threshold (int): Minimum ICP match percentage to keep a lead (default: 75)

    Returns:
        dict: Validation results with pass/fail status
    """

    # Check if Anthropic API key exists
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return {
            "status": "error",
            "message": "ANTHROPIC_API_KEY not found in .env file"
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

    # Build ICP summary for display
    icp_parts = []
    if icp_criteria.get('industry'):
        icp_parts.append(f"Industry: {icp_criteria['industry']}")
    if icp_criteria.get('location'):
        icp_parts.append(f"Location: {icp_criteria['location']}")
    if icp_criteria.get('employees'):
        icp_parts.append(f"Employees: {icp_criteria['employees']}")
    if icp_criteria.get('revenue'):
        icp_parts.append(f"Revenue: {icp_criteria['revenue']}")
    if icp_criteria.get('job_title'):
        icp_parts.append(f"Job Titles: {icp_criteria['job_title']}")

    icp_summary = " | ".join(icp_parts) if icp_parts else "No ICP criteria specified"

    print(f"🔍 Validating {len(leads)} leads against ICP:")
    print(f"   {icp_summary}")
    if icp_criteria.get('description'):
        print(f"   ICP Description: {icp_criteria['description'][:100]}{'...' if len(icp_criteria['description']) > 100 else ''}")
    if offer_name:
        print(f"   Offer: {offer_name}")
    print(f"   Match threshold: {match_threshold}% (leads below this are filtered)")
    print(f"   Pass threshold: {threshold}% (minimum valid leads to pass)")
    print(f"   Website enrichment: {'✅ Enabled' if enrich_web else '❌ Disabled'}")
    print()

    # Initialize Claude
    client = Anthropic(api_key=api_key)

    # Validate leads in batches for speed
    valid_count = 0
    validation_details = []
    batch_size = 20  # Validate 20 leads per API call (optimized for large batches)

    # Process leads in batches
    for batch_start in range(0, len(leads), batch_size):
        batch_end = min(batch_start + batch_size, len(leads))
        batch_leads = leads[batch_start:batch_end]

        print(f"   📦 Processing batch {batch_start//batch_size + 1}/{(len(leads) + batch_size - 1)//batch_size} ({len(batch_leads)} leads)...")

        # Build batch data for prompt
        batch_data = []
        for lead in batch_leads:
            company_name = lead.get("company_name") or lead.get("name") or lead.get("companyName") or "Unknown"
            company_desc = lead.get("company_description") or lead.get("description") or ""
            website = lead.get("company_website") or lead.get("website") or lead.get("url") or ""
            industry = lead.get("industry") or ""
            location = lead.get("company_country") or lead.get("country") or ""
            city = lead.get("company_city") or lead.get("city") or ""
            state = lead.get("company_state") or lead.get("state") or ""
            employees = lead.get("company_size") or lead.get("employees") or ""
            revenue = lead.get("company_annual_revenue_clean") or lead.get("revenue") or ""
            keywords = lead.get("keywords") or ""
            job_title = lead.get("job_title") or lead.get("title") or lead.get("position") or ""

            # Build location string
            location_parts = [city, state, location]
            full_location = ", ".join([p for p in location_parts if p])

            batch_data.append({
                "company_name": company_name,
                "description": company_desc[:500] if company_desc else "N/A",
                "industry": industry,
                "keywords": keywords[:400] if keywords else "N/A",
                "location": full_location,
                "employees": employees,
                "revenue": revenue,
                "website": website,
                "job_title": job_title if job_title else "N/A"
            })

        # Create batch validation prompt
        offer_context = f"\n**OFFER/PRODUCT WE'RE SELLING**: {offer_name}\n" if offer_name else ""

        # Build ICP description section
        icp_description_context = ""
        if icp_criteria.get('description'):
            icp_description_context = f"\n**DETAILED ICP DESCRIPTION**:\n{icp_criteria['description']}\n"

        # Build structured ICP criteria (exclude description and job_title as they're shown separately)
        structured_criteria = {k: v for k, v in icp_criteria.items() if k not in ['description', 'job_title'] and v}
        structured_icp = chr(10).join([f"- {k.title()}: {v}" for k, v in structured_criteria.items()]) if structured_criteria else ""

        prompt = f"""You are an expert at analyzing if companies match an Ideal Customer Profile (ICP).

TARGET ICP:
{structured_icp}
{icp_description_context}{offer_context}

TASK: Analyze each company below and provide ICP match percentages.

ANALYSIS CRITERIA:
1. **Industry/Niche Match** (30%): Does the company description, keywords, and industry show they're in our target niche?
2. **Firmographic Match** (30%): Do location, employee count, and revenue fit our ICP ranges?
3. **Job Title Match** (20%): {f"Does the contact's job title match our target roles: {icp_criteria['job_title']}?" if icp_criteria.get('job_title') else "Is this a decision-maker or relevant contact?"}
4. **ICP Description Fit** (10%): {f"Does the company match the detailed ICP description provided above?" if icp_criteria.get('description') else "Does the overall profile make sense?"}
5. **Solution Fit** (10%): Based on what they do, would our offer be relevant?

COMPANIES TO ANALYZE:
{json.dumps(batch_data, indent=2)}

RESPONSE FORMAT - Return ONLY a JSON array with this exact structure:
[
  {{"company_name": "Company Name", "percentage": 85, "reason": "Brief reason"}},
  {{"company_name": "Company Name 2", "percentage": 70, "reason": "Brief reason"}}
]

CRITICAL: Return ONLY the JSON array, no other text. One entry per company in the same order."""

        try:
            # Call Claude API for batch validation
            message = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=3000,  # Increased for larger batches (20 leads)
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text.strip()

            # Extract JSON from response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            # Parse batch results
            batch_results = json.loads(response_text)

            # Process each result
            for idx, result in enumerate(batch_results):
                if idx >= len(batch_leads):
                    break

                lead = batch_leads[idx]
                company_name = lead.get("company_name") or lead.get("name") or lead.get("companyName") or "Unknown"

                match_percentage = result.get("percentage", 0)
                reason = result.get("reason", "No reason provided")

                is_valid = match_percentage >= match_threshold
                if is_valid:
                    valid_count += 1

                # Extract firmographics for report
                industry = lead.get("industry") or ""
                location = lead.get("company_country") or lead.get("country") or ""
                city = lead.get("company_city") or lead.get("city") or ""
                state = lead.get("company_state") or lead.get("state") or ""
                employees = lead.get("company_size") or lead.get("employees") or ""
                revenue = lead.get("company_annual_revenue_clean") or lead.get("revenue") or ""
                location_parts = [city, state, location]
                full_location = ", ".join([p for p in location_parts if p])

                validation_details.append({
                    "company": company_name,
                    "valid": is_valid,
                    "match_percentage": match_percentage,
                    "reason": reason,
                    "firmographics": {
                        "industry": industry,
                        "location": full_location,
                        "employees": employees,
                        "revenue": revenue
                    },
                    "data": lead
                })

                status_icon = "✅" if is_valid else "❌"
                print(f"   {status_icon} {company_name} ({match_percentage}%): {reason[:60]}...")

        except Exception as e:
            print(f"   ⚠️  Batch validation error: {str(e)}")
            # Fall back to marking all as invalid in this batch
            for lead in batch_leads:
                company_name = lead.get("company_name") or lead.get("name") or lead.get("companyName") or "Unknown"
                validation_details.append({
                    "company": company_name,
                    "valid": False,
                    "match_percentage": 0,
                    "reason": f"Batch validation error: {str(e)[:100]}",
                    "firmographics": {},
                    "data": lead
                })

    # Calculate quality percentage
    quality_percentage = (valid_count / len(leads)) * 100
    passed = quality_percentage >= threshold

    result = {
        "status": "success",
        "passed": passed,
        "quality_percentage": round(quality_percentage, 1),
        "threshold": threshold,
        "valid_count": valid_count,
        "total_count": len(leads),
        "icp_criteria": icp_criteria,
        "validation_details": validation_details
    }

    # Save report
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".tmp", exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "="*50)
    print(f"📊 Validation Results:")
    print(f"   Valid leads: {valid_count}/{len(leads)} ({quality_percentage:.1f}%)")
    print(f"   Threshold: {threshold}%")
    print(f"   Status: {'✅ PASSED' if passed else '❌ FAILED'}")
    print(f"   Report saved to: {output_file}")

    if not passed:
        print(f"\n💡 Suggestions:")
        print(f"   - Review validation details in {output_file}")
        print(f"   - Try broader search terms or filters")
        print(f"   - Adjust ICP criteria if too restrictive")

    return result


def main():
    parser = argparse.ArgumentParser(description="Validate lead quality against full ICP using AI percentage matching")
    parser.add_argument("--input", required=True, help="Input JSON file with leads")

    # ICP criteria arguments
    parser.add_argument("--icp-industry", help="Target industry/niche (e.g., 'HVAC companies')")
    parser.add_argument("--icp-location", help="Target location/geography (e.g., 'UK', 'United States')")
    parser.add_argument("--icp-employees", help="Target employee range (e.g., '10-50', '51-200')")
    parser.add_argument("--icp-revenue", help="Target revenue range (e.g., '$1M-$10M')")
    parser.add_argument("--icp-description", help="Detailed ICP description (paragraph describing ideal customer firmographics, characteristics, etc.)")
    parser.add_argument("--icp-job-title", help="Target job titles/roles (e.g., 'CEO, Founder, Managing Director')")

    # Offer/product context
    parser.add_argument("--offer", help="Offer/product name being sold (helps AI assess fit)")

    # Legacy support for old --industry parameter
    parser.add_argument("--industry", help="(Legacy) Same as --icp-industry")

    # Thresholds
    parser.add_argument("--threshold", type=int, default=85, help="Minimum %% of valid leads to pass (default: 85)")
    parser.add_argument("--match-threshold", type=int, default=75, help="Minimum ICP match %% to keep a lead (default: 75)")

    parser.add_argument("--output", default=".tmp/validation_report.json", help="Output file path")
    parser.add_argument("--enrich-web", action="store_true", help="Fetch company websites for enrichment (slower but more accurate)")

    args = parser.parse_args()

    # Build ICP criteria dict
    icp_criteria = {}

    # Support legacy --industry parameter
    industry = args.icp_industry or args.industry
    if industry:
        icp_criteria['industry'] = industry
    if args.icp_location:
        icp_criteria['location'] = args.icp_location
    if args.icp_employees:
        icp_criteria['employees'] = args.icp_employees
    if args.icp_revenue:
        icp_criteria['revenue'] = args.icp_revenue
    if args.icp_description:
        icp_criteria['description'] = args.icp_description
    if args.icp_job_title:
        icp_criteria['job_title'] = args.icp_job_title

    if not icp_criteria:
        print("⚠️  Warning: No ICP criteria specified. Validation may not be meaningful.")
        print("   Use --icp-industry, --icp-location, --icp-employees, and/or --icp-revenue")

    result = validate_leads(
        input_file=args.input,
        icp_criteria=icp_criteria,
        threshold=args.threshold,
        output_file=args.output,
        enrich_web=args.enrich_web,
        offer_name=args.offer,
        match_threshold=args.match_threshold
    )

    # Print result as JSON
    print("\n" + "="*50)
    print(json.dumps({k: v for k, v in result.items() if k != "validation_details"}, indent=2))

    # Exit with appropriate code
    sys.exit(0 if result.get("status") == "success" and result.get("passed") else 1)


if __name__ == "__main__":
    main()

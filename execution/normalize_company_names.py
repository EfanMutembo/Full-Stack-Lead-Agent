"""
Normalize company names using AI to create friendly, readable versions.

Usage:
    python normalize_company_names.py --input leads.json --output leads_normalized.json
"""

import os
import sys
import json
import argparse
from anthropic import Anthropic
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()


def normalize_company_name_batch(company_names, api_key):
    """
    Normalize a batch of company names using Claude AI.

    Args:
        company_names (list): List of company names to normalize
        api_key (str): Anthropic API key

    Returns:
        dict: Mapping of original names to normalized names
    """

    client = Anthropic(api_key=api_key)

    # Create prompt
    prompt = f"""You are a company name normalization expert. Your task is to convert formal/legal company names into simple, friendly versions that are easy to read and use in emails.

Rules:
1. Remove legal suffixes: Ltd, Limited, LLC, Inc, Corp, GmbH, PLC, etc.
2. Remove generic words: Company, Group, Solutions, Services (unless they're core to the brand)
3. Keep abbreviations if they're part of the brand (ABC Company → ABC)
4. Capitalize properly (all caps → Title Case)
5. Remove extra spaces and punctuation
6. Keep the core brand name that people would recognize

Examples:
- "SOLAR INNOVATIONS LTD" → "Solar Innovations"
- "ABC Renewable Energy Solutions Ltd" → "ABC Renewable Energy"
- "Green Power Group PLC" → "Green Power"
- "SunTech Company Ltd" → "SunTech"

Now normalize these company names. Return ONLY a JSON object with "original_name": "normalized_name" pairs:

{json.dumps(company_names, indent=2)}
"""

    response = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    # Parse response
    response_text = response.content[0].text.strip()

    # Extract JSON from response (handle markdown code blocks)
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0].strip()

    return json.loads(response_text)


def normalize_company_names(input_file, output_file, batch_size=50):
    """
    Add normalized company names to leads data.

    Args:
        input_file (str): Path to input leads JSON file
        output_file (str): Path to output leads JSON file with normalized names
        batch_size (int): Number of names to process per API call

    Returns:
        dict: Results with count of normalized names
    """

    # Get API key
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
            "message": f"Invalid JSON in input file: {input_file}"
        }

    print(f"🏢 Normalizing company names for {len(leads)} leads...")

    # Extract unique company names
    company_names = []
    for lead in leads:
        company_name = lead.get("company_name") or lead.get("companyName") or ""
        if company_name and company_name not in company_names:
            company_names.append(company_name)

    print(f"   Found {len(company_names)} unique company names")

    # Process in batches
    normalized_mapping = {}
    batches = [company_names[i:i + batch_size] for i in range(0, len(company_names), batch_size)]

    for batch_num, batch in enumerate(batches, 1):
        print(f"   Processing batch {batch_num}/{len(batches)}...")

        try:
            batch_normalized = normalize_company_name_batch(batch, api_key)
            normalized_mapping.update(batch_normalized)
        except Exception as e:
            print(f"   ⚠️  Batch {batch_num} failed: {str(e)}")
            # Use original names as fallback
            for name in batch:
                normalized_mapping[name] = name

    # Add normalized names to leads
    for lead in leads:
        company_name = lead.get("company_name") or lead.get("companyName") or ""
        lead["company_name_normalized"] = normalized_mapping.get(company_name, company_name)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".tmp", exist_ok=True)

    # Save normalized leads
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)

    print(f"✅ Normalized {len(normalized_mapping)} company names")
    print(f"💾 Saved to: {output_file}")

    return {
        "status": "success",
        "total_leads": len(leads),
        "unique_companies": len(normalized_mapping),
        "file": output_file
    }


def main():
    parser = argparse.ArgumentParser(description="Normalize company names using AI")
    parser.add_argument("--input", required=True, help="Input leads JSON file")
    parser.add_argument("--output", required=True, help="Output leads JSON file")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size for API calls (default: 50)")

    args = parser.parse_args()

    result = normalize_company_names(
        input_file=args.input,
        output_file=args.output,
        batch_size=args.batch_size
    )

    # Print result
    if result["status"] == "success":
        print(f"\n✅ SUCCESS!")
        print(f"   Total leads: {result['total_leads']}")
        print(f"   Unique companies: {result['unique_companies']}")
    else:
        print(f"\n❌ FAILED: {result.get('message', 'Unknown error')}")

    print(f"\n{json.dumps(result, indent=2)}")

    # Exit with appropriate code
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()

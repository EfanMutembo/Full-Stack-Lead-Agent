"""
Convert Instantly CSV export to workflow JSON format.

This script converts a CSV file (exported from Instantly or other sources) into the
JSON format expected by the lead generation workflow.

Usage:
    python convert_csv_to_json.py --input file.csv --output .tmp/leads.json
"""

import os
import sys
import csv
import json
import argparse

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def convert_csv_to_json(input_file, output_file):
    """
    Convert CSV file to JSON format expected by workflow.

    Args:
        input_file (str): Path to input CSV file
        output_file (str): Path to output JSON file

    Returns:
        dict: Conversion summary with statistics
    """

    # Check if input file exists
    if not os.path.exists(input_file):
        return {
            "status": "error",
            "message": f"Input file not found: {input_file}"
        }

    leads = []
    skipped = 0

    print(f"📄 Converting CSV to JSON format...")
    print(f"   Input: {input_file}")
    print()

    try:
        # Read CSV file
        with open(input_file, 'r', encoding='utf-8-sig') as f:  # utf-8-sig handles BOM
            reader = csv.DictReader(f)

            for row_num, row in enumerate(reader, start=2):  # Start at 2 (line 1 is header)
                # Skip rows without email
                if not row.get('email') or not row['email'].strip():
                    skipped += 1
                    print(f"   ⚠️  Row {row_num}: Skipped (no email)")
                    continue

                # Extract fields from CSV (with fallbacks for missing columns)
                first_name = row.get('first_name', '').strip()
                last_name = row.get('last_name', '').strip()
                email = row.get('email', '').strip()
                company_name = row.get('company_name', '').strip()
                website = row.get('website', '').strip()
                company_domain = row.get('company_domain', '').strip()

                # Build full name
                full_name = f"{first_name} {last_name}".strip()

                # Use company_domain as website if website is missing
                if not website and company_domain:
                    website = f"http://{company_domain}"

                # Build lead object in workflow format
                lead = {
                    "first_name": first_name or None,
                    "last_name": last_name or None,
                    "email": email,
                    "full_name": full_name or None,
                    "company_name": company_name or None,
                    "company_name_normalized": company_name or None,  # Will be re-normalized by workflow
                    "company_website": website or None,
                    "company_domain": company_domain or None,

                    # Optional fields that might exist in CSV
                    "job_title": row.get('job_title', row.get('title', '')).strip() or None,
                    "linkedin": row.get('linkedin', '').strip() or None,
                    "phone": row.get('phone', row.get('mobile_number', '')).strip() or None,
                    "city": row.get('city', '').strip() or None,
                    "state": row.get('state', '').strip() or None,
                    "country": row.get('country', '').strip() or None,
                    "industry": row.get('industry', '').strip() or None,
                    "company_size": row.get('company_size', row.get('employees', '')).strip() or None,

                    # Metadata
                    "_source": "csv_import",
                    "_csv_row": row_num
                }

                leads.append(lead)

                # Print progress every 100 leads
                if len(leads) % 100 == 0:
                    print(f"   ✅ Processed {len(leads)} leads...")

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error reading CSV: {str(e)}"
        }

    if not leads:
        return {
            "status": "error",
            "message": "No valid leads found in CSV (all rows missing email)"
        }

    # Save to JSON
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".tmp", exist_ok=True)

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(leads, f, indent=2, ensure_ascii=False)
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error writing JSON: {str(e)}"
        }

    # Print summary
    print()
    print("=" * 60)
    print(f"✅ Conversion Complete!")
    print(f"   Total leads: {len(leads)}")
    print(f"   Skipped (no email): {skipped}")
    print(f"   Output: {output_file}")
    print()

    # Show sample lead
    if leads:
        print("📋 Sample lead:")
        sample = leads[0]
        print(f"   Name: {sample.get('full_name') or 'N/A'}")
        print(f"   Email: {sample.get('email') or 'N/A'}")
        print(f"   Company: {sample.get('company_name') or 'N/A'}")
        print(f"   Website: {sample.get('company_website') or 'N/A'}")

    return {
        "status": "success",
        "total_leads": len(leads),
        "skipped": skipped,
        "output_file": output_file
    }


def main():
    parser = argparse.ArgumentParser(description="Convert CSV to workflow JSON format")
    parser.add_argument("--input", required=True, help="Input CSV file")
    parser.add_argument("--output", required=True, help="Output JSON file")

    args = parser.parse_args()

    result = convert_csv_to_json(
        input_file=args.input,
        output_file=args.output
    )

    # Print result
    print()
    print("=" * 60)
    print(json.dumps(result, indent=2))

    # Exit with appropriate code
    sys.exit(0 if result.get("status") == "success" else 1)


if __name__ == "__main__":
    main()

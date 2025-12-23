"""
Filter validated leads based on validation report.

Removes leads that failed ICP validation (marked as valid: false in validation report).
This is run after full scrape validation to ensure only quality leads proceed to next steps.

Usage:
    python filter_validated_leads.py --input .tmp/full_leads.json --validation .tmp/full_validation_report.json --output .tmp/full_leads_filtered.json --report .tmp/filter_report.json
"""

import os
import sys
import json
import argparse
from collections import defaultdict

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def find_validation_for_lead(lead, validation_details):
    """
    Find the validation entry for a given lead.

    Match by company_name + email as unique identifier.

    Args:
        lead (dict): Lead data
        validation_details (list): List of validation results

    Returns:
        dict: Matching validation detail or None
    """
    company_name = lead.get('company_name') or lead.get('companyName') or ''
    email = lead.get('email') or lead.get('contact_email') or ''

    for detail in validation_details:
        detail_company = detail.get('company', '')
        detail_email = detail.get('data', {}).get('email', '') or detail.get('data', {}).get('contact_email', '')

        # Match by company name (primary) or email (secondary)
        if company_name and company_name.lower() == detail_company.lower():
            return detail
        if email and email.lower() == detail_email.lower():
            return detail

    return None


def extract_primary_reason(reason_text):
    """
    Extract primary removal reason from validation reason text.

    Args:
        reason_text (str): Full validation reason

    Returns:
        str: Primary reason category
    """
    reason_lower = reason_text.lower()

    if 'industry' in reason_lower or 'niche' in reason_lower:
        return 'wrong_industry'
    elif 'location' in reason_lower or 'geography' in reason_lower:
        return 'wrong_location'
    elif 'employee' in reason_lower or 'size' in reason_lower:
        return 'wrong_company_size'
    elif 'revenue' in reason_lower:
        return 'wrong_revenue'
    elif 'description' in reason_lower or 'profile' in reason_lower:
        return 'poor_firmographic_fit'
    else:
        return 'other'


def filter_validated_leads(input_file, validation_report_file, output_file, report_file):
    """
    Filter leads based on validation report, keeping only valid leads.

    Args:
        input_file (str): Path to input leads JSON file
        validation_report_file (str): Path to validation report JSON file
        output_file (str): Path to output filtered leads JSON file
        report_file (str): Path to filter report JSON file

    Returns:
        dict: Filter results with statistics
    """

    # Check if validation report exists
    if not os.path.exists(validation_report_file):
        return {
            "status": "error",
            "message": f"Validation report file not found: {validation_report_file}"
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

    # Load validation report
    try:
        with open(validation_report_file, 'r', encoding='utf-8') as f:
            validation_report = json.load(f)
    except json.JSONDecodeError:
        return {
            "status": "error",
            "message": f"Invalid JSON in validation report: {validation_report_file}"
        }

    validation_details = validation_report.get('validation_details', [])

    if not validation_details:
        print("⚠️  Warning: No validation details found in report, keeping all leads")
        filtered_leads = leads
        removed_leads = []
        removal_reasons = {}
    else:
        # Filter leads
        filtered_leads = []
        removed_leads = []
        removal_reasons = defaultdict(int)

        print(f"🔍 Filtering {len(leads)} leads based on validation report...")

        for lead in leads:
            # Find matching validation detail
            validation_detail = find_validation_for_lead(lead, validation_details)

            if validation_detail and validation_detail.get('valid'):
                # Lead passed validation
                filtered_leads.append(lead)
            else:
                # Lead failed validation or not found in report
                removed_leads.append(lead)

                if validation_detail:
                    reason = extract_primary_reason(validation_detail.get('reason', 'unknown'))
                else:
                    reason = 'not_in_validation_report'

                removal_reasons[reason] += 1

    # Save filtered leads
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".tmp", exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_leads, f, indent=2, ensure_ascii=False)

    # Generate filter report
    filter_report = {
        "status": "success",
        "original_count": len(leads),
        "filtered_count": len(filtered_leads),
        "removed_count": len(removed_leads),
        "removal_reasons": dict(removal_reasons),
        "input_file": input_file,
        "output_file": output_file,
        "validation_report": validation_report_file,
        "quality_percentage": round((len(filtered_leads) / len(leads)) * 100, 1) if leads else 0
    }

    # Save filter report
    os.makedirs(os.path.dirname(report_file) if os.path.dirname(report_file) else ".tmp", exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(filter_report, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "="*50)
    print(f"📊 Filter Results:")
    print(f"   Original leads: {len(leads)}")
    print(f"   Filtered leads: {len(filtered_leads)} ({filter_report['quality_percentage']}%)")
    print(f"   Removed leads: {len(removed_leads)}")

    if removal_reasons:
        print(f"\n   Removal breakdown:")
        for reason, count in sorted(removal_reasons.items(), key=lambda x: x[1], reverse=True):
            print(f"      - {reason.replace('_', ' ').title()}: {count}")

    print(f"\n💾 Filtered leads saved to: {output_file}")
    print(f"💾 Filter report saved to: {report_file}")

    # Warning if too many leads removed
    if filter_report['quality_percentage'] < 50:
        print(f"\n⚠️  WARNING: Less than 50% of leads passed validation!")
        print(f"   Consider reviewing your ICP criteria or scrape filters.")

    return filter_report


def main():
    parser = argparse.ArgumentParser(description="Filter validated leads based on validation report")
    parser.add_argument("--input", required=True, help="Input leads JSON file")
    parser.add_argument("--validation", required=True, help="Validation report JSON file")
    parser.add_argument("--output", default=".tmp/full_leads_filtered.json", help="Output filtered leads file")
    parser.add_argument("--report", default=".tmp/filter_report.json", help="Filter report output file")

    args = parser.parse_args()

    result = filter_validated_leads(
        input_file=args.input,
        validation_report_file=args.validation,
        output_file=args.output,
        report_file=args.report
    )

    # Print result
    print("\n" + "="*50)
    if result["status"] == "success":
        print(f"✅ SUCCESS!")
        print(f"   Kept: {result['filtered_count']}/{result['original_count']} leads")
        print(f"   Quality: {result['quality_percentage']}%")
    else:
        print(f"❌ FAILED: {result.get('message', 'Unknown error')}")

    print("\n" + json.dumps({k: v for k, v in result.items() if k != 'removal_reasons'}, indent=2))

    # Exit with appropriate code
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()

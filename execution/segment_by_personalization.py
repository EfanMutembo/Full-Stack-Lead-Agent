"""
Segment leads by personalization status into separate files for different campaigns.

Splits personalized leads into one file and non-personalized leads into another.

Usage:
    python segment_by_personalization.py --input .tmp/csv_leads_personalized.json --personalized-output .tmp/personalized_segment.json --non-personalized-output .tmp/non_personalized_segment.json
"""

import os
import sys
import json
import argparse

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def segment_by_personalization(input_file, personalized_output, non_personalized_output):
    """
    Segment leads by personalization status.

    Args:
        input_file (str): Path to JSON file with all leads
        personalized_output (str): Output path for personalized leads
        non_personalized_output (str): Output path for non-personalized leads

    Returns:
        dict: Results with segmentation statistics
    """

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

    print(f"📊 Segmenting {len(leads)} leads by personalization status...\n")

    # Segment leads
    personalized_leads = []
    non_personalized_leads = []

    for lead in leads:
        personalization = lead.get('personalization')

        # Lead has personalization if:
        # 1. personalization field exists and is not None
        # 2. personalization is not an empty string
        if personalization and personalization.strip():
            personalized_leads.append(lead)
        else:
            non_personalized_leads.append(lead)

    # Print statistics
    print(f"✅ Segmentation complete:")
    print(f"   Total leads: {len(leads)}")
    print(f"   Personalized: {len(personalized_leads)} ({len(personalized_leads)/len(leads)*100:.1f}%)")
    print(f"   Non-personalized: {len(non_personalized_leads)} ({len(non_personalized_leads)/len(leads)*100:.1f}%)")

    # Save personalized leads
    if personalized_leads:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(personalized_output), exist_ok=True)

        with open(personalized_output, 'w', encoding='utf-8') as f:
            json.dump(personalized_leads, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Saved {len(personalized_leads)} personalized leads to: {personalized_output}")
    else:
        print(f"\n⚠️  No personalized leads to save")

    # Save non-personalized leads
    if non_personalized_leads:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(non_personalized_output), exist_ok=True)

        with open(non_personalized_output, 'w', encoding='utf-8') as f:
            json.dump(non_personalized_leads, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved {len(non_personalized_leads)} non-personalized leads to: {non_personalized_output}")
    else:
        print(f"\n⚠️  No non-personalized leads to save")

    return {
        "status": "success",
        "total_leads": len(leads),
        "personalized_count": len(personalized_leads),
        "non_personalized_count": len(non_personalized_leads),
        "personalized_percentage": round(len(personalized_leads)/len(leads)*100, 1) if leads else 0,
        "personalized_output": personalized_output if personalized_leads else None,
        "non_personalized_output": non_personalized_output if non_personalized_leads else None,
        "message": f"Successfully segmented {len(leads)} leads into {len(personalized_leads)} personalized and {len(non_personalized_leads)} non-personalized"
    }


def main():
    parser = argparse.ArgumentParser(description='Segment leads by personalization status')
    parser.add_argument('--input', required=True, help='Input JSON file with all leads')
    parser.add_argument('--personalized-output', required=True, help='Output file for personalized leads')
    parser.add_argument('--non-personalized-output', required=True, help='Output file for non-personalized leads')

    args = parser.parse_args()

    # Segment leads
    result = segment_by_personalization(
        args.input,
        args.personalized_output,
        args.non_personalized_output
    )

    # Print results
    print("\n" + "="*60)
    if result['status'] == 'success':
        print(f"✅ {result['message']}")
        print(f"   Total leads: {result['total_leads']}")
        print(f"   Personalized: {result['personalized_count']} ({result['personalized_percentage']}%)")
        print(f"   Non-personalized: {result['non_personalized_count']}")
        if result['personalized_output']:
            print(f"   Personalized file: {result['personalized_output']}")
        if result['non_personalized_output']:
            print(f"   Non-personalized file: {result['non_personalized_output']}")
    else:
        print(f"❌ {result['message']}")
        sys.exit(1)

    print("="*60)

    # Output JSON result
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

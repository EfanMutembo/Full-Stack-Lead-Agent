"""
Generate multiple campaign copies in parallel for faster processing.

Usage:
    python generate_campaigns_parallel.py --config campaign_config.json --output-dir .tmp

    Config file format:
    {
        "campaigns": [
            {
                "offer": "Product A",
                "industry": "Marketing Agencies",
                "segment": "Executive Leadership",
                "segment_angle": "Revenue growth",
                "segment_titles": "CEO, Founder, Managing Director",
                "output": ".tmp/campaign_exec.json"
            },
            {
                "offer": "Product A",
                "industry": "Marketing Agencies",
                "segment": "Creative Leadership",
                "segment_angle": "Creative efficiency",
                "segment_titles": "Creative Director, Design Lead",
                "output": ".tmp/campaign_creative.json"
            }
        ],
        "knowledge_base": "knowledge_base/email_templates.md"
    }
"""

import os
import sys
import json
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

# Import the single campaign generator
from generate_campaign_copy import generate_campaign_copy


def generate_single_campaign(campaign_config, knowledge_base_path, campaign_num, total_campaigns):
    """
    Generate a single campaign copy (for parallel processing).

    Args:
        campaign_config (dict): Campaign configuration
        knowledge_base_path (str): Path to knowledge base file
        campaign_num (int): Campaign number for logging
        total_campaigns (int): Total number of campaigns

    Returns:
        dict: Result with status and output file
    """
    offer = campaign_config.get("offer")
    industry = campaign_config.get("industry")
    segment = campaign_config.get("segment")
    segment_angle = campaign_config.get("segment_angle")
    segment_titles = campaign_config.get("segment_titles")
    output = campaign_config.get("output")

    print(f"   📧 [{campaign_num}/{total_campaigns}] Generating: {offer} - {segment}")

    try:
        result = generate_campaign_copy(
            offer_name=offer,
            target_industry=industry,
            knowledge_base_path=knowledge_base_path,
            output_file=output,
            segment_name=segment,
            segment_angle=segment_angle,
            segment_titles=segment_titles
        )

        if result.get("status") == "success":
            print(f"   ✅ [{campaign_num}/{total_campaigns}] Generated: {segment}")
            return {
                "status": "success",
                "campaign": f"{offer} - {segment}",
                "output": output
            }
        else:
            print(f"   ❌ [{campaign_num}/{total_campaigns}] Failed: {result.get('message', 'Unknown error')}")
            return {
                "status": "error",
                "campaign": f"{offer} - {segment}",
                "message": result.get("message", "Unknown error")
            }

    except Exception as e:
        print(f"   ❌ [{campaign_num}/{total_campaigns}] Error: {str(e)}")
        return {
            "status": "error",
            "campaign": f"{offer} - {segment}",
            "message": str(e)
        }


def generate_campaigns_parallel(config_file, output_dir=".tmp"):
    """
    Generate multiple campaign copies in parallel.

    Args:
        config_file (str): Path to campaign configuration JSON file
        output_dir (str): Output directory for campaign files

    Returns:
        dict: Results with summary
    """

    # Load configuration
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        return {
            "status": "error",
            "message": f"Config file not found: {config_file}"
        }
    except json.JSONDecodeError:
        return {
            "status": "error",
            "message": f"Invalid JSON in config file: {config_file}"
        }

    campaigns = config.get("campaigns", [])
    knowledge_base_path = config.get("knowledge_base")

    if not campaigns:
        return {
            "status": "error",
            "message": "No campaigns found in config file"
        }

    if not knowledge_base_path:
        return {
            "status": "error",
            "message": "No knowledge_base path specified in config"
        }

    print(f"🚀 Generating {len(campaigns)} campaign(s) in parallel...")
    print(f"   Knowledge base: {knowledge_base_path}")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Generate campaigns in parallel
    results = []
    max_workers = min(4, len(campaigns))  # Use up to 4 concurrent generators

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all campaign generation tasks
        future_to_campaign = {
            executor.submit(
                generate_single_campaign,
                campaign,
                knowledge_base_path,
                idx + 1,
                len(campaigns)
            ): idx
            for idx, campaign in enumerate(campaigns)
        }

        # Collect results as they complete
        for future in as_completed(future_to_campaign):
            result = future.result()
            results.append(result)

    # Calculate summary
    successful = sum(1 for r in results if r.get("status") == "success")
    failed = sum(1 for r in results if r.get("status") == "error")

    print("\n" + "="*50)
    print(f"📊 Campaign Generation Summary:")
    print(f"   Total campaigns: {len(campaigns)}")
    print(f"   Successful: {successful}")
    print(f"   Failed: {failed}")

    return {
        "status": "success" if failed == 0 else "partial",
        "total": len(campaigns),
        "successful": successful,
        "failed": failed,
        "results": results
    }


def main():
    parser = argparse.ArgumentParser(description="Generate multiple campaign copies in parallel")
    parser.add_argument("--config", required=True, help="Path to campaign configuration JSON file")
    parser.add_argument("--output-dir", default=".tmp", help="Output directory for campaign files")

    args = parser.parse_args()

    result = generate_campaigns_parallel(
        config_file=args.config,
        output_dir=args.output_dir
    )

    # Print result
    print("\n" + "="*50)
    if result["status"] == "success":
        print(f"✅ ALL CAMPAIGNS GENERATED SUCCESSFULLY!")
        print(f"   Total: {result['total']}")
    elif result["status"] == "partial":
        print(f"⚠️  PARTIAL SUCCESS")
        print(f"   Successful: {result['successful']}")
        print(f"   Failed: {result['failed']}")
    else:
        print(f"❌ FAILED: {result.get('message', 'Unknown error')}")

    print("\n" + json.dumps(result, indent=2))

    # Exit with appropriate code
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()

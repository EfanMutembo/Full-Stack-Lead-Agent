"""
Segment leads by job title using AI to cluster into functional groups.

Uses Claude AI to analyze job titles and group them into 3-6 low-cardinality segments
based on business function (e.g., Executive, Operations, Marketing, Sales).

Usage:
    python segment_by_job_title.py --input .tmp/full_leads_normalized.json --output-mapping .tmp/segment_mapping.json --output-dir .tmp --min-segment-size 10
"""

import os
import sys
import json
import argparse
from datetime import datetime
from collections import defaultdict
from anthropic import Anthropic
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()


def parse_json_from_response(response_text):
    """
    Extract JSON from AI response, handling markdown code blocks.

    Args:
        response_text (str): AI response text

    Returns:
        dict: Parsed JSON object
    """
    text = response_text.strip()

    # Extract JSON from code blocks if present
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    return json.loads(text)


def cluster_job_titles(job_titles, api_key):
    """
    Use Claude AI to cluster job titles into functional segments.

    Args:
        job_titles (list): List of unique job titles
        api_key (str): Anthropic API key

    Returns:
        dict: Segment definitions with segment_id, segment_name, job_titles, messaging_angle
    """

    client = Anthropic(api_key=api_key)

    prompt = f"""You are a job title segmentation expert. Analyze these job titles and group them into 3-6 meaningful segments based on BUSINESS FUNCTION.

Job Titles to Segment:
{json.dumps(job_titles, indent=2)}

Requirements:
1. **LOW CARDINALITY**: Create 3-6 segments total (fewer is better)
   - Group similar roles together (e.g., CMO + VP Marketing + Marketing Director = "Marketing Leadership")
   - Aim for clean, meaningful buckets based on function, not just seniority

2. **FUNCTIONAL CLUSTERING**: Group by business function, not just title similarity
   - Executive (CEO, Founder, Owner, President, Managing Director)
   - Operations (COO, VP Operations, Director of Operations, Operations Manager)
   - Marketing (CMO, VP Marketing, Marketing Director, Head of Marketing, Marketing Manager)
   - Sales (VP Sales, Sales Director, Head of Sales, Sales Manager, Business Development)
   - Technical (CTO, VP Engineering, Director of Technology, IT Director, Head of Tech)
   - Finance (CFO, VP Finance, Finance Director, Controller)

3. **MESSAGING ANGLES**: Define what each segment cares about most
   - Executive: Revenue growth, strategic outcomes, ROI, competitive advantage
   - Operations: Operational efficiency + revenue impact, cost savings, process optimization
   - Marketing: Lead generation ROI, brand growth, conversion rates, customer acquisition
   - Sales: Pipeline acceleration, quota attainment, revenue growth, deal velocity
   - Technical: Innovation, scalability, technical excellence, automation
   - Finance: Cost control, profitability, financial metrics, risk management

4. **EDGE CASES**: Assign uncommon or generic titles to best-fit segment
   - "Owner" or "Founder" → Executive
   - Generic "Manager" without department → Operations
   - Unclear titles → Assign to Executive (most conservative)

Return ONLY a JSON object in this exact format:
{{
  "segments": [
    {{
      "segment_id": "exec",
      "segment_name": "Executive Leadership",
      "job_titles": ["CEO", "Founder", "Owner", ...],
      "messaging_angle": "Revenue growth and strategic outcomes"
    }},
    {{
      "segment_id": "operations",
      "segment_name": "Operations Leadership",
      "job_titles": ["COO", "VP Operations", ...],
      "messaging_angle": "Operational efficiency with revenue impact"
    }}
  ]
}}

Important:
- Use segment_id values: "exec", "operations", "marketing", "sales", "technical", "finance", "general"
- Each job title should appear in EXACTLY ONE segment
- ALL input job titles must be assigned to a segment
- Focus on creating actionable, business-function-based groups
"""

    response = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )

    # Parse AI response
    response_text = response.content[0].text.strip()
    segment_definitions = parse_json_from_response(response_text)

    return segment_definitions


def fallback_segmentation(job_titles):
    """
    Fallback heuristic segmentation if AI clustering fails.

    Groups titles into basic C-level, Director, Manager, and General categories.

    Args:
        job_titles (list): List of job titles

    Returns:
        dict: Basic segment definitions
    """
    print("   Using fallback heuristic segmentation...")

    exec_titles = []
    operations_titles = []
    marketing_titles = []
    sales_titles = []
    technical_titles = []
    general_titles = []

    for title in job_titles:
        title_lower = title.lower()

        # Executive
        if any(keyword in title_lower for keyword in ['ceo', 'founder', 'owner', 'president', 'managing director', 'chief executive']):
            exec_titles.append(title)
        # Operations
        elif any(keyword in title_lower for keyword in ['coo', 'operations', 'chief operating']):
            operations_titles.append(title)
        # Marketing
        elif any(keyword in title_lower for keyword in ['cmo', 'marketing', 'brand', 'chief marketing']):
            marketing_titles.append(title)
        # Sales
        elif any(keyword in title_lower for keyword in ['sales', 'business development', 'revenue']):
            sales_titles.append(title)
        # Technical
        elif any(keyword in title_lower for keyword in ['cto', 'technology', 'engineering', 'technical', 'chief technology']):
            technical_titles.append(title)
        # General (fallback)
        else:
            general_titles.append(title)

    # Build segment definitions
    segments = []

    if exec_titles:
        segments.append({
            "segment_id": "exec",
            "segment_name": "Executive Leadership",
            "job_titles": exec_titles,
            "messaging_angle": "Revenue growth and strategic outcomes"
        })

    if operations_titles:
        segments.append({
            "segment_id": "operations",
            "segment_name": "Operations Leadership",
            "job_titles": operations_titles,
            "messaging_angle": "Operational efficiency with revenue impact"
        })

    if marketing_titles:
        segments.append({
            "segment_id": "marketing",
            "segment_name": "Marketing Leadership",
            "job_titles": marketing_titles,
            "messaging_angle": "Lead generation ROI and brand growth"
        })

    if sales_titles:
        segments.append({
            "segment_id": "sales",
            "segment_name": "Sales Leadership",
            "job_titles": sales_titles,
            "messaging_angle": "Pipeline acceleration and quota attainment"
        })

    if technical_titles:
        segments.append({
            "segment_id": "technical",
            "segment_name": "Technical Leadership",
            "job_titles": technical_titles,
            "messaging_angle": "Innovation and technical excellence"
        })

    # Merge general into exec if general is small
    if general_titles:
        if len(general_titles) < 10 and exec_titles:
            print(f"   Merging {len(general_titles)} general titles into Executive segment")
            segments[0]['job_titles'].extend(general_titles)
        else:
            segments.append({
                "segment_id": "general",
                "segment_name": "General Management",
                "job_titles": general_titles,
                "messaging_angle": "Business growth and operational excellence"
            })

    return {"segments": segments}


def segment_by_job_title(input_file, output_mapping_file, output_dir=".tmp", min_segment_size=10):
    """
    Segment leads by job title using AI clustering.

    Args:
        input_file (str): Path to input leads JSON file
        output_mapping_file (str): Path to output segment mapping JSON file
        output_dir (str): Directory to save segment lead files
        min_segment_size (int): Minimum leads required per segment

    Returns:
        dict: Segmentation results
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

    print(f"👔 Segmenting {len(leads)} leads by job title...")

    # Extract unique job titles
    job_titles = []
    for lead in leads:
        job_title = lead.get('job_title') or lead.get('title') or ''
        if job_title and job_title not in job_titles:
            job_titles.append(job_title)

    if not job_titles:
        print("⚠️  No job titles found in leads, creating single 'General' segment")
        segment_definitions = {
            "segments": [{
                "segment_id": "general",
                "segment_name": "General",
                "job_titles": [],
                "messaging_angle": "Business growth and operational excellence"
            }]
        }
    else:
        print(f"   Found {len(job_titles)} unique job titles")

        # Use AI to cluster job titles
        try:
            segment_definitions = cluster_job_titles(job_titles, api_key)
            print(f"   AI clustered into {len(segment_definitions['segments'])} segments")
        except Exception as e:
            print(f"   ⚠️  AI clustering failed: {str(e)}")
            segment_definitions = fallback_segmentation(job_titles)
            print(f"   Fallback created {len(segment_definitions['segments'])} segments")

    # Build job_title → segment_id mapping (case-insensitive)
    title_to_segment = {}
    for segment in segment_definitions['segments']:
        for title in segment['job_titles']:
            title_to_segment[title.lower()] = segment['segment_id']

    # Split leads by segment
    segment_leads = defaultdict(list)
    unmatched_leads = []

    for lead in leads:
        job_title = (lead.get('job_title') or lead.get('title') or '').strip()

        # Try exact match (case-insensitive)
        segment_id = title_to_segment.get(job_title.lower())

        if segment_id:
            segment_leads[segment_id].append(lead)
        else:
            # No match found - assign to unmatched
            unmatched_leads.append(lead)

    # Handle unmatched leads - assign to exec segment (most conservative)
    if unmatched_leads:
        print(f"   ⚠️  {len(unmatched_leads)} leads with unmatched job titles, assigning to Executive segment")
        segment_leads['exec'].extend(unmatched_leads)

    # Filter out segments below minimum size and save segment files
    filtered_segments = []
    total_saved_leads = 0

    for segment in segment_definitions['segments']:
        segment_id = segment['segment_id']
        leads_in_segment = segment_leads[segment_id]
        lead_count = len(leads_in_segment)

        if lead_count >= min_segment_size:
            segment['lead_count'] = lead_count
            filtered_segments.append(segment)

            # Save segment leads to file
            segment_file = os.path.join(output_dir, f"segment_{segment_id}_leads.json")
            os.makedirs(output_dir, exist_ok=True)

            with open(segment_file, 'w', encoding='utf-8') as f:
                json.dump(leads_in_segment, f, indent=2, ensure_ascii=False)

            total_saved_leads += lead_count
            print(f"   ✅ {segment['segment_name']}: {lead_count} leads → {segment_file}")

        elif lead_count > 0:
            # Segment too small - merge into exec
            print(f"   ⚠️  {segment['segment_name']} has only {lead_count} leads (min: {min_segment_size}), merging into Executive")

            # Find exec segment and merge
            for existing_segment in filtered_segments:
                if existing_segment['segment_id'] == 'exec':
                    existing_segment['lead_count'] += lead_count
                    segment_leads['exec'].extend(leads_in_segment)
                    break
            else:
                # No exec segment yet, create one
                exec_segment = {
                    "segment_id": "exec",
                    "segment_name": "Executive Leadership",
                    "job_titles": segment['job_titles'],
                    "messaging_angle": "Revenue growth and strategic outcomes",
                    "lead_count": lead_count
                }
                filtered_segments.append(exec_segment)
                segment_leads['exec'].extend(leads_in_segment)

    # Re-save exec segment if it was modified by merges
    if 'exec' in segment_leads and len(segment_leads['exec']) > 0:
        segment_file = os.path.join(output_dir, "segment_exec_leads.json")
        with open(segment_file, 'w', encoding='utf-8') as f:
            json.dump(segment_leads['exec'], f, indent=2, ensure_ascii=False)

        # Update lead count in mapping
        for seg in filtered_segments:
            if seg['segment_id'] == 'exec':
                seg['lead_count'] = len(segment_leads['exec'])
                break

    # Save mapping
    mapping = {
        "segments": filtered_segments,
        "total_leads": len(leads),
        "total_segments": len(filtered_segments),
        "generated_at": datetime.now().isoformat()
    }

    os.makedirs(os.path.dirname(output_mapping_file) if os.path.dirname(output_mapping_file) else output_dir, exist_ok=True)
    with open(output_mapping_file, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "="*50)
    print(f"📊 Segmentation Results:")
    print(f"   Total leads: {len(leads)}")
    print(f"   Segments created: {len(filtered_segments)}")
    print(f"   Leads assigned: {total_saved_leads}")

    for segment in filtered_segments:
        print(f"      - {segment['segment_name']}: {segment['lead_count']} leads")

    print(f"\n💾 Segment mapping saved to: {output_mapping_file}")

    return {
        "status": "success",
        "total_leads": len(leads),
        "total_segments": len(filtered_segments),
        "mapping_file": output_mapping_file,
        "segments": filtered_segments
    }


def main():
    parser = argparse.ArgumentParser(description="Segment leads by job title using AI clustering")
    parser.add_argument("--input", required=True, help="Input leads JSON file")
    parser.add_argument("--output-mapping", required=True, help="Output segment mapping JSON file")
    parser.add_argument("--output-dir", default=".tmp", help="Directory for segment lead files")
    parser.add_argument("--min-segment-size", type=int, default=10, help="Minimum leads per segment")

    args = parser.parse_args()

    result = segment_by_job_title(
        input_file=args.input,
        output_mapping_file=args.output_mapping,
        output_dir=args.output_dir,
        min_segment_size=args.min_segment_size
    )

    # Print result
    print("\n" + "="*50)
    if result["status"] == "success":
        print(f"✅ SUCCESS!")
        print(f"   Created {result['total_segments']} segments from {result['total_leads']} leads")
    else:
        print(f"❌ FAILED: {result.get('message', 'Unknown error')}")

    print("\n" + json.dumps({k: v for k, v in result.items() if k != 'segments'}, indent=2))

    # Exit with appropriate code
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()

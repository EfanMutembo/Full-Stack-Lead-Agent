"""
Enrich leads with personalization data by scraping company websites.

This script scrapes common pages (homepage, about, testimonials, etc.) from each lead's
website and uses AI to extract a 1-sentence personalization referencing recent projects,
testimonials, clients, or achievements.

Usage:
    python enrich_personalization.py --input .tmp/full_leads_verified.json --output .tmp/full_leads_personalized.json --report .tmp/personalization_report.json
"""

import os
import sys
import json
import argparse
import requests
import time
from dotenv import load_dotenv
from anthropic import Anthropic
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse
import random
from bs4 import BeautifulSoup
import re
from firecrawl import FirecrawlApp

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()


def normalize_url(url):
    """
    Normalize URL to ensure it has proper scheme.

    Args:
        url (str): URL to normalize

    Returns:
        str: Normalized URL with https:// scheme
    """
    if not url:
        return None

    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'

    return url


def scrape_page(url, timeout=5):
    """
    Scrape a single page and return its HTML content.

    Args:
        url (str): URL to scrape
        timeout (int): Request timeout in seconds

    Returns:
        dict: Result with status and content/error
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    try:
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)

        if response.status_code == 200:
            # Extract clean text from HTML using BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove script and style elements
            for script in soup(['script', 'style', 'nav', 'footer', 'header']):
                script.decompose()

            # Get text and clean it up
            text = soup.get_text()

            # Break into lines and remove leading/trailing space on each
            lines = (line.strip() for line in text.splitlines())

            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))

            # Drop blank lines and join
            clean_text = '\n'.join(chunk for chunk in chunks if chunk)

            # Limit to 10KB of clean text per page
            clean_text = clean_text[:10000]

            return {
                'status': 'success',
                'url': url,
                'content': clean_text,
                'length': len(clean_text)
            }
        elif response.status_code == 403:
            return {
                'status': 'blocked',
                'url': url,
                'error': 'Access forbidden (403)'
            }
        elif response.status_code == 429:
            return {
                'status': 'rate_limited',
                'url': url,
                'error': 'Rate limited (429)'
            }
        else:
            return {
                'status': 'failed',
                'url': url,
                'error': f'HTTP {response.status_code}'
            }

    except requests.exceptions.Timeout:
        return {
            'status': 'timeout',
            'url': url,
            'error': 'Request timed out'
        }
    except requests.exceptions.RequestException as e:
        return {
            'status': 'error',
            'url': url,
            'error': str(e)[:100]
        }
    except Exception as e:
        return {
            'status': 'error',
            'url': url,
            'error': str(e)[:100]
        }


def scrape_website(base_url, delay=0.5):
    """
    Scrape common pages from a website.

    Args:
        base_url (str): Base URL of the website
        delay (float): Delay between requests in seconds

    Returns:
        dict: Scraped pages with content
    """
    # Common page paths prioritized by personalization value (scrape until we get 1 good page + homepage)
    common_paths = [
        '/',                  # Homepage (ALWAYS scrape)
        '/case-studies',      # Best: specific client work and results
        '/casestudies',       # Best: alternate spelling
        '/testimonials',      # Best: client names and outcomes
        '/reviews',           # Good: client feedback and ratings
        '/portfolio',         # Good: recent projects and clients
        '/clients',           # Good: notable client names
        '/our-clients',       # Good: alternate naming
        '/projects',          # Good: specific work examples
        '/our-work',          # Good: alternate naming
        '/work',              # Medium: examples of work
        '/success-stories',   # Good: detailed client outcomes
        '/success',           # Good: alternate naming
        '/about',             # Medium: company background
        '/about-us',          # Medium: alternate naming
        '/customer-stories',  # Good: customer case studies
        '/case-study',        # Good: singular form
        '/client-success'     # Good: client outcomes
    ]

    base_url = normalize_url(base_url)
    if not base_url:
        return {'status': 'error', 'error': 'Invalid URL'}

    scraped_pages = []
    homepage_scraped = False
    firecrawl_fallback_attempted = False

    for i, path in enumerate(common_paths):
        url = urljoin(base_url, path)

        # Add delay between requests (polite scraping)
        if i > 0:  # Skip delay for first request
            time.sleep(delay)

        result = scrape_page(url)

        if result['status'] == 'success':
            scraped_pages.append(result)
            if path == '/':
                homepage_scraped = True

        # If blocked, try Firecrawl fallback (bypasses anti-bot protection)
        if result['status'] in ['blocked', 'rate_limited'] and not firecrawl_fallback_attempted:
            firecrawl_fallback_attempted = True

            try:
                # Try Firecrawl for the homepage only (most important page)
                firecrawl_api_key = os.getenv('FIRECRAWL_API_KEY')
                if firecrawl_api_key:
                    firecrawl = FirecrawlApp(api_key=firecrawl_api_key)
                    homepage_url = urljoin(base_url, '/')

                    # Scrape with Firecrawl (uses headless browser to bypass blocks)
                    scrape_result = firecrawl.scrape(homepage_url, formats=['markdown'])

                    if scrape_result and hasattr(scrape_result, 'markdown') and scrape_result.markdown:
                        clean_text = scrape_result.markdown[:10000]  # Limit to 10KB
                        scraped_pages.append({
                            'status': 'success',
                            'url': homepage_url,
                            'content': clean_text,
                            'length': len(clean_text)
                        })
                        homepage_scraped = True
                    else:
                        # Firecrawl failed, stop trying
                        break
                else:
                    # No Firecrawl API key, stop trying
                    break
            except Exception as e:
                # Firecrawl failed, stop trying
                print(f"   ⚠️  Firecrawl fallback failed: {str(e)}")
                break
        elif result['status'] in ['blocked', 'rate_limited']:
            # Already tried Firecrawl, stop
            break

        # Stop after homepage + 1 additional good page (optimized for speed)
        if homepage_scraped and len(scraped_pages) >= 2:
            break

    return {
        'status': 'success' if scraped_pages else 'failed',
        'base_url': base_url,
        'pages_scraped': len(scraped_pages),
        'pages': scraped_pages
    }


def extract_personalization(company_name, scraped_data, api_key):
    """
    Use AI to extract a 1-sentence personalization from scraped website content.

    Args:
        company_name (str): Company name
        scraped_data (dict): Scraped website data
        api_key (str): Anthropic API key

    Returns:
        dict: Personalization result
    """
    if scraped_data['status'] != 'success' or not scraped_data.get('pages'):
        return {
            'status': 'no_data',
            'personalization': None,
            'reason': 'No website content available'
        }

    # Build combined content from all scraped pages
    combined_content = ""
    for page in scraped_data['pages']:
        combined_content += f"\n\n=== {page['url']} ===\n{page['content'][:3000]}"  # Max 3KB per page

    # Truncate to reasonable size for AI (max 20KB)
    combined_content = combined_content[:20000]

    client = Anthropic(api_key=api_key)

    prompt = f"""You are an expert at extracting personalization nuggets from website content for cold email outreach.

<company>{company_name}</company>

<website_content>
{combined_content}
</website_content>

<task>
Extract ONE specific, credible personalization to use as an opening line.

USE THIS PRIORITY ORDER (try each level, move to next if nothing found):

<priority_1>
BEST: Specific client names or project names
- Look for: Client testimonials with names, case studies with client names, specific project titles
- Examples: "Hope T.'s estate sale", "Ellen Diehl's house", "Rutherford Farmhouse model home"
</priority_1>

<priority_2>
FALLBACK: Awards, certifications, or notable achievements
- Look for: Industry awards, certifications, recognitions, milestones
- Examples: "2024 Excellence in Real Estate award", "Certified Green Builder designation", "20-year anniversary"
</priority_2>

<priority_3>
FALLBACK: Recent news or company milestones
- Look for: Expansions, new locations, company milestones, recent announcements
- Examples: "recent expansion to three locations", "new downtown office opening"
</priority_3>

<priority_4>
LAST RESORT: Industry-specific niche or specialization
- Look for: Specific service focus, unique specialization, market niche
- Examples: "focus on estate liquidations", "specialization in custom home builds"
</priority_4>
</task>

<requirements>
1. Keep it SHORT - maximum 10-12 words
2. MATTER-OF-FACT tone - NO enthusiasm like "impressive", "amazing", "incredible"
3. Start with "I saw" or "I noticed" or "I came across"
4. Be specific, not generic
</requirements>

<good_examples>
Priority 1 (BEST):
- "I noticed the complex estate sale with Hope"
- "I saw your 4-day sale on Ellen Diehl's house"
- "I came across your Rutherford Farmhouse model home"

Priority 2-4 (FALLBACK):
- "I saw your 2024 Excellence in Real Estate award"
- "I noticed your recent expansion to three locations"
- "I saw you specialize in estate liquidations"
</good_examples>

<bad_examples>
- "I noticed how you helped Hope T. navigate a complex estate sale, providing expert guidance while managing the property remotely over several months" (TOO LONG)
- "I noticed your goal is to help families find their perfect home" (TOO GENERIC)
- "I saw how your team sold Ellen Diehl's house in just 4 days, which is incredibly impressive" (DON'T ADD PRAISE)
</bad_examples>

<response_format>
Return ONLY a JSON object:
{{
  "personalization": "I saw [your specific observation]",
  "confidence": "high|medium|low",
  "source": "brief description of where you found this"
}}

Return null ONLY if you truly cannot find anything relevant in the content.
</response_format>

Return ONLY the JSON, no other text."""

    try:
        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text.strip()

        # Extract JSON from response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        result = json.loads(response_text)

        return {
            'status': 'success',
            'personalization': result.get('personalization'),
            'confidence': result.get('confidence', 'unknown'),
            'source': result.get('source', 'unknown')
        }

    except Exception as e:
        return {
            'status': 'error',
            'personalization': None,
            'reason': f'AI extraction failed: {str(e)[:100]}'
        }


def enrich_lead(lead, api_key, delay=0.5):
    """
    Enrich a single lead with personalization data.

    Args:
        lead (dict): Lead data
        api_key (str): Anthropic API key
        delay (float): Delay between page requests

    Returns:
        dict: Enriched lead with personalization
    """
    company_name = lead.get("company_name_normalized") or lead.get("company_name") or "Unknown"
    website = lead.get("company_website") or lead.get("website") or ""

    if not website:
        return {
            **lead,
            'personalization': None,
            'personalization_status': 'no_website'
        }

    # Scrape website
    scraped_data = scrape_website(website, delay=delay)

    if scraped_data['status'] != 'success':
        return {
            **lead,
            'personalization': None,
            'personalization_status': 'scrape_failed',
            'personalization_error': scraped_data.get('error', 'Unknown error')
        }

    # Extract personalization with AI
    personalization_result = extract_personalization(company_name, scraped_data, api_key)

    return {
        **lead,
        'personalization': personalization_result.get('personalization'),
        'personalization_confidence': personalization_result.get('confidence'),
        'personalization_source': personalization_result.get('source'),
        'personalization_status': personalization_result.get('status'),
        'pages_scraped': scraped_data.get('pages_scraped', 0)
    }


def enrich_leads(input_file, output_file, report_file, batch_size=5, delay=0.5):
    """
    Enrich all leads with personalization data.

    Args:
        input_file (str): Path to input JSON file with leads
        output_file (str): Path to output JSON file with enriched leads
        report_file (str): Path to enrichment report JSON file
        batch_size (int): Number of concurrent enrichment tasks
        delay (float): Delay between page requests

    Returns:
        dict: Enrichment summary with statistics
    """
    # Check API key
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

    # Pre-filter: separate leads with and without websites
    leads_with_website = []
    leads_without_website = []

    for lead in leads:
        website = lead.get("company_website") or lead.get("website") or ""
        if website and website.strip():
            leads_with_website.append(lead)
        else:
            # Mark as no_website upfront
            leads_without_website.append({
                **lead,
                'personalization': None,
                'personalization_status': 'no_website'
            })

    print(f"🎯 Enriching {len(leads)} leads with personalization data...")
    print(f"   Leads with websites: {len(leads_with_website)}")
    print(f"   Leads without websites: {len(leads_without_website)} (skipped)")
    print(f"   Batch size: {batch_size} concurrent tasks")
    print(f"   Page delay: {delay}s between requests")
    print()

    enriched_leads = []
    enrichment_details = []
    stats = {
        "total": len(leads),
        "success": 0,
        "no_website": 0,
        "scrape_failed": 0,
        "no_personalization": 0,
        "high_confidence": 0,
        "medium_confidence": 0,
        "low_confidence": 0
    }

    # Add no_website leads to enriched_leads and details (already processed)
    for lead in leads_without_website:
        company_name = lead.get("company_name_normalized") or lead.get("company_name") or "Unknown"
        stats['no_website'] += 1
        enrichment_details.append({
            'company': company_name,
            'status': 'no_website',
            'personalization': None,
            'confidence': 'none',
            'pages_scraped': 0
        })

    # Process leads with websites in parallel
    with ThreadPoolExecutor(max_workers=batch_size) as executor:
        future_to_lead = {
            executor.submit(enrich_lead, lead, api_key, delay): lead
            for lead in leads_with_website
        }

        for i, future in enumerate(as_completed(future_to_lead), 1):
            enriched_lead = future.result()
            enriched_leads.append(enriched_lead)

            company_name = enriched_lead.get("company_name_normalized") or enriched_lead.get("company_name") or "Unknown"
            status = enriched_lead.get('personalization_status', 'unknown')
            personalization = enriched_lead.get('personalization')
            confidence = enriched_lead.get('personalization_confidence', 'none')

            # Update stats
            if status == 'no_website':
                stats['no_website'] += 1
                icon = "⚠️"
            elif status == 'scrape_failed':
                stats['scrape_failed'] += 1
                icon = "❌"
            elif status == 'success' and personalization:
                stats['success'] += 1
                if confidence == 'high':
                    stats['high_confidence'] += 1
                    icon = "✅"
                elif confidence == 'medium':
                    stats['medium_confidence'] += 1
                    icon = "✅"
                else:
                    stats['low_confidence'] += 1
                    icon = "⚠️"
            else:
                stats['no_personalization'] += 1
                icon = "⚠️"

            # Store enrichment details
            enrichment_details.append({
                'company': company_name,
                'status': status,
                'personalization': personalization,
                'confidence': confidence,
                'pages_scraped': enriched_lead.get('pages_scraped', 0)
            })

            # Print progress
            preview = personalization[:60] + "..." if personalization and len(personalization) > 60 else personalization or "None"
            print(f"   {icon} [{i}/{len(leads_with_website)}] {company_name}: {preview}")

    # Add no_website leads to final output
    enriched_leads.extend(leads_without_website)

    # Calculate percentages
    success_percentage = (stats['success'] / len(leads) * 100) if len(leads) > 0 else 0

    # Create report
    report = {
        "status": "success",
        "statistics": {
            **stats,
            "success_percentage": round(success_percentage, 1)
        },
        "enrichment_details": enrichment_details
    }

    # Save enriched leads
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".tmp", exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(enriched_leads, f, indent=2, ensure_ascii=False)

    # Save report
    os.makedirs(os.path.dirname(report_file) if os.path.dirname(report_file) else ".tmp", exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "="*60)
    print(f"📊 Personalization Enrichment Summary:")
    print(f"   Total leads: {stats['total']}")
    print(f"   ✅ Personalization found: {stats['success']} ({success_percentage:.1f}%)")
    print(f"      - High confidence: {stats['high_confidence']}")
    print(f"      - Medium confidence: {stats['medium_confidence']}")
    print(f"      - Low confidence: {stats['low_confidence']}")
    print(f"   ⚠️  No personalization: {stats['no_personalization']}")
    print(f"   ⚠️  No website: {stats['no_website']}")
    print(f"   ❌ Scrape failed: {stats['scrape_failed']}")
    print(f"\n   Enriched leads saved to: {output_file}")
    print(f"   Report saved to: {report_file}")

    return report


def main():
    parser = argparse.ArgumentParser(description="Enrich leads with personalization data from their websites")
    parser.add_argument("--input", required=True, help="Input JSON file with leads")
    parser.add_argument("--output", required=True, help="Output JSON file for enriched leads")
    parser.add_argument("--report", default=".tmp/personalization_report.json", help="Enrichment report output file")
    parser.add_argument("--batch-size", type=int, default=15, help="Number of concurrent enrichment tasks (default: 15)")
    parser.add_argument("--delay", type=float, default=0.2, help="Delay between page requests in seconds (default: 0.2)")

    args = parser.parse_args()

    result = enrich_leads(
        input_file=args.input,
        output_file=args.output,
        report_file=args.report,
        batch_size=args.batch_size,
        delay=args.delay
    )

    # Print result as JSON
    print("\n" + "="*60)
    print(json.dumps({k: v for k, v in result.items() if k != "enrichment_details"}, indent=2))

    # Exit with appropriate code
    sys.exit(0 if result.get("status") == "success" else 1)


if __name__ == "__main__":
    main()

# Lead Generation Workflow

## Goal
Scrape leads from a specified industry using Apify, validate lead quality with AI, verify email deliverability, enrich with personalized website data, segment by personalization status (for bifurcated campaign strategy), optionally segment by job title, export to Google Sheets, and automatically create Instantly campaigns with AI-generated copy based on high-performing templates.

## Quick Start Guide

**How to run this workflow in a new chat:**

1. **Start with your requirements** - Tell Claude:
   ```
   "Run the lead generation workflow for [INDUSTRY] companies that fit:
   - Industry: [specific niche]
   - Company Size: [X-Y employees]
   - Revenue: [$X-$Y]
   - Location: [region/country]
   - Keywords: [relevant keywords for targeting]
   - Job Titles: [CEO, Founder, etc.]
   - ICP Description: [Detailed description of ideal customer]
   - Scrape [NUMBER] leads

   My offer is: [Your offer/value proposition]"
   ```

2. **Claude will automatically**:
   - Scrape a 25-lead test batch
   - Validate quality (needs 80%+ match rate)
   - If validation passes → scrape full amount
   - Normalize company names
   - Verify email addresses (AnyMailFinder)
   - Enrich with personalization (website scraping + AI)
   - Segment by personalization status (personalized vs non-personalized)
   - Optionally segment leads by job title (if multi-segment campaigns needed)
   - Export to Google Sheets
   - Ask for your offer details
   - Generate email campaign copy
   - Create Instantly campaigns (separate campaigns for personalized/non-personalized segments)
   - Upload leads to respective campaigns

3. **You'll receive**:
   - Google Sheet link with all leads
   - Multiple Instantly campaign IDs (personalized segment, non-personalized segment, and optional job title segments)
   - Upload confirmation for all segments

**Example prompt**:
```
Run the lead generation workflow for HVAC companies:
- Industry: HVAC installation & maintenance
- Company Size: 10-50 employees
- Revenue: $1M-$10M
- Location: United Kingdom
- Keywords: heating, ventilation, air conditioning, HVAC service
- Job Titles: CEO, Founder, Managing Director, Operations Director
- ICP Description: Companies struggling with lead generation, have tried paid ads without success, need consistent pipeline of qualified opportunities
- Scrape 500 leads

My offer is: Free HVAC system audit worth £500 + financing options
```

**Important**: Make sure you provide your **offer/value proposition** so Claude can generate proper email campaign copy!

## Inputs
- **Industry**: Target industry/niche to scrape (e.g., "SaaS startups", "Real estate agencies", "Dental practices")
- **Location** (optional): Geographic filter
- **Employee count** (optional): Company size range (e.g., "10-50", "50-200")
- **Revenue** (optional): Annual revenue range (e.g., "$1M-$10M")
- **ICP Description** (optional): Detailed paragraph describing ideal customer characteristics, firmographics, pain points
- **Job Titles** (optional): Target decision-maker roles (e.g., "CEO, Founder, Managing Director")
- **Total leads desired**: Full amount to scrape (default: 100)
- **Test batch size**: Number of leads for test run (default: 15)
- **Quality threshold**: Minimum percentage of valid leads to proceed (default: 80%)
- **Offers**: List of offers/products to create campaigns for (e.g., ["Product A", "Service B"])
- **Campaign knowledge base**: Path to file with high-performing email copy examples

## Process Flow

**Standard Workflow Order:**
1. Scrape test batch (25 leads)
2. Validate quality (80% threshold)
3. Scrape full batch
4. Validate full batch
5. Filter invalid leads
6. Normalize company names
7. Verify email addresses
8. Enrich with personalization
9. **Segment by personalization status** (personalized vs non-personalized)
10. Export to Google Sheets (optional)
11. Optionally segment by job title (within personalization segments)
12. Generate campaign copy (separate for each segment)
13. Create Instantly campaigns (one per segment)
14. Upload leads to respective campaigns

**Key Decision Point:**
After Step 9, you have two lead segments ready for different campaign strategies:
- **Personalized segment** (typically 40-60%): Higher quality prospects with documented achievements
- **Non-personalized segment** (typically 40-60%): Generic approach for companies without visible achievements

### Step 1: Test Run Scraping
**Tool**: `execution/scrape_leads_direct_api.py`

**Action**: Scrape EXACTLY 25 leads (no more, no less) using Apify's direct API endpoint
- Use the direct API endpoint: `https://api.apify.com/v2/acts/code_crafter~leads-finder/run-sync-get-dataset-items`
- Set maxResults to exactly 25 for test run
- Apply industry filters based on user input
- Save results to `.tmp/test_leads.json`
- DO NOT use Google Maps scraper for this workflow

**Expected output**: JSON file with ~25 leads containing:
- Company name
- Industry/category
- Website
- Contact info (if available)
- Location

### Step 2: Quality Validation
**Tool**: `execution/validate_lead_quality.py`

**Action**: Use AI to validate that scraped leads match the full ICP (Ideal Customer Profile)
- Read `.tmp/test_leads.json`
- Validates leads in batches of 10 (faster than sequential validation)
- For each lead, validate against ALL ICP criteria (not just industry)
- AI analyzes company description, keywords, firmographics, and optionally website content
- Calculate percentage of valid leads
- Save validation report to `.tmp/validation_report.json`

**Performance**: Batch processing validates 20 leads per API call (optimized for large batches), reducing validation time by 80-85%

**ICP validation criteria**:
- **Industry/niche**: Does the company operate in the target industry?
- **Location**: Is the company in the target geography (country, region, state)?
- **Employee count**: Does the company size match the target range?
- **Revenue**: Is the annual revenue within the target range?
- **Job title**: Does the contact's job title match target decision-maker roles?
- **ICP description**: Does the company match the detailed ICP description (firmographics, characteristics, pain points)?
- **Overall fit**: Does the firmographic profile match the ICP?

**Validation modes**:
- **Standard** (default): Validates using data from Apify (company description, keywords, industry, location, employees, revenue)
- **Web-enriched** (optional): Also fetches company websites to gather additional context for validation. Use `--enrich-web` flag to enable (slower but more accurate).

**Usage examples**:
```bash
# Standard validation with multiple ICP criteria
python validate_lead_quality.py \
  --input .tmp/test_leads.json \
  --icp-industry "HVAC companies" \
  --icp-location "United States" \
  --icp-employees "50-200" \
  --icp-revenue "$1M-$50M" \
  --threshold 80

# With detailed ICP description and job title filtering
python validate_lead_quality.py \
  --input .tmp/test_leads.json \
  --icp-industry "HVAC companies" \
  --icp-location "United States" \
  --icp-description "Companies struggling with lead generation, have tried paid ads without success, need consistent pipeline of qualified opportunities" \
  --icp-job-title "CEO, Founder, Managing Director, Operations Director" \
  --threshold 80

# With website enrichment (slower but more accurate)
python validate_lead_quality.py \
  --input .tmp/test_leads.json \
  --icp-industry "HVAC companies" \
  --enrich-web \
  --threshold 80
```

**Decision point**:
- If ≥80% valid → Proceed to Step 3
- If <80% valid → Return to Step 1 with adjusted filters

### Step 3: Full Scraping
**Tool**: `execution/scrape_leads_direct_api.py`

**Action**: If quality check passes (≥80%), scrape the full amount requested by user
- Use the EXACT same query that passed validation
- Set maxResults to the total number requested by user (e.g., 10)
- Save results to `.tmp/full_leads.json`

### Step 3b: Quality Validation (Full Scrape)
**Tool**: `execution/validate_lead_quality.py`

**Action**: Validate ALL full scraped leads against ICP (80% threshold)
- Read `.tmp/full_leads.json`
- For each lead, validate against ALL ICP criteria
- Calculate percentage of valid leads
- Save validation report to `.tmp/full_validation_report.json`

**Validation threshold**: 80% (lower than test run to allow slightly weaker matches)

**Usage**:
```bash
python validate_lead_quality.py \
  --input .tmp/full_leads.json \
  --icp-industry "HVAC companies" \
  --icp-location "United States" \
  --icp-employees "50-200" \
  --icp-revenue "$1M-$50M" \
  --icp-description "Companies struggling with lead generation, have tried paid ads without success" \
  --icp-job-title "CEO, Founder, Managing Director, Operations Director" \
  --threshold 80 \
  --output .tmp/full_validation_report.json
```

**Note**: This is informational - workflow continues regardless of threshold pass/fail

### Step 3c: Filter Invalid Leads
**Tool**: `execution/filter_validated_leads.py`

**Action**: Remove leads that failed ICP validation
- Read `.tmp/full_leads.json` and `.tmp/full_validation_report.json`
- Filter out leads marked as invalid (valid: false)
- Save filtered leads to `.tmp/full_leads_filtered.json`
- Generate filter report with removal statistics

**Usage**:
```bash
python filter_validated_leads.py \
  --input .tmp/full_leads.json \
  --validation .tmp/full_validation_report.json \
  --output .tmp/full_leads_filtered.json \
  --report .tmp/filter_report.json
```

**Expected output**: JSON file with only valid leads (≥80% ICP match) + filter statistics report

**Decision point**:
- If <50% valid → Hard stop, ask user to review ICP criteria
- If 50-80% → Log warning but continue
- If ≥80% → Proceed normally

### Step 4: Normalize Company Names
**Tool**: `execution/normalize_company_names.py`

**Action**: Use AI to normalize company names to friendly, readable versions
- Read `.tmp/full_leads_filtered.json` (CHANGED: now uses filtered leads)
- Extract unique company names
- Use AI to remove legal suffixes (Ltd, LLC, PLC, etc.) and create clean names
- Processes 50 names per API call (batch size optimized for speed)
- Add `company_name_normalized` field to each lead
- Save results to `.tmp/full_leads_normalized.json`

**Performance**: Batch size of 50 (up from 20) reduces API calls by 60% with no quality tradeoff

**Example transformations**:
- "SOLAR INNOVATIONS LTD" → "Solar Innovations"
- "ABC Renewable Energy Solutions Ltd" → "ABC Renewable Energy"
- "Green Power Group PLC" → "Green Power"

### Step 5: Verify Email Addresses
**Tool**: `execution/verify_emails.py`

**Action**: Verify all email addresses using AnyMailFinder API to ensure deliverability
- Read `.tmp/full_leads_normalized.json`
- Verify each email address via AnyMailFinder API
- Filter out leads with invalid or undeliverable emails
- Optionally keep "risky" emails (default: remove)
- Save verified leads to `.tmp/full_leads_verified.json`
- Generate verification report with statistics

**API Details**:
- Uses AnyMailFinder v5.1 API endpoint: `https://api.anymailfinder.com/v5.1/verify-email`
- Requires `ANYMAILFINDER_API_KEY` in `.env` file
- Parallel verification (5 concurrent requests by default)
- Automatic retry logic with exponential backoff for rate limits
- 180-second timeout per verification

**Email Status Values**:
- **valid**: Email is deliverable and verified (KEEP)
- **risky**: Email may exist but verification is inconclusive (OPTIONAL: keep with `--keep-risky` flag)
- **invalid**: Email is not deliverable or doesn't exist (REMOVE)

**Usage**:
```bash
# Standard verification (removes risky emails)
python verify_emails.py \
  --input .tmp/full_leads_normalized.json \
  --output .tmp/full_leads_verified.json \
  --report .tmp/verification_report.json

# Keep risky emails (less strict filtering)
python verify_emails.py \
  --input .tmp/full_leads_normalized.json \
  --output .tmp/full_leads_verified.json \
  --keep-risky \
  --batch-size 10
```

**Performance**: Parallel verification (5 concurrent requests) processes ~300 emails/minute

**Pricing**: 0.2 credits per verification; repeated verifications within 30 days are free

**Expected output**:
- `.tmp/full_leads_verified.json` - Leads with verified emails only
- `.tmp/verification_report.json` - Verification statistics and details

**Decision point**:
- If <50% valid emails → Consider data quality issues with scraping source
- If 50-70% valid → Normal for cold leads, proceed
- If >70% valid → Good quality, proceed normally

### Step 6: Enrich with Personalization Data
**Tool**: `execution/enrich_personalization.py`

**Action**: Extract personalized opening lines from company websites
- Input: `.tmp/full_leads_verified.json`
- Output: `.tmp/full_leads_personalized.json` with personalization data
- Report: `.tmp/personalization_report.json` with statistics

**What it does**:
- Scrapes company websites to find specific client names, projects, or achievements
- Returns 10-12 word matter-of-fact personalization (no enthusiasm)
- Automatically handles blocked sites with Firecrawl fallback

**Personalization quality priorities**:
1. Best: Specific client names or project names (e.g., "Hope T.'s estate sale")
2. Fallback: Awards, certifications, milestones (e.g., "20-year anniversary")
3. Fallback: Recent news or expansions (e.g., "expansion to three locations")
4. Last resort: Industry niche (e.g., "focus on estate liquidations")

**Usage**:
```bash
python enrich_personalization.py \
  --input .tmp/full_leads_verified.json \
  --output .tmp/full_leads_personalized.json \
  --report .tmp/personalization_report.json \
  --batch-size 30 \
  --delay 0.2
```

**Expected performance**:
- Speed: ~30-60 leads/minute
- Success rate: 70-85% (Firecrawl handles blocked sites automatically)
- Cost: ~$0.50-$2.00 per 1000 leads (Firecrawl only used for blocked sites)

**Expected output**:
- `.tmp/full_leads_personalized.json` - Leads with personalization data added
- `.tmp/personalization_report.json` - Statistics (success rate, confidence breakdown)

**Decision point**:
- If >70% success → Excellent, proceed
- If 50-70% success → Good, proceed
- If <50% success → Check `FIRECRAWL_API_KEY` in `.env`, review error report

### Step 6.5: Segment by Personalization Status
**Tool**: `execution/segment_by_personalization.py`

**Action**: Split leads into personalized and non-personalized segments for different campaign strategies
- Input: `.tmp/full_leads_personalized.json`
- Output: `.tmp/personalized_segment.json` and `.tmp/non_personalized_segment.json`

**What it does**:
- Filters leads with successful personalization into one file
- Filters leads without personalization into another file
- Allows running different campaign strategies for each segment

**Usage**:
```bash
python segment_by_personalization.py \
  --input .tmp/full_leads_personalized.json \
  --personalized-output .tmp/personalized_segment.json \
  --non-personalized-output .tmp/non_personalized_segment.json
```

**Strategy**:
- **Personalized leads** (typically 40-60%): Upload to Campaign A with highly personalized messaging
- **Non-personalized leads** (typically 40-60%): Upload to Campaign B with different approach (generic messaging, different offer, etc.)

**Expected output**:
- `.tmp/personalized_segment.json` - Leads with personalization field populated
- `.tmp/non_personalized_segment.json` - Leads without personalization
- Both files ready for separate campaign uploads

**Why this matters**:
Companies with successful personalization are better prospects (they publicize achievements, have quality websites, are likely more established and ready for your services). Segmenting allows you to prioritize and tailor outreach accordingly.

### Step 7: Segment by Job Title (Optional)
**Tool**: `execution/segment_by_job_title.py`

**Action**: OPTIONAL - Use AI to cluster job titles into functional segments for multi-dimensional segmentation
- Input: `.tmp/personalized_segment.json` OR `.tmp/non_personalized_segment.json` (or both separately)
- Can be run on either segment independently if you want job title segmentation within personalization segments
- Extract unique job titles
- Use Claude AI to group into 3-6 low-cardinality segments by business function
- Split leads into segment-specific files
- Save segment mapping for downstream use

**When to use this step**:
- Skip if you only want personalization-based segmentation (most common)
- Use if you want additional segmentation by job role WITHIN each personalization segment
- Example: Personalized leads → split into Executive/Operations/Marketing sub-segments

**Segmentation criteria**:
- **Low cardinality**: 3-6 segments total (e.g., Executive, Operations, Marketing, Sales)
- **Functional grouping**: All marketing roles together (CMO + VP Marketing + Marketing Director = "Marketing Leadership")
- **Messaging angles**: Each segment gets tailored messaging approach
  - Executive: Revenue growth, strategic outcomes
  - Operations: Efficiency + revenue impact
  - Marketing: Lead generation ROI, brand growth
  - Sales: Pipeline, conversion, revenue
  - Technical: Innovation, scalability

**Usage**:
```bash
python segment_by_job_title.py \
  --input .tmp/full_leads_personalized.json \
  --output-mapping .tmp/segment_mapping.json \
  --output-dir .tmp \
  --min-segment-size 10
```

**Expected output**:
- `.tmp/segment_mapping.json` - Segment definitions with job title mappings
- `.tmp/segment_{id}_leads.json` - One file per segment with leads
- Segments with <10 leads are merged into "Executive" segment (configurable)

**Edge cases**:
- Missing job titles → Assigned to "Executive" segment by default
- Uncommon job titles → AI assigns to best-fit segment
- All segments too small → Fallback to single "General" segment
- AI clustering fails → Uses heuristic fallback (C-level vs Directors vs Managers)

### Step 8: Export to Google Sheets (Optional)
**Tool**: `execution/export_to_sheets.py`

**Action**: OPTIONAL - Create a new Google Sheet with all leads including personalization and segment identifiers
- Create a new sheet with timestamp in name (e.g., "Leads - HVAC - 2024-12-12")
- Format with headers: Company Name, Company (Friendly), **Segment**, **Job Title**, Industry, Website, Email, Phone, Location, LinkedIn, Description
- The "Segment" column shows which functional segment the lead belongs to (e.g., "Executive Leadership")
- The "Job Title" column shows the original job title from lead data
- Apply basic formatting (frozen header row, auto-sized columns, bold headers)
- Return the shareable link

**Performance**: Automatically uses batch API for datasets >1000 rows, reducing export time by 60% for large batches

**Usage**:
```bash
python export_to_sheets.py \
  --input .tmp/full_leads_normalized.json \
  --segments .tmp/segment_mapping.json \
  --title "Leads - HVAC - 2024-12-12"
```

**New columns**:
- **Segment**: Shows functional segment (e.g., "Executive Leadership", "Operations Leadership")
- **Job Title**: Shows original job title (e.g., "CEO", "VP Operations")

### Step 9: Generate Campaign Copy for Personalization Segments
**Tool**: `execution/generate_campaigns_parallel.py`

**Action**: Generate email campaign copy for personalized and non-personalized segments (minimum 2 campaigns)
- Read high-performing email examples from knowledge base file (if available)
- Create campaign copy for personalized segment (uses {{personalization}} variable)
- Create campaign copy for non-personalized segment (generic industry-focused approach)
- Optionally read job title segment definitions from `.tmp/segment_mapping.json` if using job title segmentation
- For each offer, for each segment, generate tailored campaign copy
- Use AI to adapt messaging based on segment's priorities and role
- Save generated copy to `.tmp/campaign_copy_{offer}_{segment}.json`
- **CRITICAL**: Use camelCase for Instantly variables: `{{firstName}}`, `{{lastName}}`, `{{companyName}}`, `{{senderName}}` (NOT snake_case)
- **Email Formatting**: Uses HTML formatting with `<br><br>` for paragraph spacing and `<br>` for line breaks (ensures proper rendering in email clients)

**Performance**: Generates multiple campaigns concurrently (50% faster than sequential generation)

**Segment-specific messaging**:
- **Executive/C-Suite**: Focus on revenue growth, strategic outcomes, high-level ROI
- **Operations**: Emphasize efficiency gains, cost savings, operational impact + revenue
- **Marketing**: Lead generation, conversion rates, brand growth, marketing ROI
- **Sales**: Pipeline acceleration, quota attainment, revenue growth

**Usage**:
```bash
# Generate campaigns for both personalized and non-personalized segments
python generate_campaigns_parallel.py \
  --config campaign_config.json \
  --output-dir .tmp
```

**Config file example** (`campaign_config.json`):
```json
{
  "segments": [
    {
      "name": "personalized",
      "offer": "AI Automation",
      "industry": "Various",
      "angle": "Personalized approach with specific achievements"
    },
    {
      "name": "non_personalized",
      "offer": "AI Automation",
      "industry": "Various",
      "angle": "Generic industry-focused approach"
    }
  ]
}
```

**Expected output**: Multiple JSON files (one per offer × segment)
- Campaign name (includes segment, e.g., "Product A - Executive Leadership - HVAC")
- Subject line variants
- Email sequence (3-5 emails)
- Personalization variables in camelCase format
- Segment metadata

### Step 10: Create Campaigns for Each Segment
**Tool**: `execution/create_instantly_campaigns.py`

**Action**: Create Instantly campaigns for personalized and non-personalized segments via Instantly V2 API
- Minimum: 2 campaigns (personalized segment + non-personalized segment)
- Optional: Additional campaigns if using job title segmentation within personalization segments
- For each segment-specific campaign copy file, create a campaign
- Upload AI-generated email sequences
- Configure campaign settings (send schedule, delays, timezone)
- Campaign schedule requires "Atlantic/Canary" timezone
- Campaign names automatically include segment identifier
- Save campaign IDs to `.tmp/campaign_ids.json`

**Usage**:
```bash
python create_instantly_campaigns.py \
  --campaign-copy \
    .tmp/campaign_copy_product_a_exec.json \
    .tmp/campaign_copy_product_a_operations.json \
    .tmp/campaign_copy_product_a_marketing.json \
  --output .tmp/campaign_ids.json
```

**Result**: Multiple campaigns created based on segmentation strategy
- Basic segmentation (2 campaigns):
  - "AI Automation - Personalized Segment"
  - "AI Automation - Generic Segment"
- With job title segmentation (4+ campaigns):
  - "AI Automation - Personalized - Executive Leadership"
  - "AI Automation - Personalized - Operations Leadership"
  - "AI Automation - Generic - Executive Leadership"
  - "AI Automation - Generic - Operations Leadership"

**API endpoint**: `POST https://api.instantly.ai/api/v2/campaigns`

**Required fields**:
- `name`: Campaign name (includes segment)
- `campaign_schedule`: Object with schedules array (timing, days, timezone)
- `sequences`: Array of email sequence steps

### Step 11: Upload Leads to Respective Campaigns

**Tools**:
- `execution/add_personalization_to_campaign.py` - For personalized segment
- `execution/add_leads_to_instantly.py` - For non-personalized segment
- `execution/add_leads_to_campaigns_segmented.py` - For job title segments (optional)

**Action**: Upload segmented leads to their respective campaigns
- Upload `.tmp/personalized_segment.json` to personalized campaign
- Upload `.tmp/non_personalized_segment.json` to non-personalized campaign
- If using job title segmentation, upload segment-specific files to matching campaigns using `add_leads_to_campaigns_segmented.py`
- Read campaign IDs from `.tmp/campaign_ids.json`
- Read segment mapping from `.tmp/segment_mapping.json`
- For each campaign, identify its segment from campaign name
- Load ONLY that segment's leads
- Upload segment-specific leads in batches of 100 (parallel processing)

**Performance**: Batches are uploaded concurrently using ThreadPoolExecutor (5 workers), reducing upload time by 75% for large batches

**Key difference from simple upload**: Each campaign receives ONLY the leads from its matching segment
- "Product A - Executive Leadership" campaign → receives only `.tmp/segment_exec_leads.json`
- "Product A - Operations Leadership" campaign → receives only `.tmp/segment_operations_leads.json`

**Usage**:
```bash
python add_leads_to_campaigns_segmented.py \
  --campaigns .tmp/campaign_ids.json \
  --segments .tmp/segment_mapping.json \
  --leads-dir .tmp \
  --output .tmp/upload_report.json
```

**Campaign-to-segment matching**:
- Extracts segment name from campaign name
- Matches to segment_id in mapping
- Loads corresponding `segment_{id}_leads.json` file
- Uploads only those leads to that campaign

**Edge cases**:
- Campaign name doesn't match any segment → Skip with warning
- Segment leads file missing → Error and skip campaign
- Segment has 0 leads → Skip upload, log warning

**API endpoint**: `POST https://api.instantly.ai/api/v2/leads/add`

**Request format** (snake_case field names):
```json
{
  "campaign_id": "campaign-uuid",
  "leads": [
    {
      "email": "contact@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "company_name": "Example Corp",
      "website": "https://example.com",
      "personalization": "Example Corp"
    }
  ]
}
```

## Outputs
- **Deliverables**:
  - Google Sheet link with all validated leads (includes "Segment" and "Job Title" columns)
  - Instantly campaign links (one per offer × segment)
- **Intermediate files** (in `.tmp/`):
  - `test_leads.json` - Initial test batch (25 leads)
  - `validation_report.json` - Test validation results (80% threshold)
  - `full_leads.json` - Full scrape results
  - **`full_validation_report.json`** - Full scrape validation (80% threshold)
  - **`full_leads_filtered.json`** - Leads after removing invalid entries
  - **`filter_report.json`** - Filter statistics and removal reasons
  - `full_leads_normalized.json` - Filtered leads with AI-normalized company names
  - **`full_leads_verified.json`** - Verified leads with valid email addresses only
  - **`verification_report.json`** - Email verification statistics and details
  - **`full_leads_personalized.json`** - Verified leads with personalization data
  - **`personalization_report.json`** - Personalization enrichment statistics
  - **`personalized_segment.json`** - Leads with successful personalization (for Campaign A)
  - **`non_personalized_segment.json`** - Leads without personalization (for Campaign B)
  - **`segment_mapping.json`** - Segment definitions and job title mappings
  - **`segment_exec_leads.json`** - Executive segment leads
  - **`segment_operations_leads.json`** - Operations segment leads
  - **`segment_marketing_leads.json`** - Marketing segment leads
  - **`segment_{id}_leads.json`** - Additional segments as generated
  - **`campaign_copy_{offer}_{segment}.json`** - Segment-specific campaign copy (e.g., `campaign_copy_product_a_exec.json`)
  - `campaign_ids.json` - Instantly campaign IDs and links (multiple campaigns)
  - `upload_report.json` - Segmented lead upload results

## Edge Cases & Error Handling

### Apify API Issues
- **Free tier limitation**: Apify free plan only allows running actors through the UI, NOT via API. User must have a paid Apify plan or manually export leads from Apify UI to `.tmp/test_leads.json`
- **Rate limiting**: If rate limited, wait and retry with exponential backoff
- **Actor timeout**: Increase timeout parameter or reduce batch size
- **No results**: Check if filters are too restrictive, suggest broadening search

### Quality Validation Issues
- **Anthropic API credits exhausted**: User needs to add credits at https://console.anthropic.com/settings/billing. Alternative: Skip validation and proceed directly to Google Sheets for manual review
- **All leads invalid**: Leads don't match ICP criteria. Suggestions:
  - Check if ICP criteria are too restrictive (try broader location, wider revenue range)
  - Review Apify search keywords and industry filters
  - Check validation report in `.tmp/validation_report.json` to see why leads failed
  - Consider using `--enrich-web` flag to fetch websites for better validation context
- **Low quality (30-70%)**: Partial match - some leads are valid but many aren't. Options:
  - Refine Apify search filters to better target the ICP
  - Adjust ICP criteria if they're too narrow
  - Review individual validation reasons in the report
  - Proceed with valid leads only if acceptable
- **Borderline quality (70-80%)**: Ask user if they want to proceed or refine filters
- **Validation API failure**: Fall back to manual review by showing sample leads
- **Website enrichment slow**: Using `--enrich-web` significantly increases validation time (10s per lead). Only use when standard validation is insufficient
- **ICP mismatch**: If scraped leads don't match expected ICP, the Apify query or industry filters may be incorrect

### Email Verification Issues
- **AnyMailFinder API key missing**: Check `ANYMAILFINDER_API_KEY` in `.env` file. Get API key from https://anymailfinder.com/
- **Authentication failure (401)**: Invalid API key - verify key is correct in `.env`
- **Rate limiting (429)**: Script automatically retries with exponential backoff. If persistent, reduce `--batch-size` parameter
- **Timeout errors**: AnyMailFinder uses 180-second timeout for SMTP verification. Timeouts are normal for ~5-10% of emails
- **Low verification rate (<50%)**: Possible causes:
  - Poor data quality from scraping source
  - Many disposable/temporary emails in dataset
  - Company email servers blocking verification attempts
  - Consider using `--keep-risky` flag to retain borderline emails
- **All emails invalid**: Check if leads have valid email format. Review `.tmp/verification_report.json` for details
- **High cost**: Verification costs 0.2 credits per email. Repeated verifications within 30 days are free. Consider budget before verifying large batches

### Personalization Enrichment Issues
- **Low success rate (<50%)**: With Firecrawl fallback, you should get 70-85% success. If lower:
  - Check `FIRECRAWL_API_KEY` is set correctly in `.env` file
  - Verify Firecrawl API key is valid at https://firecrawl.dev/
  - Check `.tmp/personalization_report.json` for Firecrawl error messages
  - If Firecrawl is working but success still low, websites may have minimal content
- **Firecrawl not being used**: Check for blocked sites in report
  - Blocked sites should automatically trigger Firecrawl fallback
  - Look for "Firecrawl fallback failed" messages in console output
  - Verify API key format starts with `fc-` prefix
- **Firecrawl costs higher than expected**:
  - Firecrawl charges $0.003 per page scraped (~$3 per 1000 pages)
  - Only triggers for blocked sites (typically 5-15% of total)
  - Expected cost: ~$0.50-$2.00 per 1000 leads
  - Monitor usage at https://firecrawl.dev/dashboard
- **Many timeouts**: Slow website response times
  - Normal for ~5-10% of sites with optimized settings
  - Script automatically skips after 5-second timeout
  - Timeouts reduced from 10s to 5s for faster processing
- **AI extraction fails**: Anthropic API issues or rate limits
  - Check `ANTHROPIC_API_KEY` in `.env` file
  - Review `.tmp/personalization_report.json` for error details
  - Script continues and marks personalization as unavailable
- **No website URLs in leads**: Leads missing `company_website` field
  - Check Apify scraper is configured to capture website URLs
  - Leads without websites will skip personalization enrichment
- **Personalizations too generic**: AI finding fallback content instead of Priority 1
  - This is expected for ~30-40% of leads (Priority 2-4 fallbacks)
  - Websites may lack client testimonials or case studies
  - Generic personalizations still better than no personalization
  - High-confidence (Priority 1) should be 40-60% of successful extractions

### Google Sheets Issues
- **Authentication failure**: Check `credentials.json` and `token.json` exist
- **Permission denied**: Ensure OAuth scopes include Sheets write access
- **Quota exceeded**: Wait and retry, or batch the upload

### Instantly API Issues
- **Authentication failure**: Check `INSTANTLY_API_KEY` in `.env` file. V2 API requires both `Authorization: Bearer <key>` and `x-api-key: <key>` headers
- **Rate limiting**: Implement exponential backoff (wait 5s, 10s, 20s between retries)
- **Campaign creation fails**:
  - Check campaign name uniqueness and API quotas
  - Ensure `campaign_schedule` object is included with valid timezone
  - Use "Atlantic/Canary" timezone (not "Europe/London" or other standard timezones)
  - Verify schedules array has timing, days, and timezone fields
- **Lead upload fails**:
  - Verify email format and required fields (email, first_name)
  - Ensure using correct V2 endpoint: `POST /api/v2/leads/add`
  - Request must include `campaign_id` and `leads` array
  - Check batch size (max 100 leads per request recommended)
  - Leads go to workspace if wrong endpoint used - verify they appear IN the campaign
- **Duplicate leads**: Instantly will skip duplicates automatically
- **Invalid email format**: Filter out leads without valid email addresses before upload
- **Wrong endpoint**: V2 endpoints differ from V1 - `/api/v2/leads/add` (not `/api/v1/lead/add`)

### Personalization Segmentation Issues
- **All leads personalized or all non-personalized**: Rare but possible. If <10% in one segment, consider skipping that campaign
- **Personalization field missing**: Check that `enrich_personalization.py` completed successfully
- **Upload to wrong campaign**: Use `add_personalization_to_campaign.py` for personalized segment, `add_leads_to_instantly.py` for non-personalized
- **Non-personalized segment upload fails with personalization script**: Expected - use generic upload script for non-personalized leads

### Job Title Segmentation Issues (Optional Step)
- **No job titles in data**: If leads don't have job_title field, create single "General" segment with all leads
- **AI clustering fails**: Fallback to simple heuristic (C-level vs Director vs Manager vs Individual Contributor)
- **All segments too small**: Lower `--min-segment-size` threshold or use single segment
- **Uncommon job titles**: AI assigns to best-fit segment; if unclear, defaults to "Executive"
- **Segment name mismatch in upload**: Campaign upload may fail if campaign names don't match segment names exactly - ensure campaign names include segment names
- **Empty segments after filtering**: If a segment has no leads after validation filtering, skip campaign creation for that segment

## Utility Scripts (Optional Workflow Tools)

### CSV Import
**Tool**: `execution/convert_csv_to_json.py`

**Purpose**: Import leads from CSV files (Instantly exports, manual lists, etc.)

**Usage**:
```bash
python convert_csv_to_json.py \
  --input leads_export.csv \
  --output .tmp/csv_import_leads.json
```

**When to use**: When you have existing leads from CSV sources instead of Apify scraping

### Update Existing Campaigns
**Tool**: `execution/update_instantly_personalization.py`

**Purpose**: Add personalization to leads already in Instantly campaigns

**How it works**:
1. Fetches existing leads from campaign
2. Matches by email address
3. Deletes + re-adds with personalization data

**Usage**:
```bash
python update_instantly_personalization.py \
  --input .tmp/csv_leads_personalized.json \
  --campaign-id YOUR_CAMPAIGN_ID
```

**When to use**: When you've already uploaded leads but want to add personalization after the fact

### Update Google Sheets
**Tool**: `execution/update_sheet_personalization.py`

**Purpose**: Add personalization column to existing Google Sheets

**Usage**:
```bash
python update_sheet_personalization.py \
  --input .tmp/csv_leads_personalized.json \
  --sheet-id YOUR_SHEET_ID
```

**When to use**: When you have an existing sheet and want to add personalization data

### Debug & Admin Tools
- **`execution/check_instantly_leads.py`** - Inspect lead data in Instantly campaigns (debugging)
- **`execution/delete_instantly_campaign.py`** - Delete campaigns via API (cleanup)
- **`execution/cleanup_old_files.py`** - Remove redundant temporary files (maintenance)

## Filter Adjustment Strategy
When quality < 80%, try these adjustments in order:
1. **Broaden location** (if location filter was used)
2. **Adjust search keywords** (try synonyms or related terms)
3. **Remove optional filters** (focus on core industry match)
4. **Increase result pool** (get more results to filter from)

## Success Metrics
- Test batch quality ≥80%
- Full scrape completes without errors
- Google Sheet created and accessible
- All Instantly campaigns created successfully
- Leads uploaded to all campaigns
- User receives Google Sheet link and campaign links

## Performance Optimizations

The workflow has been optimized for speed while maintaining quality:

### Optimization Summary (1000 leads)
| Step | Original Time | Optimized Time | Improvement |
|------|--------------|----------------|-------------|
| Test scrape (25) | 10-15s | 10-15s | - |
| Test validation (25) | 8-10s | 8-10s | - |
| Full scrape (1000) | 30-60s | 30-60s | - |
| **Full validation (1000)** | **120s** | **60s** | **50% faster** |
| Filter invalid | 2s | 2s | - |
| Normalize names | 60s | 60s | - |
| **Email verification (1000)** | **200s** | **200s** | - |
| **Personalization (1000)** | **N/A** | **3000-6000s** | **NEW** |
| **Segment by personalization** | **N/A** | **2s** | **NEW** |
| Segment by job title (optional) | 10s | 10s | - |
| **Export to Sheets** | **20s** | **8s** | **60% faster** |
| **Generate campaigns (2)** | **30s** | **15s** | **50% faster** |
| Create campaigns | 10s | 10s | - |
| **Upload leads (1000)** | **60s** | **15s** | **75% faster** |
| **TOTAL (without personalization)** | **~6 mins** | **~4 mins** | **~33% faster** |
| **TOTAL (with personalization)** | **N/A** | **~54-104 mins** | **NEW** |

### Key Optimizations
1. **Validation Batching (20 leads/call)** - Validates 20 leads per API call instead of 10, reducing API overhead
2. **Parallel Email Verification** - Verifies 5 emails concurrently (can increase to 10 with `--batch-size` parameter)
3. **Parallel Personalization Enrichment** - Scrapes 5 websites concurrently (can increase to 10 for faster processing)
4. **Parallel Lead Upload** - Uses ThreadPoolExecutor with 5 workers to upload batches concurrently
5. **Batch Sheets Export** - Automatically uses batch API for datasets >1000 rows
6. **Parallel Campaign Generation** - Generates multiple campaign copies concurrently

### For Maximum Speed
- Always use `generate_campaigns_parallel.py` for concurrent campaign generation
- Increase personalization `--batch-size` to 10 for faster enrichment (if websites are responsive)
- Keep web enrichment disabled (default) unless accuracy issues arise
- Validation batch size of 20 is optimal for speed/accuracy balance

### Performance Notes
- **Personalization is the slowest step** (~50-100 minutes for 1000 leads)
  - Each site needs ~10-15 page requests (0.5s delay between requests = 5-7s per site)
  - AI extraction adds ~2-3s per lead
  - Total: ~10-30s per lead depending on website response times
  - Can be skipped if personalization is not critical for your campaign

## Notes
- Always prefer the test-validate-proceed approach to avoid wasting Apify credits
- Store API tokens in `.env`:
  - `APIFY_API_TOKEN` - Apify API key
  - `INSTANTLY_API_KEY` - Instantly.ai API key
  - `ANTHROPIC_API_KEY` - Anthropic API key for validation and copy generation
  - `ANYMAILFINDER_API_KEY` - AnyMailFinder API key for email verification
- Keep intermediate files for debugging until workflow completes
- Log all filter adjustments for future learning
- Campaign copy generation uses the same AI model as validation (cost-efficient)
- Email verification costs 0.2 credits per email; budget accordingly for large batches

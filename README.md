# Lead Gen Workflow (Cold Email via Instantly)

**Automated lead generation workflow that scrapes, validates, personalizes, and launches cold email campaigns in minutes.**

## What Is This?

This is a **3-layer agentic workflow** that automates the entire lead generation process from scraping to campaign launch. Instead of spending hours manually finding leads, verifying emails, and writing personalized outreach—this system does it all automatically using AI orchestration and deterministic Python scripts.

**What makes it different:**
- ✅ **Self-annealing** - Learns from errors and updates itself
- ✅ **Reliable** - Uses deterministic scripts (not pure LLM guessing)
- ✅ **Personalized at scale** - Enriches leads with company-specific achievements
- ✅ **Bifurcated campaigns** - Separate strategies for personalized vs generic leads
- ✅ **Instantly.ai integration** - Automatically creates and populates campaigns

## Quick Start

**Tell the AI agent what you want:**

```
Run the lead generation workflow for HVAC companies in the UK:
- Company Size: 10-50 employees
- Revenue: $1M-$10M
- Total leads: 500
- Offer: AI Automation Implementation
```

**The system will automatically:**
1. Scrape 25 test leads and validate quality (80%+ match required)
2. If quality passes → scrape full 500 leads
3. Verify email deliverability (AnyMailFinder)
4. Enrich with personalization (scrape websites for achievements)
5. Segment into personalized vs non-personalized groups
6. Generate AI campaign copy (separate for each segment)
7. Create 2 Instantly campaigns (one per segment)
8. Upload leads to respective campaigns

**Time:** ~4 minutes without personalization, ~54-104 minutes with personalization (for 1000 leads)

**Result:** Ready-to-launch Instantly campaigns with segmented, verified leads

## Features

### Core Capabilities
- **Smart scraping** - Uses Apify LinkedIn Sales Navigator scraper
- **AI validation** - Claude validates leads match your ICP (80%+ threshold)
- **Email verification** - AnyMailFinder checks deliverability before upload
- **Website personalization** - Scrapes company websites for specific achievements
- **Personalization segmentation** - Splits leads by personalization success (40-60% typically)
- **Optional job title segmentation** - Further segment by role (Executive/Operations/Marketing/Sales)
- **Parallel processing** - Concurrent verification, personalization, and uploads (50-75% faster)
- **AI campaign copy** - Generates email sequences based on your templates
- **Multi-campaign creation** - Creates separate Instantly campaigns per segment
- **Google Sheets export** - Optional export with all lead data

### 3-Layer Architecture

**Why this matters:** LLMs are probabilistic—if each step has 90% accuracy, after 5 steps you only have 59% success (0.9^5). This system fixes that by pushing complexity into deterministic code.

1. **Layer 1: Directives** (`directives/`) - Natural language SOPs (what to do)
2. **Layer 2: Orchestration** - AI agent (intelligent routing and decision-making)
3. **Layer 3: Execution** (`execution/`) - Python scripts (reliable, testable, fast)

### Self-Annealing Loop

When something breaks:
1. AI reads error message
2. Fixes the script
3. Tests the fix
4. Updates the directive with learnings
5. System is now stronger

## API Accounts & Affiliate Links

You'll need API keys from these services:

### Required Services

**1. Apify** (Lead Scraping)
- Get your API token: [Apify Console](https://console.apify.com/account/integrations)
- Affiliate link: `[YOUR_APIFY_AFFILIATE_LINK]`
- Cost: Pay-as-you-go (~$0.01-0.05 per lead depending on filters)

**2. Anthropic Claude** (AI Validation & Campaign Copy)
- Get your API key: [Anthropic Console](https://console.anthropic.com/)
- Affiliate link: `[YOUR_ANTHROPIC_AFFILIATE_LINK]`
- Cost: ~$0.50-2.00 per 1000 leads (validation + copy generation)

**3. Instantly.ai** (Campaign Management)
- Get your API key: [Instantly Settings](https://app.instantly.ai/app/settings/api)
- Affiliate link: `[YOUR_INSTANTLY_AFFILIATE_LINK]`
- Cost: Subscription-based ($37-297/month depending on plan)

**4. AnyMailFinder** (Email Verification)
- Get your API key: [AnyMailFinder Account](https://anymailfinder.com/account.php)
- Affiliate link: `[YOUR_ANYMAILFINDER_AFFILIATE_LINK]`
- Cost: 0.2 credits per email (~$0.002 per verification)

**5. Firecrawl** (Website Personalization)
- Get your API key: [Firecrawl Dashboard](https://firecrawl.dev/)
- Affiliate link: `[YOUR_FIRECRAWL_AFFILIATE_LINK]`
- Cost: Free tier available, then pay-as-you-go

### Optional Services

**6. Google Cloud** (Google Sheets Export - Optional)
- Get OAuth credentials: [Google Cloud Console](https://console.cloud.google.com/)
- Affiliate link: `[YOUR_GOOGLE_CLOUD_AFFILIATE_LINK]`
- Cost: Free for Sheets/Drive API usage

## Installation

### 1. Clone the repository
```bash
git clone [YOUR_GITHUB_REPO_URL]
cd lead-gen-workflow
```

### 2. Create Python virtual environment
```bash
python -m venv venv
```

### 3. Activate virtual environment

**Windows:**
```bash
venv\Scripts\activate
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure environment variables
```bash
# Copy the example template
cp .env.example .env

# Edit .env with your actual API keys
# Use a text editor to add your keys from the services above
```

### 6. (Optional) Set up Google Sheets export
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Google Sheets API and Google Drive API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download `credentials.json` to project root
6. First time you export, it will prompt for authentication

### 7. Run your first workflow

Start Claude Code (or your preferred AI agent) and say:

```
Run the lead generation workflow for [YOUR INDUSTRY] companies:
- Industry: [e.g., HVAC, Solar, SaaS]
- Company Size: [e.g., 10-50 employees]
- Location: [e.g., United Kingdom]
- Total leads: [e.g., 100]
- Offer: [e.g., AI Automation Services]
```

## Directory Structure

```
.
├── directives/              # Markdown SOPs for AI agent
│   └── lead_generation_workflow.md
├── execution/               # Python scripts (19 scripts)
│   ├── scrape_leads_direct_api.py
│   ├── validate_icp_batch.py
│   ├── filter_invalid_leads.py
│   ├── verify_emails_anymailfinder.py
│   ├── enrich_personalization.py
│   ├── segment_by_personalization.py
│   └── ... (13 more scripts)
├── .tmp/                    # Temporary files (auto-generated, not in git)
├── .env                     # Your API keys (NOT in git)
├── .env.example             # Template for API keys
├── credentials.json         # Google OAuth (optional, not in git)
├── requirements.txt         # Python dependencies
├── CLAUDE.md                # AI agent operating instructions
└── README.md                # This file
```

## How It Works

### Process Flow

```
1. Scrape test batch (25 leads)
2. Validate quality with AI (80% threshold)
3. If passed → Scrape full batch
4. Filter invalid leads
5. Normalize company names
6. Verify email addresses
7. Enrich with personalization (website scraping)
8. Segment by personalization status
9. (Optional) Export to Google Sheets
10. (Optional) Segment by job title
11. Generate campaign copy (AI, separate per segment)
12. Create Instantly campaigns (one per segment)
13. Upload leads to respective campaigns
```

### Performance Benchmarks

**For 1000 leads:**
- Without personalization: ~4 minutes total
- With personalization: ~54-104 minutes total
- Personalization is the slowest step (50-100 minutes)

**Optimizations:**
- Parallel email verification (5 concurrent)
- Parallel personalization enrichment (5 concurrent)
- Parallel lead uploads (5 workers, 75% faster)
- Batch Sheets export (60% faster for large datasets)
- Parallel campaign generation (50% faster)

## Key Principles

- **Self-anneal when things break** - Errors are learning opportunities
- **Update directives as you learn** - Living documents that improve over time
- **Deterministic execution** - Push complexity into reliable Python scripts
- **Deliverables in cloud** - Google Sheets/Slides, not local files
- **Intermediates are temporary** - Everything in `.tmp/` can be regenerated

## Customization

### Add Your Own Campaign Templates

Create `knowledge_base/email_templates.md` with your high-performing email examples. The AI will use these as reference when generating new campaign copy.

### Adjust Segmentation

Edit `directives/lead_generation_workflow.md` to:
- Change personalization threshold (default: any lead with personalization data)
- Add custom job title segments (default: Executive/Operations/Marketing/Sales)
- Modify campaign generation strategies per segment

### Create New Workflows

1. Create new directive in `directives/your_workflow.md`
2. Create execution scripts in `execution/`
3. Tell the AI agent to run your new workflow

## Troubleshooting

### Common Issues

**"Quality validation failed (below 80%)"**
- Solution: Broaden your ICP filters or adjust search keywords

**"Email verification rate low"**
- Solution: Check AnyMailFinder credits, verify API key in `.env`

**"Personalization success rate <50%"**
- Solution: Check FIRECRAWL_API_KEY, review error report in `.tmp/personalization_report.json`

**"Campaign upload failed"**
- Solution: Verify INSTANTLY_API_KEY, check campaign IDs in `.tmp/campaign_ids.json`

**"Google Sheets export failed"**
- Solution: Ensure `credentials.json` exists, re-authenticate if needed

## Contributing

When adding new functionality:
1. Create a directive in `directives/` describing the workflow
2. Create execution scripts in `execution/` for reliable operations
3. Update this README if adding new dependencies or setup steps
4. Test with small batch first (25 leads)

## License

[Add your license here]

## Support

Questions or issues? [Add your support contact/link here]

---

**Built with the 3-layer agentic architecture - reliable, self-improving, production-ready.**

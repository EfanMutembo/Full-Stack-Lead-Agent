# Full Stack Lead Gen Agent

![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

## What Is This?

Imagine hiring a dream team to handle your lead generation:

- **A Quality Control Specialist** who scrapes LinkedIn and validates every lead matches your ICP
- **An Email Verification Expert** who checks deliverability so you never hit a spam trap
- **A Research Analyst** who digs through company websites finding achievements and client names
- **A Copywriter** who writes personalized email sequences based on your best-performing templates
- **A Campaign Manager** who sets up your Instantly campaigns and uploads everything

This project brings that dream team to life using AI agents and deterministic automation. Give it your ICP, and watch as it scrapes, validates, personalizes, and launches campaigns automatically.

**The result:** 20+ hours of manual work compressed into 4 minutes. Ready-to-send Instantly campaigns with verified, segmented, personalized leads.

*Built on the DOE (Directives, Orchestration, Execution) framework—shoutout to the architects. Enhanced with self-annealment so it learns from errors and gets smarter over time.*


## What You Get

Tell it your ideal customer profile, and it:

🎯 **Finds your exact ICP** - Scrapes LinkedIn Using APIFY , validates with AI (80%+ match rate)  
✉️ **Verifies every email** - No bounces, no spam traps, only deliverable addresses  
🌐 **Personalizes at scale** - Scrapes company websites for achievements, awards, client names  
📊 **Segments intelligently** - Splits personalized vs generic leads for different campaign strategies  
📝 **Writes your campaigns** - AI generates email sequences based on your proven templates  
⚡ **Launches in Instantly** - Creates campaigns, uploads leads, ready to send  

**One command. Minutes later, you're ready to launch.**

## Quick Start

### What You'll Say
```
Run the lead generation workflow for HVAC companies in the UK:
- Company Size: 10-50 employees
- Revenue: $1M-$10M
- Total leads: 500
- Offer: AI Automation Implementation
```

### What Happens Next

The system automatically:

1. ✅ Scrapes and validates 25 test leads (80%+ match required)
2. ✅ Scrapes full 500 leads (if quality check passes)
3. ✅ Verifies all email addresses
4. ✅ Enriches with website personalization
5. ✅ Segments into personalized vs generic groups
6. ✅ Generates AI campaign copy (tailored per segment)
7. ✅ Creates Instantly campaigns and uploads leads

**Time:** 4 minutes (or 15 minutes with deep personalization)

**You get:** Ready-to-send Instantly campaigns with verified, segmented leads

## How It Works (The Simple Version)

**Step 1: Tell it your ICP**
```
"Run lead gen for HVAC companies in the UK:
- 10-50 employees
- $1M-$10M revenue  
- 500 leads total"
```

**Step 2: It validates quality**
- Scrapes 25 test leads
- AI checks if they match your ICP (80%+ required)
- If passed → scrapes the full batch

**Step 3: It cleans and verifies**
- Normalizes company names
- Verifies email deliverability (AnyMailFinder)
- Filters out bounces and spam traps

**Step 4: It personalizes (optional)**
- Scrapes company websites
- Finds specific achievements, awards, client names
- Segments into personalized vs generic buckets

**Step 5: It creates campaigns**
- Generates AI email copy from your templates
- Creates separate Instantly campaigns (personalized vs generic)
- Uploads leads to respective campaigns

**Step 6: You're ready to send**

### Why It's Reliable

Most AI automation breaks after a few steps. This doesn't.

**The secret:** 3-layer architecture (DOE framework)
- **Directives** = What to do (living documents that improve over time)
- **Orchestration** = AI decides how to do it
- **Execution** = Deterministic Python scripts do the work

When something breaks, it self-anneals: reads the error, fixes the code, tests it, updates the directive. Gets smarter with each failure.

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
# Use a text editor to add your keys from the services below
```

### 6. (Optional) Set up Google Sheets export
1. Go to [Google Cloud Console](https://console.cloud.google.com)
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

## API Keys & Services

You'll need API keys from these services:

### Required Services

| Service | Get Key From | Cost | Purpose |
|---------|-------------|------|---------|
| **Apify** | [Console](https://console.apify.com) | Pay-as-you-go (~$0.01-0.05/lead) | Lead scraping |
| **Anthropic Claude** | [Console](https://console.anthropic.com) | ~$0.50-2.00 per 1000 leads | AI validation & copy |
| **Instantly.ai** | [Settings](https://app.instantly.ai/app/settings/integrations) | $37-297/month | Campaign management |
| **AnyMailFinder** | [Account](https://anymailfinder.com) | ~$0.002/verification | Email verification |
| **Firecrawl** | [Dashboard](https://firecrawl.dev) | Free tier + pay-as-you-go | Website personalization |

### Optional Services

| Service | Get Key From | Cost | Purpose |
|---------|-------------|------|---------|
| **Google Cloud** | [Console](https://console.cloud.google.com) | Free for Sheets API | Google Sheets export |

## Performance Benchmarks

**For 1000 leads:**

- **Without personalization:** ~4 minutes total
- **With personalization:** ~54-104 minutes total

Personalization is the slowest step (50-100 minutes)

**Optimizations:**
- Parallel email verification (5 concurrent)
- Parallel personalization enrichment (5 concurrent)
- Parallel lead uploads (5 workers, 75% faster)
- Batch Sheets export (60% faster for large datasets)
- Parallel campaign generation (50% faster)

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

## Key Principles

- **Self-anneal when things break** - Errors are learning opportunities
- **Update directives as you learn** - Living documents that improve over time
- **Deterministic execution** - Push complexity into reliable Python scripts
- **Deliverables in cloud** - Google Sheets/Slides, not local files
- **Intermediates are temporary** - Everything in `.tmp/` can be regenerated

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

**Built with the 3-layer agentic architecture** - reliable, self-improving, production-ready.

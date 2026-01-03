# Client Setup Guide - Lead Generation Workflow

## Overview
This system automatically scrapes, validates, personalizes, and launches cold email campaigns through Instantly.ai. It typically takes 4 minutes for 1000 leads (without personalization) or 54-104 minutes with personalization.

---

## Step 1: Download the Code

### Option A: Using Git (Recommended)

**Install Git first (if you don't have it):**
- Download from: https://git-scm.com/downloads
- Run the installer with default settings

**Clone the repository:**
```bash
# Open Command Prompt or Terminal
# Navigate to where you want the code (e.g., your Documents folder)
cd Documents

# Download the code
git clone https://github.com/EfanMutembo/Full-Stack-Lead-Agent.git

# Go into the folder
cd Full-Stack-Lead-Agent
```

### Option B: Download ZIP (Simpler, but no updates)

1. Go to: https://github.com/EfanMutembo/Full-Stack-Lead-Agent
2. Click the green **"Code"** button
3. Click **"Download ZIP"**
4. Extract the ZIP file to your Documents folder
5. Open Command Prompt and navigate to the folder:
   ```bash
   cd Documents\Full-Stack-Lead-Agent-main
   ```

---

## Step 2: Install Python

**Check if you have Python:**
```bash
python --version
```

If you see "Python 3.8" or higher, you're good. If not:

1. Download Python from: https://www.python.org/downloads/
2. **IMPORTANT:** Check "Add Python to PATH" during installation
3. Restart your computer after installation

---

## Step 3: Set Up the Environment

**Open Command Prompt in the project folder and run:**

```bash
# Create a virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# You should see (venv) appear in your command prompt

# Install required packages
pip install -r requirements.txt
```

**For Mac/Linux users:**
```bash
# Activate virtual environment
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

---

## Step 4: Get Your API Keys

You need accounts with these services. Sign up and get API keys:

### Required Services (Must Have)

| Service | Purpose | Sign Up Link | Where to Find API Key | Approx. Cost |
|---------|---------|--------------|----------------------|--------------|
| **Apify** | Lead scraping | [console.apify.com](https://console.apify.com/account/integrations) | Integrations tab | ~$10-50 per 1000 leads |
| **Anthropic** | AI validation & copy | [console.anthropic.com](https://console.anthropic.com/) | Settings → API Keys | ~$1-2 per 1000 leads |
| **Instantly.ai** | Email campaigns | [app.instantly.ai](https://app.instantly.ai/app/settings/api) | Settings → API | $37-297/month |
| **AnyMailFinder** | Email verification | [anymailfinder.com](https://anymailfinder.com/account.php) | Account page | ~$2 per 1000 emails |
| **Firecrawl** | Website scraping | [firecrawl.dev](https://firecrawl.dev/) | Dashboard | Free tier + $0.003/page |

### Optional Services

| Service | Purpose | Sign Up Link | Cost |
|---------|---------|--------------|------|
| **Google Cloud** | Export to Sheets | [console.cloud.google.com](https://console.cloud.google.com/) | Free |

**For Google Sheets (optional):**
1. Create a new project in Google Cloud Console
2. Enable "Google Sheets API" and "Google Drive API"
3. Create OAuth 2.0 credentials (type: Desktop app)
4. Download the `credentials.json` file
5. Place it in the project root folder (same folder as this file)

---

## Step 5: Configure Your API Keys

**Create your environment file:**

```bash
# Copy the example file
copy .env.example .env

# Open it in Notepad (Windows)
notepad .env

# Or use any text editor you prefer
```

**Fill in your API keys:**

```env
# Replace the placeholder values with your actual API keys

APIFY_API_TOKEN=apify_api_YOUR_KEY_HERE
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY_HERE
INSTANTLY_API_KEY=YOUR_KEY_HERE
ANYMAILFINDER_API_KEY=YOUR_KEY_HERE
FIRECRAWL_API_KEY=fc-YOUR_KEY_HERE

# Optional (only if using Google Sheets export)
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
```

**Save the file** (Ctrl+S in Notepad)

---

## Step 6: Install Claude Code (AI Agent)

This system uses Claude Code to orchestrate the workflow.

**Install Claude Code:**
```bash
npm install -g @anthropics/claude-code
```

**Or use alternative AI tools:**
- Cursor IDE
- Cline VS Code extension
- Any AI agent that can run Python scripts

---

## Step 7: Test the System

**Run a small test first (25 leads):**

1. Make sure your virtual environment is activated:
   ```bash
   # You should see (venv) in your prompt
   # If not, run:
   venv\Scripts\activate
   ```

2. Start Claude Code:
   ```bash
   claude-code
   ```

3. Give it this test prompt:
   ```
   Run the lead generation workflow for HVAC companies:
   - Industry: HVAC installation and maintenance
   - Location: United States
   - Company Size: 10-50 employees
   - Total leads: 25
   - Offer: Free HVAC system audit
   ```

4. The system will automatically:
   - Scrape 25 test leads
   - Validate quality (needs 80%+ match)
   - If passed → scrape, verify, personalize, create campaigns
   - Give you Instantly campaign links

**Expected time:** ~2-3 minutes for 25 leads

---

## Step 8: Run Production Workflows

Once testing works, scale up:

```
Run the lead generation workflow for [YOUR INDUSTRY]:
- Industry: [e.g., Solar companies, SaaS startups, Dental practices]
- Location: [e.g., United Kingdom, California, Australia]
- Company Size: [e.g., 10-50 employees, 50-200 employees]
- Revenue: [e.g., $1M-$10M] (optional)
- Job Titles: [e.g., CEO, Founder, Managing Director]
- ICP Description: [Detailed description of ideal customer]
- Total leads: [e.g., 500, 1000]
- Offer: [Your value proposition]
```

**Example:**
```
Run the lead generation workflow for solar companies:
- Industry: Residential solar installation
- Location: California
- Company Size: 10-100 employees
- Revenue: $1M-$50M
- Job Titles: CEO, Founder, Owner, President
- ICP Description: Companies struggling with lead generation, have tried paid ads without success, need consistent pipeline
- Total leads: 500
- Offer: Free solar lead generation audit + 30-day trial
```

---

## What You'll Get

After the workflow completes:

✅ **Verified leads** - Emails checked for deliverability
✅ **Personalized data** - Company-specific achievements scraped from websites
✅ **Segmented campaigns** - Separate campaigns for personalized vs generic leads
✅ **AI-generated email copy** - Sequences tailored to each segment
✅ **Instantly campaigns** - Ready-to-launch campaigns with leads uploaded
✅ **Google Sheet** (optional) - Spreadsheet with all lead data

---

## Costs Breakdown

**For 1000 leads:**

| Service | Cost |
|---------|------|
| Apify (scraping) | $10-50 |
| AnyMailFinder (verification) | ~$2 |
| Anthropic (AI validation + copy) | $1-2 |
| Firecrawl (personalization) | $0.50-2 |
| **Total one-time cost** | **$15-60** |

**Plus monthly subscriptions:**
- Instantly.ai: $37-297/month

---

## Timing

**Without personalization:** ~4 minutes for 1000 leads
**With personalization:** ~54-104 minutes for 1000 leads

Personalization is the slowest step but provides much better results.

---

## Troubleshooting

### "Virtual environment not activating"
```bash
# Windows
venv\Scripts\activate.bat

# Mac/Linux
source venv/bin/activate
```

### "pip not found"
```bash
# Try python -m pip instead
python -m pip install -r requirements.txt
```

### "API authentication failed"
- Double-check your API keys in `.env`
- Make sure there are no extra spaces or quotes
- Verify the keys are valid in each service's dashboard

### "Quality validation failed (below 80%)"
- Your ICP filters might be too restrictive
- Try broader location or industry keywords
- The system will suggest adjustments

### "Email verification rate low"
- Check your AnyMailFinder credits
- Verify the API key is correct
- This is normal for some data sources (50-70% is acceptable)

### "Personalization success rate low"
- Check your Firecrawl API key
- Review `.tmp/personalization_report.json` for details
- Some industries have minimal web presence (expected)

---

## Support

**If you get stuck:**

1. Check the detailed docs: `README.md`
2. Review workflow steps: `directives/lead_generation_workflow.md`
3. Check `.tmp/` folder for error reports
4. Contact support: [Add your support email/contact]

---

## Quick Reference

**Every time you want to run the workflow:**

```bash
# 1. Navigate to project folder
cd Documents\Full-Stack-Lead-Agent

# 2. Activate environment
venv\Scripts\activate

# 3. Start Claude Code
claude-code

# 4. Give your workflow prompt
# "Run the lead generation workflow for..."
```

---

**Built with the 3-layer agentic architecture - reliable, self-improving, production-ready.**

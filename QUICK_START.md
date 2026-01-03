# Quick Start - Lead Generation System

## 🚀 5-Minute Setup

### 1. Download the Code

**Easy way (no Git needed):**
1. Go to: https://github.com/EfanMutembo/Full-Stack-Lead-Agent
2. Click green **"Code"** button → **"Download ZIP"**
3. Extract to your Documents folder

**Or use Git:**
```bash
git clone https://github.com/EfanMutembo/Full-Stack-Lead-Agent.git
cd Full-Stack-Lead-Agent
```

### 2. Install Python

Download from: https://www.python.org/downloads/

**IMPORTANT:** Check ✅ "Add Python to PATH" during installation

### 3. Set Up Environment

Open Command Prompt in the project folder:

```bash
# Create virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

**Mac/Linux:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Get API Keys

Sign up for these services and get API keys:

| Service | Link | What It Does |
|---------|------|--------------|
| **Apify** | [console.apify.com](https://console.apify.com/account/integrations) | Scrapes leads |
| **Anthropic** | [console.anthropic.com](https://console.anthropic.com/) | AI validation |
| **Instantly** | [app.instantly.ai](https://app.instantly.ai/app/settings/api) | Email campaigns |
| **AnyMailFinder** | [anymailfinder.com](https://anymailfinder.com/account.php) | Email verification |
| **Firecrawl** | [firecrawl.dev](https://firecrawl.dev/) | Website scraping |

### 5. Configure Keys

```bash
# Copy template
copy .env.example .env

# Edit with Notepad
notepad .env
```

Paste your API keys:
```env
APIFY_API_TOKEN=your_key_here
ANTHROPIC_API_KEY=your_key_here
INSTANTLY_API_KEY=your_key_here
ANYMAILFINDER_API_KEY=your_key_here
FIRECRAWL_API_KEY=your_key_here
```

Save and close.

### 6. Install Claude Code

```bash
npm install -g @anthropics/claude-code
```

### 7. Run Test Workflow

```bash
# Start Claude Code
claude-code
```

Then tell it:
```
Run the lead generation workflow for HVAC companies:
- Industry: HVAC installation
- Location: United States
- Company Size: 10-50 employees
- Total leads: 25
- Offer: Free system audit
```

---

## 📊 What You Get

- ✅ Verified email addresses
- ✅ Personalized company data
- ✅ AI-generated email sequences
- ✅ Ready-to-launch Instantly campaigns
- ✅ Google Sheets export (optional)

---

## 💰 Costs

**Per 1000 leads:** ~$15-60 one-time
**Monthly:** Instantly subscription ($37-297/mo)

---

## ⏱️ Time

- **Without personalization:** ~4 minutes for 1000 leads
- **With personalization:** ~54-104 minutes for 1000 leads

---

## 🔄 Daily Usage

Every time you want to run it:

```bash
# 1. Go to folder
cd Full-Stack-Lead-Agent

# 2. Activate environment
venv\Scripts\activate

# 3. Start Claude Code
claude-code

# 4. Give your prompt
"Run the lead generation workflow for..."
```

---

## 📖 Full Documentation

- Detailed setup: `CLIENT_SETUP.md`
- Complete guide: `README.md`
- Workflow details: `directives/lead_generation_workflow.md`

---

## 🆘 Need Help?

- Check `CLIENT_SETUP.md` for detailed troubleshooting
- Review error logs in `.tmp/` folder
- Contact: [Your support email/contact]

---

**Repository:** https://github.com/EfanMutembo/Full-Stack-Lead-Agent

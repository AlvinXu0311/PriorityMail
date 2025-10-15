# PriorityMail - Email Priority Classification System

> **DRAFT VERSION - FOR TESTING AND EVALUATION PURPOSES ONLY**
>
> This is a prototype implementation developed for academic evaluation. Not intended for production use without further testing and refinement.

**Multi-Class Classification Approach** - Direct priority prediction using manually labeled training data.

---

## Quick Start (3 Commands)

```bash
# 1. Install dependencies
pip install -r requirements.txt
ollama pull qwen3-embedding

# 2. Run full pipeline (extract → manual label → train → predict)
# Note: Step 2 (auto-labeling) is now commented out - use manual labeling instead
python pipeline/run_full_pipeline.py --source data/enron_mail_20150507 --limit 1500

# 3. View results
cat data/predictions/predicted_emails.csv
```

**Total time:** ~3 minutes for 1500 emails

---

## Environment Setup

All configuration is centralized in a single `.env` file. See [ENV_SETUP.md](ENV_SETUP.md) for details.

**Quick setup:**
```bash
# Copy template and fill in your API keys
cp .env.example .env
nano .env  # Add your OPENAI_API_KEY and GEMINI_API_KEY
```

**Required API Keys:**
- `OPENAI_API_KEY` - If using OpenAI embeddings (optional)
- `GEMINI_API_KEY` - For Gmail addon todo generation (optional)

**Priority Mode Configuration:**
- `PRIORITY_MODE=ml_model` - Use local ML model + LLM for todos (RECOMMENDED - Fast & Accurate)
- `PRIORITY_MODE=llm_only` - Use LLM for both classification and todos (No ML model needed)

---

## Pipeline Architecture

### Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          TRAINING PHASE (One-time)                           │
└─────────────────────────────────────────────────────────────────────────────┘

    Raw Email Dataset
    (Enron/Mailbox)
           │
           ▼
    ┌──────────────────┐
    │  01_EXTRACT      │ ──► Extract emails from mailbox
    │  emails.py       │     Parse subject, body, sender, timestamp
    └──────────────────┘
           │
           ▼
    emails_raw.csv
    (1500 emails, unlabeled)
           │
           ▼
    ┌──────────────────┐
    │  02_MANUAL_LABEL │ ──► Manual Labeling
    │  emails.py       │     • Manually assign priority labels
    └──────────────────┘     • HIGH/MEDIUM/LOW classification
           │
           ▼
    emails_labeled.csv
    (1500 emails with manually assigned priority labels)
           │
           ▼
    ┌──────────────────┐
    │  03_TRAIN        │ ──► Train ML Classifier
    │  classifier.py   │     • Generate embeddings (Ollama/OpenAI)
    └──────────────────┘     • Train SVM/RF/GB model
           │                 • 80/20 train/test split
           ▼
    priority_classifier.pkl
    (Trained ML classification model)


┌─────────────────────────────────────────────────────────────────────────────┐
│                       PREDICTION PHASE (Production Use)                      │
└─────────────────────────────────────────────────────────────────────────────┘

    New Emails (CSV/API)
           │
           ▼
    ┌──────────────────┐
    │  04_PREDICT      │ ──► Load trained model
    │  priority.py     │     Generate embeddings
    └──────────────────┘     Predict priority + confidence
           │
           ▼
    predicted_emails.csv
    (Emails with HIGH/MEDIUM/LOW + confidence scores)


┌─────────────────────────────────────────────────────────────────────────────┐
│                      GMAIL ADD-ON (Real-time Integration)                   │
└─────────────────────────────────────────────────────────────────────────────┘

    Gmail Email
           │
           ▼
    ┌──────────────────┐      ┌─────────────────┐
    │  Apps Script     │ ───► │  API Server     │
    │  Sidebar         │      │  (Flask)        │
    └──────────────────┘      └─────────────────┘
                                      │
                        ┌─────────────┴─────────────┐
                        ▼                           ▼
                ┌──────────────┐          ┌──────────────┐
                │  ML Model    │          │  Gemini LLM  │
                │  (Classify)  │          │  (Gen Todos) │
                └──────────────┘          └──────────────┘
                        │                           │
                        └─────────────┬─────────────┘
                                      ▼
                           Display in Gmail Sidebar
                           • Priority: HIGH/MEDIUM/LOW
                           • Confidence: 0.87
                           • Action items extracted


┌─────────────────────────────────────────────────────────────────────────────┐
│                          PRIORITY MODE OPTIONS                               │
└─────────────────────────────────────────────────────────────────────────────┘

Mode 1: ML_MODEL (RECOMMENDED)          Mode 2: LLM_ONLY
┌────────────────────────┐              ┌────────────────────────┐
│ Email → ML Classifier  │              │ Email → Gemini LLM     │
│         ↓              │              │         ↓              │
│    Priority            │              │    Priority            │
│         ↓              │              │         ↓              │
│ Email → Gemini LLM     │              │    Action Items        │
│         ↓              │              └────────────────────────┘
│    Action Items        │              • Slower (2 API calls)
└────────────────────────┘              • Higher cost
• Faster (1 API call)                   • No ML model needed
• Lower cost
```
---

## Project Structure

```
PriorityMail/
│
├── pipeline/                      # Main pipeline (numbered steps)
│   ├── 01_extract_emails.py            # Extract raw emails → CSV
│   ├── 02_auto_label_emails.py         # (COMMENTED OUT - Use manual labeling)
│   ├── 03_train_classifier.py          # Train classifier → PKL
│   ├── 04_predict_priority.py          # Predict → CSV
│   └── run_full_pipeline.py            # Master runner
│
├── core/                          # Reusable modules
│   ├── hybrid_labeler.py               # (COMMENTED OUT - Use manual labeling)
│   ├── reference_examples.py           # Reference emails for similarity
│   └── embeddings.py                   # Embedding generation
│
├── addon/                         # PriorityMail Gmail Add-ons
│   ├── app.py                          # Flask web app
│   ├── api_server/                     # API server for Apps Script
│   ├── apps_script/                    # Gmail sidebar addon
│   └── utils/                          # Shared utilities
│
├── data/                          # All data (CSV/PKL format)
│   ├── raw/                            # Step 1 output
│   ├── labeled/                        # Step 2 output
│   ├── models/                         # Step 3 output
│   └── predictions/                    # Step 4 output
│
├── config.py                      # Centralized configuration
├── .env.example                   # Environment template
├── ENV_SETUP.md                   # Environment setup guide
│
├── docs/                          # Documentation
│   ├── Technical_Report.md             # Academic technical report
│   └── User_Guide.md                   # Academic user guide
│
└── tests/                         # Test data
    └── test_emails_15.json
```

---

## Step-by-Step Usage

### Step 1: Extract Raw Emails

```bash
python pipeline/01_extract_emails.py \
  --source data/enron_mail_20150507 \
  --output data/raw/emails_raw.csv \
  --limit 1500
```

**Output:** `data/raw/emails_raw.csv` (unlabeled)

### Step 2: Manual Label Emails

Manually label emails in `data/raw/emails_raw.csv` and save to `data/labeled/emails_labeled.csv`.

Required columns: `email_id`, `subject`, `body`, `sender`, `timestamp`, `folder`, `priority`

**Output:** `data/labeled/emails_labeled.csv` (with manually assigned labels)

### Step 3: Train Classification Model

```bash
python pipeline/03_train_classifier.py \
  --input data/labeled/emails_labeled.csv \
  --output data/models/priority_classifier.pkl \
  --model-type random_forest \
  --embedder ollama \
  --embedding-model qwen3-embedding
```

**Output:** `data/models/priority_classifier.pkl` - Multi-class classifier

**Supported models:**
- `svm`: Support Vector Machine (default)
- `random_forest`: Random Forest
- `gradient_boost`: Gradient Boosting

### Step 4: Predict Email Priorities

```bash
python pipeline/04_predict_priority.py \
  --input data/raw/new_emails.csv \
  --model data/models/priority_classifier.pkl \
  --output data/predictions/predicted_emails.csv
```

**Output:** `data/predictions/predicted_emails.csv` (with predictions and confidence scores)

---

## CSV Data Formats

### emails_raw.csv (Step 1)
```csv
email_id,subject,body,sender,timestamp,folder
1,"Meeting tomorrow","...","alice@company.com","2025-01-15 10:30","inbox"
```

### emails_labeled.csv (Step 2)
```csv
email_id,subject,body,sender,timestamp,folder,priority,confidence,label_method
1,"Meeting","...","alice@company.com","2025-01-15 10:30","inbox","MEDIUM",0.65,"embedding"
```

### predicted_emails.csv (Step 4)
```csv
email_id,subject,body,sender,timestamp,folder,predicted_priority,confidence
1,"Meeting","...","alice@company.com","2025-01-15 10:30","inbox","MEDIUM",0.87
```

---

## Performance Metrics

- **Training Time:** 20-40 seconds (1500 emails)
- **Prediction Time:** <1 second per email
- **Cost:** $0 (using free local embeddings via Ollama)
- **Multi-class Classification:** Balanced performance across HIGH/MEDIUM/LOW

---

## Why Classification?

**Direct prediction:** Email → Predict HIGH/MEDIUM/LOW → Immediate actionable result

**Practical benefits:**
- No threshold tuning needed - Direct class prediction
- Fast inference - Single forward pass per email
- Confidence scores - Probability estimates for each prediction
- Production-ready - Works with unlabeled real-world emails

**Trade-off:** Classification predicts absolute priority levels directly, which is practical for production systems where you need immediate filtering decisions without comparing all emails.

---

## PriorityMail Gmail Add-on - THREE Options!

**AI-powered task extraction from your Gmail inbox!**

### Option 1: Hybrid Approach (RECOMMENDED)

**ML Model + Gemini API = Best Performance + Minimum Cost**

Located in `addon/apps_script/` - Gmail sidebar with:
- ML Model API for priority classification
- Gemini API for excellent to-do generation (only when needed)
- Smart caching that never regenerates (saves 67% tokens)
- Gmail sidebar works directly in browser
- Fallback to rules-based if API unavailable

**Quick Start (5 min - ONE command!):**
```bash
# 1. Setup environment
cp .env.example .env
nano .env  # Add GEMINI_API_KEY and generate API_KEY
# Set PRIORITY_MODE=ml_model (default)

# 2. Deploy API server with ngrok (Windows)
cd addon/api_server
setup.bat
deploy_ngrok.bat          # Starts server + ngrok on port 4999

# OR Linux/Mac
./setup.sh
./deploy_ngrok.sh

# Output: https://abc123.ngrok.io ← Copy this URL!

# 3. Copy 3 files to Apps Script:
#    - Code_Hybrid.gs → Code.gs (paste ngrok URL on line 12)
#    - Sidebar.html
#    - appsscript.json

# 4. Deploy → Test → Done!
```

**Documentation:**
- [api_server/DEPLOY_GUIDE.md](addon/api_server/DEPLOY_GUIDE.md) - Complete deployment guide
- [apps_script/RECOMMENDED_SETUP.md](addon/apps_script/RECOMMENDED_SETUP.md) - 10-min hybrid setup
- [apps_script/Code_Hybrid.gs](addon/apps_script/Code_Hybrid.gs) - Main code

---

### Option 2: Standalone (No Server - Easiest!)

**100% browser-based - NO server needed!**

- 5-minute setup
- $0 cost forever
- Gemini AI for classification
- Cannot use trained ML model

**Quick Start (5 min):**
```bash
# 1. Get Gemini API key (add to .env)
# 2. Copy Code_Standalone.gs to Apps Script
# 3. Paste API key
# 4. Deploy → Done!
```

**Documentation:**
- [apps_script/STANDALONE_SETUP.md](addon/apps_script/STANDALONE_SETUP.md) - 5-min setup
- [apps_script/Code_Standalone.gs](addon/apps_script/Code_Standalone.gs) - Standalone code

---

### Option 3: Flask Web App (Full Dashboard)

**Standalone web application with complete UI**

- Beautiful dashboard
- Full task management
- Batch processing
- Not in Gmail sidebar

**Quick Start:**
```bash
cd addon
cp .env.example .env
nano .env  # Setup OAuth + Gemini API key
python app.py
# Open http://localhost:5000
```

**Documentation:**
- [QUICK_START.md](addon/QUICK_START.md) - Web app setup

---

## Configuration Management

All environment variables are centralized in `.env`:
- API keys (OpenAI, Gemini)
- Security keys (Flask, API server)
- Priority mode (ml_model or llm_only)
- Server configuration
- Gmail API settings
- File paths

**See [ENV_SETUP.md](ENV_SETUP.md) for complete configuration reference.**

---

## Priority Mode Options

**ML Model Mode (RECOMMENDED - Default):**
```bash
PRIORITY_MODE=ml_model
```
- Uses trained ML model for classification
- Uses Gemini only for todo generation
- Faster, lower cost

**LLM-Only Mode:**
```bash
PRIORITY_MODE=llm_only
```
- Uses Gemini for both classification and todos
- No ML model required
- Slower, higher API costs

---

## Git Safety

The project is configured for safe Git uploads:
- `.gitignore` protects all sensitive files (.env, credentials, tokens, cache)
- `.env.example` provides a template with placeholder values
- No API keys or credentials in code

**Before first commit:**
```bash
# Verify .env is not tracked
git status

# Should NOT show .env, credentials.json, or token.pickle
```

---

## Documentation

- **[ENV_SETUP.md](ENV_SETUP.md)** - Environment configuration guide
- **[addon/api_server/DEPLOY_GUIDE.md](addon/api_server/DEPLOY_GUIDE.md)** - API server deployment
- **[addon/apps_script/RECOMMENDED_SETUP.md](addon/apps_script/RECOMMENDED_SETUP.md)** - Gmail add-on setup
- **[docs/Technical_Report.md](docs/Technical_Report.md)** - Academic technical report
- **[docs/User_Guide.md](docs/User_Guide.md)** - User guide

---

## Project Status

**DRAFT VERSION - Testing and Evaluation**

This is a prototype implementation for academic purposes. The system demonstrates:
- Production-Ready architecture
- Multi-class email classification (HIGH/MEDIUM/LOW)
- $0 Cost with local embeddings
- 3-minute training pipeline
- Gmail Add-on integration
- Git-Safe configuration

**Note:** This version is intended for testing and evaluation. Further refinement and testing would be needed before production deployment.

---

## License

This project is a draft implementation for academic evaluation purposes.

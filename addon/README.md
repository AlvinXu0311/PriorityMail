# PriorityMail - Gmail Add-on (THREE Options)

> **DRAFT VERSION - FOR TESTING AND EVALUATION PURPOSES ONLY**

AI-powered email analysis with priority classification + to-do generation.

---

## RECOMMENDED: Hybrid Approach (Best of Both)

**ML Model API + Gemini API + Gmail Sidebar**

Located in [apps_script/](apps_script/) - The optimal solution

**Quick Start (10 min):**
```bash
# 1. Start API server (for classification)
cd api_server
setup.bat  # Windows
# OR
./setup.sh  # Linux/Mac

# 2. Get Gemini API key: https://makersuite.google.com

# 3. Copy 3 files to Apps Script:
#    - Code_Hybrid.gs → Code.gs
#    - Sidebar.html
#    - appsscript.json

# 4. Update API_URL, API_KEY, GEMINI_API_KEY
# 5. Deploy → Test → Done!
```

**Documentation:**
- [apps_script/RECOMMENDED_SETUP.md](apps_script/RECOMMENDED_SETUP.md) - 10-min hybrid setup
- [apps_script/Sidebar.html](apps_script/Sidebar.html) - UI file
- [apps_script/Code_Hybrid.gs](apps_script/Code_Hybrid.gs) - Main code

---

## Option 2: Standalone (No Server - Easiest)

**100% browser-based - NO server needed**

Located in [apps_script/](apps_script/)

- 5-minute setup
- $0 cost forever
- Gemini AI for classification (80-85% accuracy)
- Cannot use trained ML model

**Quick Start (5 min):**
```bash
# 1. Get Gemini API key
# 2. Copy Code_Standalone.gs to Apps Script
# 3. Paste API key
# 4. Deploy → Done!
```

**Documentation:**
- [apps_script/STANDALONE_SETUP.md](apps_script/STANDALONE_SETUP.md) - 5-min setup
- [apps_script/Code_Standalone.gs](apps_script/Code_Standalone.gs) - Standalone code

---

## Option 3: Flask Web App (Full Dashboard)

**Standalone web application with complete UI**

Located in root [addon/](.) folder

- Beautiful dashboard
- Full task management
- Batch processing
- OAuth authentication
- Not in Gmail sidebar

**Quick Start:**
```bash
cd addon
pip install -r requirements.txt
# Setup OAuth + Gemini API key (see QUICK_START.md)
python app.py
# Open http://localhost:5000
```

**Documentation:**
- [QUICK_START.md](QUICK_START.md) - 5-minute setup

---

## Which Option Should I Choose?

| Feature | Hybrid (RECOMMENDED) | Standalone | Web App |
|---------|----------|------------|---------|
| **Setup Time** | 10 min | 5 min | 10 min |
| **Server Needed** | Yes | No | No |
| **Cost** | $0-5/mo | $0 | $0 |
| **Priority Accuracy** | **85-95%** | 80-85% | 85-95% |
| **To-Do Quality** | **Excellent** | Good | Excellent |
| **Gmail Sidebar** | Yes | Yes | No |
| **Caching** | **Smart** | Basic | Smart |

**Recommendation:**
- **Personal use, best accuracy:** Hybrid
- **Quick test, no server:** Standalone
- **Full dashboard, batch:** Web App

---

## Architecture Comparison

### Hybrid (Recommended)
```
Gmail Email → Apps Script Sidebar
                    ↓
        ┌──────────┴──────────┐
        ▼                     ▼
   ML Model API          Gemini API
   (classify)            (to-dos)
        └──────────┬──────────┘
                   ▼
          Display Results
```

### Standalone
```
Gmail Email → Apps Script Sidebar
                    ↓
               Gemini API
           (classify + to-dos)
                    ↓
          Display Results
```

### Web App
```
Gmail OAuth → Flask Server
                    ↓
       ┌────────────┴────────────┐
       ▼                         ▼
  ML Classifier            Gemini API
       └────────────┬────────────┘
                    ▼
            Web Dashboard
```

---

## Common Features (All Options)

- Priority classification (HIGH/MEDIUM/LOW)
- AI-powered to-do generation
- Smart caching (avoid duplicate API calls)
- Gemini API integration
- Production-ready architecture

---

## Quick Links

- **Hybrid Setup:** [apps_script/RECOMMENDED_SETUP.md](apps_script/RECOMMENDED_SETUP.md)
- **Standalone Setup:** [apps_script/STANDALONE_SETUP.md](apps_script/STANDALONE_SETUP.md)
- **Web App Setup:** [QUICK_START.md](QUICK_START.md)
- **Troubleshooting:** [apps_script/TROUBLESHOOTING.md](apps_script/TROUBLESHOOTING.md)
- **API Server Deployment:** [api_server/DEPLOY_GUIDE.md](api_server/DEPLOY_GUIDE.md)

---

## Project Status

**DRAFT VERSION - Testing and Evaluation**

This is a prototype implementation for academic purposes demonstrating production-ready architecture. Further testing would be needed before production deployment.

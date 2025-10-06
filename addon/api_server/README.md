# PriorityMail - API Server

> **DRAFT VERSION - FOR TESTING AND EVALUATION PURPOSES ONLY**

Flask API server that exposes the trained ML model for email classification and integrates with Gemini for to-do generation.

## Features

- ML Classification - 85-95% accurate priority prediction (HIGH/MEDIUM/LOW)
- LLM-Only Mode - Use Gemini for classification when ML model unavailable
- Gemini To-Dos - AI-powered actionable task extraction
- Smart Caching - Avoids duplicate API calls
- REST API - Works with Apps Script, web apps, mobile apps
- Bearer Token Auth - Secure API access

---

## Quick Deploy (ONE Command)

### Windows

```batch
# Setup + Deploy with ngrok
setup.bat
notepad .env          # Add your API keys
deploy_ngrok.bat      # Starts server + ngrok on port 4999
```

### Linux/Mac

```bash
# Setup + Deploy with ngrok
./setup.sh
nano .env             # Add your API keys
./deploy_ngrok.sh     # Starts server + ngrok on port 4999
```

**Output:**
```
Starting API server on port 4999...
Starting ngrok tunnel...

Your API will be available at: https://abc123.ngrok.io
Copy the HTTPS URL and paste it in Code_Hybrid.gs (line 12)
```

---

## Priority Mode Configuration

Set in `.env` file:

```bash
# Option 1: ML Model Mode (RECOMMENDED - Default)
PRIORITY_MODE=ml_model
# - Uses trained ML model for classification
# - Uses Gemini only for todo generation
# - Faster, more accurate (85-95%), lower cost

# Option 2: LLM-Only Mode
PRIORITY_MODE=llm_only
# - Uses Gemini for both classification and todos
# - No ML model required
# - Slower, lower accuracy (80-85%), higher API costs
```

---

## API Endpoints

### 1. Classify Email Priority

```
POST /api/classify
Authorization: Bearer your_api_key

Response includes:
- priority: HIGH/MEDIUM/LOW
- confidence: 0.0-1.0
- method: "ml_model" or "llm"
```

### 2. Generate To-Dos

```
POST /api/generate-todos
Authorization: Bearer your_api_key
```

### 3. Complete Workflow

```
POST /api/process-email
Authorization: Bearer your_api_key
```

See [DEPLOY_GUIDE.md](DEPLOY_GUIDE.md) for full documentation and testing examples.

---

## Deployment Options

### Option 1: ngrok (Easiest - 5 min)

```batch
deploy_ngrok.bat      # Windows
./deploy_ngrok.sh     # Linux/Mac
```

- Free HTTPS tunnel
- Works behind firewall
- URL changes on restart

### Option 2: Railway (Production - Permanent URL)

1. Deploy to https://railway.app
2. Set environment variables from .env
3. Copy public URL (permanent)
4. Cost: $5/month

### Option 3: Manual

```bash
python app.py         # Starts on port 4999
ngrok http 4999       # Separate terminal
```

---

## Project Status

**DRAFT VERSION - Testing and Evaluation**

This API server demonstrates production-ready architecture for academic evaluation. Further testing would be needed before production deployment.

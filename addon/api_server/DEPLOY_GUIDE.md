# API Server Deployment Guide

Complete guide for deploying the Email Priority API server with ngrok.

---

## Quick Deploy (5 Minutes)

### Windows

```batch
# 1. Setup environment
setup.bat

# 2. Edit .env file with your keys
notepad .env

# 3. Deploy with ngrok
deploy_ngrok.bat
```

### Linux/Mac

```bash
# 1. Setup environment
./setup.sh

# 2. Edit .env file with your keys
nano .env

# 3. Deploy with ngrok
./deploy_ngrok.sh
```

---

## Step-by-Step Setup

### Step 1: Get ngrok Token

1. Download ngrok from https://ngrok.com/download
2. Extract and add to PATH
3. Sign up for free account at https://dashboard.ngrok.com
4. Get your authtoken from https://dashboard.ngrok.com/get-started/your-authtoken
5. Copy the token (you'll add it to `.env` in Step 2)

### Step 2: Configure Environment

Edit `.env` file:

```env
# Path to trained model (relative to api_server folder)
MODEL_PATH=../../data/models/priority_classifier.pkl

# Gemini API key (from https://makersuite.google.com)
GEMINI_API_KEY=your_gemini_key_from_makersuite

# API security key (generate random 32-char string)
API_KEY=your_random_api_key_here

# Server port (ngrok will tunnel this)
PORT=4999

# Ngrok authentication token (from https://dashboard.ngrok.com/get-started/your-authtoken)
NG_KEY=your_ngrok_authtoken_here
```

**Generate secure API key:**
```bash
python -c "import secrets; print(secrets.token_hex(16))"
```

**Note:** The deploy script will automatically authenticate ngrok using `NG_KEY` from `.env`

### Step 3: Train Model (if not done)

```bash
cd ../..
python pipeline/run_full_pipeline.py --source data/enron_mail_20150507 --limit 1500
```

This creates `data/models/priority_classifier.pkl`

### Step 4: Deploy

Run the deployment script:

**Windows:**
```batch
deploy_ngrok.bat
```

**Linux/Mac:**
```bash
./deploy_ngrok.sh
```

You'll see output like:
```
Starting API server on port 4999...

Starting ngrok tunnel...

Your API will be available at: https://abc123.ngrok.io
Copy the HTTPS URL and paste it in Code_Hybrid.gs (line 12)

Press Ctrl+C to stop both server and ngrok
```

### Step 5: Copy ngrok URL

1. Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)
2. Open `addon/apps_script/Code_Hybrid.gs`
3. Update line 12:
   ```javascript
   const API_URL = 'https://abc123.ngrok.io';  // Your ngrok URL
   ```
4. Also update `API_KEY` with the same value from `.env`

---

## Testing Your Deployment

### Test 1: Health Check

```bash
curl https://your-ngrok-url.ngrok.io/health
```

Expected response:
```json
{
    "status": "ok",
    "model_loaded": true,
    "gemini_available": true,
    "cached_emails": 0,
    "cached_todos": 0
}
```

### Test 2: Classification

```bash
curl https://your-ngrok-url.ngrok.io/api/classify \
  -H "Authorization: Bearer your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "email": {
      "subject": "URGENT: Server down",
      "body": "Production server crashed. Need immediate help."
    }
  }'
```

Expected response:
```json
{
    "priority": "HIGH",
    "confidence": 0.94
}
```

### Test 3: Complete Workflow

```bash
curl https://your-ngrok-url.ngrok.io/api/process-email \
  -H "Authorization: Bearer your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "email": {
      "subject": "Board meeting tomorrow",
      "body": "Please prepare Q4 slides and review financials.",
      "sender": "ceo@company.com"
    }
  }'
```

Expected response:
```json
{
    "priority": "HIGH",
    "confidence": 0.92,
    "todos": [
        "Prepare Q4 slides for board meeting",
        "Review financial metrics"
    ],
    "cached": false
}
```

---

## ngrok Free Tier Limitations

### What's Included (Free)

- ✅ HTTPS tunnel to localhost
- ✅ 1 online ngrok process
- ✅ 4 tunnels/ngrok process
- ✅ 40 connections/minute
- ✅ Web inspection interface

### Limitations

- ⚠️ **URL changes on restart** - You'll need to update Code_Hybrid.gs each time
- ⚠️ **Session timeout** - Need to restart after 8 hours
- ⚠️ **No custom domain** - Random URL like abc123.ngrok.io

### Solutions

**For Testing:** Use free tier, update URL when it changes

**For Production:** Upgrade to ngrok Pro ($8/mo) or deploy to:
- Railway (free $5 credit)
- Heroku (free tier)
- Google Cloud Run (free tier)

---

## Production Deployment (Optional)

### Railway (Recommended - $5/month)

1. Go to https://railway.app
2. New Project → Deploy from GitHub
3. Connect your repository
4. Set root directory: `addon/api_server`
5. Add environment variables from `.env`
6. Deploy → Get permanent HTTPS URL
7. No need to update URL anymore!

### Google Cloud Run

```bash
# Build container
gcloud builds submit --tag gcr.io/YOUR_PROJECT/email-api

# Deploy
gcloud run deploy email-api \
  --image gcr.io/YOUR_PROJECT/email-api \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars PORT=4999,GEMINI_API_KEY=xxx,API_KEY=xxx
```

---

## Monitoring

### View ngrok Web Interface

While ngrok is running, visit:
```
http://localhost:4040
```

This shows:
- All HTTP requests in real-time
- Request/response details
- Timing information
- Error logs

### View Server Logs

The Flask server logs appear in your terminal:
```
[2025-01-15 10:30:45] POST /api/classify → 200 (234ms)
[2025-01-15 10:30:52] POST /api/process-email → 200 (1.8s)
```

---

## Troubleshooting

### Issue: "ngrok: command not found"

**Solution:** Install ngrok from https://ngrok.com/download

### Issue: "Model not found"

```
FileNotFoundError: ../../data/models/priority_classifier.pkl
```

**Solution:** Train the model first:
```bash
cd ../..
python pipeline/run_full_pipeline.py --source data/enron_mail_20150507 --limit 1500
```

### Issue: "Unauthorized" error

**Solution:** Make sure API_KEY in Code_Hybrid.gs matches .env file

### Issue: ngrok URL changes

**Solution:** 
- Free tier: Update Code_Hybrid.gs with new URL each restart
- Paid tier: Get static domain ($8/mo)
- Production: Deploy to Railway/Heroku (permanent URL)

### Issue: "CORS error" from Apps Script

**Solution:** Already handled! The API has CORS enabled for all origins.

---

## Security Best Practices

1. **Never commit .env file** - Add to .gitignore
2. **Use strong API_KEY** - Generate with `secrets.token_hex(16)`
3. **HTTPS only** - ngrok provides this automatically
4. **Rotate keys** - Change API_KEY periodically
5. **Monitor usage** - Check ngrok dashboard for suspicious activity

---

## Cost Breakdown

### Development (ngrok free)

- API Server: $0
- ngrok: $0
- Gemini API: $0 (60 req/min free)
- **Total: $0/month** ✅

### Production (Railway)

- Railway Hobby: $5/month
- Gemini API: $0 (rarely hit limits)
- **Total: $5/month**

### Production (ngrok Pro)

- API Server: $0 (run on your machine)
- ngrok Pro: $8/month
- Gemini API: $0
- **Total: $8/month**

---

## Next Steps

1. ✅ Deploy API with ngrok
2. ✅ Test endpoints with curl
3. ✅ Copy ngrok URL to Code_Hybrid.gs
4. ✅ Deploy Apps Script to Gmail
5. ✅ Open email in Gmail → See results!

**Ready to go!** Your ML model is now accessible via API. 🚀

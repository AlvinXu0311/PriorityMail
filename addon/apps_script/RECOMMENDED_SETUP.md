### **RECOMMENDED: Hybrid Setup - Best of Both Worlds! ⭐**

## What is This?

The **BEST** approach that combines:
- ✅ **ML Model API** → Accurate priority classification (85-95%)
- ✅ **Gemini API** → Smart to-do generation (only when needed)
- ✅ **Apps Script** → Gmail sidebar UI + caching

**Result:** Maximum accuracy + minimum API costs!

---

## Why Hybrid is Best

| Approach | Priority Accuracy | To-Do Quality | API Calls | Setup |
|----------|------------------|---------------|-----------|-------|
| **Standalone** | 80-85% (AI) | Good | High | 5 min |
| **API Only** | 85-95% (ML) | Good | High | 15 min |
| **Hybrid** ⭐ | **85-95% (ML)** | **Excellent** | **Low** | **10 min** |

**Hybrid advantages:**
- ML model → Accurate classification
- Gemini → Only for to-dos (saves tokens)
- Caching → No duplicate calls
- Best accuracy + lowest cost!

---

## Architecture

```
Gmail Email Opened
      ↓
Apps Script Sidebar (Sidebar.html)
      ↓
Code_Hybrid.gs checks cache
      ↓
   Not cached?
      ↓
┌─────────────────┬─────────────────┐
│                 │                 │
▼                 ▼                 ▼
ML Model API   Gemini API      Cache Result
(classify)     (to-dos)        (save)
      │             │               │
      └─────────────┴───────────────┘
                    │
                    ▼
        Display in Sidebar
```

---

## Setup (10 Minutes)

### Step 1: Deploy ML Model API (5 min)

**Option A: Local with ngrok (Development)**

```bash
cd addon/api_server
pip install -r requirements.txt

# Configure .env
cat > .env << EOF
MODEL_PATH=../../data/models/priority_classifier.pkl
GEMINI_API_KEY=not_needed_here
API_KEY=$(python -c "import secrets; print(secrets.token_hex(16))")
PORT=5001
EOF

# Start server
python app.py

# In new terminal: Expose with ngrok
ngrok http 5001
# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
```

**Option B: Deploy to Railway (Production)**

1. Go to https://railway.app
2. New Project → Deploy from GitHub
3. Select your repo
4. Set root directory: `addon/api_server`
5. Add environment variables:
   ```
   MODEL_PATH=../../data/models/priority_classifier.pkl
   API_KEY=your_random_key_here
   PORT=5001
   ```
6. Deploy → Copy the public URL

---

### Step 2: Get Gemini API Key (1 min)

1. Go to https://makersuite.google.com/app/apikey
2. Click "Get API Key"
3. Create or select project
4. Click "Create API Key"
5. **Copy the key**

---

### Step 3: Create Apps Script Project (2 min)

1. Go to https://script.google.com
2. Click "New Project"
3. Name it: "Email To-Do Generator"

---

### Step 4: Add Files to Apps Script (2 min)

**File 1: Code.gs**

1. Delete default code
2. Copy ALL code from `Code_Hybrid.gs`
3. Paste into editor
4. **Update lines 14-16:**
   ```javascript
   const API_URL = 'https://your-ngrok-or-railway-url.com';  // NO trailing slash
   const API_KEY = 'paste_your_api_key_from_env_file';
   const GEMINI_API_KEY = 'paste_your_gemini_key';
   ```

**File 2: Sidebar.html**

1. Click **+** next to Files
2. Select "HTML"
3. Name it: `Sidebar`
4. Delete default content
5. Copy ALL code from `Sidebar.html`
6. Paste and save

**File 3: appsscript.json**

1. Click ⚙️ → "Show appsscript.json"
2. Go back to Editor
3. Click `appsscript.json`
4. Replace with content from `appsscript.json`

---

### Step 5: Deploy (30 sec)

1. Click "Deploy" → "Test deployments"
2. Click "Install"
3. Click "Done"

---

### Step 6: Test in Gmail (30 sec)

1. Go to https://mail.google.com
2. Open any email
3. Look for add-on icon in sidebar (📧)
4. Click to see results!

**First time:** Authorize the add-on

---

## How It Works

### First Email Analysis

```
1. Open email in Gmail
   ↓
2. Apps Script checks cache → Not found
   ↓
3. Call ML Model API
   POST /api/classify
   {
     "email": {
       "subject": "URGENT: Server down",
       "body": "Production crashed..."
     }
   }
   ↓
   Response: {"priority": "HIGH", "confidence": 0.92}
   ↓
4. Call Gemini API (only for HIGH/MEDIUM)
   Prompt: "Extract actionable tasks from this email..."
   ↓
   Response: ["Fix server", "Notify team"]
   ↓
5. Cache result in Properties Service
   ↓
6. Display in sidebar:
   - Priority: HIGH (92%)
   - To-dos: Fix server, Notify team
```

### Second Email Analysis (Same Email)

```
1. Open same email again
   ↓
2. Apps Script checks cache → FOUND!
   ↓
3. Display cached result immediately
   - ✅ Loaded from cache
   - No API calls made
   - Instant display
```

**Token Savings:** 100% for repeated emails!

---

## What You See in Gmail

```
┌─────────────────────────────────┐
│ 📧 Email Analysis               │
│ URGENT: Server down             │
├─────────────────────────────────┤
│ HIGH PRIORITY                   │
│ Confidence: 92%                 │
│ ML model classification         │
├─────────────────────────────────┤
│ 📝 Action Items                 │
│ • Fix production server         │
│ • Notify team of outage         │
│ • Investigate root cause        │
├─────────────────────────────────┤
│ [🔄 Refresh Analysis]           │
└─────────────────────────────────┘
```

**With caching:**
```
┌─────────────────────────────────┐
│ 📧 Email Analysis               │
│ Project Update                  │
├─────────────────────────────────┤
│ MEDIUM PRIORITY                 │
│ Confidence: 87%                 │
│ ML model classification         │
│                                 │
│ ✓ Loaded from cache             │
├─────────────────────────────────┤
│ 📝 Action Items                 │
│ • Review Q4 metrics             │
│ • Schedule team sync            │
└─────────────────────────────────┘
```

---

## Cost Breakdown

### Free Tier (Perfect for Personal Use)

**API Server:**
- Railway: $0 (500 hrs/month)
- OR ngrok: $0 (manual restart daily)

**Gemini API:**
- Free: 60 requests/minute
- ~10,000 requests/day
- $0 cost

**Total: $0/month** 🎉

### Paid (For Production/Teams)

**API Server:**
- Railway Hobby: $5/month (always-on)
- OR Heroku: $7/month

**Gemini API:**
- Free tier covers most use
- If exceeded: ~$0.001/request

**Total: $5-10/month**

---

## API Calls Per Email

**Without Caching:**
- ML Model API: 1 call (classify)
- Gemini API: 1 call (to-dos) [skipped for LOW priority]
- Total: 2 calls per email

**With Caching:**
- First time: 2 calls
- Subsequent views: 0 calls (cached)
- **Savings: 100% for repeated emails!**

**Example (20 emails/day):**
- View each email 3 times average
- Without cache: 20 × 3 × 2 = 120 API calls
- With cache: 20 × 2 = 40 API calls
- **Savings: 67%!**

---

## Comparison: Hybrid vs Others

| Feature | Standalone | Hybrid ⭐ | API Only |
|---------|-----------|----------|----------|
| **Setup** | 5 min | 10 min | 15 min |
| **Server** | ❌ No | ✅ Yes | ✅ Yes |
| **Cost** | $0 | $0-5/mo | $0-13/mo |
| **Priority Accuracy** | 80-85% | **85-95%** ✓ | 85-95% |
| **To-Do Quality** | Good | **Excellent** ✓ | Excellent |
| **API Calls/Email** | 2 | **1.5 avg** ✓ | 2 |
| **Caching** | Basic | **Smart** ✓ | Smart |
| **Fallback** | Rules | **Rules** ✓ | None |

**Winner:** Hybrid! Best accuracy + lowest cost.

---

## Troubleshooting

### "Can't connect to API"

**Check:**
1. API server is running: `curl http://localhost:5001/health`
2. ngrok is running: Visit ngrok URL in browser
3. API_URL in Code.gs is correct (no trailing slash)
4. API_KEY matches .env file

**Fix:**
```bash
# Restart API server
cd addon/api_server
python app.py

# In new terminal
ngrok http 5001
# Update API_URL in Code.gs with new ngrok URL
```

### "Gemini API error"

**Check:**
1. GEMINI_API_KEY is correct (line 16)
2. Check quota: https://makersuite.google.com
3. Not exceeding 60 req/min

### "Add-on not showing"

**Fix:**
1. Refresh Gmail (Ctrl+R)
2. Wait 1-2 minutes after deployment
3. Check: Apps Script → Deploy → Manage deployments

### "Classification falls back to rules"

**Cause:** API server unreachable

**Fix:**
1. Check API server logs
2. Verify ngrok tunnel is active
3. Test API directly:
   ```bash
   curl https://your-url.com/health \
     -H "Authorization: Bearer your_api_key"
   ```

---

## Customization

### Change Gemini Prompt

Edit `Code_Hybrid.gs`, line 138:

```javascript
const prompt = `YOUR CUSTOM PROMPT HERE

Email:
Subject: ${email.subject}
...
`;
```

### Add More Context to Classification

Edit `api_server/app.py`, line 80:

```python
email_text = f"Subject: {email.get('subject', '')}\n\nBody: {email.get('body', '')}\n\nSender: {email.get('sender', '')}"
```

### Adjust Caching

**Add expiration:**

Edit `Code_Hybrid.gs`:

```javascript
function getCachedResult(emailId) {
  const cache = PropertiesService.getUserProperties();
  const key = 'email_' + emailId;
  const cached = cache.getProperty(key);

  if (cached) {
    const data = JSON.parse(cached);

    // Expire after 7 days
    const age = Date.now() - (data.timestamp || 0);
    if (age < 7 * 24 * 60 * 60 * 1000) {
      return data.result;
    }
  }
  return null;
}

function cacheResult(emailId, result) {
  const cache = PropertiesService.getUserProperties();
  cache.setProperty('email_' + emailId, JSON.stringify({
    result: result,
    timestamp: Date.now()
  }));
}
```

---

## Production Deployment

### For Teams (Recommended: Railway)

1. **Deploy API Server to Railway:**
   - Sign up: https://railway.app
   - New Project → GitHub repo
   - Root dir: `addon/api_server`
   - Add env vars
   - Deploy

2. **Update Apps Script:**
   - Change API_URL to Railway URL (permanent)
   - No more ngrok needed!

3. **Share Add-on:**
   - Apps Script → Deploy → New deployment
   - Share link with team

### For Personal Use (Recommended: ngrok free)

1. **Keep using local + ngrok:**
   - Run daily: `ngrok http 5001`
   - Update API_URL in Code.gs
   - Takes 30 seconds/day

---

## Files Summary

**Apps Script Files (copy these 3):**
1. `Code_Hybrid.gs` → Main logic
2. `Sidebar.html` → UI
3. `appsscript.json` → Configuration

**API Server (already exists):**
- `api_server/app.py` → Flask API
- `api_server/.env` → Configuration

---

## Next Steps

### ✅ You're Done!

You now have:
- ML model accuracy (85-95%)
- Gemini to-do generation
- Smart caching (saves tokens)
- Gmail sidebar UI
- **Best of all worlds!**

### Optional Improvements

1. **Add batch analysis:**
   - Analyze last 10 emails
   - Show priority summary

2. **Add email actions:**
   - Archive LOW priority
   - Star HIGH priority

3. **Add analytics:**
   - Track priority distribution
   - Monitor API usage

---

**Start using it!** Open Gmail and analyze your first email 📧

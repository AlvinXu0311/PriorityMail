# Gmail Add-on - STANDALONE Setup (NO API SERVER!)

## What's Different?

This version runs **100% in Google Apps Script** - no API server needed!

✅ **Pros:**
- Super simple setup (5 minutes)
- No server to maintain
- Free forever
- Works everywhere (browser-based)

❌ **Cons:**
- Cannot use the trained ML model (Python-only)
- Uses Gemini AI for both priority classification AND to-do generation
- Slightly less accurate than ML model

---

## Setup (5 Minutes)

### Step 1: Get Gemini API Key (1 min)

1. Go to: https://makersuite.google.com/app/apikey
2. Click "Get API Key"
3. Create or select a project
4. Click "Create API Key"
5. **Copy the key** (you'll need it)

---

### Step 2: Create Apps Script Project (2 min)

1. Go to: https://script.google.com
2. Click "New Project"
3. Name it: "Email To-Do Generator"

---

### Step 3: Add Code (1 min)

1. **Delete** the default code in the editor

2. **Copy ALL code** from [`Code_Standalone.gs`](Code_Standalone.gs)

3. **Paste** into the editor

4. **Update line 11** with your Gemini API key:
   ```javascript
   const GEMINI_API_KEY = 'paste_your_actual_key_here';
   ```

---

### Step 4: Add Configuration (30 sec)

1. Click **gear icon** ⚙️ (Project Settings)
2. Check **"Show appsscript.json in editor"**
3. Go back to **Editor**
4. Click **`appsscript.json`** file
5. **Replace content** with code from [`appsscript.json`](appsscript.json)

---

### Step 5: Deploy (30 sec)

1. Click **"Deploy"** → **"Test deployments"**
2. Click **"Install"**
3. Click **"Done"**

---

### Step 6: Use It! (30 sec)

1. Go to: https://mail.google.com
2. Open any email
3. Look for add-on icon in sidebar (📧)
4. Click to see analysis!

**First time:** Click "Authorize" and allow permissions

---

## What You'll See

```
┌──────────────────────────────┐
│ 📧 Email Analysis            │
│ Project Update               │
├──────────────────────────────┤
│ Priority                     │
│ HIGH                         │
│ Confidence: 92%              │
│ Urgent deadline mentioned    │
├──────────────────────────────┤
│ 📝 Action Items              │
│ • Submit Q4 report by Friday │
│ • Review budget proposal     │
│ • Schedule team meeting      │
├──────────────────────────────┤
│ ✅ Loaded from cache         │
└──────────────────────────────┘
```

---

## Features

### ✅ Smart Caching

Once an email is analyzed:
- Results are cached using Properties Service
- No repeat Gemini API calls
- Instant loading on revisit
- Shows "✅ Loaded from cache"

### ✅ Priority Classification

Gemini AI analyzes:
- Urgency keywords (urgent, asap, critical)
- Sender importance
- Time sensitivity
- Context and tone

Returns:
- Priority: HIGH/MEDIUM/LOW
- Confidence: 0-100%
- Reason: Brief explanation

### ✅ To-Do Generation

Extracts actionable tasks:
- Specific tasks mentioned
- Deadlines included
- Ignores greetings/signatures
- Skips LOW priority (saves API calls)

### ✅ Batch Analysis

Click "Analyze Last 10 Emails":
- Processes recent inbox
- Shows priority breakdown
- Lists high-priority emails

---

## How It Works

### Priority Classification

1. **Email content** sent to Gemini
2. **AI analyzes** urgency, sender, context
3. **Returns** HIGH/MEDIUM/LOW + confidence
4. **Fallback:** Rule-based if Gemini fails

**Prompt example:**
```
Analyze this email and classify its priority level.

Email:
Subject: URGENT: Server down
From: admin@company.com
Body: Production server crashed...

Priority Levels:
- HIGH: Urgent, time-sensitive...
- MEDIUM: Important but not urgent...
- LOW: Informational, newsletters...

Respond with JSON: {"priority": "HIGH", "confidence": 0.95}
```

### To-Do Generation

1. **Email + priority** sent to Gemini
2. **AI extracts** actionable tasks
3. **Returns** JSON array of tasks
4. **Cached** for future visits

**Prompt example:**
```
Extract actionable to-do items from this email.

Email:
Subject: Project deadline
From: boss@company.com
Body: Please submit report by Friday...

Return JSON array: ["Submit report by Friday", "..."]
```

---

## Cost

**Gemini API (Free Tier):**
- 60 requests per minute
- ~10,000 requests per day
- $0 cost!

**For typical use:**
- 20 emails/day = 40 API calls (classify + todos)
- Well within free tier
- Cost: **$0/month** 🎉

**If you exceed free tier:**
- Pay-as-you-go pricing
- ~$0.001 per request
- 100 emails/day = ~$3/month

---

## Comparison: Standalone vs API Server

| Feature | Standalone (This) | API Server |
|---------|------------------|------------|
| **Setup** | 5 minutes | 15+ minutes |
| **Maintenance** | None | Server upkeep |
| **Cost** | $0 forever | $0-13/month |
| **Priority Accuracy** | 80-85% (AI) | 85-95% (ML model) |
| **To-Do Quality** | High (Gemini) | High (Gemini) |
| **Speed** | 2-3 sec | 1-2 sec |
| **Caching** | ✅ Yes | ✅ Yes |
| **Offline** | ❌ No | ❌ No |

**Recommendation:** Use standalone for personal use, API server for teams.

---

## Troubleshooting

### "Gemini API error"

**Fix:**
1. Check API key is correct (line 11)
2. Verify key at https://makersuite.google.com
3. Check you haven't exceeded quota (60 req/min)

### "Permission denied"

**Fix:**
1. Click add-on icon
2. Click "Authorize"
3. Choose your Gmail account
4. Click "Advanced" → "Go to Email To-Do Generator (unsafe)"
5. Click "Allow"

### "Add-on not showing"

**Fix:**
1. Refresh Gmail (Ctrl+R)
2. Wait 1-2 minutes after deployment
3. Check deployment: Apps Script → Deploy → Manage deployments

### "No tasks found for HIGH priority email"

**Possible reasons:**
- Email truly has no actionable items
- Gemini interpreted it as informational
- Try clicking "Refresh" to re-analyze

### "Cache not working"

**Fix:**
1. Check Properties Service quota (not exceeded)
2. Try "Clear Cache" button
3. Re-authorize add-on

---

## Customization

### Adjust Priority Keywords

Edit `classifyPriorityWithRules()` function (line 141):

```javascript
const highKeywords = ['urgent', 'asap', 'critical', 'emergency', 'important', 'deadline', 'immediately', 'YOUR_KEYWORD'];
```

### Modify Gemini Prompts

**Priority classification** (line 115):
```javascript
const prompt = `Your custom classification prompt...`;
```

**To-do generation** (line 180):
```javascript
const prompt = `Your custom to-do extraction prompt...`;
```

### Change Cache Duration

Properties Service stores data indefinitely. To add expiration:

```javascript
function cacheTodos(emailId, todos) {
  const cache = PropertiesService.getUserProperties();
  cache.setProperty('todos_' + emailId, JSON.stringify({
    todos: todos,
    timestamp: Date.now()
  }));
}

function getCachedTodos(emailId) {
  const cache = PropertiesService.getUserProperties();
  const cached = cache.getProperty('todos_' + emailId);

  if (cached) {
    const data = JSON.parse(cached);
    const age = Date.now() - data.timestamp;

    // Expire after 7 days
    if (age < 7 * 24 * 60 * 60 * 1000) {
      return data.todos;
    }
  }
  return null;
}
```

---

## Advanced: Share with Team

### Step 1: Deploy as Add-on

1. Click "Deploy" → "New deployment"
2. Type: "Add-on"
3. Description: "AI-powered email analysis"
4. Click "Deploy"

### Step 2: Share Link

1. Copy installation URL
2. Send to team members
3. They click link → Install

**Note:** They'll use YOUR Gemini API key. For teams, consider API server approach.

---

## Security & Privacy

**What data is accessed:**
- Email subject, body, sender (read-only)
- Sent to Gemini API for analysis
- Cached in your Google account

**What we DON'T do:**
- Send emails
- Delete emails
- Modify emails
- Store emails externally

**Gemini API:**
- Processes in real-time
- Not stored by Google (unless opted in)
- See: https://ai.google.dev/terms

---

## Limitations

### Cannot Use ML Model

The trained scikit-learn model is Python-only. Apps Script is JavaScript.

**Workaround:** Use Gemini AI for classification (80-85% accuracy vs 85-95% ML)

### Rate Limits

**Gemini API:**
- Free: 60 requests/minute
- Paid: Higher limits

**Properties Service:**
- 500 KB total storage
- ~500 cached emails max

**Gmail API:**
- 1 billion quota units/day (plenty)

### No Real-time Updates

- Analyzes when you open email
- Not automatic for all incoming emails
- Can manually trigger batch analysis

---

## Next Steps

### ✅ Done!

You now have:
- Gmail sidebar add-on
- AI-powered priority classification
- Automatic to-do extraction
- Smart caching (saves API calls)
- **Total cost: $0!**

### Want More Accuracy?

Use the API server approach:
- 85-95% priority accuracy (ML model)
- Same Gemini to-do generation
- Requires server setup

See: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---

**Start using it now!** Open Gmail and click any email 📧

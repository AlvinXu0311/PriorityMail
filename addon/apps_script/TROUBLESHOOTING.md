# Troubleshooting Apps Script Deployment

## Error: "Cannot read properties of undefined (reading 'name')"

This error has been FIXED with better error handling. If you still see it:

### Solution 1: Update Your Code

Make sure you're using the LATEST version of Code_Hybrid.gs with these fixes:

1. **Line 23-26:** Checks if `e.gmail` exists
2. **Line 370-372:** Validates message structure  
3. **Line 389-401:** Safe header reading with null checks
4. **Line 45-48:** Better error logging

### Solution 2: Check Deployment Steps

**IMPORTANT:** You CANNOT test by clicking "Run" in the editor!

✅ **Correct way to test:**

1. **Deploy as Test Deployment**
   - Click **Deploy** → **Test deployments**
   - Click **Install**
   - Grant permissions

2. **Test in Gmail (NOT in Apps Script editor)**
   - Open https://mail.google.com
   - Refresh page (Ctrl+R)
   - Click ANY email
   - Look for add-on in right sidebar
   - Click the add-on icon

❌ **Wrong way (causes errors):**
- Clicking "Run" button in Apps Script editor
- Testing without deploying first
- Not refreshing Gmail after deployment

### Solution 3: Check Configuration

Before deploying, verify these lines in Code.gs:

```javascript
// Line 12: Your ngrok HTTPS URL
const API_URL = 'https://abc123.ngrok.io';  // ← Must be YOUR ngrok URL

// Line 13: Your API key from .env file
const API_KEY = 'your_actual_api_key';      // ← Must match api_server/.env

// Line 14: Your Gemini API key
const GEMINI_API_KEY = 'AIza...';           // ← From Google AI Studio
```

### Solution 4: View Logs for Details

1. In Apps Script editor: **View** → **Logs**
2. Look for error details:
   ```
   Processing email: 18c1234567890abcd
   Email fetched: Meeting tomorrow
   Processing complete. Priority: MEDIUM
   ```

If you see errors in logs, they'll show exactly what failed.

---

## Error: "Please open this add-on from an actual Gmail message"

**Cause:** Trying to run the add-on from Apps Script editor

**Solution:** Deploy as "Test deployment" and open in Gmail

---

## Error: "API server is running" or connection errors

**Cause:** ngrok not running or wrong URL

**Solution:**

1. Start API server:
   ```batch
   cd addon\api_server
   deploy_ngrok.bat
   ```

2. Copy the HTTPS URL from output:
   ```
   https://abc123.ngrok.io
   ```

3. Update Code.gs line 12 with this URL

4. **Re-deploy** the add-on (Deploy → Test deployments)

5. **Refresh Gmail** page

---

## Error: "Unauthorized" from API

**Cause:** API_KEY mismatch

**Solution:**

1. Check API key in `addon/api_server/.env`:
   ```
   API_KEY=abc123def456
   ```

2. Update Code.gs line 13 with SAME key:
   ```javascript
   const API_KEY = 'abc123def456';
   ```

3. **Re-deploy** the add-on

---

## Add-on doesn't appear in Gmail

**Possible causes & solutions:**

### 1. Not deployed yet
- Deploy → Test deployments → Install

### 2. Permissions not granted
- Re-install and click "Allow" on all permission requests

### 3. Gmail not refreshed
- Press Ctrl+R or F5 to refresh Gmail

### 4. Wrong Gmail account
- Make sure you're logged into the SAME Google account where you installed the add-on

### 5. Browser cache
- Clear browser cache and cookies
- Or try incognito mode

---

## No results showing / Blank card

**Cause:** API server not responding or Gemini error

**Check:**

1. **API server running?**
   - Should see Flask logs in terminal
   - Test: Open http://localhost:4999/health in browser
   - Should return: `{"status": "ok", "model_loaded": true}`

2. **ngrok tunnel active?**
   - Should see ngrok dashboard at http://localhost:4040
   - Shows all API requests

3. **Gemini API key valid?**
   - Test at https://aistudio.google.com
   - Make sure key has quota remaining

4. **Check Apps Script logs:**
   - View → Logs
   - Look for specific error messages

---

## "Invalid manifest" error in appsscript.json

**Cause:** Using old version with invalid fields

**Solution:** Use the corrected appsscript.json:

```json
{
  "timeZone": "America/New_York",
  "dependencies": {
    "enabledAdvancedServices": [
      {
        "userSymbol": "Gmail",
        "version": "v1",
        "serviceId": "gmail"
      }
    ]
  },
  "exceptionLogging": "STACKDRIVER",
  "runtimeVersion": "V8",
  "gmail": {
    "name": "Email To-Do Generator",
    "logoUrl": "https://www.gstatic.com/images/branding/product/1x/gmail_48dp.png",
    "contextualTriggers": [
      {
        "unconditional": {},
        "onTriggerFunction": "onGmailMessageOpen"
      }
    ],
    "homepageTrigger": {
      "runFunction": "onHomepage",
      "enabled": true
    }
  },
  "oauthScopes": [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.addons.current.message.readonly",
    "https://www.googleapis.com/auth/script.external_request"
  ]
}
```

---

## Complete Deployment Checklist

### Before Deployment:

- [ ] API server running (`deploy_ngrok.bat`)
- [ ] ngrok URL copied
- [ ] Code.gs line 12: ngrok URL updated
- [ ] Code.gs line 13: API_KEY from .env
- [ ] Code.gs line 14: Gemini API key
- [ ] appsscript.json copied (Settings → Show manifest)

### Deployment:

- [ ] Deploy → Test deployments
- [ ] Click Install
- [ ] Grant all permissions

### Testing:

- [ ] Open Gmail (https://mail.google.com)
- [ ] Refresh page (Ctrl+R)
- [ ] Click any email
- [ ] See add-on in right sidebar
- [ ] Click add-on icon
- [ ] See priority + to-dos!

---

## Still Having Issues?

1. **Check logs** (View → Logs in Apps Script)
2. **Check API logs** (terminal where deploy_ngrok.bat is running)
3. **Check ngrok dashboard** (http://localhost:4040)

Error messages will show exactly what's wrong!

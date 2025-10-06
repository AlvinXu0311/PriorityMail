# Quick Start - 5 Minutes ⚡

Get the Gmail To-Do Generator running in 5 minutes!

## Prerequisites Check

```bash
# Python 3.8+
python --version

# Pip installed
pip --version

# Ollama running (for embeddings)
ollama list
```

---

## Step 1: Install (1 min)

```bash
cd addon
pip install -r requirements.txt
```

---

## Step 2: Setup OAuth (2 min)

1. Go to https://console.cloud.google.com/
2. Create project → Enable Gmail API
3. Create OAuth credentials (Web app)
4. Add redirect URI: `http://localhost:5000/oauth2callback`
5. Download JSON → Save as `addon/credentials.json`

---

## Step 3: Get Gemini Key (1 min)

1. Go to https://makersuite.google.com/app/apikey
2. Create API key
3. Copy it

---

## Step 4: Configure (30 sec)

Create `addon/.env`:

```env
GEMINI_API_KEY=paste_your_key_here
FLASK_SECRET_KEY=any_random_string_here
MODEL_PATH=../data/models/priority_classifier.pkl
```

---

## Step 5: Run (30 sec)

```bash
python app.py
```

Open: http://localhost:5000

**Done!** 🎉

---

## First Use

1. Click "Sign in with Google"
2. Authorize the app
3. Click "Check for New Emails"
4. Wait ~30-60 seconds
5. See your AI-generated to-do list!

---

## Troubleshooting

**"credentials.json not found"**
→ Download OAuth credentials from Google Cloud Console

**"GEMINI_API_KEY not set"**
→ Add your Gemini key to `.env` file

**"Model not found"**
→ Train model first:
```bash
cd ..
python pipeline/run_full_pipeline.py --source data/enron_mail_20150507 --limit 1500
```

**"Ollama not responding"**
→ Start Ollama:
```bash
ollama pull nomic-embed-text
ollama serve
```

---

## What's Next?

- Read [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed setup
- Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand how it works
- Read [README.md](README.md) for features overview

---

**Questions?** Open an issue or check the docs!

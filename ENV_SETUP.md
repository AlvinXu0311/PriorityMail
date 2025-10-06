# PriorityMail - Environment Variables Setup Guide

> **DRAFT VERSION - FOR TESTING AND EVALUATION PURPOSES ONLY**

## Overview

All environment variables have been consolidated into a single `.env` file at the project root. The codebase now uses a centralized configuration module (`config.py`) for all settings.

## Quick Start

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` and fill in your actual values:**
   - Replace all `your_*_here` placeholders with real values
   - Generate secure keys where indicated

3. **Required API Keys:**
   - `OPENAI_API_KEY` - If using OpenAI embeddings
   - `GEMINI_API_KEY` - For todo generation features

## Security Keys Generation

Generate secure random keys for production:

```bash
# Flask Secret Key (64 characters)
python -c "import secrets; print(secrets.token_hex(32))"

# API Key (32 characters)
python -c "import secrets; print(secrets.token_hex(16))"
```

## Important Notes

WARNING: NEVER commit the `.env` file to Git!
- The `.env` file is already in `.gitignore`
- Only commit `.env.example` with placeholder values
- Share actual credentials securely (password manager, secrets vault, etc.)

## Configuration Module

### Centralized Config (`config.py`)
All configuration is now loaded through `config.py`:
- Loads environment variables with sensible defaults
- Provides validation for required settings
- Creates necessary directories automatically

### Usage in Code
```python
import config

# Access configuration
api_key = config.GEMINI_API_KEY
model_path = config.CLASSIFIER_MODEL_PATH
```

## Environment Variables Reference

### API Keys (Required)
| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key | If using OpenAI embeddings |
| `GEMINI_API_KEY` | Google Gemini API key | For todo generation |

### Security Keys (Required for Production)
| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_SECRET_KEY` | Flask session secret | `dev-secret-key-change-in-production` |
| `API_KEY` | API server auth key | `dev-api-key-change-in-production` |

### Priority Classification Mode
| Variable | Description | Default |
|----------|-------------|---------|
| `PRIORITY_MODE` | Classification mode: `ml_model` or `llm_only` | `ml_model` |

**Mode Options:**
- `ml_model` (RECOMMENDED): Uses trained ML model for classification + Gemini for todo generation
  - Faster (no API calls for classification)
  - More accurate (85-95%)
  - Lower cost (only uses API for todos)

- `llm_only`: Uses Gemini LLM for both classification and todo generation
  - No ML model needed
  - Slower (API calls for everything)
  - Higher API costs
  - Accuracy: 80-85%

### Gemini Configuration
| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_MODEL_NAME` | Gemini model name | `gemini-pro` |

### Server Configuration
| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_HOST` | Flask server host | `0.0.0.0` |
| `FLASK_PORT` | Flask server port | `5000` |
| `FLASK_DEBUG` | Debug mode | `false` |
| `API_SERVER_PORT` | API server port | `4999` |

### Gmail API Configuration
| Variable | Description | Default |
|----------|-------------|---------|
| `GMAIL_SCOPES` | Gmail API scopes | `https://www.googleapis.com/auth/gmail.readonly` |
| `EMAIL_FETCH_DAYS` | Days to look back | `7` |
| `EMAIL_FETCH_MAX_RESULTS` | Max emails per fetch | `100` |

### File Paths
| Variable | Description | Default |
|----------|-------------|---------|
| `CACHE_DIR` | Cache directory | `cache` |
| `DATA_MODELS_DIR` | Models directory | `data/models` |
| `CLASSIFIER_MODEL_FILE` | Classifier model filename | `priority_classifier.pkl` |
| `GMAIL_CREDENTIALS_FILE` | Gmail OAuth credentials | `credentials.json` |
| `GMAIL_TOKEN_FILE` | Gmail OAuth token | `token.pickle` |

## Directory Structure

The following directories are auto-created by `config.ensure_directories()`:
- `cache/` - Application cache
- `data/models/` - Trained models

## Troubleshooting

### Missing Configuration Error
If you see validation errors about missing configuration:
1. Check your `.env` file exists in the project root
2. Ensure all required variables are set
3. Remove placeholder values like `your_*_here`

### Import Errors
If you get import errors for `config` module:
- Ensure `config.py` is in the project root
- Check that `sys.path.insert()` is at the top of the file

### Path Issues
If files aren't found:
- Run `config.ensure_directories()` to create all needed directories
- Check that paths in `.env` are relative to project root

## Best Practices

1. **Development vs Production:**
   - Use `.env` for development
   - Use environment variables or secrets manager in production
   - Never use default security keys in production

2. **Git Safety:**
   - Always check `.gitignore` before committing
   - Use `git status` to verify `.env` is not staged
   - If `.env` was committed, rotate all keys immediately

3. **Team Sharing:**
   - Share `.env.example` with the team
   - Document any new variables you add
   - Use consistent naming conventions

4. **API Keys:**
   - Rotate keys regularly
   - Use different keys for dev/staging/prod
   - Monitor API usage for suspicious activity

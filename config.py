"""
PriorityMail - Centralized Configuration Module

DRAFT VERSION - FOR TESTING AND EVALUATION PURPOSES ONLY

Loads all configuration from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# API KEYS
# ============================================================================

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# ============================================================================
# SECURITY KEYS
# ============================================================================

FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
API_KEY = os.getenv('API_KEY', 'dev-api-key-change-in-production')

# ============================================================================
# PRIORITY CLASSIFICATION MODE
# ============================================================================

PRIORITY_MODE = os.getenv('PRIORITY_MODE', 'ml_model')  # 'ml_model' or 'llm_only'

# ============================================================================
# GEMINI CONFIGURATION
# ============================================================================

GEMINI_MODEL_NAME = os.getenv('GEMINI_MODEL_NAME', 'gemini-pro')

# ============================================================================
# FILE PATHS & DIRECTORIES
# ============================================================================

# Cache Directory
CACHE_DIR = os.getenv('CACHE_DIR', 'cache')

# Model Path
DATA_MODELS_DIR = os.getenv('DATA_MODELS_DIR', 'data/models')
CLASSIFIER_MODEL_FILE = os.getenv('CLASSIFIER_MODEL_FILE', 'priority_classifier.pkl')
CLASSIFIER_MODEL_PATH = os.path.join(DATA_MODELS_DIR, CLASSIFIER_MODEL_FILE)

# OAuth Files
GMAIL_CREDENTIALS_FILE = os.getenv('GMAIL_CREDENTIALS_FILE', 'credentials.json')
GMAIL_TOKEN_FILE = os.getenv('GMAIL_TOKEN_FILE', 'token.pickle')

# ============================================================================
# SERVER CONFIGURATION
# ============================================================================

FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'

API_SERVER_PORT = int(os.getenv('API_SERVER_PORT', '4999'))

# ============================================================================
# GMAIL API CONFIGURATION
# ============================================================================

GMAIL_SCOPES = os.getenv('GMAIL_SCOPES', 'https://www.googleapis.com/auth/gmail.readonly').split(',')
EMAIL_FETCH_DAYS = int(os.getenv('EMAIL_FETCH_DAYS', '7'))
EMAIL_FETCH_MAX_RESULTS = int(os.getenv('EMAIL_FETCH_MAX_RESULTS', '100'))


def validate_required_config(required_keys):
    """
    Validate that required configuration keys are set.

    Args:
        required_keys: List of required configuration variable names

    Raises:
        ValueError: If any required keys are missing or have placeholder values
    """
    missing = []
    placeholders = []

    for key in required_keys:
        value = globals().get(key)
        if not value:
            missing.append(key)
        elif isinstance(value, str) and ('your_' in value or 'change-in-production' in value):
            placeholders.append(key)

    if missing or placeholders:
        error_msg = "Configuration validation failed:\n"
        if missing:
            error_msg += f"Missing required configuration: {', '.join(missing)}\n"
        if placeholders:
            error_msg += f"Placeholder values detected: {', '.join(placeholders)}\n"
        error_msg += "\nPlease update your .env file with actual values."
        raise ValueError(error_msg)


def ensure_directories():
    """Create necessary directories if they don't exist."""
    directories = [
        CACHE_DIR,
        DATA_MODELS_DIR
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

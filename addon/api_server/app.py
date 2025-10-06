"""
PriorityMail - Flask API Server

DRAFT VERSION - FOR TESTING AND EVALUATION PURPOSES ONLY

This API server provides endpoints for:
1. Email priority classification (ML model or LLM-based)
2. AI-powered to-do generation
3. Caching to avoid token waste

Designed to work with Google Apps Script Gmail add-on.
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import config
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import google.generativeai as genai
import json
import hashlib

from core.embeddings import EmailEmbedder

# Load environment
load_dotenv()

# Ensure directories exist
config.ensure_directories()

# Initialize Flask
app = Flask(__name__)
CORS(app)  # Enable CORS for Apps Script

# Configuration
MODEL_PATH = config.CLASSIFIER_MODEL_PATH
GEMINI_API_KEY = config.GEMINI_API_KEY
API_KEY = config.API_KEY
PRIORITY_MODE = config.PRIORITY_MODE

# In-memory cache (for demo - use Redis in production)
processed_cache = set()
todos_cache = {}

# Initialize based on mode
classifier = None
embedder = None

if PRIORITY_MODE == 'ml_model':
    # Load ML model for classification
    print(f"Mode: ML Model + LLM Generation (PRIORITY_MODE={PRIORITY_MODE})")
    print("Loading classification model...")
    with open(MODEL_PATH, 'rb') as f:
        model_data = pickle.load(f)

    classifier = model_data['model']
    embedder = EmailEmbedder(
        provider=model_data['embedder_provider'],
        model=model_data['embedder_model']
    )

    print(f"Model loaded: {type(classifier).__name__}")
    print(f"Embedder: {model_data['embedder_provider']} ({model_data['embedder_model']})")
else:
    print(f"Mode: LLM Only (PRIORITY_MODE={PRIORITY_MODE})")
    print("Classification will use Gemini LLM instead of ML model")

# Initialize Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel(config.GEMINI_MODEL_NAME)
    print("Gemini API initialized")
else:
    print("Warning: GEMINI_API_KEY not set")
    gemini_model = None


def verify_api_key():
    """Verify API key from request header."""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return False
    token = auth_header.replace('Bearer ', '')
    return token == API_KEY


def classify_with_llm(email_subject, email_body):
    """
    Classify email priority using Gemini LLM.

    Returns:
        tuple: (priority, confidence)
    """
    if not gemini_model:
        raise Exception("Gemini API not configured")

    prompt = f"""Classify this email's priority level as HIGH, MEDIUM, or LOW.

Email Subject: {email_subject}
Email Body: {email_body[:1000]}

Classification Criteria:
- HIGH: Urgent deadlines, critical issues, important meetings, direct requests from superiors
- MEDIUM: Regular work tasks, scheduled meetings, project updates, non-urgent requests
- LOW: Newsletters, notifications, FYI emails, automated messages

Respond with ONLY a JSON object in this exact format:
{{"priority": "HIGH|MEDIUM|LOW", "confidence": 0.0-1.0}}"""

    try:
        response = gemini_model.generate_content(prompt)
        result_text = response.text.strip()

        # Extract JSON from response
        if '```json' in result_text:
            result_text = result_text.split('```json')[1].split('```')[0].strip()
        elif '```' in result_text:
            result_text = result_text.split('```')[1].split('```')[0].strip()

        result = json.loads(result_text)
        priority = result.get('priority', 'MEDIUM')
        confidence = float(result.get('confidence', 0.5))

        return priority, confidence
    except Exception as e:
        print(f"LLM classification error: {e}")
        # Fallback to simple rules
        if any(word in email_subject.lower() for word in ['urgent', 'asap', 'critical', 'important']):
            return 'HIGH', 0.6
        elif any(word in email_subject.lower() for word in ['fyi', 'newsletter', 'notification']):
            return 'LOW', 0.6
        else:
            return 'MEDIUM', 0.5


def get_email_hash(email):
    """Generate hash for email to check if processed."""
    content = f"{email.get('subject', '')}{email.get('body', '')}{email.get('timestamp', '')}"
    return hashlib.md5(content.encode()).hexdigest()


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'model_loaded': classifier is not None,
        'gemini_available': gemini_model is not None,
        'cached_emails': len(processed_cache),
        'cached_todos': len(todos_cache)
    })


@app.route('/api/classify', methods=['POST'])
def classify_email():
    """
    Classify email priority.

    Request body:
    {
        "email": {
            "subject": "Meeting tomorrow",
            "body": "Let's discuss the project..."
        }
    }

    Response:
    {
        "priority": "HIGH",
        "confidence": 0.89,
        "method": "ml_model" or "llm"
    }
    """
    # Verify API key
    if not verify_api_key():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.json
        email = data.get('email', {})
        subject = email.get('subject', '')
        body = email.get('body', '')

        if PRIORITY_MODE == 'ml_model' and classifier and embedder:
            # Use ML model
            email_text = f"Subject: {subject}\n\nBody: {body}"
            embedding = embedder.embed_text(email_text)

            priority = classifier.predict([embedding])[0]

            if hasattr(classifier, 'predict_proba'):
                probs = classifier.predict_proba([embedding])[0]
                class_to_idx = {cls: idx for idx, cls in enumerate(classifier.classes_)}
                confidence = float(probs[class_to_idx[priority]])
            else:
                confidence = 1.0

            method = 'ml_model'
        else:
            # Use LLM
            priority, confidence = classify_with_llm(subject, body)
            method = 'llm'

        return jsonify({
            'priority': priority,
            'confidence': confidence,
            'method': method
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/classify-batch', methods=['POST'])
def classify_batch():
    """
    Classify multiple emails at once.

    Request body:
    {
        "emails": [
            {"subject": "...", "body": "..."},
            {"subject": "...", "body": "..."}
        ]
    }

    Response:
    {
        "results": [
            {"priority": "HIGH", "confidence": 0.89},
            {"priority": "MEDIUM", "confidence": 0.76}
        ]
    }
    """
    if not verify_api_key():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.json
        emails = data.get('emails', [])

        results = []
        for email in emails:
            subject = email.get('subject', '')
            body = email.get('body', '')

            if PRIORITY_MODE == 'ml_model' and classifier and embedder:
                # Use ML model
                email_text = f"Subject: {subject}\n\nBody: {body}"
                embedding = embedder.embed_text(email_text)

                priority = classifier.predict([embedding])[0]

                if hasattr(classifier, 'predict_proba'):
                    probs = classifier.predict_proba([embedding])[0]
                    class_to_idx = {cls: idx for idx, cls in enumerate(classifier.classes_)}
                    confidence = float(probs[class_to_idx[priority]])
                else:
                    confidence = 1.0

                method = 'ml_model'
            else:
                # Use LLM
                priority, confidence = classify_with_llm(subject, body)
                method = 'llm'

            results.append({
                'priority': priority,
                'confidence': confidence,
                'method': method
            })

        return jsonify({'results': results})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate-todos', methods=['POST'])
def generate_todos():
    """
    Generate to-dos from email using Gemini.

    Request body:
    {
        "email": {
            "subject": "Project deadline",
            "body": "Please submit the report by Friday...",
            "sender": "boss@company.com",
            "timestamp": "2025-01-15 10:30"
        },
        "priority": "HIGH"
    }

    Response:
    {
        "todos": [
            "Submit project report by Friday",
            "Review final draft with team"
        ],
        "cached": false
    }
    """
    if not verify_api_key():
        return jsonify({'error': 'Unauthorized'}), 401

    if not gemini_model:
        return jsonify({'error': 'Gemini API not configured'}), 500

    try:
        data = request.json
        email = data.get('email', {})
        priority = data.get('priority', 'MEDIUM')

        # Check cache
        email_hash = get_email_hash(email)
        if email_hash in processed_cache:
            return jsonify({
                'todos': todos_cache.get(email_hash, []),
                'cached': True
            })

        # Skip LOW priority to save tokens
        if priority == 'LOW':
            return jsonify({
                'todos': [],
                'cached': False,
                'skipped': 'LOW priority emails are skipped to save API tokens'
            })

        # Generate with Gemini
        prompt = f"""Analyze this email and extract actionable to-do items.

Email Details:
- Subject: {email.get('subject', '')}
- From: {email.get('sender', '')}
- Priority: {priority}
- Body: {email.get('body', '')[:1000]}

Instructions:
1. Extract ONLY actionable tasks (things the recipient needs to do)
2. Ignore informational content, greetings, or marketing emails
3. Be concise - one task per line
4. If no actionable tasks exist, return an empty array

Return your response as a JSON array of strings. Example:
["Reply to client proposal by Friday", "Schedule meeting with team"]

Response (JSON only):"""

        response = gemini_model.generate_content(prompt)
        text = response.text.strip()

        # Parse JSON (remove markdown if present)
        if text.startswith('```'):
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]

        todos = json.loads(text)

        # Cache the result
        processed_cache.add(email_hash)
        todos_cache[email_hash] = todos

        return jsonify({
            'todos': todos,
            'cached': False
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/process-email', methods=['POST'])
def process_email():
    """
    Complete workflow: Classify + Generate To-Dos in one call.

    Request body:
    {
        "email": {
            "subject": "Project deadline",
            "body": "Please submit...",
            "sender": "boss@company.com",
            "timestamp": "2025-01-15 10:30"
        }
    }

    Response:
    {
        "priority": "HIGH",
        "confidence": 0.92,
        "todos": ["Submit report by Friday"],
        "cached": false
    }
    """
    if not verify_api_key():
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.json
        email = data.get('email', {})

        # Step 1: Classify
        email_text = f"Subject: {email.get('subject', '')}\n\nBody: {email.get('body', '')}"
        embedding = embedder.embed_text(email_text)
        priority = classifier.predict([embedding])[0]

        if hasattr(classifier, 'predict_proba'):
            probs = classifier.predict_proba([embedding])[0]
            class_to_idx = {cls: idx for idx, cls in enumerate(classifier.classes_)}
            confidence = float(probs[class_to_idx[priority]])
        else:
            confidence = 1.0

        # Step 2: Check cache
        email_hash = get_email_hash(email)
        if email_hash in processed_cache:
            return jsonify({
                'priority': priority,
                'confidence': confidence,
                'todos': todos_cache.get(email_hash, []),
                'cached': True
            })

        # Step 3: Generate to-dos (if not LOW priority)
        todos = []
        if priority != 'LOW' and gemini_model:
            prompt = f"""Extract actionable to-do items from this email.

Subject: {email.get('subject', '')}
From: {email.get('sender', '')}
Priority: {priority}
Body: {email.get('body', '')[:1000]}

Return only a JSON array of task strings. If no tasks, return [].
Response:"""

            response = gemini_model.generate_content(prompt)
            text = response.text.strip()

            if text.startswith('```'):
                text = text.split('```')[1]
                if text.startswith('json'):
                    text = text[4:]

            todos = json.loads(text)

            # Cache
            processed_cache.add(email_hash)
            todos_cache[email_hash] = todos

        return jsonify({
            'priority': priority,
            'confidence': confidence,
            'todos': todos,
            'cached': False
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cache/stats', methods=['GET'])
def cache_stats():
    """Get cache statistics."""
    if not verify_api_key():
        return jsonify({'error': 'Unauthorized'}), 401

    return jsonify({
        'processed_emails': len(processed_cache),
        'cached_todos': len(todos_cache)
    })


@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Clear cache (for testing)."""
    if not verify_api_key():
        return jsonify({'error': 'Unauthorized'}), 401

    processed_cache.clear()
    todos_cache.clear()

    return jsonify({'message': 'Cache cleared'})


if __name__ == '__main__':
    port = config.API_SERVER_PORT
    app.run(host='0.0.0.0', port=port, debug=True)

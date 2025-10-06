"""
PriorityMail - Gmail To-Do List Generator Flask App

DRAFT VERSION - FOR TESTING AND EVALUATION PURPOSES ONLY
"""

import sys
from pathlib import Path

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, render_template, redirect, url_for, request, session, jsonify
import config

from utils.gmail_auth import GmailAuthenticator
from utils.email_fetcher import EmailFetcher
from utils.priority_classifier import PriorityClassifier
from utils.todo_generator import TodoGenerator
from utils.cache_manager import CacheManager

# Initialize Flask app
app = Flask(__name__)
app.secret_key = config.FLASK_SECRET_KEY

# Ensure required directories exist
config.ensure_directories()

# Global instances
gmail_auth = GmailAuthenticator()
cache_manager = CacheManager()
priority_classifier = None
todo_generator = None

# Initialize classifier if model exists
if Path(config.CLASSIFIER_MODEL_PATH).exists():
    priority_classifier = PriorityClassifier(config.CLASSIFIER_MODEL_PATH)
else:
    print(f"Warning: Model not found at {config.CLASSIFIER_MODEL_PATH}")

# Initialize Gemini if API key exists
if config.GEMINI_API_KEY:
    todo_generator = TodoGenerator(config.GEMINI_API_KEY)
else:
    print("Warning: GEMINI_API_KEY not set")


@app.route('/')
def index():
    """Home page."""
    if not gmail_auth.is_authenticated():
        return render_template('login.html')

    # Get cache stats
    stats = cache_manager.get_stats()

    return render_template('index.html', stats=stats)


@app.route('/login')
def login():
    """Initiate OAuth flow."""
    flow = gmail_auth.create_auth_flow(
        redirect_uri=url_for('oauth2callback', _external=True)
    )

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )

    session['state'] = state
    return redirect(authorization_url)


@app.route('/oauth2callback')
def oauth2callback():
    """OAuth callback handler."""
    state = session['state']

    flow = gmail_auth.create_auth_flow(
        redirect_uri=url_for('oauth2callback', _external=True)
    )
    flow.fetch_token(authorization_response=request.url)

    # Save credentials
    credentials = flow.credentials
    gmail_auth.save_credentials(credentials)

    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    """Logout and clear session."""
    # Delete token file
    token_path = Path(config.GMAIL_TOKEN_FILE)
    if token_path.exists():
        token_path.unlink()

    session.clear()
    return redirect(url_for('index'))


@app.route('/generate-todos')
def generate_todos():
    """Generate to-dos from recent emails."""
    if not gmail_auth.is_authenticated():
        return jsonify({'error': 'Not authenticated'}), 401

    if not priority_classifier or not todo_generator:
        return jsonify({'error': 'Model or API not configured'}), 500

    try:
        # Get Gmail service
        service = gmail_auth.get_gmail_service()
        fetcher = EmailFetcher(service)

        # Fetch recent emails
        all_emails = fetcher.fetch_recent_emails(
            days=config.EMAIL_FETCH_DAYS,
            max_results=config.EMAIL_FETCH_MAX_RESULTS
        )

        # Filter out already-processed emails
        new_emails = cache_manager.get_new_emails(all_emails)

        if not new_emails:
            return jsonify({
                'message': 'No new emails to process',
                'new_todos': 0,
                'stats': cache_manager.get_stats()
            })

        # Classify priorities
        priorities = priority_classifier.predict_batch(new_emails)

        # Generate to-dos (only for HIGH and MEDIUM priority)
        emails_with_priorities = []
        for email, pred in zip(new_emails, priorities):
            if pred['priority'] in ['HIGH', 'MEDIUM']:
                emails_with_priorities.append((email, pred['priority']))

        new_todos = todo_generator.generate_todos_batch(emails_with_priorities)

        # Cache the new to-dos
        cache_manager.add_todos(new_todos)

        return jsonify({
            'message': f'Generated {len(new_todos)} new tasks',
            'new_todos': len(new_todos),
            'processed_emails': len(new_emails),
            'stats': cache_manager.get_stats()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/todos')
def get_todos():
    """Get all to-dos."""
    todos = cache_manager.get_all_todos()

    # Sort by priority (HIGH first) and completion status
    priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
    todos_sorted = sorted(
        todos,
        key=lambda t: (t.get('completed', False), priority_order.get(t['priority'], 3))
    )

    return jsonify({
        'todos': todos_sorted,
        'stats': cache_manager.get_stats()
    })


@app.route('/todos/<int:todo_id>/complete', methods=['POST'])
def complete_todo(todo_id):
    """Mark a to-do as completed."""
    cache_manager.mark_completed(todo_id)
    return jsonify({'success': True})


@app.route('/todos/<int:todo_id>/delete', methods=['DELETE'])
def delete_todo(todo_id):
    """Delete a to-do."""
    cache_manager.delete_todo(todo_id)
    return jsonify({'success': True})


@app.route('/todos/clear-completed', methods=['POST'])
def clear_completed():
    """Clear all completed to-dos."""
    cache_manager.clear_completed()
    return jsonify({'success': True})


@app.route('/reset', methods=['POST'])
def reset_cache():
    """Reset all cache (for testing)."""
    cache_manager.clear_all()
    return jsonify({'success': True, 'message': 'Cache cleared'})


if __name__ == '__main__':
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG
    )

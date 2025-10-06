"""
To-Do List Generator using Google Gemini API
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import config
import google.generativeai as genai
import json


class TodoGenerator:
    """Generate to-do items from emails using Gemini AI."""

    def __init__(self, api_key):
        """
        Initialize Gemini API.

        Args:
            api_key: Google Gemini API key
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(config.GEMINI_MODEL_NAME)

    def generate_todos_from_email(self, email, priority):
        """
        Generate to-do items from a single email.

        Args:
            email: Email dictionary with 'subject', 'body', 'sender'
            priority: Priority level (HIGH/MEDIUM/LOW)

        Returns:
            List of to-do item dictionaries
        """
        prompt = f"""Analyze this email and extract actionable to-do items.

Email Details:
- Subject: {email['subject']}
- From: {email['sender']}
- Priority: {priority}
- Body: {email['body'][:1000]}

Instructions:
1. Extract ONLY actionable tasks (things the recipient needs to do)
2. Ignore informational content, greetings, or marketing emails
3. Be concise - one task per line
4. If no actionable tasks exist, return an empty list

Return your response as a JSON array of strings. Example:
["Reply to client proposal by Friday", "Schedule meeting with team"]

Response (JSON only):"""

        try:
            response = self.model.generate_content(prompt)

            # Parse JSON response
            text = response.text.strip()

            # Remove markdown code blocks if present
            if text.startswith('```'):
                text = text.split('```')[1]
                if text.startswith('json'):
                    text = text[4:]

            todos = json.loads(text)

            # Format todos with metadata
            formatted_todos = []
            for todo_text in todos:
                formatted_todos.append({
                    'task': todo_text,
                    'email_id': email['id'],
                    'email_subject': email['subject'],
                    'priority': priority,
                    'completed': False
                })

            return formatted_todos

        except Exception as e:
            print(f"Error generating todos for email {email['id']}: {e}")
            return []

    def generate_todos_batch(self, emails_with_priorities):
        """
        Generate to-dos for multiple emails.

        Args:
            emails_with_priorities: List of (email, priority) tuples

        Returns:
            List of all to-do items
        """
        all_todos = []

        for email, priority in emails_with_priorities:
            # Skip LOW priority emails to save tokens
            if priority == 'LOW':
                continue

            todos = self.generate_todos_from_email(email, priority)
            all_todos.extend(todos)

        return all_todos

    def generate_summary(self, all_todos):
        """
        Generate a summary of all to-dos.

        Args:
            all_todos: List of to-do dictionaries

        Returns:
            Summary string
        """
        if not all_todos:
            return "No actionable tasks found in recent emails."

        high_count = sum(1 for t in all_todos if t['priority'] == 'HIGH')
        medium_count = sum(1 for t in all_todos if t['priority'] == 'MEDIUM')

        summary = f"Generated {len(all_todos)} tasks from your emails:\n"
        summary += f"- {high_count} high priority\n"
        summary += f"- {medium_count} medium priority"

        return summary

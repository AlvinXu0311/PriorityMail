"""
Cache Manager for To-Do Lists

Avoids regenerating to-dos for emails that have already been processed.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import config
import json
import os
from datetime import datetime


class CacheManager:
    """Manage cached to-dos and processed email IDs."""

    def __init__(self, cache_dir=None):
        """
        Initialize cache manager.

        Args:
            cache_dir: Directory to store cache files
        """
        if cache_dir is None:
            cache_dir = config.CACHE_DIR
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        self.processed_file = self.cache_dir / 'processed_emails.json'
        self.todos_file = self.cache_dir / 'todos.json'

        self.processed_emails = self._load_processed_emails()
        self.todos = self._load_todos()

    def _load_processed_emails(self):
        """Load set of already-processed email IDs."""
        if self.processed_file.exists():
            with open(self.processed_file, 'r') as f:
                data = json.load(f)
                return set(data.get('email_ids', []))
        return set()

    def _load_todos(self):
        """Load existing to-do list."""
        if self.todos_file.exists():
            with open(self.todos_file, 'r') as f:
                return json.load(f)
        return []

    def is_processed(self, email_id):
        """Check if email has been processed."""
        return email_id in self.processed_emails

    def get_new_emails(self, emails):
        """
        Filter emails to only include unprocessed ones.

        Args:
            emails: List of email dictionaries

        Returns:
            List of new (unprocessed) emails
        """
        new_emails = [e for e in emails if e['id'] not in self.processed_emails]
        return new_emails

    def add_todos(self, new_todos):
        """
        Add new to-dos to the list and mark emails as processed.

        Args:
            new_todos: List of to-do dictionaries
        """
        # Add to existing todos
        self.todos.extend(new_todos)

        # Mark email IDs as processed
        for todo in new_todos:
            self.processed_emails.add(todo['email_id'])

        # Save to disk
        self._save_cache()

    def get_all_todos(self):
        """Get all cached to-dos."""
        return self.todos

    def mark_completed(self, todo_index):
        """
        Mark a to-do as completed.

        Args:
            todo_index: Index of the to-do item
        """
        if 0 <= todo_index < len(self.todos):
            self.todos[todo_index]['completed'] = True
            self._save_cache()

    def delete_todo(self, todo_index):
        """
        Delete a to-do item.

        Args:
            todo_index: Index of the to-do item
        """
        if 0 <= todo_index < len(self.todos):
            del self.todos[todo_index]
            self._save_cache()

    def clear_completed(self):
        """Remove all completed to-dos."""
        self.todos = [t for t in self.todos if not t.get('completed', False)]
        self._save_cache()

    def clear_all(self):
        """Clear all cache (useful for reset)."""
        self.todos = []
        self.processed_emails = set()
        self._save_cache()

    def _save_cache(self):
        """Save cache to disk."""
        # Save processed email IDs
        with open(self.processed_file, 'w') as f:
            json.dump({
                'email_ids': list(self.processed_emails),
                'last_updated': datetime.now().isoformat()
            }, f, indent=2)

        # Save to-dos
        with open(self.todos_file, 'w') as f:
            json.dump(self.todos, f, indent=2)

    def get_stats(self):
        """Get cache statistics."""
        return {
            'total_todos': len(self.todos),
            'completed': sum(1 for t in self.todos if t.get('completed', False)),
            'pending': sum(1 for t in self.todos if not t.get('completed', False)),
            'processed_emails': len(self.processed_emails),
            'high_priority': sum(1 for t in self.todos if t['priority'] == 'HIGH'),
            'medium_priority': sum(1 for t in self.todos if t['priority'] == 'MEDIUM')
        }

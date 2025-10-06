"""
Gmail Email Fetcher
"""

import base64
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime


class EmailFetcher:
    """Fetch emails from Gmail API."""

    def __init__(self, gmail_service):
        """
        Initialize email fetcher.

        Args:
            gmail_service: Authenticated Gmail API service
        """
        self.service = gmail_service

    def fetch_recent_emails(self, days=7, max_results=100):
        """
        Fetch emails from the last N days.

        Args:
            days: Number of days to look back
            max_results: Maximum number of emails to fetch

        Returns:
            List of email dictionaries
        """
        # Calculate date range
        after_date = datetime.now() - timedelta(days=days)
        after_str = after_date.strftime('%Y/%m/%d')

        # Build query
        query = f'after:{after_str}'

        try:
            # Get message IDs
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])

            if not messages:
                return []

            # Fetch full message details
            emails = []
            for msg in messages:
                email = self._get_email_details(msg['id'])
                if email:
                    emails.append(email)

            return emails

        except Exception as e:
            print(f"Error fetching emails: {e}")
            return []

    def fetch_new_emails_since(self, email_ids, days=7):
        """
        Fetch emails that are NOT in the provided email_ids list.

        Args:
            email_ids: Set of already-processed email IDs
            days: Number of days to look back

        Returns:
            List of new email dictionaries
        """
        all_emails = self.fetch_recent_emails(days=days)
        new_emails = [e for e in all_emails if e['id'] not in email_ids]
        return new_emails

    def _get_email_details(self, msg_id):
        """
        Get detailed email information.

        Args:
            msg_id: Gmail message ID

        Returns:
            Email dictionary with subject, body, sender, etc.
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            ).execute()

            headers = message['payload']['headers']

            # Extract headers
            subject = self._get_header(headers, 'Subject') or '(No Subject)'
            sender = self._get_header(headers, 'From') or ''
            date_str = self._get_header(headers, 'Date') or ''

            # Parse date
            try:
                date_obj = parsedate_to_datetime(date_str)
                timestamp = date_obj.strftime('%Y-%m-%d %H:%M:%S')
            except:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Extract body
            body = self._get_email_body(message['payload'])

            return {
                'id': msg_id,
                'email_id': msg_id,  # For compatibility with classifier
                'subject': subject,
                'body': body[:2000],  # Limit body length
                'sender': sender,
                'timestamp': timestamp,
                'folder': 'inbox'
            }

        except Exception as e:
            print(f"Error getting email {msg_id}: {e}")
            return None

    def _get_header(self, headers, name):
        """Extract specific header value."""
        for header in headers:
            if header['name'].lower() == name.lower():
                return header['value']
        return None

    def _get_email_body(self, payload):
        """
        Extract email body from payload.

        Args:
            payload: Gmail message payload

        Returns:
            Email body text
        """
        body = ""

        # Check for plain text part
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                        break
                elif part['mimeType'] == 'multipart/alternative':
                    # Recursively search for text/plain
                    body = self._get_email_body(part)
                    if body:
                        break
        elif 'body' in payload and 'data' in payload['body']:
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')

        return body.strip()

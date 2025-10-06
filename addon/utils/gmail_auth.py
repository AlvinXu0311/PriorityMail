"""
Gmail OAuth Authentication Handler
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import config
import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# Scopes for Gmail API
SCOPES = config.GMAIL_SCOPES

class GmailAuthenticator:
    """Handle Gmail OAuth authentication."""

    def __init__(self, credentials_file=None, token_file=None):
        """
        Initialize authenticator.

        Args:
            credentials_file: Path to OAuth client credentials JSON
            token_file: Path to store user token
        """
        if credentials_file is None:
            credentials_file = config.GMAIL_CREDENTIALS_FILE
        if token_file is None:
            token_file = config.GMAIL_TOKEN_FILE
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.creds = None

    def get_credentials(self):
        """
        Get valid user credentials.

        Returns:
            Credentials object
        """
        # Load token if exists
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                self.creds = pickle.load(token)

        # Refresh or create new credentials
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                return None  # Need to authenticate via OAuth flow

        return self.creds

    def create_auth_flow(self, redirect_uri):
        """
        Create OAuth flow for authentication.

        Args:
            redirect_uri: OAuth redirect URI

        Returns:
            Flow object
        """
        flow = Flow.from_client_secrets_file(
            self.credentials_file,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
        return flow

    def save_credentials(self, creds):
        """
        Save credentials to file.

        Args:
            creds: Credentials object
        """
        self.creds = creds
        with open(self.token_file, 'wb') as token:
            pickle.dump(creds, token)

    def get_gmail_service(self):
        """
        Get authenticated Gmail API service.

        Returns:
            Gmail API service object
        """
        creds = self.get_credentials()
        if not creds:
            return None

        service = build('gmail', 'v1', credentials=creds)
        return service

    def is_authenticated(self):
        """Check if user is authenticated."""
        creds = self.get_credentials()
        return creds is not None and creds.valid

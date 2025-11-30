import os
import json
from typing import Any, List
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from shared_utils import setup_logging, get_project_root

logger = setup_logging("GoogleAuth")

# Scopes required for the application
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive'
]

class GoogleAuthManager:
    """
    Handles authentication with Google Services using OAuth 2.0 (User Credentials).
    This bypasses Service Account storage quotas by acting as the actual user.
    """
    
    def __init__(self, credentials_file: str = "geminicli_oauth_credentials.json"):
        # The file downloaded from Google Cloud Console (User credentials)
        self.credentials_path = get_project_root() / credentials_file
        # The file where we save the valid access token
        self.token_path = get_project_root() / "token.json"
        self.creds = None
        self._authenticate()

    def _authenticate(self):
        """Authenticates using OAuth 2.0 User Flow."""
        self.creds = None
        
        # 1. Load existing token if available
        if self.token_path.exists():
            try:
                self.creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)
            except Exception as e:
                logger.warning(f"Corrupt token found, refreshing: {e}")

        # 2. Refresh or Login if invalid
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    logger.info("Refreshing expired access token...")
                    self.creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Failed to refresh token: {e}. Initiating re-login.")
                    self.creds = None # Force re-login

            # If still no valid creds, start interactive flow
            if not self.creds:
                if not self.credentials_path.exists():
                    logger.error(f"OAuth Client Secret file not found at {self.credentials_path}")
                    raise FileNotFoundError(f"Please download your OAuth 2.0 Client ID JSON and save it as '{self.credentials_path.name}' in the project root.")

                logger.info("Initiating OAuth 2.0 Browser Login...")
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_path), SCOPES
                    )
                    self.creds = flow.run_local_server(port=0)
                except Exception as e:
                    logger.error(f"OAuth Login Failed: {e}")
                    raise e

            # 3. Save the new token
            with open(self.token_path, 'w') as token:
                token.write(self.creds.to_json())
                logger.info("Authentication successful! Token saved.")

    def get_service(self, service_name: str, version: str) -> Any:
        """
        Returns an authorized Google API service instance.
        
        Args:
            service_name: e.g., 'calendar', 'sheets', 'drive'
            version: e.g., 'v3', 'v4'
        """
        try:
            service = build(service_name, version, credentials=self.creds)
            return service
        except Exception as e:
            logger.error(f"Failed to build service {service_name} ({version}): {e}")
            raise e
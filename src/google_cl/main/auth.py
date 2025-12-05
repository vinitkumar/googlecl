"""
Authentication module for Google APIs using OAuth 2.0.

This module handles OAuth 2.0 authentication flow for Google services,
including token management, refresh, and secure storage.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

if TYPE_CHECKING:
    from googleapiclient.discovery import Resource

log = logging.getLogger(__name__)

# Default paths for credentials and tokens
DEFAULT_CONFIG_DIR = Path.home() / ".config" / "googlecl"
DEFAULT_CREDENTIALS_FILE = DEFAULT_CONFIG_DIR / "credentials.json"
DEFAULT_TOKEN_FILE = DEFAULT_CONFIG_DIR / "token.json"

# All available scopes for Google services
SCOPES = {
    "gmail": [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.compose",
        "https://www.googleapis.com/auth/gmail.labels",
    ],
    "drive": [
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive.metadata.readonly",
    ],
    "calendar": [
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/calendar.events",
    ],
    "sheets": [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/spreadsheets",
    ],
}


def get_all_scopes() -> list[str]:
    """Get all available scopes combined."""
    all_scopes: list[str] = []
    for scope_list in SCOPES.values():
        all_scopes.extend(scope_list)
    return list(set(all_scopes))


def ensure_config_dir() -> Path:
    """Ensure the config directory exists and return its path."""
    DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return DEFAULT_CONFIG_DIR


class GoogleAuth:
    """
    Handles Google OAuth 2.0 authentication.

    This class manages the OAuth flow, token storage, and refresh
    for authenticating with Google APIs.
    """

    def __init__(
        self,
        credentials_file: Path | None = None,
        token_file: Path | None = None,
        scopes: list[str] | None = None,
    ) -> None:
        """
        Initialize GoogleAuth.

        Args:
            credentials_file: Path to the OAuth credentials JSON file.
            token_file: Path to store/load the authentication token.
            scopes: List of OAuth scopes to request.
        """
        ensure_config_dir()
        self.credentials_file = credentials_file or DEFAULT_CREDENTIALS_FILE
        self.token_file = token_file or DEFAULT_TOKEN_FILE
        self.scopes = scopes or get_all_scopes()
        self._credentials: Credentials | None = None

    @property
    def credentials(self) -> Credentials | None:
        """Get the current credentials."""
        return self._credentials

    def load_token(self) -> Credentials | None:
        """
        Load saved token from file if it exists.

        Returns:
            Credentials object if token exists, None otherwise.
        """
        if not self.token_file.exists():
            log.debug("No token file found at %s", self.token_file)
            return None

        try:
            creds = Credentials.from_authorized_user_file(
                str(self.token_file), self.scopes
            )
            log.debug("Loaded token from %s", self.token_file)
            return creds
        except (json.JSONDecodeError, ValueError) as e:
            log.warning("Failed to load token: %s", e)
            return None

    def save_token(self, credentials: Credentials) -> None:
        """
        Save credentials to the token file.

        Args:
            credentials: The credentials to save.
        """
        with open(self.token_file, "w") as token:
            token.write(credentials.to_json())
        # Set secure permissions
        self.token_file.chmod(0o600)
        log.debug("Saved token to %s", self.token_file)

    def authenticate(self, force_new: bool = False) -> Credentials:
        """
        Authenticate with Google and return credentials.

        This method will:
        1. Try to load existing token
        2. Refresh if expired
        3. Run OAuth flow if no valid token exists

        Args:
            force_new: Force a new authentication flow.

        Returns:
            Valid Credentials object.

        Raises:
            FileNotFoundError: If credentials file doesn't exist.
            ValueError: If authentication fails.
        """
        creds: Credentials | None = None

        if not force_new:
            creds = self.load_token()

        # Check if we have valid credentials
        if creds and creds.valid:
            self._credentials = creds
            return creds

        # Try to refresh expired credentials
        if creds and creds.expired and creds.refresh_token:
            try:
                log.info("Refreshing expired token...")
                creds.refresh(Request())
                self.save_token(creds)
                self._credentials = creds
                return creds
            except Exception as e:
                log.warning("Failed to refresh token: %s", e)
                creds = None

        # Need to run OAuth flow
        if not self.credentials_file.exists():
            raise FileNotFoundError(
                f"Credentials file not found: {self.credentials_file}\n"
                "Please download your OAuth credentials from Google Cloud Console:\n"
                "1. Go to https://console.cloud.google.com/\n"
                "2. Create a project or select existing\n"
                "3. Enable the APIs you want to use\n"
                "4. Go to APIs & Services > Credentials\n"
                "5. Create OAuth 2.0 Client ID (Desktop application)\n"
                "6. Download JSON and save to: {self.credentials_file}"
            )

        log.info("Starting OAuth flow...")
        flow = InstalledAppFlow.from_client_secrets_file(
            str(self.credentials_file), self.scopes
        )

        # Run the local server for OAuth callback
        creds = flow.run_local_server(port=0)

        # Save the credentials for future use
        self.save_token(creds)
        self._credentials = creds

        log.info("Authentication successful!")
        return creds

    def is_authenticated(self) -> bool:
        """Check if we have valid credentials."""
        if self._credentials is None:
            creds = self.load_token()
            if creds and creds.valid:
                self._credentials = creds
                return True
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    self.save_token(creds)
                    self._credentials = creds
                    return True
                except Exception:
                    return False
            return False
        return self._credentials.valid

    def revoke(self) -> bool:
        """
        Revoke the current credentials and remove token file.

        Returns:
            True if revocation was successful.
        """
        if self.token_file.exists():
            self.token_file.unlink()
            log.info("Removed token file")

        self._credentials = None
        return True


def build_service(service_name: str, version: str, credentials: Credentials) -> "Resource":
    """
    Build a Google API service client.

    Args:
        service_name: Name of the Google service (e.g., 'gmail', 'drive').
        version: API version (e.g., 'v1', 'v3').
        credentials: Valid OAuth credentials.

    Returns:
        Google API service resource.
    """
    from googleapiclient.discovery import build

    return build(service_name, version, credentials=credentials)


# Global auth instance for convenience
_auth: GoogleAuth | None = None


def get_auth() -> GoogleAuth:
    """Get or create the global auth instance."""
    global _auth
    if _auth is None:
        _auth = GoogleAuth()
    return _auth


def authenticate(force_new: bool = False) -> Credentials:
    """Convenience function to authenticate using global auth."""
    return get_auth().authenticate(force_new=force_new)

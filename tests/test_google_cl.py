"""Tests for GoogleCL package."""

import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock

from google_cl.main.cli import app
from google_cl import __version__


runner = CliRunner()


@pytest.fixture
def mock_auth():
    """Mock authentication for tests."""
    with patch("google_cl.main.cli.GoogleAuth") as mock:
        mock_instance = MagicMock()
        mock_instance.is_authenticated.return_value = True
        mock_instance.credentials = MagicMock()
        mock.return_value = mock_instance
        yield mock


class TestCLI:
    """Tests for the CLI interface."""

    def test_version(self):
        """Test version command."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert __version__ in result.stdout

    def test_help(self):
        """Test help output."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Command-line interface for Google services" in result.stdout

    def test_gmail_help(self):
        """Test Gmail subcommand help."""
        result = runner.invoke(app, ["gmail", "--help"])
        assert result.exit_code == 0
        assert "Gmail operations" in result.stdout

    def test_drive_help(self):
        """Test Drive subcommand help."""
        result = runner.invoke(app, ["drive", "--help"])
        assert result.exit_code == 0
        assert "Google Drive operations" in result.stdout

    def test_calendar_help(self):
        """Test Calendar subcommand help."""
        result = runner.invoke(app, ["calendar", "--help"])
        assert result.exit_code == 0
        assert "Google Calendar operations" in result.stdout

    def test_auth_help(self):
        """Test Auth subcommand help."""
        result = runner.invoke(app, ["auth", "--help"])
        assert result.exit_code == 0
        assert "Authentication management" in result.stdout


class TestAuthModule:
    """Tests for the authentication module."""

    def test_scopes_defined(self):
        """Test that OAuth scopes are properly defined."""
        from google_cl.main.auth import SCOPES

        assert "gmail" in SCOPES
        assert "drive" in SCOPES
        assert "calendar" in SCOPES
        assert "sheets" in SCOPES

        # Each service should have at least one scope
        for service, scopes in SCOPES.items():
            assert len(scopes) > 0
            assert all(s.startswith("https://www.googleapis.com/auth/") for s in scopes)

    def test_get_all_scopes(self):
        """Test that all scopes can be combined."""
        from google_cl.main.auth import get_all_scopes

        scopes = get_all_scopes()
        assert isinstance(scopes, list)
        assert len(scopes) > 0
        # Should be unique
        assert len(scopes) == len(set(scopes))


class TestExceptions:
    """Tests for custom exceptions."""

    def test_exception_hierarchy(self):
        """Test exception inheritance."""
        from google_cl.exceptions import (
            GoogleCLException,
            ExecutionError,
            EarlyQuit,
            AuthenticationError,
            ServiceError,
            ConfigurationError,
        )

        assert issubclass(ExecutionError, GoogleCLException)
        assert issubclass(EarlyQuit, GoogleCLException)
        assert issubclass(AuthenticationError, GoogleCLException)
        assert issubclass(ServiceError, GoogleCLException)
        assert issubclass(ConfigurationError, GoogleCLException)


class TestGmailService:
    """Tests for Gmail service."""

    def test_email_dataclass(self):
        """Test Email dataclass creation from API response."""
        from google_cl.services.gmail import Email

        mock_response = {
            "id": "test123",
            "threadId": "thread123",
            "snippet": "Test snippet",
            "labelIds": ["INBOX"],
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Test Subject"},
                    {"name": "From", "value": "test@example.com"},
                    {"name": "To", "value": "recipient@example.com"},
                    {"name": "Date", "value": "Mon, 1 Jan 2024 12:00:00 +0000"},
                ]
            },
        }

        email = Email.from_api_response(mock_response)
        assert email.id == "test123"
        assert email.thread_id == "thread123"
        assert email.subject == "Test Subject"
        assert email.sender == "test@example.com"
        assert email.to == "recipient@example.com"


class TestDriveService:
    """Tests for Drive service."""

    def test_drivefile_dataclass(self):
        """Test DriveFile dataclass creation from API response."""
        from google_cl.services.drive import DriveFile

        mock_response = {
            "id": "file123",
            "name": "test.txt",
            "mimeType": "text/plain",
            "size": "1024",
            "createdTime": "2024-01-01T12:00:00.000Z",
            "modifiedTime": "2024-01-02T12:00:00.000Z",
            "parents": ["folder123"],
            "webViewLink": "https://drive.google.com/file/d/file123",
        }

        drive_file = DriveFile.from_api_response(mock_response)
        assert drive_file.id == "file123"
        assert drive_file.name == "test.txt"
        assert drive_file.size == 1024
        assert not drive_file.is_folder

    def test_folder_detection(self):
        """Test that folders are properly detected."""
        from google_cl.services.drive import DriveFile

        mock_folder = {
            "id": "folder123",
            "name": "TestFolder",
            "mimeType": "application/vnd.google-apps.folder",
            "createdTime": "2024-01-01T12:00:00.000Z",
            "modifiedTime": "2024-01-02T12:00:00.000Z",
        }

        folder = DriveFile.from_api_response(mock_folder)
        assert folder.is_folder


class TestCalendarService:
    """Tests for Calendar service."""

    def test_event_dataclass(self):
        """Test Event dataclass creation from API response."""
        from google_cl.services.calendar import Event

        mock_response = {
            "id": "event123",
            "summary": "Test Event",
            "description": "Test Description",
            "location": "Test Location",
            "start": {"dateTime": "2024-01-01T10:00:00"},
            "end": {"dateTime": "2024-01-01T11:00:00"},
            "status": "confirmed",
            "htmlLink": "https://calendar.google.com/event/event123",
            "creator": {"email": "creator@example.com"},
        }

        event = Event.from_api_response(mock_response)
        assert event.id == "event123"
        assert event.summary == "Test Event"
        assert event.location == "Test Location"
        assert not event.all_day

    def test_all_day_event(self):
        """Test all-day event detection."""
        from google_cl.services.calendar import Event

        mock_response = {
            "id": "event123",
            "summary": "All Day Event",
            "start": {"date": "2024-01-01"},
            "end": {"date": "2024-01-02"},
            "status": "confirmed",
            "htmlLink": "",
            "creator": {},
        }

        event = Event.from_api_response(mock_response)
        assert event.all_day

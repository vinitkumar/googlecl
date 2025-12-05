"""
GoogleCL - Command-line interface for Google services.

This package provides a Pythonic interface to interact with Google services
including Gmail, Google Drive, and Google Calendar from the command line.
"""

__author__ = "Vinit Kumar"
__email__ = "mail@vinitkumar.me"
__version__ = "0.1.0"


def __getattr__(name: str):
    """Lazy loading of heavy modules to speed up CLI startup."""
    if name == "GoogleAuth":
        from google_cl.main.auth import GoogleAuth
        return GoogleAuth
    if name == "authenticate":
        from google_cl.main.auth import authenticate
        return authenticate
    if name == "GmailService":
        from google_cl.services.gmail import GmailService
        return GmailService
    if name == "DriveService":
        from google_cl.services.drive import DriveService
        return DriveService
    if name == "CalendarService":
        from google_cl.services.calendar import CalendarService
        return CalendarService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "GoogleAuth",
    "authenticate",
    "GmailService",
    "DriveService",
    "CalendarService",
]

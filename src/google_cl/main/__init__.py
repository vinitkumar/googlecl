"""Main module for GoogleCL CLI."""

__all__ = ["Application", "app"]


def __getattr__(name: str):
    """Lazy loading to avoid import issues."""
    if name == "Application":
        from google_cl.main.application import Application
        return Application
    if name == "app":
        from google_cl.main.cli import app
        return app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


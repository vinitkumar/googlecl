"""Main application module for GoogleCL."""

import logging
import time
from collections.abc import Sequence

from google_cl import exceptions

LOG = logging.getLogger(__name__)


class Application:
    """Main application class for GoogleCL."""

    def __init__(self) -> None:
        """Initialize the application."""
        self.start_time = time.time()
        self.catastrophic_failure = False

    def exit_code(self) -> int:
        """Get the exit code based on application state."""
        if self.catastrophic_failure:
            return 1
        return 0

    def initialize(self, argv: Sequence[str]) -> None:
        """Initialize the application with command line arguments."""
        # Import here to avoid circular imports
        from google_cl.main.cli import app

        # If argv is empty, show help
        if not argv:
            argv = ["--help"]

        # Run the Typer app
        app(argv)

    def _run(self, argv: Sequence[str]) -> None:
        """Internal run method."""
        self.initialize(argv)

    def run(self, argv: Sequence[str]) -> None:
        """Run the application."""
        try:
            self._run(argv)
        except KeyboardInterrupt as exc:
            print("\n... stopped")
            LOG.critical("Caught keyboard interrupt from user")
            LOG.exception(exc)
            self.catastrophic_failure = True
        except exceptions.ExecutionError as exc:
            print(f"There was a critical error during execution: {exc}")
            LOG.exception(exc)
            self.catastrophic_failure = True
        except exceptions.EarlyQuit:
            self.catastrophic_failure = True
        except SystemExit as exc:
            # Typer raises SystemExit, handle it gracefully
            if exc.code != 0:
                self.catastrophic_failure = True

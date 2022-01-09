import time
import logging
from google_cl import exceptions

from typing import Sequence


LOG = logging.getLogger(__name__)

class Application:

    def __init__(self) -> None:
        self.start_time = time.time()
        self.catastrophic_failure = False

    def exit_code(self) -> int:
        if self.catastrophic_failure:
            return 1
        return 0

    def initialize(self, argv: Sequence[str]):
        print(argv)

    def _run(self, argv: Sequence[str]) -> None:
        self.initialize(argv)

    def run(self, argv: Sequence[str]) -> None:
        try:
            self._run(argv)
        except KeyboardInterrupt as exc:
            print("... stopped")
            LOG.critical("Caught keyboard interrupt from user")
            LOG.exception(exc)
            self.catastrophic_failure = True
        except exceptions.ExecutionError as exc:
            print("There was a critical error during execution of Flake8:")
            print(exc)
            LOG.exception(exc)
            self.catastrophic_failure = True
        except exceptions.EarlyQuit:
            self.catastrophic_failure = True

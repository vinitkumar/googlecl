import time
import logging
from pathlib import Path
from google_cl import exceptions
from google_cl.main.auth import Authorize

from typing import Sequence


LOG = logging .getLogger(__name__)
APP_NAME = "googlecl"

class Application:

    def __init__(self) -> None:
        self.start_time = time.time()
        self.catastrophic_failure = False
        root_folder = Path(args.root_folder).absolute()

        compare_folder = None
        if args.compare_folder:
            compare_folder = Path(args.compare_folder).absolute()
        app_dirs = AppDirs(APP_NAME)

        self.data_store = LocalData(db_path, args.flush_index)

        credentials_file = db_path / ".gphotos.token"
        if args.secret:
            secret_file = Path(args.secret)
        else:
            secret_file = Path(app_dirs.user_config_dir) / "client_secret.json"
        if args.new_token and credentials_file.exists():
            credentials_file.unlink()

        scope = [
            "https://www.googleapis.com/auth/photoslibrary.readonly",
            "https://www.googleapis.com/auth/photoslibrary.sharing",
        ]
        photos_api_url = (
            "https://photoslibrary.googleapis.com/$discovery" "/rest?version=v1"
        )
        self.auth = Authorize(
            scope, credentials_file, secret_file, int(args.max_retries)
        )
        self.auth.authorize()

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

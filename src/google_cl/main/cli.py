# -*- coding: utf-8 -*-

"""Console script for google_cl."""
import sys

from typing import Optional
from typing import Sequence


from google_cl.main import application


def main(argv: Optional[Sequence[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    app = application.Application()
    app.run(argv)
    return app.exit_code()



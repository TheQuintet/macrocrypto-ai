"""Entry point for the CLI package.

Allows invocation via ``python -m app.cli`` as a shortcut for
``python -m app.cli.pipeline``.
"""

import sys

from app.cli.pipeline import main


if __name__ == "__main__":
    sys.exit(main())
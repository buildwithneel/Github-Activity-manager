"""Main launcher for GitHub Activity Generator."""

import sys
from pathlib import Path

# Ensure src/ is importable when running `python main.py` directly without editable install
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from github_activity_generator.cli.menu import run_cli  # noqa: E402


def main() -> None:
    """Launch the interactive GitHub Activity Generator CLI."""
    run_cli()


if __name__ == "__main__":
    main()

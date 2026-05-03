"""Command-line runner for the ASCII Art Generator."""

from __future__ import annotations

import sys

try:
    from src.ascii_art_generator import main
except ModuleNotFoundError:  # Allows running as: python src/main.py
    from ascii_art_generator import main


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

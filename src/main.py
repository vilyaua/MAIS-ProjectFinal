"""Command-line interface for the ASCII art generator."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from ascii_art import (
    AsciiArtError,
    available_fonts,
    generate_ascii_art,
    save_ascii_art,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""

    parser = argparse.ArgumentParser(
        description="Generate ASCII art from printable text input."
    )
    parser.add_argument(
        "text",
        nargs="?",
        help=(
            "Text to render. If omitted, text is read from standard input. "
            "Use quotes for spaces and shell-specific newline syntax for "
            "multi-line input."
        ),
    )
    parser.add_argument(
        "-f",
        "--font",
        default="block",
        choices=available_fonts(),
        help="ASCII art font/layout style to use (default: block).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Save generated ASCII art to this text file instead of printing it.",
    )
    parser.add_argument(
        "--spacing",
        type=int,
        default=1,
        help="Number of spaces between large-font glyphs (default: 1).",
    )
    return parser


def _read_stdin() -> str:
    """Read all text supplied on standard input."""

    return sys.stdin.read()


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the ASCII art command-line interface.

    Returns a process-style exit code: ``0`` for success and ``1`` when a
    user-correctable error occurs.
    """

    parser = build_parser()
    args = parser.parse_args(argv)
    text = args.text if args.text is not None else _read_stdin()

    try:
        art = generate_ascii_art(text=text, font=args.font, spacing=args.spacing)
        if args.output:
            save_ascii_art(art, args.output)
            print(f"ASCII art saved to {args.output}")
        else:
            print(art)
    except (AsciiArtError, ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

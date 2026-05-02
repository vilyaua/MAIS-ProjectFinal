"""Command-line interface for the ASCII Art Text Generator."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

try:  # Supports both `python src/main.py` and `from src.main import main`.
    from .ascii_art import MAX_LENGTH, AsciiArtError, render_ascii_art
except ImportError:  # pragma: no cover - exercised when run as a script.
    from ascii_art import MAX_LENGTH, AsciiArtError, render_ascii_art


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate ASCII art from letters, numbers, and common punctuation.",
        epilog=(
            "Examples:\n  python src/main.py Hello\n  echo 'Hello, World!' | python src/main.py"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "text",
        nargs="*",
        help="Text to render. If omitted, text is read from standard input.",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=MAX_LENGTH,
        help=f"Maximum input length (default: {MAX_LENGTH}).",
    )
    return parser


def _read_text_from_args_or_stdin(args: argparse.Namespace) -> str:
    """Read text from positional arguments or standard input."""
    if args.text:
        return " ".join(args.text)
    return sys.stdin.read().rstrip("\n")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line application.

    Args:
        argv: Optional argument list. Uses sys.argv when omitted.

    Returns:
        Process exit code. Zero means success; non-zero means validation failed.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.max_length < 1:
        print("Error: --max-length must be at least 1.", file=sys.stderr)
        return 2

    text = _read_text_from_args_or_stdin(args)
    try:
        result = render_ascii_art(text, max_length=args.max_length)
    except AsciiArtError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("\nASCII Art:\n")
    print(result.art)
    if result.warning:
        print(f"\n{result.warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Command-line entry point for the ASCII art generator."""

from __future__ import annotations

import argparse
import sys

from ascii_art import DEFAULT_MAX_WIDTH, generate_ascii_art


def build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""
    parser = argparse.ArgumentParser(description="Generate ASCII art from text input.")
    parser.add_argument(
        "text",
        nargs="?",
        help="Text to render. If omitted, text is read from standard input.",
    )
    parser.add_argument(
        "--max-width",
        type=int,
        default=DEFAULT_MAX_WIDTH,
        help=f"Maximum rendered width before wrapping (default: {DEFAULT_MAX_WIDTH}).",
    )
    return parser


def main() -> int:
    """Run the ASCII art generator CLI."""
    parser = build_parser()
    args = parser.parse_args()

    text = args.text if args.text is not None else sys.stdin.read().rstrip("\n")

    try:
        print(generate_ascii_art(text, max_width=args.max_width))
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

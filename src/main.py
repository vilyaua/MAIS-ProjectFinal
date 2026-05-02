"""Command-line entry point for the ASCII art generator."""

from __future__ import annotations

import argparse
import sys

from ascii_art import (
    DEFAULT_FONT,
    InputValidationError,
    get_supported_fonts,
    render_ascii_art,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""

    parser = argparse.ArgumentParser(
        description="Convert command-line text into terminal ASCII art."
    )
    parser.add_argument(
        "text",
        nargs="*",
        help="Text to convert. Quote the text if it contains shell-sensitive characters.",
    )
    parser.add_argument(
        "-f",
        "--font",
        default=DEFAULT_FONT,
        choices=get_supported_fonts(),
        help=f"Font style to use (default: {DEFAULT_FONT}).",
    )
    parser.add_argument(
        "--list-fonts",
        action="store_true",
        help="List supported font styles and exit.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the ASCII art generator CLI.

    Args:
        argv: Optional argument list, excluding program name. If omitted,
            arguments are read from ``sys.argv``.

    Returns:
        Process exit code. ``0`` indicates success; ``1`` indicates a handled
        error.
    """

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_fonts:
        print("Supported fonts: " + ", ".join(get_supported_fonts()))
        return 0

    text = " ".join(args.text)

    try:
        print(render_ascii_art(text, args.font))
    except InputValidationError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception:
        print(
            "Error: An unexpected problem occurred while generating ASCII art.",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

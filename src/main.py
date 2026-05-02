"""Command-line interface for the ASCII art generator."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ascii_art import (
    available_fonts,
    format_unsupported_warning,
    generate_ascii_art,
    save_art_to_file,
    validate_text,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""

    parser = argparse.ArgumentParser(
        description="Generate readable ASCII art from text input."
    )
    parser.add_argument(
        "text",
        nargs="?",
        help="Text to render. If omitted, you will be prompted interactively.",
    )
    parser.add_argument(
        "-f",
        "--font",
        default="block",
        choices=available_fonts(),
        help="ASCII art style to use (default: block).",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Optional file path where the ASCII art should be saved.",
    )
    return parser


def prompt_for_text() -> str:
    """Prompt until the user provides non-empty text."""

    while True:
        text = input("Enter text to convert to ASCII art: ")
        try:
            return validate_text(text)
        except ValueError as error:
            print(error)


def prompt_for_output_path() -> str | None:
    """Ask an interactive user whether the output should be saved."""

    choice = input("Save output to a file? [y/N]: ").strip().lower()
    if choice not in {"y", "yes"}:
        return None

    while True:
        filepath = input("Enter output file path: ").strip()
        if filepath:
            return filepath
        print("Please provide a non-empty file path.")


def run(args: list[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""

    parser = build_parser()
    namespace = parser.parse_args(args)

    try:
        text = validate_text(namespace.text) if namespace.text is not None else prompt_for_text()
        result = generate_ascii_art(text, namespace.font)
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    warning = format_unsupported_warning(result.unsupported_characters)
    if warning:
        print(warning, file=sys.stderr)

    output_path = namespace.output
    if output_path is None and namespace.text is None:
        output_path = prompt_for_output_path()

    if output_path:
        try:
            saved_path = save_art_to_file(result.art, Path(output_path))
        except OSError as error:
            print(f"Error: could not save file: {error}", file=sys.stderr)
            return 1
        except ValueError as error:
            print(f"Error: {error}", file=sys.stderr)
            return 1
        print(f"ASCII art saved to: {saved_path}")
    else:
        print(result.art)

    return 0


if __name__ == "__main__":
    raise SystemExit(run())

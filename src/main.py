"""Command-line interface for the password generator."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

try:  # Supports both ``python src/main.py`` and ``python -m src.main``.
    from .password_generator import (
        DEFAULT_LENGTH,
        CharacterOptions,
        PasswordGeneratorError,
        evaluate_strength,
        generate_password,
    )
except ImportError:  # pragma: no cover - exercised when run as a script.
    from password_generator import (
        DEFAULT_LENGTH,
        CharacterOptions,
        PasswordGeneratorError,
        evaluate_strength,
        generate_password,
    )


def _add_character_option(
    parser: argparse.ArgumentParser,
    name: str,
    destination: str,
    help_text: str,
) -> None:
    """Add include/exclude flags for a character class."""
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        f"--{name}",
        dest=destination,
        action="store_true",
        default=None,
        help=f"include {help_text}",
    )
    group.add_argument(
        f"--no-{name}",
        dest=destination,
        action="store_false",
        help=f"exclude {help_text}",
    )


def build_parser() -> argparse.ArgumentParser:
    """Create and configure the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate a random password and report its strength."
    )
    parser.add_argument(
        "-l",
        "--length",
        type=int,
        default=DEFAULT_LENGTH,
        help=f"password length as a positive integer (default: {DEFAULT_LENGTH})",
    )
    _add_character_option(parser, "uppercase", "uppercase", "uppercase letters")
    _add_character_option(parser, "lowercase", "lowercase", "lowercase letters")
    _add_character_option(parser, "digits", "digits", "digits")
    _add_character_option(
        parser, "special", "special", "special characters"
    )
    return parser


def _resolve_character_options(args: argparse.Namespace) -> CharacterOptions:
    """Resolve optional include/exclude flags to concrete character options."""
    return CharacterOptions(
        uppercase=True if args.uppercase is None else args.uppercase,
        lowercase=True if args.lowercase is None else args.lowercase,
        digits=True if args.digits is None else args.digits,
        special=True if args.special is None else args.special,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run the password generator CLI.

    Args:
        argv: Optional argument list for testing. If omitted, command-line
            arguments from ``sys.argv`` are used.

    Returns:
        Process exit code. ``0`` indicates success; ``2`` indicates invalid
        user input.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    options = _resolve_character_options(args)

    try:
        password = generate_password(args.length, options)
    except PasswordGeneratorError as exc:
        parser.exit(status=2, message=f"error: {exc}\n")

    print(f"Password: {password}")
    print(f"Strength: {evaluate_strength(password)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

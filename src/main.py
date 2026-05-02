"""Command-line interface for the password generator."""

from __future__ import annotations

import argparse
import sys

try:  # Supports both `python -m src.main` and test/package imports.
    from .password_generator import (
        CharacterSetConfig,
        MAX_LENGTH,
        MIN_LENGTH,
        evaluate_strength,
        generate_password,
    )
except ImportError:  # Supports direct execution: `python src/main.py`.
    from password_generator import (
        CharacterSetConfig,
        MAX_LENGTH,
        MIN_LENGTH,
        evaluate_strength,
        generate_password,
    )


def build_parser() -> argparse.ArgumentParser:
    """Create and configure the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate a secure password with a strength rating."
    )
    parser.add_argument(
        "-l",
        "--length",
        type=int,
        required=True,
        help=f"Password length ({MIN_LENGTH}-{MAX_LENGTH} characters).",
    )

    parser.add_argument(
        "--uppercase",
        dest="uppercase",
        action="store_true",
        default=True,
        help="Include uppercase letters (enabled by default).",
    )
    parser.add_argument(
        "--no-uppercase",
        dest="uppercase",
        action="store_false",
        help="Exclude uppercase letters.",
    )
    parser.add_argument(
        "--lowercase",
        dest="lowercase",
        action="store_true",
        default=True,
        help="Include lowercase letters (enabled by default).",
    )
    parser.add_argument(
        "--no-lowercase",
        dest="lowercase",
        action="store_false",
        help="Exclude lowercase letters.",
    )
    parser.add_argument(
        "--digits",
        dest="digits",
        action="store_true",
        default=True,
        help="Include digits (enabled by default).",
    )
    parser.add_argument(
        "--no-digits",
        dest="digits",
        action="store_false",
        help="Exclude digits.",
    )
    parser.add_argument(
        "--special",
        dest="special",
        action="store_true",
        default=True,
        help="Include special characters (enabled by default).",
    )
    parser.add_argument(
        "--no-special",
        dest="special",
        action="store_false",
        help="Exclude special characters.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the password generator CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    config = CharacterSetConfig(
        uppercase=args.uppercase,
        lowercase=args.lowercase,
        digits=args.digits,
        special=args.special,
    )

    try:
        password = generate_password(args.length, config)
    except ValueError as exc:
        parser.exit(status=2, message=f"Error: {exc}\n")

    strength = evaluate_strength(password)
    print(f"Password: {password}")
    print(f"Strength: {strength.value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

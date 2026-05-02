"""CLI entry point for the password generator."""

from __future__ import annotations

import argparse
import sys

try:  # pragma: no cover - exercised by direct script execution
    from password_generator import (
        CharacterOptions,
        PasswordGeneratorError,
        evaluate_strength,
        generate_password,
        parse_length,
        validate_options,
    )
except ImportError:  # pragma: no cover - exercised when imported as package
    from src.password_generator import (
        CharacterOptions,
        PasswordGeneratorError,
        evaluate_strength,
        generate_password,
        parse_length,
        validate_options,
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate a secure password with a strength meter."
    )
    parser.add_argument(
        "-l",
        "--length",
        required=True,
        help="Desired password length (1-256).",
    )

    parser.add_argument(
        "--uppercase",
        dest="uppercase",
        action="store_true",
        default=True,
        help="Include uppercase letters (default).",
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
        help="Include lowercase letters (default).",
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
        help="Include digits (default).",
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
        help="Include special characters (default).",
    )
    parser.add_argument(
        "--no-special",
        dest="special",
        action="store_false",
        help="Exclude special characters.",
    )
    return parser


def options_from_args(args: argparse.Namespace) -> CharacterOptions:
    """Create character options from parsed CLI arguments."""
    return CharacterOptions(
        uppercase=args.uppercase,
        lowercase=args.lowercase,
        digits=args.digits,
        special=args.special,
    )


def main(argv: list[str] | None = None) -> int:
    """Run the CLI password generator."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        length = parse_length(args.length)
        options = options_from_args(args)
        validate_options(options)
        password = generate_password(length, options)
        category, score = evaluate_strength(password)
    except PasswordGeneratorError as exc:
        parser.exit(status=2, message=f"Error: {exc}\n")

    print(f"Password: {password}")
    print(f"Strength: {category.value} ({score}/100)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

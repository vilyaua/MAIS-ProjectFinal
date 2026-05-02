"""Command line interface for the password generator."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parent))
    from password_generator import (  # type: ignore[no-redef]
        CharacterSelection,
        PasswordError,
        evaluate_strength,
        format_strength_meter,
        generate_password,
    )
else:
    from .password_generator import (
        CharacterSelection,
        PasswordError,
        evaluate_strength,
        format_strength_meter,
        generate_password,
    )


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate a password and display its strength meter."
    )
    parser.add_argument(
        "--length",
        "-l",
        required=True,
        type=int,
        help="Desired password length as a positive integer.",
    )
    parser.add_argument(
        "--uppercase",
        action="store_true",
        help="Include uppercase letters (A-Z).",
    )
    parser.add_argument(
        "--lowercase",
        action="store_true",
        help="Include lowercase letters (a-z).",
    )
    parser.add_argument(
        "--digits",
        action="store_true",
        help="Include digits (0-9).",
    )
    parser.add_argument(
        "--special",
        action="store_true",
        help="Include special characters.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the password generator CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    selection = CharacterSelection(
        uppercase=args.uppercase,
        lowercase=args.lowercase,
        digits=args.digits,
        special=args.special,
    )

    try:
        password = generate_password(args.length, selection)
    except PasswordError as exc:
        parser.exit(status=2, message=f"Error: {exc}\n")

    strength = evaluate_strength(password)
    print(f"Generated password: {password}")
    print(f"Strength meter: {format_strength_meter(strength)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

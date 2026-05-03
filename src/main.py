"""Command-line interface for the password generator."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

try:  # Supports both `python src/main.py` and importing `src.main` in tests.
    from .password_generator import (
        MAX_LENGTH,
        MIN_LENGTH,
        PasswordGenerationError,
        PasswordOptions,
        evaluate_strength,
        generate_password,
        validate_options,
    )
except ImportError:  # pragma: no cover - exercised when run as a script
    from password_generator import (
        MAX_LENGTH,
        MIN_LENGTH,
        PasswordGenerationError,
        PasswordOptions,
        evaluate_strength,
        generate_password,
        validate_options,
    )


def _parse_length(raw_value: str) -> int:
    """Parse and validate the length argument for argparse."""
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("length must be an integer") from exc

    if value <= 0:
        raise argparse.ArgumentTypeError(
            "length must be a positive integer greater than zero"
        )
    if value < MIN_LENGTH or value > MAX_LENGTH:
        raise argparse.ArgumentTypeError(
            f"length must be between {MIN_LENGTH} and {MAX_LENGTH}"
        )
    return value


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate a random password and display its strength rating."
    )
    parser.add_argument(
        "-l",
        "--length",
        type=_parse_length,
        help=f"password length ({MIN_LENGTH}-{MAX_LENGTH})",
    )
    parser.add_argument(
        "-u",
        "--uppercase",
        action="store_true",
        help="include uppercase letters",
    )
    parser.add_argument(
        "--lowercase",
        action="store_true",
        help="include lowercase letters",
    )
    parser.add_argument(
        "-d",
        "--digits",
        action="store_true",
        help="include digits",
    )
    parser.add_argument(
        "-s",
        "--special",
        action="store_true",
        help="include special characters",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="prompt for inputs interactively",
    )
    return parser


def _prompt_yes_no(prompt: str) -> bool:
    """Prompt the user for a yes/no answer until valid input is supplied."""
    while True:
        answer = input(prompt).strip().lower()
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print("Please answer 'y' or 'n'.")


def prompt_for_options() -> PasswordOptions:
    """Interactively prompt until valid password options are entered."""
    while True:
        raw_length = input(f"Password length ({MIN_LENGTH}-{MAX_LENGTH}): ").strip()
        try:
            length = _parse_length(raw_length)
        except argparse.ArgumentTypeError as exc:
            print(f"Error: {exc}")
            continue

        options = PasswordOptions(
            length=length,
            uppercase=_prompt_yes_no("Include uppercase letters? (y/n): "),
            lowercase=_prompt_yes_no("Include lowercase letters? (y/n): "),
            digits=_prompt_yes_no("Include digits? (y/n): "),
            special=_prompt_yes_no("Include special characters? (y/n): "),
        )
        try:
            validate_options(options)
        except PasswordGenerationError as exc:
            print(f"Error: {exc}")
            print("Please enter the options again.\n")
            continue
        return options


def options_from_args(args: argparse.Namespace) -> PasswordOptions:
    """Convert parsed arguments to password options."""
    if args.length is None:
        raise PasswordGenerationError(
            "Password length is required. Provide --length or use --interactive."
        )

    options = PasswordOptions(
        length=args.length,
        uppercase=args.uppercase,
        lowercase=args.lowercase,
        digits=args.digits,
        special=args.special,
    )
    validate_options(options)
    return options


def run(argv: Sequence[str] | None = None) -> int:
    """Run the CLI application and return a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.interactive or (argv is None and len(sys.argv) == 1):
            options = prompt_for_options()
        else:
            options = options_from_args(args)

        password = generate_password(options)
        strength = evaluate_strength(password)
    except PasswordGenerationError as exc:
        parser.exit(status=2, message=f"Error: {exc}\n")

    print(f"Generated password: {password}")
    print(f"Strength: {strength.rating} ({strength.score}/100)")
    print(
        "Strength details: "
        f"length {strength.length_points}/50, "
        f"variety {strength.variety_points}/50"
    )
    return 0


def main() -> None:
    """CLI entry point."""
    raise SystemExit(run())


if __name__ == "__main__":
    main()

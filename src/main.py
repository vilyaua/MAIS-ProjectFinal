"""Command line interface for the secure password generator."""

from __future__ import annotations

import argparse
from typing import Sequence

from password_generator import (
    MAX_LENGTH,
    MIN_LENGTH,
    PasswordGeneratorError,
    PasswordOptions,
    calculate_strength,
    generate_password,
    validate_length,
)


def parse_length(value: str) -> int:
    """Parse and validate a CLI length value for argparse."""
    try:
        length = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("length must be an integer") from exc

    try:
        validate_length(length)
    except PasswordGeneratorError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    return length


def build_parser() -> argparse.ArgumentParser:
    """Build the command line argument parser."""
    parser = argparse.ArgumentParser(
        prog="password-generator",
        description="Generate secure random passwords with a strength meter.",
    )
    parser.add_argument(
        "-l",
        "--length",
        type=parse_length,
        help=f"password length ({MIN_LENGTH}-{MAX_LENGTH}); prompts if omitted",
    )
    parser.add_argument(
        "--uppercase",
        dest="uppercase",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="include uppercase letters (default: enabled)",
    )
    parser.add_argument(
        "--lowercase",
        dest="lowercase",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="include lowercase letters (default: enabled)",
    )
    parser.add_argument(
        "--digits",
        dest="digits",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="include digits (default: enabled)",
    )
    parser.add_argument(
        "--special",
        dest="special",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="include special characters (default: enabled)",
    )
    return parser


def prompt_for_length() -> int:
    """Prompt until the user enters a valid password length."""
    while True:
        raw_value = input(f"Password length ({MIN_LENGTH}-{MAX_LENGTH}): ").strip()
        try:
            length = int(raw_value)
            validate_length(length)
        except PasswordGeneratorError as exc:
            print(f"Error: {exc} Please try again.")
        except ValueError:
            print("Error: Length must be an integer. Please try again.")
        else:
            return length


def prompt_yes_no(label: str, default: bool = True) -> bool:
    """Prompt for a yes/no answer, repeating until the answer is valid."""
    default_hint = "Y/n" if default else "y/N"
    while True:
        raw_value = input(f"Include {label}? ({default_hint}): ").strip().lower()
        if not raw_value:
            return default
        if raw_value in {"y", "yes"}:
            return True
        if raw_value in {"n", "no"}:
            return False
        print("Error: Please answer 'yes' or 'no'.")


def prompt_for_options() -> PasswordOptions:
    """Interactively prompt until a valid option combination is entered."""
    print("Interactive password generator. Press Ctrl+C to cancel.")
    while True:
        length = prompt_for_length()
        options = PasswordOptions(
            length=length,
            uppercase=prompt_yes_no("uppercase letters"),
            lowercase=prompt_yes_no("lowercase letters"),
            digits=prompt_yes_no("digits"),
            special=prompt_yes_no("special characters"),
        )
        if options.selected_categories():
            return options
        print("Error: At least one character type must be chosen. Please try again.")


def options_from_args(args: argparse.Namespace) -> PasswordOptions:
    """Create password options from parsed argparse values."""
    if args.length is None:
        return prompt_for_options()
    return PasswordOptions(
        length=args.length,
        uppercase=args.uppercase,
        lowercase=args.lowercase,
        digits=args.digits,
        special=args.special,
    )


def display_password(password: str) -> None:
    """Display a generated password and its strength meter."""
    strength = calculate_strength(password)
    print(f"Generated password: {password}")
    print(
        "Strength: "
        f"{strength.bar} {strength.score}/100 "
        f"({strength.label.value}, {strength.variety_count} character types)"
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run the password generator CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        options = options_from_args(args)
        password = generate_password(options)
    except KeyboardInterrupt:
        print("\nCancelled.")
        return 130
    except PasswordGeneratorError as exc:
        parser.error(str(exc))
        return 2

    display_password(password)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

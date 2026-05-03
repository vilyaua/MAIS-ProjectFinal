"""Command-line interface for the password generator."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

try:
    from password_generator import (
        CharacterSetOptions,
        PasswordError,
        evaluate_strength,
        generate_password,
        parse_positive_length,
    )
except ModuleNotFoundError:  # pragma: no cover - supports `python -m src.main`
    from src.password_generator import (  # type: ignore[no-redef]
        CharacterSetOptions,
        PasswordError,
        evaluate_strength,
        generate_password,
        parse_positive_length,
    )


def _yes_no_prompt(prompt: str) -> bool:
    """Prompt until the user provides a yes/no answer."""
    while True:
        answer = input(f"{prompt} [y/n]: ").strip().lower()
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print("Please answer 'y' or 'n'.")


def prompt_for_length() -> int:
    """Prompt until a valid positive integer length is provided."""
    while True:
        raw_length = input("Enter password length (positive integer): ").strip()
        try:
            return parse_positive_length(raw_length)
        except PasswordError as exc:
            print(f"Error: {exc}")


def prompt_for_options() -> CharacterSetOptions:
    """Prompt until at least one character set is selected."""
    while True:
        options = CharacterSetOptions(
            uppercase=_yes_no_prompt("Include uppercase letters?"),
            lowercase=_yes_no_prompt("Include lowercase letters?"),
            digits=_yes_no_prompt("Include digits?"),
            special=_yes_no_prompt("Include special characters?"),
        )
        if options.has_any_selected():
            return options
        print("Error: Select at least one character set.")


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate a random password and display its strength."
    )
    parser.add_argument(
        "-l",
        "--length",
        help="Password length as a positive integer. If omitted, you will be prompted.",
    )
    parser.add_argument(
        "--uppercase",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Include uppercase letters.",
    )
    parser.add_argument(
        "--lowercase",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Include lowercase letters.",
    )
    parser.add_argument(
        "--digits",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Include digits.",
    )
    parser.add_argument(
        "--special",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Include special characters.",
    )
    return parser


def _options_from_args(args: argparse.Namespace) -> CharacterSetOptions | None:
    values = [args.uppercase, args.lowercase, args.digits, args.special]
    if all(value is None for value in values):
        return None
    return CharacterSetOptions(
        uppercase=bool(args.uppercase),
        lowercase=bool(args.lowercase),
        digits=bool(args.digits),
        special=bool(args.special),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI password generator.

    Args:
        argv: Optional command-line arguments, excluding the program name.

    Returns:
        Process exit code.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.length is None:
        length = prompt_for_length()
    else:
        try:
            length = parse_positive_length(args.length)
        except PasswordError as exc:
            print(f"Error: {exc}")
            return 1

    options = _options_from_args(args)
    if options is None:
        options = prompt_for_options()
    elif not options.has_any_selected():
        print("Error: Select at least one character set.")
        return 1

    try:
        password = generate_password(length, options)
    except PasswordError as exc:
        print(f"Error: {exc}")
        return 1

    strength = evaluate_strength(password)
    print(f"Generated password: {password}")
    print(f"Strength: {strength.value}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

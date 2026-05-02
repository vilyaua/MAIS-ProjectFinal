"""Command-line interface for the password generator."""

from __future__ import annotations

import argparse
import sys

try:
    from src.password_generator import (
        MAX_LENGTH,
        MIN_LENGTH,
        CharacterOptions,
        PasswordGeneratorError,
        evaluate_strength,
        generate_password,
    )
except ModuleNotFoundError:  # Allows running as: python src/main.py
    from password_generator import (  # type: ignore[no-redef]
        MAX_LENGTH,
        MIN_LENGTH,
        CharacterOptions,
        PasswordGeneratorError,
        evaluate_strength,
        generate_password,
    )


def bounded_length(value: str) -> int:
    """Parse and validate the CLI length argument."""
    try:
        length = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("length must be an integer") from exc

    if length < MIN_LENGTH or length > MAX_LENGTH:
        raise argparse.ArgumentTypeError(
            f"length must be between {MIN_LENGTH} and {MAX_LENGTH}"
        )
    return length


def build_parser() -> argparse.ArgumentParser:
    """Build the password generator argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate a random password and display its strength rating.",
        epilog=(
            "Example: python src/main.py --length 16 --uppercase --lowercase "
            "--digits --special"
        ),
    )
    parser.add_argument(
        "-l",
        "--length",
        type=bounded_length,
        required=True,
        help=f"password length ({MIN_LENGTH}-{MAX_LENGTH})",
    )
    parser.add_argument(
        "--uppercase",
        action="store_true",
        help="include uppercase letters (A-Z)",
    )
    parser.add_argument(
        "--lowercase",
        action="store_true",
        help="include lowercase letters (a-z)",
    )
    parser.add_argument(
        "--digits",
        action="store_true",
        help="include digits (0-9)",
    )
    parser.add_argument(
        "--special",
        action="store_true",
        help="include special characters",
    )
    return parser


def reject_unknown_options(
    parser: argparse.ArgumentParser, arguments: list[str]
) -> None:
    """Emit an argparse error for unknown options before required checks.

    argparse reports missing required arguments before unknown options in some
    cases. This pre-check keeps invalid option feedback descriptive while still
    allowing values such as ``--length -1`` to be handled by the length parser.
    """
    known_options = set(parser._option_string_actions)  # noqa: SLF001
    unknown_options: list[str] = []
    skip_next = False

    for argument in arguments:
        if skip_next:
            skip_next = False
            continue
        if argument in {"-l", "--length"}:
            skip_next = True
            continue
        if argument == "--":
            break
        if argument.startswith("-") and argument not in known_options:
            unknown_options.append(argument)

    if unknown_options:
        parser.error(f"unrecognized arguments: {' '.join(unknown_options)}")


def main(argv: list[str] | None = None) -> int:
    """Run the CLI.

    Args:
        argv: Optional argument list, excluding the program name.

    Returns:
        Process exit code.
    """
    parser = build_parser()
    arguments = sys.argv[1:] if argv is None else argv
    reject_unknown_options(parser, arguments)
    args = parser.parse_args(arguments)

    options = CharacterOptions(
        uppercase=args.uppercase,
        lowercase=args.lowercase,
        digits=args.digits,
        special=args.special,
    )

    try:
        password = generate_password(args.length, options)
    except PasswordGeneratorError as exc:
        parser.error(str(exc))
        return 2

    strength = evaluate_strength(password)
    print(f"Generated password: {password}")
    print(f"Strength: {strength.value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

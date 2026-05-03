"""CLI weekday calculator.

Parse common free-form date inputs and print the corresponding weekday.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime
from typing import Iterable, Sequence, TextIO


SUPPORTED_FORMATS: tuple[str, ...] = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%Y.%m.%d",
    "%m/%d/%Y",
    "%m-%d-%Y",
    "%m.%d.%Y",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%d.%m.%Y",
    "%d %B %Y",
    "%d %b %Y",
    "%B %d %Y",
    "%b %d %Y",
    "%d %B, %Y",
    "%d %b, %Y",
    "%B %d, %Y",
    "%b %d, %Y",
)


class DateParseError(ValueError):
    """Raised when a date string cannot be parsed as a valid date."""


def normalize_date_text(value: str) -> str:
    """Normalize user-entered date text for parsing.

    The parser remains intentionally deterministic: it supports a documented set
    of common formats instead of guessing every possible locale-specific date.
    """
    normalized = " ".join(value.strip().split())
    return normalized.rstrip(",")


def parse_date(date_text: str, formats: Iterable[str] = SUPPORTED_FORMATS) -> date:
    """Parse a date string using supported formats.

    Args:
        date_text: User-provided date text.
        formats: Date formats to try, primarily useful for tests.

    Returns:
        A ``datetime.date`` instance.

    Raises:
        DateParseError: If the input is empty or cannot be parsed.
    """
    normalized = normalize_date_text(date_text)
    if not normalized:
        raise DateParseError("No date was provided.")

    for date_format in formats:
        try:
            return datetime.strptime(normalized, date_format).date()
        except ValueError:
            continue

    raise DateParseError(
        "Invalid or unparseable date. Please use a valid date such as "
        "'YYYY-MM-DD', 'MM/DD/YYYY', or 'DD Month YYYY'."
    )


def weekday_name(date_text: str) -> str:
    """Return the weekday name for a user-provided date string."""
    parsed_date = parse_date(date_text)
    return parsed_date.strftime("%A")


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="weekday-calculator",
        description="Calculate the day of the week for a date.",
    )
    parser.add_argument(
        "date",
        nargs="*",
        help=(
            "Date to evaluate, for example: 2020-02-29, 02/29/2020, "
            "or '29 February 2020'."
        ),
    )
    return parser


def _read_missing_input(stdin: TextIO, stdout: TextIO) -> str | None:
    """Prompt for a missing date when possible.

    In non-interactive contexts, return ``None`` so the caller can show usage
    instructions instead of blocking unexpectedly.
    """
    if stdin.isatty():
        stdout.write("Enter a date: ")
        stdout.flush()
        return stdin.readline().strip()
    return None


def main(argv: Sequence[str] | None = None) -> int:
    """Run the weekday calculator CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    date_text = " ".join(args.date).strip()
    if not date_text:
        prompted_input = _read_missing_input(sys.stdin, sys.stdout)
        if prompted_input is None or not prompted_input.strip():
            parser.print_usage(sys.stderr)
            print(
                "Error: missing date input. Provide a date such as '2020-02-29' "
                "or '29 February 2020'.",
                file=sys.stderr,
            )
            return 2
        date_text = prompted_input

    try:
        result = weekday_name(date_text)
    except DateParseError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"{date_text} is a {result}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Command-line entry point for the CSV statistical summary tool."""

from __future__ import annotations

import argparse
import sys

from csv_summary import CsvSummaryError, analyze_csv, format_summary


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate a statistical summary report for a CSV file."
    )
    parser.add_argument("csv_file", help="Path to the CSV file to summarize")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CSV summary CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        summary = analyze_csv(args.csv_file)
    except CsvSummaryError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(format_summary(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

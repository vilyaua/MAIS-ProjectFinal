"""Command-line entry point for the CSV statistical summary tool."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from csv_summary import CSVSummaryError, render_summary, summarize_csv


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Print a statistical summary for a CSV file."
    )
    parser.add_argument("csv_file", help="Path to the CSV file to summarize")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CSV summary CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        summary = summarize_csv(Path(args.csv_file))
    except CSVSummaryError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(render_summary(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

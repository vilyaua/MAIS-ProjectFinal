"""Command-line entry point for the CSV Statistical Summary tool."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parent))
    from csv_summary import (  # type: ignore[import-not-found]  # noqa: E402
        CSVFileNotFoundError,
        CSVSummaryError,
        format_summary,
        summarize_csv,
    )
else:
    from .csv_summary import (  # noqa: E402
        CSVFileNotFoundError,
        CSVSummaryError,
        format_summary,
        summarize_csv,
    )


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate a statistical summary for a CSV file."
    )
    parser.add_argument("csv_file", help="Path to the CSV file to summarize")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CSV summary CLI and return a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        summary = summarize_csv(args.csv_file)
    except CSVFileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except CSVSummaryError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(format_summary(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

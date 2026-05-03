"""CSV statistical summary CLI tool.

This module provides functions to parse a CSV file, infer column types, and
produce a concise statistical/frequency summary. It can also be executed as a
command line application.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from statistics import mean, median
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

NULL_VALUES = {"", "na", "n/a", "null", "none", "nan"}


class CsvSummaryError(Exception):
    """Base class for user-facing CSV summary errors."""


class FileValidationError(CsvSummaryError):
    """Raised when an input file cannot be used."""


class CsvParseError(CsvSummaryError):
    """Raised when CSV content cannot be parsed."""


def is_missing(value: Optional[str]) -> bool:
    """Return True when *value* should be treated as null/missing."""
    if value is None:
        return True
    return value.strip().lower() in NULL_VALUES


def parse_number(value: str) -> Optional[float]:
    """Parse a string as a float, returning None when it is not numeric."""
    try:
        return float(value.strip())
    except (TypeError, ValueError):
        return None


def validate_input_path(file_path: str) -> Path:
    """Validate and return the CSV path supplied by the user.

    Raises:
        FileValidationError: If the path does not exist, is not a file, or does
            not look like a CSV file based on extension.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileValidationError(f"File not found: {file_path}")
    if not path.is_file():
        raise FileValidationError(f"Input path is not a file: {file_path}")
    if path.suffix.lower() != ".csv":
        raise FileValidationError(
            f"Input file must be a CSV file with a .csv extension: {file_path}"
        )
    return path


def read_csv(path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    """Read CSV data from *path* and return headers plus row dictionaries.

    The parser uses strict CSV mode and additionally checks for inconsistent row
    lengths, which are common signs of malformed CSV input.
    """
    try:
        if path.stat().st_size == 0:
            return [], []

        rows: List[Dict[str, str]] = []
        with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.reader(csv_file, strict=True)
            try:
                header = next(reader)
            except StopIteration:
                return [], []

            if not header or all(cell.strip() == "" for cell in header):
                raise CsvParseError("CSV file does not contain a valid header row.")

            if len(set(header)) != len(header):
                raise CsvParseError("CSV file contains duplicate column names.")

            for line_number, row in enumerate(reader, start=2):
                if len(row) != len(header):
                    raise CsvParseError(
                        "CSV file could not be parsed: "
                        f"row {line_number} has {len(row)} fields but "
                        f"expected {len(header)}."
                    )
                rows.append(dict(zip(header, row)))
    except UnicodeDecodeError as exc:
        raise CsvParseError("CSV file could not be decoded as UTF-8 text.") from exc
    except csv.Error as exc:
        raise CsvParseError(f"CSV file could not be parsed: {exc}") from exc
    except OSError as exc:
        raise FileValidationError(f"Unable to read file: {exc}") from exc

    return header, rows


def infer_column_type(values: Iterable[str]) -> str:
    """Infer whether a column is numeric or categorical.

    A column is considered numeric when it has at least one non-missing value and
    all non-missing values can be parsed as floats. Otherwise it is categorical.
    """
    non_missing = [value for value in values if not is_missing(value)]
    if not non_missing:
        return "categorical"
    return (
        "numeric"
        if all(parse_number(value) is not None for value in non_missing)
        else "categorical"
    )


def top_five(values: Sequence[str]) -> List[Dict[str, Any]]:
    """Return the top five most common values, including missing values.

    Missing values are normalized to the display token ``<MISSING>`` so empty
    strings, NULL, NA, etc. are counted together.
    """
    normalized_values = ["<MISSING>" if is_missing(value) else value for value in values]
    counter = Counter(normalized_values)
    return [{"value": value, "count": count} for value, count in counter.most_common(5)]


def summarize_csv(file_path: str) -> Dict[str, Any]:
    """Build a statistical summary for the CSV file at *file_path*.

    Returns a dictionary suitable for JSON rendering.
    """
    path = validate_input_path(file_path)
    headers, rows = read_csv(path)

    summary: Dict[str, Any] = {
        "file": str(path),
        "row_count": len(rows),
        "column_count": len(headers),
        "columns": {},
    }

    if not headers or not rows:
        summary["message"] = "No data to process."
        return summary

    for column in headers:
        values = [row[column] for row in rows]
        column_type = infer_column_type(values)
        column_summary: Dict[str, Any] = {
            "type": column_type,
            "missing_count": sum(1 for value in values if is_missing(value)),
            "top_5_values": top_five(values),
        }

        if column_type == "numeric":
            numeric_values = [
                number
                for value in values
                if not is_missing(value)
                for number in [parse_number(value)]
                if number is not None
            ]
            column_summary["statistics"] = {
                "min": min(numeric_values),
                "max": max(numeric_values),
                "mean": mean(numeric_values),
                "median": median(numeric_values),
            }

        summary["columns"][column] = column_summary

    return summary


def format_summary(summary: Dict[str, Any]) -> str:
    """Format a summary dictionary as stable, human-readable JSON."""
    return json.dumps(summary, indent=2, sort_keys=False)


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate statistical and frequency summaries for a CSV file."
    )
    parser.add_argument("csv_file", help="Path to the CSV file to summarize")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the CSV summary command line interface."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        summary = summarize_csv(args.csv_file)
    except CsvSummaryError as exc:
        print(f"Error: {exc}")
        return 1

    print(format_summary(summary))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

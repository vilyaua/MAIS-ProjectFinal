"""CSV Statistical Summary CLI Tool.

This module implements a small command-line application that reads a CSV file,
infers column types, and prints a JSON statistical summary.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Sequence


MISSING_TOKENS = {"", "na", "n/a", "null", "none", "nan"}
DATETIME_FORMATS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%m/%d/%Y",
    "%d/%m/%Y",
    "%Y-%m-%d %H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%d %H:%M",
    "%b %d %Y",
    "%B %d %Y",
)


class CsvSummaryError(Exception):
    """Base exception for user-facing CSV summary errors."""


class MalformedCsvError(CsvSummaryError):
    """Raised when CSV content cannot be parsed consistently."""


@dataclass(frozen=True)
class CsvTable:
    """In-memory representation of a CSV file."""

    headers: list[str]
    rows: list[list[str]]


def is_missing(value: str) -> bool:
    """Return True when *value* should be counted as missing."""

    return value.strip().lower() in MISSING_TOKENS


def parse_number(value: str) -> float | None:
    """Parse a numeric value, returning None when parsing fails."""

    normalized = value.strip().replace(",", "")
    if normalized == "":
        return None
    try:
        return float(normalized)
    except ValueError:
        return None


def parse_datetime(value: str) -> datetime | None:
    """Parse common datetime representations.

    Numeric-only strings are intentionally rejected so identifiers or years are
    not misclassified as datetimes.
    """

    stripped = value.strip()
    if not stripped or stripped.isdigit():
        return None

    try:
        return datetime.fromisoformat(stripped.replace("Z", "+00:00"))
    except ValueError:
        pass

    for date_format in DATETIME_FORMATS:
        try:
            return datetime.strptime(stripped, date_format)
        except ValueError:
            continue
    return None


def infer_column_type(values: Sequence[str]) -> str:
    """Infer a column type as numeric, datetime, or categorical."""

    present_values = [value for value in values if not is_missing(value)]
    if not present_values:
        return "categorical"

    if all(parse_number(value) is not None for value in present_values):
        return "numeric"

    if all(parse_datetime(value) is not None for value in present_values):
        return "datetime"

    return "categorical"


def read_csv(path: Path) -> CsvTable:
    """Read and validate a CSV file.

    The parser sniffs common dialect differences such as delimiter and quote
    style, and then validates that every row has the same number of fields as
    the header.
    """

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not path.is_file():
        raise CsvSummaryError(f"Path is not a file: {path}")

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as file_obj:
            sample = file_obj.read(4096)
            if not sample:
                raise MalformedCsvError("CSV file is empty.")
            file_obj.seek(0)

            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
            except csv.Error:
                dialect = csv.excel
            dialect.strict = True

            reader = csv.reader(file_obj, dialect)
            try:
                headers = next(reader)
            except StopIteration as exc:
                raise MalformedCsvError("CSV file is empty.") from exc
            except csv.Error as exc:
                raise MalformedCsvError(f"Malformed CSV header: {exc}") from exc

            if not headers or all(header.strip() == "" for header in headers):
                raise MalformedCsvError("CSV header row is missing or empty.")

            normalized_headers = [
                header.strip() or f"column_{index + 1}"
                for index, header in enumerate(headers)
            ]
            expected_width = len(normalized_headers)
            rows: list[list[str]] = []
            for row_number, row in enumerate(reader, start=2):
                if len(row) != expected_width:
                    raise MalformedCsvError(
                        "Malformed CSV data at row "
                        f"{row_number}: expected {expected_width} fields, "
                        f"found {len(row)}."
                    )
                rows.append(row)
    except UnicodeDecodeError as exc:
        raise CsvSummaryError(f"Unable to read file as UTF-8 text: {path}") from exc
    except PermissionError as exc:
        raise CsvSummaryError(f"File is not readable: {path}") from exc
    except csv.Error as exc:
        raise MalformedCsvError(f"Malformed CSV data: {exc}") from exc

    return CsvTable(headers=normalized_headers, rows=rows)


def format_number(value: float) -> int | float:
    """Return integers without a trailing decimal when possible."""

    if value.is_integer():
        return int(value)
    return value


def numeric_statistics(values: Iterable[str]) -> dict[str, int | float] | None:
    """Calculate min, max, mean, and median for present numeric values."""

    numbers = [
        parsed
        for value in values
        if not is_missing(value)
        for parsed in [parse_number(value)]
        if parsed is not None
    ]
    if not numbers:
        return None

    return {
        "min": format_number(min(numbers)),
        "max": format_number(max(numbers)),
        "mean": format_number(statistics.fmean(numbers)),
        "median": format_number(float(statistics.median(numbers))),
    }


def top_values(values: Iterable[str], limit: int = 5) -> list[dict[str, str | int]]:
    """Return the most frequent non-missing values and counts."""

    normalized_values = [value.strip() for value in values if not is_missing(value)]
    counts = Counter(normalized_values)
    return [
        {"value": value, "count": count}
        for value, count in counts.most_common(limit)
    ]


def summarize_table(table: CsvTable) -> dict[str, Any]:
    """Build a JSON-serializable statistical summary for a table."""

    columns: dict[str, Any] = {}
    for index, header in enumerate(table.headers):
        values = [row[index] for row in table.rows]
        column_type = infer_column_type(values)
        column_summary: dict[str, Any] = {
            "type": column_type,
            "missing_values": sum(1 for value in values if is_missing(value)),
            "top_values": top_values(values),
        }
        if column_type == "numeric":
            column_summary["statistics"] = numeric_statistics(values)
        columns[header] = column_summary

    return {
        "row_count": len(table.rows),
        "column_count": len(table.headers),
        "columns": columns,
    }


def summarize_csv(path: Path) -> dict[str, Any]:
    """Read a CSV file and return its statistical summary."""

    return summarize_table(read_csv(path))


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""

    parser = argparse.ArgumentParser(
        description="Generate a statistical summary for a CSV file."
    )
    parser.add_argument("csv_path", type=Path, help="Path to the CSV file")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        summary = summarize_csv(args.csv_path)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except MalformedCsvError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except CsvSummaryError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

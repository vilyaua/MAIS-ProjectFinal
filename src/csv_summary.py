"""CSV Statistical Summary CLI Tool.

This module provides a command line interface and reusable functions for
summarising CSV files without requiring third-party dependencies.
"""

from __future__ import annotations

import argparse
import csv
import math
import statistics
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Sequence, TextIO

MISSING_VALUES = {"", "na", "n/a", "null", "none", "nan"}
DATETIME_FORMATS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%m/%d/%Y",
    "%d/%m/%Y",
    "%Y-%m-%d %H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
    "%m/%d/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M:%S",
)


class CsvSummaryError(Exception):
    """Raised when the CSV summary tool cannot process an input file."""


@dataclass
class ColumnAccumulator:
    """Incrementally collect summary data for one CSV column."""

    name: str
    total_count: int = 0
    missing_count: int = 0
    non_missing_count: int = 0
    top_values: Counter[str] = field(default_factory=Counter)
    could_be_numeric: bool = True
    could_be_datetime: bool = True
    numeric_values: list[float] = field(default_factory=list)

    def add(self, raw_value: str | None) -> None:
        """Add a raw CSV field value to this accumulator."""
        self.total_count += 1
        value = "" if raw_value is None else str(raw_value).strip()

        if is_missing(value):
            self.missing_count += 1
            return

        self.non_missing_count += 1
        self.top_values[value] += 1

        if self.could_be_numeric:
            parsed = parse_float(value)
            if parsed is None:
                self.could_be_numeric = False
                self.numeric_values.clear()
            else:
                self.numeric_values.append(parsed)

        if self.could_be_datetime and parse_datetime(value) is None:
            self.could_be_datetime = False

    def summary(self) -> dict[str, Any]:
        """Return a serialisable summary for the column."""
        column_type = self.detect_type()
        numeric_stats = None
        if column_type == "numeric":
            numeric_stats = numeric_summary(self.numeric_values)

        return {
            "name": self.name,
            "type": column_type,
            "missing_count": self.missing_count,
            "total_count": self.total_count,
            "non_missing_count": self.non_missing_count,
            "numeric_stats": numeric_stats,
            "top_values": self.top_values.most_common(5),
        }

    def detect_type(self) -> str:
        """Determine the most appropriate type label for this column."""
        if self.non_missing_count == 0:
            return "all_missing"
        if self.could_be_numeric:
            return "numeric"
        if self.could_be_datetime:
            return "datetime"
        return "categorical"


def is_missing(value: str) -> bool:
    """Return True if a value should be treated as missing."""
    return value.strip().lower() in MISSING_VALUES


def parse_float(value: str) -> float | None:
    """Parse a finite float, returning None for non-numeric values."""
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(parsed):
        return None
    return parsed


def parse_datetime(value: str) -> datetime | None:
    """Parse common datetime string formats, returning None when invalid."""
    stripped = value.strip()
    if not stripped:
        return None

    # Handle ISO-8601 variants supported by datetime.fromisoformat, including
    # a trailing Z UTC marker.
    iso_candidate = stripped[:-1] + "+00:00" if stripped.endswith("Z") else stripped
    try:
        return datetime.fromisoformat(iso_candidate)
    except ValueError:
        pass

    for date_format in DATETIME_FORMATS:
        try:
            return datetime.strptime(stripped, date_format)
        except ValueError:
            continue
    return None


def numeric_summary(values: Sequence[float]) -> dict[str, float] | None:
    """Compute min, max, mean, and median for numeric values."""
    if not values:
        return None
    return {
        "min": min(values),
        "max": max(values),
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
    }


def validate_csv_path(file_path: str) -> Path:
    """Validate a user-supplied CSV path and return it as a Path."""
    path = Path(file_path)
    if not path.exists():
        raise CsvSummaryError(f"Input file does not exist: {file_path}")
    if not path.is_file():
        raise CsvSummaryError(f"Input path is not a file: {file_path}")
    if path.suffix.lower() != ".csv":
        raise CsvSummaryError(f"Input file must have a .csv extension: {file_path}")
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            handle.read(1)
    except OSError as exc:
        raise CsvSummaryError(f"Input file is not readable: {file_path}") from exc
    except UnicodeDecodeError as exc:
        raise CsvSummaryError(
            f"Input file is not valid UTF-8 text and cannot be read: {file_path}"
        ) from exc
    return path


def sniff_csv_dialect(handle: TextIO) -> csv.Dialect:
    """Detect the CSV dialect, falling back to Excel CSV defaults."""
    sample = handle.read(4096)
    handle.seek(0)
    try:
        return csv.Sniffer().sniff(sample)
    except csv.Error:
        return csv.excel


def summarise_csv(file_path: str) -> list[dict[str, Any]]:
    """Read a CSV file and return per-column statistical summaries.

    The file is streamed row-by-row. Exact medians for numeric columns require
    retaining numeric values for columns that remain numeric.
    """
    path = validate_csv_path(file_path)

    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            dialect = sniff_csv_dialect(handle)
            reader = csv.DictReader(handle, dialect=dialect)
            if not reader.fieldnames:
                raise CsvSummaryError("CSV file is empty or missing a header row.")

            headers = normalise_headers(reader.fieldnames)
            if not headers:
                raise CsvSummaryError("CSV file has no columns.")

            accumulators = [ColumnAccumulator(name=header) for header in headers]
            for row in reader:
                for index, accumulator in enumerate(accumulators):
                    # DictReader stores duplicate/missing header values by key; use
                    # fieldnames[index] to access the original parsed column key.
                    original_header = reader.fieldnames[index]
                    accumulator.add(row.get(original_header))

            return [accumulator.summary() for accumulator in accumulators]
    except csv.Error as exc:
        raise CsvSummaryError(f"Failed to parse CSV file: {exc}") from exc
    except OSError as exc:
        raise CsvSummaryError(f"Failed to read CSV file: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise CsvSummaryError("Failed to decode CSV file as UTF-8 text.") from exc


def normalise_headers(fieldnames: Iterable[str | None]) -> list[str]:
    """Return display-safe header names for possibly blank CSV headers."""
    headers: list[str] = []
    for index, fieldname in enumerate(fieldnames, start=1):
        clean_name = "" if fieldname is None else str(fieldname).strip()
        headers.append(clean_name or f"column_{index}")
    return headers


def format_number(value: float) -> str:
    """Format a numeric statistic compactly and consistently."""
    return f"{value:.10g}"


def format_top_values(values: Sequence[tuple[str, int]]) -> str:
    """Format top value counts for display."""
    if not values:
        return "None (no non-missing values)"
    return ", ".join(f"{value!r} ({count})" for value, count in values)


def format_summary(summaries: Sequence[dict[str, Any]]) -> str:
    """Render summaries as human-readable CLI output."""
    lines = ["CSV Statistical Summary", "======================="]
    for column in summaries:
        lines.extend(
            [
                "",
                f"Column: {column['name']}",
                f"  Type: {column['type']}",
                f"  Missing values: {column['missing_count']} of {column['total_count']}",
                f"  Top 5 values: {format_top_values(column['top_values'])}",
            ]
        )
        stats = column["numeric_stats"]
        if stats is not None:
            lines.extend(
                [
                    "  Numeric statistics:",
                    f"    min: {format_number(stats['min'])}",
                    f"    max: {format_number(stats['max'])}",
                    f"    mean: {format_number(stats['mean'])}",
                    f"    median: {format_number(stats['median'])}",
                ]
            )
        elif column["type"] == "all_missing":
            lines.append("  Numeric statistics: N/A (all values are missing)")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    """Create the command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Detect column types and compute statistical summaries for a CSV file."
    )
    parser.add_argument("csv_file", help="Path to the input CSV file")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point. Returns a process exit status code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        summaries = summarise_csv(args.csv_file)
    except CsvSummaryError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(format_summary(summaries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

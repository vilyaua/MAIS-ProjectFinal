"""CSV statistical summary functionality."""

from __future__ import annotations

import argparse
import csv
import statistics
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, TextIO


MISSING_MARKERS = {"", "na", "n/a", "null", "none"}
DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%m/%d/%Y",
    "%d/%m/%Y",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
)


class CsvSummaryError(Exception):
    """Base exception for user-facing CSV summary errors."""


class EmptyCsvError(CsvSummaryError):
    """Raised when a CSV file has no usable data."""


class CsvParsingError(CsvSummaryError):
    """Raised when a CSV file cannot be parsed consistently."""


@dataclass(frozen=True)
class NumericStats:
    """Statistics for a numeric column."""

    minimum: float
    maximum: float
    mean: float
    median: float


@dataclass(frozen=True)
class ColumnSummary:
    """Summary information for a single CSV column."""

    name: str
    data_type: str
    total_values: int
    missing_count: int
    missing_percentage: float
    top_values: list[tuple[str, int]]
    numeric_stats: NumericStats | None = None


@dataclass(frozen=True)
class CsvSummary:
    """Summary information for a CSV file."""

    path: Path
    row_count: int
    column_summaries: list[ColumnSummary]


def is_missing(value: str | None) -> bool:
    """Return whether a cell value should be treated as missing."""
    if value is None:
        return True
    return value.strip().lower() in MISSING_MARKERS


def parse_float(value: str) -> float:
    """Parse a floating point value, accepting thousands separators."""
    return float(value.strip().replace(",", ""))


def can_parse_date(value: str) -> bool:
    """Return whether a value can be interpreted as a date/datetime."""
    stripped = value.strip()
    if not stripped:
        return False
    try:
        datetime.fromisoformat(stripped)
        return True
    except ValueError:
        pass

    for date_format in DATE_FORMATS:
        try:
            datetime.strptime(stripped, date_format)
            return True
        except ValueError:
            continue
    return False


def infer_data_type(values: Iterable[str]) -> str:
    """Infer a column type from non-missing string values."""
    non_missing = [value for value in values if not is_missing(value)]
    if not non_missing:
        return "empty"

    numeric = True
    for value in non_missing:
        try:
            parse_float(value)
        except ValueError:
            numeric = False
            break
    if numeric:
        return "numeric"

    if all(can_parse_date(value) for value in non_missing):
        return "date"

    return "string"


def read_csv(path: Path) -> tuple[list[str], list[list[str]]]:
    """Read a CSV file and return headers and rows.

    The delimiter is inferred with ``csv.Sniffer`` when possible, falling back
    to comma-separated parsing. Rows with inconsistent field counts are treated
    as parsing errors so malformed files fail gracefully.
    """
    try:
        raw_text = path.read_text(encoding="utf-8-sig", newline="")
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"File not found: {path}") from exc
    except OSError as exc:
        raise CsvSummaryError(f"Unable to read file '{path}': {exc}") from exc

    if not raw_text.strip():
        raise EmptyCsvError("The file contains no data.")

    sample = raw_text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample)
    except csv.Error:
        dialect = csv.excel

    try:
        reader = csv.reader(raw_text.splitlines(), dialect=dialect, strict=True)
        rows = list(reader)
    except csv.Error as exc:
        raise CsvParsingError(f"CSV parsing error: {exc}") from exc

    rows = [row for row in rows if row and any(cell.strip() for cell in row)]
    if not rows:
        raise EmptyCsvError("The file contains no data.")

    headers = [header.strip() or f"Column {index}" for index, header in enumerate(rows[0], 1)]
    if not headers:
        raise EmptyCsvError("The file contains no data.")

    expected_columns = len(headers)
    data_rows = rows[1:]
    for row_number, row in enumerate(data_rows, start=2):
        if len(row) != expected_columns:
            raise CsvParsingError(
                "CSV parsing error: row "
                f"{row_number} has {len(row)} fields; expected {expected_columns}."
            )

    if not data_rows:
        raise EmptyCsvError("The file contains headers but no data rows.")

    return headers, data_rows


def summarize_csv(path: str | Path) -> CsvSummary:
    """Create a statistical summary for a CSV file."""
    file_path = Path(path)
    headers, rows = read_csv(file_path)
    column_summaries: list[ColumnSummary] = []

    for index, name in enumerate(headers):
        values = [row[index] for row in rows]
        missing_count = sum(1 for value in values if is_missing(value))
        non_missing_values = [value.strip() for value in values if not is_missing(value)]
        data_type = infer_data_type(values)
        numeric_stats = None

        if data_type == "numeric" and non_missing_values:
            numeric_values = [parse_float(value) for value in non_missing_values]
            numeric_stats = NumericStats(
                minimum=min(numeric_values),
                maximum=max(numeric_values),
                mean=statistics.fmean(numeric_values),
                median=statistics.median(numeric_values),
            )

        top_values = Counter(non_missing_values).most_common(5)
        total_values = len(values)
        missing_percentage = (missing_count / total_values * 100) if total_values else 0.0
        column_summaries.append(
            ColumnSummary(
                name=name,
                data_type=data_type,
                total_values=total_values,
                missing_count=missing_count,
                missing_percentage=missing_percentage,
                top_values=top_values,
                numeric_stats=numeric_stats,
            )
        )

    return CsvSummary(path=file_path, row_count=len(rows), column_summaries=column_summaries)


def format_number(value: float) -> str:
    """Format numbers compactly while preserving useful precision."""
    return f"{value:.10g}"


def format_top_values(top_values: list[tuple[str, int]]) -> str:
    """Format top value counts for display."""
    if not top_values:
        return "None"
    return ", ".join(f"{value!r} ({count})" for value, count in top_values)


def format_summary(summary: CsvSummary) -> str:
    """Render a CSV summary as a human-readable report."""
    lines = [
        "CSV Statistical Summary",
        f"File: {summary.path}",
        f"Rows: {summary.row_count}",
        f"Columns: {len(summary.column_summaries)}",
        "",
    ]

    for column in summary.column_summaries:
        lines.extend(
            [
                f"Column: {column.name}",
                f"  Type: {column.data_type}",
                "  Missing: "
                f"{column.missing_count}/{column.total_values} "
                f"({column.missing_percentage:.2f}%)",
                f"  Top 5 Values: {format_top_values(column.top_values)}",
            ]
        )
        if column.numeric_stats is not None:
            stats = column.numeric_stats
            lines.extend(
                [
                    f"  Min: {format_number(stats.minimum)}",
                    f"  Max: {format_number(stats.maximum)}",
                    f"  Mean: {format_number(stats.mean)}",
                    f"  Median: {format_number(stats.median)}",
                ]
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(description="Summarize statistics for a CSV file.")
    parser.add_argument("csv_file", help="Path to the CSV file to summarize")
    return parser


def main(argv: list[str] | None = None, output: TextIO | None = None) -> int:
    """Run the CSV summary command-line interface."""
    parser = build_parser()
    args = parser.parse_args(argv)
    stream = output if output is not None else sys.stdout

    try:
        summary = summarize_csv(args.csv_file)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except EmptyCsvError as exc:
        print(f"No data: {exc}", file=sys.stderr)
        return 1
    except CsvParsingError as exc:
        print(f"Parsing error: {exc}", file=sys.stderr)
        return 1
    except CsvSummaryError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(format_summary(summary), end="", file=stream)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

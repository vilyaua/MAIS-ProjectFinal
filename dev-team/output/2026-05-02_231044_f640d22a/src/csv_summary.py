"""CSV statistical summary CLI tool.

This module provides both a reusable summary API and a command-line
interface for inspecting CSV files. It intentionally uses only the Python
standard library so it can run in constrained environments without extra
runtime dependencies.
"""

from __future__ import annotations

import argparse
import csv
import statistics
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

MISSING_TOKENS = {"", "na", "n/a", "null", "none", "nan"}


class CSVSummaryError(Exception):
    """Raised when a CSV file cannot be summarized for a user-facing reason."""


@dataclass(frozen=True)
class NumericStats:
    """Statistical measures for a numeric column."""

    minimum: float
    maximum: float
    mean: float
    median: float


@dataclass(frozen=True)
class ColumnSummary:
    """Summary details for a single CSV column."""

    name: str
    data_type: str
    missing_count: int
    total_count: int
    top_values: list[tuple[str, int]]
    numeric_stats: NumericStats | None = None


@dataclass(frozen=True)
class CSVSummary:
    """Summary details for an entire CSV file."""

    file_path: Path
    row_count: int
    columns: list[ColumnSummary]


def is_missing(value: str | None) -> bool:
    """Return True when a CSV value should be treated as missing."""

    if value is None:
        return True
    return value.strip().lower() in MISSING_TOKENS


def parse_numeric(value: str) -> float | None:
    """Parse a string as a finite float, returning None when invalid."""

    try:
        number = float(value.strip())
    except (TypeError, ValueError):
        return None

    # Reject NaN and infinity for statistics because they make summaries noisy.
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def detect_column_type(non_missing_values: Sequence[str]) -> str:
    """Detect whether a column is numeric, categorical, string, or all missing."""

    if not non_missing_values:
        return "all_missing"

    numeric_values = [parse_numeric(value) for value in non_missing_values]
    if all(value is not None for value in numeric_values):
        return "numeric"

    unique_count = len({value.strip() for value in non_missing_values})
    value_count = len(non_missing_values)

    # A practical heuristic: repeated, low-cardinality text is categorical;
    # mostly unique text is better described as string/free text.
    if unique_count <= 20 or unique_count / value_count <= 0.5:
        return "categorical"
    return "string"


def _validate_path(file_path: Path) -> None:
    """Validate that the supplied path points to a readable CSV file."""

    if not file_path.exists():
        raise CSVSummaryError(f"File does not exist: {file_path}")
    if not file_path.is_file():
        raise CSVSummaryError(f"Path is not a file: {file_path}")
    if file_path.suffix.lower() != ".csv":
        raise CSVSummaryError(f"Input file must have a .csv extension: {file_path}")
    try:
        with file_path.open("r", encoding="utf-8", newline="") as handle:
            handle.read(1)
    except UnicodeDecodeError as exc:
        raise CSVSummaryError("File is not a valid UTF-8 text CSV file.") from exc
    except OSError as exc:
        raise CSVSummaryError(f"Could not read file: {exc}") from exc


def _read_csv(file_path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Read a CSV file and return headers plus row dictionaries."""

    try:
        with file_path.open("r", encoding="utf-8", newline="") as handle:
            sample = handle.read(4096)
            if not sample.strip():
                raise CSVSummaryError("CSV file has no data to process.")

            handle.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample)
            except csv.Error:
                dialect = csv.excel

            reader = csv.DictReader(handle, dialect=dialect)
            if not reader.fieldnames:
                raise CSVSummaryError("CSV file has no header row to process.")

            headers = [header.strip() if header else "" for header in reader.fieldnames]
            if any(not header for header in headers):
                raise CSVSummaryError("CSV header contains an empty column name.")
            if len(set(headers)) != len(headers):
                raise CSVSummaryError("CSV header contains duplicate column names.")

            rows: list[dict[str, str]] = []
            for row in reader:
                # csv.DictReader stores extra fields under key None. Treat that as
                # malformed CSV because row lengths are inconsistent with headers.
                if None in row:
                    raise CSVSummaryError(
                        "CSV file is malformed: a row has more values than headers."
                    )
                rows.append({header: row.get(header, "") for header in reader.fieldnames})
    except csv.Error as exc:
        raise CSVSummaryError(f"CSV parsing error: {exc}") from exc
    except OSError as exc:
        raise CSVSummaryError(f"Could not read file: {exc}") from exc

    if not rows:
        raise CSVSummaryError("CSV file has no data rows to process.")

    return headers, rows


def summarize_csv(path: str | Path) -> CSVSummary:
    """Create a statistical summary for a CSV file.

    Args:
        path: Path to the CSV file.

    Returns:
        A CSVSummary containing per-column type, missing-value, frequency,
        and numeric-statistical information.

    Raises:
        CSVSummaryError: If validation or parsing fails.
    """

    file_path = Path(path).expanduser()
    _validate_path(file_path)
    headers, rows = _read_csv(file_path)

    column_summaries: list[ColumnSummary] = []
    for header in headers:
        raw_values = [row.get(header, "") for row in rows]
        missing_count = sum(1 for value in raw_values if is_missing(value))
        non_missing_values = [value.strip() for value in raw_values if not is_missing(value)]
        data_type = detect_column_type(non_missing_values)
        counts = Counter(non_missing_values)
        top_values = counts.most_common(5)

        numeric_stats: NumericStats | None = None
        if data_type == "numeric":
            numeric_values = [parse_numeric(value) for value in non_missing_values]
            valid_numbers = [value for value in numeric_values if value is not None]
            if valid_numbers:
                numeric_stats = NumericStats(
                    minimum=min(valid_numbers),
                    maximum=max(valid_numbers),
                    mean=statistics.fmean(valid_numbers),
                    median=statistics.median(valid_numbers),
                )

        column_summaries.append(
            ColumnSummary(
                name=header,
                data_type=data_type,
                missing_count=missing_count,
                total_count=len(raw_values),
                top_values=top_values,
                numeric_stats=numeric_stats,
            )
        )

    return CSVSummary(
        file_path=file_path,
        row_count=len(rows),
        columns=column_summaries,
    )


def format_number(value: float) -> str:
    """Format a number compactly while preserving useful precision."""

    return f"{value:.6g}"


def format_top_values(top_values: Iterable[tuple[str, int]]) -> str:
    """Format top-frequency values for display."""

    formatted = [f"{value!r} ({count})" for value, count in top_values]
    return ", ".join(formatted) if formatted else "No non-missing values"


def format_report(summary: CSVSummary) -> str:
    """Format a CSVSummary as a user-friendly text report."""

    lines = [
        "CSV Statistical Summary",
        "=======================",
        f"File: {summary.file_path}",
        f"Rows: {summary.row_count}",
        f"Columns: {len(summary.columns)}",
        "",
    ]

    for column in summary.columns:
        lines.extend(
            [
                f"Column: {column.name}",
                f"  Type: {column.data_type}",
                f"  Missing Values: {column.missing_count} / {column.total_count}",
                f"  Top 5 Values: {format_top_values(column.top_values)}",
            ]
        )
        if column.numeric_stats is not None:
            stats = column.numeric_stats
            lines.extend(
                [
                    "  Numeric Summary:",
                    f"    Min: {format_number(stats.minimum)}",
                    f"    Max: {format_number(stats.maximum)}",
                    f"    Mean: {format_number(stats.mean)}",
                    f"    Median: {format_number(stats.median)}",
                ]
            )
        else:
            lines.append("  Numeric Summary: Not applicable")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""

    parser = argparse.ArgumentParser(
        description="Generate a statistical summary report for a CSV file."
    )
    parser.add_argument("csv_file", help="Path to the CSV file to summarize")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CSV summary CLI and return a process exit code."""

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        summary = summarize_csv(args.csv_file)
    except CSVSummaryError as exc:
        print(f"Error: {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - last-resort user safety net
        print(f"Error: An unexpected problem occurred: {exc}")
        return 1

    print(format_report(summary), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

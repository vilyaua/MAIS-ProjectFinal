"""CSV statistical summary generation utilities."""

from __future__ import annotations

import csv
import math
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean, median
from typing import Any, Iterable

MISSING_MARKERS = {"", "na", "n/a", "null", "none", "nan"}
DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%m/%d/%Y",
    "%d/%m/%Y",
    "%Y-%m-%d %H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
    "%m/%d/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M:%S",
)


class CSVSummaryError(Exception):
    """Base exception for CSV summary errors."""


class CSVFileNotFoundError(CSVSummaryError):
    """Raised when an input file path cannot be found."""


class InvalidCSVError(CSVSummaryError):
    """Raised when input cannot be parsed as a usable CSV file."""


@dataclass(frozen=True)
class ColumnSummary:
    """Summary information for one CSV column."""

    name: str
    data_type: str
    missing_count: int
    top_values: list[tuple[str, int]]
    numeric_stats: dict[str, float] | None = None
    non_missing_count: int = 0


@dataclass(frozen=True)
class CSVSummary:
    """Summary information for a CSV file."""

    path: str
    row_count: int
    columns: list[ColumnSummary]


def is_missing(value: str | None) -> bool:
    """Return True when a value should be treated as missing."""
    if value is None:
        return True
    return value.strip().lower() in MISSING_MARKERS


def parse_number(value: str) -> float | None:
    """Parse a finite numeric value, or return None when parsing fails."""
    try:
        parsed = float(value.strip().replace(",", ""))
    except (TypeError, ValueError):
        return None
    if not math.isfinite(parsed):
        return None
    return parsed


def parse_date(value: str) -> datetime | None:
    """Parse common date/datetime formats, or return None when parsing fails."""
    text = value.strip()
    if not text:
        return None

    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        pass

    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(text, date_format)
        except ValueError:
            continue
    return None


def detect_column_type(non_missing_values: list[str]) -> str:
    """Detect a column type from non-missing values."""
    if not non_missing_values:
        return "all_missing"

    numeric_count = sum(parse_number(value) is not None for value in non_missing_values)
    if numeric_count == len(non_missing_values):
        return "numeric"

    date_count = sum(parse_date(value) is not None for value in non_missing_values)
    if date_count == len(non_missing_values):
        return "date"

    if numeric_count > 0 or date_count > 0:
        return "mixed"

    return "categorical"


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Read CSV rows with validation and return headers and row dictionaries."""
    if not path.exists():
        raise CSVFileNotFoundError(f"File not found: {path}")
    if not path.is_file():
        raise InvalidCSVError(f"Path is not a file: {path}")

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
            sample = csv_file.read(4096)
            if sample == "":
                raise InvalidCSVError("CSV file is empty.")
            csv_file.seek(0)

            try:
                dialect = csv.Sniffer().sniff(sample)
            except csv.Error:
                dialect = csv.excel
            dialect.strict = True

            reader = csv.reader(csv_file, dialect)
            try:
                raw_header = next(reader)
            except StopIteration as exc:
                raise InvalidCSVError("CSV file is empty.") from exc

            headers = [header.strip() for header in raw_header]
            if not headers or all(header == "" for header in headers):
                raise InvalidCSVError("CSV file must contain a header row.")

            normalized_headers = make_unique_headers(headers)
            rows: list[dict[str, str]] = []
            expected_columns = len(normalized_headers)

            for line_number, row in enumerate(reader, start=2):
                if len(row) > expected_columns:
                    raise InvalidCSVError(
                        f"Row {line_number} has {len(row)} fields; "
                        f"expected at most {expected_columns}."
                    )
                padded = row + [""] * (expected_columns - len(row))
                rows.append(dict(zip(normalized_headers, padded, strict=True)))
    except UnicodeDecodeError as exc:
        raise InvalidCSVError("File is not valid UTF-8 text.") from exc
    except csv.Error as exc:
        raise InvalidCSVError(f"Could not parse CSV: {exc}") from exc
    except OSError as exc:
        raise InvalidCSVError(f"Could not read file: {exc}") from exc

    return normalized_headers, rows


def make_unique_headers(headers: Iterable[str]) -> list[str]:
    """Return non-empty, unique header names."""
    counts: dict[str, int] = {}
    unique_headers: list[str] = []

    for index, header in enumerate(headers, start=1):
        base_name = header.strip() or f"column_{index}"
        count = counts.get(base_name, 0) + 1
        counts[base_name] = count
        unique_headers.append(base_name if count == 1 else f"{base_name}_{count}")

    return unique_headers


def summarize_column(name: str, values: list[str]) -> ColumnSummary:
    """Build a summary for one column."""
    non_missing_values = [value.strip() for value in values if not is_missing(value)]
    missing_count = len(values) - len(non_missing_values)
    data_type = detect_column_type(non_missing_values)
    top_values = Counter(non_missing_values).most_common(5)

    numeric_stats: dict[str, float] | None = None
    if data_type == "numeric":
        numeric_values = [
            number
            for value in non_missing_values
            if (number := parse_number(value)) is not None
        ]
        if numeric_values:
            numeric_stats = {
                "min": min(numeric_values),
                "max": max(numeric_values),
                "mean": mean(numeric_values),
                "median": median(numeric_values),
            }

    return ColumnSummary(
        name=name,
        data_type=data_type,
        missing_count=missing_count,
        top_values=top_values,
        numeric_stats=numeric_stats,
        non_missing_count=len(non_missing_values),
    )


def summarize_csv(file_path: str | Path) -> CSVSummary:
    """Generate a statistical summary for a CSV file."""
    path = Path(file_path)
    headers, rows = read_csv(path)
    column_summaries = [
        summarize_column(header, [row.get(header, "") for row in rows])
        for header in headers
    ]
    return CSVSummary(path=str(path), row_count=len(rows), columns=column_summaries)


def format_number(value: float) -> str:
    """Format numeric output compactly and consistently."""
    if value.is_integer():
        return str(int(value))
    return f"{value:.6g}"


def format_top_values(top_values: list[tuple[str, int]]) -> str:
    """Format top value counts for display."""
    if not top_values:
        return "None (no non-missing values)"
    return ", ".join(f"{value!r} ({count})" for value, count in top_values)


def format_summary(summary: CSVSummary) -> str:
    """Format a CSV summary as human-readable text."""
    lines: list[str] = [
        f"CSV Summary: {summary.path}",
        f"Rows: {summary.row_count}",
        f"Columns: {len(summary.columns)}",
    ]

    for column in summary.columns:
        lines.extend(
            [
                "",
                f"Column: {column.name}",
                f"  Type: {column.data_type}",
                f"  Missing values: {column.missing_count}",
                f"  Non-missing values: {column.non_missing_count}",
                f"  Top 5 values: {format_top_values(column.top_values)}",
            ]
        )
        if column.numeric_stats is not None:
            lines.append("  Numeric statistics:")
            for stat_name in ("min", "max", "mean", "median"):
                lines.append(
                    f"    {stat_name}: "
                    f"{format_number(column.numeric_stats[stat_name])}"
                )
        elif column.data_type == "all_missing":
            lines.append("  Numeric statistics: Not available (all values missing)")
        else:
            lines.append("  Numeric statistics: Not applicable")

    return "\n".join(lines)


def summary_to_dict(summary: CSVSummary) -> dict[str, Any]:
    """Convert a summary into plain Python data for tests or integrations."""
    return {
        "path": summary.path,
        "row_count": summary.row_count,
        "columns": [
            {
                "name": column.name,
                "data_type": column.data_type,
                "missing_count": column.missing_count,
                "non_missing_count": column.non_missing_count,
                "top_values": column.top_values,
                "numeric_stats": column.numeric_stats,
            }
            for column in summary.columns
        ],
    }

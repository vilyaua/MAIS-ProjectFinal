"""CSV statistical summary functionality."""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median
from typing import Any, Iterable


MISSING_VALUES = {"", "na", "n/a", "nan", "null", "none"}
DATETIME_FORMATS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%m/%d/%Y",
    "%d/%m/%Y",
    "%Y-%m-%d %H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%d %H:%M:%S%z",
)


class CSVSummaryError(Exception):
    """User-facing error raised while reading or summarizing a CSV file."""


@dataclass(frozen=True)
class ColumnSummary:
    """Summary information for a single CSV column."""

    name: str
    data_type: str
    missing_count: int
    total_count: int
    statistics: dict[str, Any]
    top_values: list[tuple[str, int]]


@dataclass(frozen=True)
class CSVSummary:
    """Summary report for an entire CSV file."""

    path: Path
    row_count: int
    columns: list[ColumnSummary]
    no_data_message: str | None = None


def is_missing(value: str | None) -> bool:
    """Return True when a CSV cell should be treated as missing."""
    if value is None:
        return True
    return value.strip().lower() in MISSING_VALUES


def parse_float(value: str) -> float | None:
    """Parse a float value, returning None when parsing fails."""
    try:
        return float(value.strip())
    except (TypeError, ValueError):
        return None


def parse_datetime(value: str) -> datetime | None:
    """Parse common datetime representations, returning None when parsing fails."""
    text = value.strip()
    if not text:
        return None

    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        pass

    for date_format in DATETIME_FORMATS:
        try:
            return datetime.strptime(text, date_format)
        except ValueError:
            continue
    return None


def detect_type(values: Iterable[str]) -> str:
    """Detect a column type from non-missing values."""
    concrete_values = list(values)
    if not concrete_values:
        return "categorical"

    if all(parse_float(value) is not None for value in concrete_values):
        return "numeric"

    if all(parse_datetime(value) is not None for value in concrete_values):
        return "datetime"

    return "categorical"


def format_number(value: float) -> str:
    """Format numbers compactly while retaining useful precision."""
    return f"{value:.10g}"


def format_datetime(value: datetime) -> str:
    """Format datetimes consistently for reports."""
    return value.isoformat(sep=" ")


def datetime_to_timestamp(value: datetime) -> float:
    """Convert naive or aware datetime to a timestamp for calculations."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc).timestamp()
    return value.timestamp()


def timestamp_to_datetime(value: float, template: datetime) -> datetime:
    """Convert a timestamp back to datetime using the template's timezone style."""
    tzinfo = template.tzinfo or timezone.utc
    result = datetime.fromtimestamp(value, tz=tzinfo)
    if template.tzinfo is None:
        return result.replace(tzinfo=None)
    return result


def summarize_column(name: str, values: list[str | None]) -> ColumnSummary:
    """Build a summary for one column."""
    non_missing = [value.strip() for value in values if not is_missing(value)]
    missing_count = len(values) - len(non_missing)
    data_type = detect_type(non_missing)
    statistics: dict[str, Any] = {}
    top_values: list[tuple[str, int]] = []

    if data_type == "numeric" and non_missing:
        numbers = [parse_float(value) for value in non_missing]
        numeric_values = [value for value in numbers if value is not None]
        statistics = {
            "min": min(numeric_values),
            "max": max(numeric_values),
            "mean": mean(numeric_values),
            "median": median(numeric_values),
        }
    elif data_type == "datetime" and non_missing:
        datetimes = [parse_datetime(value) for value in non_missing]
        datetime_values = [value for value in datetimes if value is not None]
        timestamps = [datetime_to_timestamp(value) for value in datetime_values]
        statistics = {
            "min": min(datetime_values),
            "max": max(datetime_values),
            "mean": timestamp_to_datetime(mean(timestamps), datetime_values[0]),
            "median": timestamp_to_datetime(median(timestamps), datetime_values[0]),
        }
    else:
        top_values = Counter(non_missing).most_common(5)

    return ColumnSummary(
        name=name,
        data_type=data_type,
        missing_count=missing_count,
        total_count=len(values),
        statistics=statistics,
        top_values=top_values,
    )


def read_csv_rows(path: Path) -> tuple[list[str], list[list[str | None]]]:
    """Read a CSV file and return headers and row values."""
    if not path.exists():
        raise CSVSummaryError(f"File not found: {path}")
    if not path.is_file():
        raise CSVSummaryError(f"Path is not a file: {path}")
    if path.suffix.lower() != ".csv":
        raise CSVSummaryError(
            f"Input does not appear to be a CSV file (expected .csv): {path}"
        )

    try:
        if path.stat().st_size == 0:
            return [], []
        with path.open("r", newline="", encoding="utf-8-sig") as csv_file:
            sample = csv_file.read(4096)
            csv_file.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample) if sample else csv.excel
            except csv.Error:
                dialect = csv.excel
            reader = csv.reader(csv_file, dialect=dialect, strict=True)
            try:
                headers = next(reader)
            except StopIteration:
                return [], []

            headers = [header.strip() for header in headers]
            if not headers or all(header == "" for header in headers):
                return [], []
            if len(set(headers)) != len(headers):
                raise CSVSummaryError("Invalid CSV format: duplicate column names found.")

            rows: list[list[str | None]] = []
            for row_number, row in enumerate(reader, start=2):
                if len(row) > len(headers):
                    raise CSVSummaryError(
                        "Invalid CSV format: row "
                        f"{row_number} has too many fields ({len(row)} > {len(headers)})."
                    )
                if len(row) < len(headers):
                    row = row + [None] * (len(headers) - len(row))
                rows.append(row)
            return headers, rows
    except UnicodeDecodeError as exc:
        raise CSVSummaryError(
            "Unable to read file as UTF-8 text. Please provide a valid CSV file."
        ) from exc
    except csv.Error as exc:
        raise CSVSummaryError(f"Invalid CSV format: {exc}") from exc
    except OSError as exc:
        raise CSVSummaryError(f"Unable to read file: {exc}") from exc


def summarize_csv(path: str | Path) -> CSVSummary:
    """Read and summarize a CSV file."""
    csv_path = Path(path)
    headers, rows = read_csv_rows(csv_path)
    if not headers:
        return CSVSummary(
            path=csv_path,
            row_count=0,
            columns=[],
            no_data_message="No data to summarize: the CSV file is empty or has no headers.",
        )
    if not rows:
        return CSVSummary(
            path=csv_path,
            row_count=0,
            columns=[],
            no_data_message="No data rows to summarize.",
        )

    columns = []
    for index, header in enumerate(headers):
        values = [row[index] for row in rows]
        columns.append(summarize_column(header, values))

    return CSVSummary(path=csv_path, row_count=len(rows), columns=columns)


def render_summary(summary: CSVSummary) -> str:
    """Render a CSV summary as a readable console report."""
    lines = [
        "CSV Statistical Summary",
        "=======================",
        f"File: {summary.path}",
        f"Rows: {summary.row_count}",
        f"Columns: {len(summary.columns)}",
    ]

    if summary.no_data_message is not None:
        lines.extend(["", summary.no_data_message])
        return "\n".join(lines)

    for column in summary.columns:
        lines.extend(
            [
                "",
                f"Column: {column.name}",
                "-" * (8 + len(column.name)),
                f"Type: {column.data_type}",
                f"Missing values: {column.missing_count} of {column.total_count}",
            ]
        )

        if column.statistics:
            lines.append("Statistics:")
            for key in ("min", "max", "mean", "median"):
                value = column.statistics[key]
                if isinstance(value, float):
                    rendered_value = format_number(value)
                elif isinstance(value, datetime):
                    rendered_value = format_datetime(value)
                else:
                    rendered_value = str(value)
                lines.append(f"  {key}: {rendered_value}")

        if column.top_values:
            lines.append("Top values:")
            for value, count in column.top_values:
                lines.append(f"  {value}: {count}")

    return "\n".join(lines)

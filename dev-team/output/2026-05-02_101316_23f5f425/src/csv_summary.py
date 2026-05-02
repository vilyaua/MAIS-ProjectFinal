"""CSV statistical summary functionality."""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean, median
from typing import Any, Iterable

MISSING_VALUES = {"", "na", "n/a", "null", "none", "nan"}
DATETIME_FORMATS = (
    "%Y-%m-%d",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%m/%d/%Y",
    "%d/%m/%Y",
    "%m/%d/%y",
    "%d/%m/%y",
    "%Y/%m/%d",
    "%b %d %Y",
    "%B %d %Y",
)


class CsvSummaryError(Exception):
    """Raised when a CSV file cannot be summarized."""


@dataclass(frozen=True)
class ColumnSummary:
    """Summary details for a CSV column."""

    name: str
    column_type: str
    missing_count: int
    total_count: int
    numeric_stats: dict[str, float] | None = None
    top_values: list[tuple[str, int]] | None = None


@dataclass(frozen=True)
class CsvSummary:
    """Summary details for a CSV file."""

    path: Path
    row_count: int
    columns: list[ColumnSummary]
    message: str | None = None


def is_missing(value: Any) -> bool:
    """Return True when a CSV cell should be counted as missing."""
    if value is None:
        return True
    return str(value).strip().lower() in MISSING_VALUES


def parse_float(value: str) -> float:
    """Parse a numeric CSV value, allowing thousands separators."""
    return float(value.strip().replace(",", ""))


def can_parse_datetime(value: str) -> bool:
    """Return True if value matches a common date/datetime format."""
    candidate = value.strip()
    for fmt in DATETIME_FORMATS:
        try:
            datetime.strptime(candidate, fmt)
            return True
        except ValueError:
            continue
    try:
        datetime.fromisoformat(candidate.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def detect_column_type(non_missing_values: list[str]) -> str:
    """Infer a simple semantic column type from non-missing values."""
    if not non_missing_values:
        return "unknown"

    if all(_is_numeric(value) for value in non_missing_values):
        return "numeric"

    if all(can_parse_datetime(value) for value in non_missing_values):
        return "datetime"

    unique_count = len(set(non_missing_values))
    value_count = len(non_missing_values)
    average_length = sum(len(value) for value in non_missing_values) / value_count

    if unique_count <= 20 or unique_count / value_count <= 0.5:
        return "categorical"
    if average_length > 30:
        return "text"
    return "categorical"


def analyze_csv(file_path: str | Path) -> CsvSummary:
    """Analyze a CSV file and return column-level summaries.

    Raises:
        CsvSummaryError: if the input path is invalid or parsing fails.
    """
    path = Path(file_path)
    _validate_path(path)

    try:
        if path.stat().st_size == 0:
            return CsvSummary(path=path, row_count=0, columns=[], message="CSV file is empty.")
    except OSError as exc:
        raise CsvSummaryError(f"Unable to read file metadata: {exc}") from exc

    try:
        with path.open("r", newline="", encoding="utf-8-sig") as csv_file:
            sample = csv_file.read(4096)
            csv_file.seek(0)
            dialect = _sniff_dialect(sample)
            reader = csv.DictReader(csv_file, dialect=dialect)

            if not reader.fieldnames:
                return CsvSummary(
                    path=path,
                    row_count=0,
                    columns=[],
                    message="CSV file does not contain a header row.",
                )

            fieldnames = _clean_fieldnames(reader.fieldnames)
            _validate_fieldnames(fieldnames)
            reader.fieldnames = fieldnames

            rows = []
            for line_number, row in enumerate(reader, start=2):
                if None in row:
                    raise CsvSummaryError(
                        "CSV parsing error on line "
                        f"{line_number}: row has more fields than the header."
                    )
                rows.append(row)
    except UnicodeDecodeError as exc:
        raise CsvSummaryError(
            "Unable to decode file as UTF-8 text. Please provide a valid CSV file."
        ) from exc
    except csv.Error as exc:
        raise CsvSummaryError(f"CSV parsing error: {exc}") from exc
    except OSError as exc:
        raise CsvSummaryError(f"Unable to read file: {exc}") from exc

    if not rows:
        columns = [
            ColumnSummary(
                name=fieldname,
                column_type="unknown",
                missing_count=0,
                total_count=0,
            )
            for fieldname in fieldnames
        ]
        return CsvSummary(
            path=path,
            row_count=0,
            columns=columns,
            message="CSV file contains a header but no data rows.",
        )

    return CsvSummary(
        path=path,
        row_count=len(rows),
        columns=[_summarize_column(fieldname, rows) for fieldname in fieldnames],
    )


def format_summary(summary: CsvSummary) -> str:
    """Format a CSV summary as a human-readable report."""
    lines = [f"CSV Summary Report: {summary.path}", f"Rows: {summary.row_count}"]
    if summary.columns:
        lines.append(f"Columns: {len(summary.columns)}")
    if summary.message:
        lines.append(f"Note: {summary.message}")
    if not summary.columns:
        return "\n".join(lines)

    for column in summary.columns:
        lines.extend(
            [
                "",
                f"Column: {column.name}",
                f"  Type: {column.column_type}",
                f"  Missing values: {column.missing_count}",
            ]
        )
        if column.numeric_stats:
            lines.extend(
                [
                    f"  Min: {_format_number(column.numeric_stats['min'])}",
                    f"  Max: {_format_number(column.numeric_stats['max'])}",
                    f"  Mean: {_format_number(column.numeric_stats['mean'])}",
                    f"  Median: {_format_number(column.numeric_stats['median'])}",
                ]
            )
        if column.top_values is not None:
            lines.append("  Top values:")
            if column.top_values:
                for value, count in column.top_values:
                    lines.append(f"    {value}: {count}")
            else:
                lines.append("    (none)")

    return "\n".join(lines)


def _summarize_column(fieldname: str, rows: list[dict[str, str]]) -> ColumnSummary:
    values = [row.get(fieldname, "") for row in rows]
    missing_count = sum(1 for value in values if is_missing(value))
    non_missing_values = [str(value).strip() for value in values if not is_missing(value)]
    column_type = detect_column_type(non_missing_values)

    numeric_stats: dict[str, float] | None = None
    top_values: list[tuple[str, int]] | None = None

    if column_type == "numeric":
        numbers = [parse_float(value) for value in non_missing_values]
        numeric_stats = {
            "min": min(numbers),
            "max": max(numbers),
            "mean": mean(numbers),
            "median": median(numbers),
        }
    elif column_type in {"categorical", "text"}:
        top_values = Counter(non_missing_values).most_common(5)

    return ColumnSummary(
        name=fieldname,
        column_type=column_type,
        missing_count=missing_count,
        total_count=len(values),
        numeric_stats=numeric_stats,
        top_values=top_values,
    )


def _validate_path(path: Path) -> None:
    if not str(path):
        raise CsvSummaryError("Please provide a CSV file path.")
    if not path.exists():
        raise CsvSummaryError(f"File not found: {path}")
    if not path.is_file():
        raise CsvSummaryError(f"Path is not a file: {path}")
    if path.suffix.lower() != ".csv":
        raise CsvSummaryError(
            f"Input file must have a .csv extension; received: {path.suffix or '(none)'}"
        )


def _sniff_dialect(sample: str) -> csv.Dialect:
    if not sample.strip():
        return csv.excel
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        return csv.excel


def _clean_fieldnames(fieldnames: Iterable[str | None]) -> list[str]:
    return ["" if fieldname is None else str(fieldname).strip() for fieldname in fieldnames]


def _validate_fieldnames(fieldnames: list[str]) -> None:
    if not any(fieldnames):
        raise CsvSummaryError("CSV header row is empty or invalid.")
    duplicates = [name for name, count in Counter(fieldnames).items() if name and count > 1]
    if duplicates:
        raise CsvSummaryError(
            "CSV header row contains duplicate column names: " + ", ".join(duplicates)
        )


def _is_numeric(value: str) -> bool:
    try:
        parse_float(value)
    except ValueError:
        return False
    return True


def _format_number(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return f"{value:.6g}"

"""CSV statistical summary utilities."""

from __future__ import annotations

import csv
import statistics
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


MISSING_TOKENS = {"", "na", "n/a", "null", "none", "nan"}


class CSVSummaryError(Exception):
    """Raised when a CSV file cannot be summarized."""


@dataclass(frozen=True)
class ColumnSummary:
    """Summary information for one CSV column."""

    name: str
    data_type: str
    total_rows: int
    missing_count: int
    min_value: float | None
    max_value: float | None
    mean_value: float | None
    median_value: float | None
    top_values: list[tuple[str, int]]
    numeric_count: int
    non_numeric_count: int


@dataclass(frozen=True)
class CSVSummary:
    """Summary information for a CSV file."""

    path: Path
    total_rows: int
    columns: list[ColumnSummary]


def is_missing(value: Any) -> bool:
    """Return True when a cell value should be treated as missing."""

    if value is None:
        return True
    return str(value).strip().lower() in MISSING_TOKENS


def parse_float(value: str) -> float | None:
    """Parse a value as float, returning None when parsing is not possible."""

    try:
        return float(value.strip())
    except (AttributeError, ValueError):
        return None


def _format_number(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.6g}"


def _infer_type(numeric_count: int, non_numeric_count: int) -> str:
    if numeric_count == 0 and non_numeric_count == 0:
        return "empty"
    if numeric_count > 0 and non_numeric_count == 0:
        return "numeric"
    if numeric_count == 0:
        return "categorical"
    return "mixed"


def _validate_headers(headers: list[str] | None) -> list[str]:
    if not headers:
        raise CSVSummaryError("CSV file does not contain a header row.")

    cleaned_headers = [header.strip() if header is not None else "" for header in headers]
    if any(not header for header in cleaned_headers):
        raise CSVSummaryError("CSV header row contains an empty column name.")

    duplicates = [
        header
        for header, count in Counter(cleaned_headers).items()
        if count > 1
    ]
    if duplicates:
        duplicate_list = ", ".join(sorted(duplicates))
        raise CSVSummaryError(f"CSV header row contains duplicate columns: {duplicate_list}.")

    return cleaned_headers


def validate_csv_path(file_path: str | Path) -> Path:
    """Validate the input file path and return it as a Path."""

    path = Path(file_path)
    if not path.exists():
        raise CSVSummaryError(f"File not found: {path}")
    if not path.is_file():
        raise CSVSummaryError(f"Path is not a file: {path}")
    return path


def read_csv_rows(file_path: str | Path) -> tuple[Path, list[str], list[dict[str, str | None]]]:
    """Read CSV rows after validating the file and its structure."""

    path = validate_csv_path(file_path)
    try:
        with path.open("r", newline="", encoding="utf-8-sig") as csv_file:
            try:
                sample = csv_file.read(4096)
            except UnicodeDecodeError as exc:
                raise CSVSummaryError(
                    f"File is not readable as UTF-8 text: {path}"
                ) from exc
            csv_file.seek(0)

            if not sample.strip():
                raise CSVSummaryError("CSV file is empty.")

            if "," in sample:
                try:
                    dialect = csv.Sniffer().sniff(sample)
                except csv.Error:
                    dialect = csv.excel
            else:
                dialect = csv.excel
            reader = csv.DictReader(
                csv_file, dialect=dialect, restkey="__extra_fields__"
            )
            headers = _validate_headers(reader.fieldnames)

            rows: list[dict[str, str | None]] = []
            for line_number, row in enumerate(reader, start=2):
                if "__extra_fields__" in row:
                    raise CSVSummaryError(
                        f"Malformed CSV structure at line {line_number}: "
                        "too many fields."
                    )
                normalized_row = {header: row.get(header) for header in headers}
                rows.append(normalized_row)
    except OSError as exc:
        raise CSVSummaryError(f"Unable to read file {path}: {exc}") from exc
    except csv.Error as exc:
        raise CSVSummaryError(f"Invalid CSV format in {path}: {exc}") from exc

    return path, headers, rows


def summarize_values(name: str, values: Iterable[str | None]) -> ColumnSummary:
    """Build a statistical summary for one column."""

    value_list = list(values)
    missing_count = 0
    numeric_values: list[float] = []
    non_numeric_count = 0
    frequencies: Counter[str] = Counter()

    for raw_value in value_list:
        if is_missing(raw_value):
            missing_count += 1
            continue

        normalized_value = str(raw_value).strip()
        frequencies[normalized_value] += 1
        numeric_value = parse_float(normalized_value)
        if numeric_value is None:
            non_numeric_count += 1
        else:
            numeric_values.append(numeric_value)

    data_type = _infer_type(len(numeric_values), non_numeric_count)
    if data_type == "numeric":
        min_value = min(numeric_values)
        max_value = max(numeric_values)
        mean_value = statistics.fmean(numeric_values)
        median_value = statistics.median(numeric_values)
    else:
        min_value = None
        max_value = None
        mean_value = None
        median_value = None

    top_values = sorted(
        frequencies.items(),
        key=lambda item: (-item[1], item[0]),
    )[:5]

    return ColumnSummary(
        name=name,
        data_type=data_type,
        total_rows=len(value_list),
        missing_count=missing_count,
        min_value=min_value,
        max_value=max_value,
        mean_value=mean_value,
        median_value=median_value,
        top_values=top_values,
        numeric_count=len(numeric_values),
        non_numeric_count=non_numeric_count,
    )


def summarize_csv(file_path: str | Path) -> CSVSummary:
    """Read and summarize a CSV file."""

    path, headers, rows = read_csv_rows(file_path)
    columns = [
        summarize_values(header, (row.get(header) for row in rows))
        for header in headers
    ]
    return CSVSummary(path=path, total_rows=len(rows), columns=columns)


def format_summary(summary: CSVSummary) -> str:
    """Format a CSV summary as a CLI-friendly textual report."""

    lines = [
        "CSV Statistical Summary",
        "=======================",
        f"File: {summary.path}",
        f"Rows: {summary.total_rows}",
        f"Columns: {len(summary.columns)}",
        "",
    ]

    for column in summary.columns:
        lines.extend(
            [
                f"Column: {column.name}",
                "-" * (8 + len(column.name)),
                f"Type: {column.data_type}",
                f"Missing values: {column.missing_count}",
            ]
        )

        if column.data_type == "mixed":
            lines.append(
                "Type note: mixed numeric and non-numeric values "
                f"({column.numeric_count} numeric, "
                f"{column.non_numeric_count} non-numeric)."
            )

        if column.data_type == "numeric":
            lines.extend(
                [
                    f"Minimum: {_format_number(column.min_value)}",
                    f"Maximum: {_format_number(column.max_value)}",
                    f"Mean: {_format_number(column.mean_value)}",
                    f"Median: {_format_number(column.median_value)}",
                ]
            )
        else:
            lines.append("Minimum: N/A")
            lines.append("Maximum: N/A")
            lines.append("Mean: N/A")
            lines.append("Median: N/A")

        lines.append("Top 5 values:")
        if column.top_values:
            for value, count in column.top_values:
                lines.append(f"  {value}: {count}")
        else:
            lines.append("  N/A")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"

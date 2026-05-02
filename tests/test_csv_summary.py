"""Tests for the CSV statistical summary CLI tool."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.csv_summary import (
    CSVFileNotFoundError,
    InvalidCSVError,
    format_summary,
    summarize_csv,
    summary_to_dict,
)
from src.main import main


def write_csv(tmp_path: Path, content: str, filename: str = "data.csv") -> Path:
    """Write test CSV content and return its path."""
    path = tmp_path / filename
    path.write_text(content, encoding="utf-8")
    return path


def test_valid_csv_summary_detects_types_stats_missing_and_top_values(
    tmp_path: Path,
) -> None:
    path = write_csv(
        tmp_path,
        "name,age,joined,city\n"
        "Alice,30,2024-01-01,London\n"
        "Bob,40,2024-01-02,Paris\n"
        "Alice,,2024-01-03,London\n"
        "Cara,20,2024-01-04,London\n",
    )

    summary = summarize_csv(path)
    result = summary_to_dict(summary)
    columns = {column["name"]: column for column in result["columns"]}

    assert result["row_count"] == 4
    assert columns["name"]["data_type"] == "categorical"
    assert columns["age"]["data_type"] == "numeric"
    assert columns["joined"]["data_type"] == "date"
    assert columns["city"]["missing_count"] == 0
    assert columns["age"]["missing_count"] == 1
    assert columns["age"]["numeric_stats"] == {
        "min": 20.0,
        "max": 40.0,
        "mean": 30.0,
        "median": 30.0,
    }
    assert columns["city"]["top_values"][0] == ("London", 3)

    rendered = format_summary(summary)
    assert "Column: age" in rendered
    assert "mean: 30" in rendered
    assert "Top 5 values: 'London' (3), 'Paris' (1)" in rendered


def test_invalid_file_path_raises_and_cli_reports_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    missing_path = tmp_path / "missing.csv"

    with pytest.raises(CSVFileNotFoundError):
        summarize_csv(missing_path)

    exit_code = main([str(missing_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "File not found" in captured.err


def test_empty_file_is_handled_gracefully(tmp_path: Path) -> None:
    path = write_csv(tmp_path, "")

    with pytest.raises(InvalidCSVError, match="empty"):
        summarize_csv(path)


def test_columns_with_all_missing_values_are_reported(tmp_path: Path) -> None:
    path = write_csv(
        tmp_path,
        "id,empty_col,mostly_missing\n"
        "1,,\n"
        "2,NA,\n"
        "3,null,value\n",
    )

    summary = summarize_csv(path)
    columns = {column.name: column for column in summary.columns}

    assert columns["empty_col"].data_type == "all_missing"
    assert columns["empty_col"].missing_count == 3
    assert columns["empty_col"].top_values == []
    assert columns["mostly_missing"].data_type == "categorical"
    assert columns["mostly_missing"].missing_count == 2
    assert "all values missing" in format_summary(summary)


def test_mixed_or_ambiguous_data_types_are_classified_mixed(
    tmp_path: Path,
) -> None:
    path = write_csv(
        tmp_path,
        "value\n"
        "10\n"
        "twenty\n"
        "2024-01-01\n",
    )

    summary = summarize_csv(path)
    column = summary.columns[0]

    assert column.data_type == "mixed"
    assert column.numeric_stats is None
    assert column.top_values == [("10", 1), ("twenty", 1), ("2024-01-01", 1)]


def test_invalid_csv_with_too_many_fields_reports_error(tmp_path: Path) -> None:
    path = write_csv(tmp_path, "a,b\n1,2,3\n")

    with pytest.raises(InvalidCSVError, match="Row 2"):
        summarize_csv(path)

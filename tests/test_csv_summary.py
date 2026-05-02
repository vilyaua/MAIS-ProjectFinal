"""Tests for the CSV statistical summary tool."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.csv_summary import (
    CsvParsingError,
    EmptyCsvError,
    format_summary,
    infer_data_type,
    main,
    summarize_csv,
)


def write_csv(tmp_path: Path, content: str, name: str = "data.csv") -> Path:
    """Write CSV test content and return the file path."""
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_mixed_csv_summary_contains_types_stats_missing_and_top_values(tmp_path: Path) -> None:
    csv_path = write_csv(
        tmp_path,
        (
            "name,age,joined,city\n"
            "Alice,30,2023-01-01,London\n"
            "Bob,40,2023-01-02,Paris\n"
            "Alice,,2023-01-03,London\n"
            "Cara,20,2023-01-04,London\n"
        ),
    )

    summary = summarize_csv(csv_path)
    report = format_summary(summary)

    assert summary.row_count == 4
    columns = {column.name: column for column in summary.column_summaries}
    assert columns["name"].data_type == "string"
    assert columns["age"].data_type == "numeric"
    assert columns["joined"].data_type == "date"
    assert columns["age"].missing_count == 1
    assert columns["age"].numeric_stats is not None
    assert columns["age"].numeric_stats.minimum == 20
    assert columns["age"].numeric_stats.maximum == 40
    assert columns["age"].numeric_stats.mean == 30
    assert columns["age"].numeric_stats.median == 30
    assert columns["city"].top_values[0] == ("London", 3)
    assert "Column: age" in report
    assert "Missing: 1/4 (25.00%)" in report
    assert "Top 5 Values: 'London' (3), 'Paris' (1)" in report


def test_semicolon_delimiter_and_quoted_values_are_parsed(tmp_path: Path) -> None:
    csv_path = write_csv(
        tmp_path,
        'product;price;note\n"Widget; Large";10.5;"contains delimiter"\nGadget;12.5;plain\n',
        "semicolon.csv",
    )

    summary = summarize_csv(csv_path)
    columns = {column.name: column for column in summary.column_summaries}

    assert columns["product"].top_values[0] == ("Widget; Large", 1)
    assert columns["price"].data_type == "numeric"
    assert columns["price"].numeric_stats is not None
    assert columns["price"].numeric_stats.mean == pytest.approx(11.5)


def test_missing_values_markers_are_counted(tmp_path: Path) -> None:
    csv_path = write_csv(tmp_path, "a,b\n,NA\nnull,value\nNone,n/a\n")

    summary = summarize_csv(csv_path)
    columns = {column.name: column for column in summary.column_summaries}

    assert columns["a"].missing_count == 3
    assert columns["b"].missing_count == 2
    assert columns["b"].top_values == [("value", 1)]


def test_top_five_values_are_reported_in_frequency_order(tmp_path: Path) -> None:
    csv_path = write_csv(tmp_path, "color\nred\nblue\nred\ngreen\nblue\nred\nyellow\nblack\nwhite\n")

    summary = summarize_csv(csv_path)
    color = summary.column_summaries[0]

    assert color.top_values == [
        ("red", 3),
        ("blue", 2),
        ("green", 1),
        ("yellow", 1),
        ("black", 1),
    ]


def test_infer_data_type_empty_numeric_date_and_string() -> None:
    assert infer_data_type(["", "NA"]) == "empty"
    assert infer_data_type(["1", "2.5", ""]) == "numeric"
    assert infer_data_type(["2023-01-01", "2023-02-01"]) == "date"
    assert infer_data_type(["abc", "2023-02-01"]) == "string"


def test_non_existent_file_returns_clear_error(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["does-not-exist.csv"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "File not found" in captured.err


def test_improperly_formatted_csv_reports_parsing_error(tmp_path: Path) -> None:
    csv_path = write_csv(tmp_path, "a,b\n1,2\n3\n")

    with pytest.raises(CsvParsingError, match="row 3 has 1 fields; expected 2"):
        summarize_csv(csv_path)


def test_cli_reports_parsing_error_without_crashing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    csv_path = write_csv(tmp_path, 'a,b\n"unterminated,2\n')

    exit_code = main([str(csv_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Parsing error" in captured.err


def test_empty_file_reports_no_data(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    csv_path = write_csv(tmp_path, "   \n", "empty.csv")

    with pytest.raises(EmptyCsvError):
        summarize_csv(csv_path)

    exit_code = main([str(csv_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "No data" in captured.err


def test_cli_prints_summary(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    csv_path = write_csv(tmp_path, "value\n1\n2\n3\n")

    exit_code = main([str(csv_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "CSV Statistical Summary" in captured.out
    assert "Mean: 2" in captured.out
    assert captured.err == ""

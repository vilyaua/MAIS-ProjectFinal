from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from csv_summary import CsvSummaryError, analyze_csv, format_summary
from main import main


def test_analyze_valid_csv_with_various_types(tmp_path: Path) -> None:
    csv_path = tmp_path / "people.csv"
    csv_path.write_text(
        "name,age,city,signup_date,bio\n"
        "Alice,30,NY,2024-01-01,Enjoys long distance running\n"
        "Bob,25,LA,2024-02-03,Writes software documentation\n"
        "Alice,35,NY,2024-03-05,Enjoys long distance running\n"
        "Cara,,SF,,Short note\n",
        encoding="utf-8",
    )

    summary = analyze_csv(csv_path)
    by_name = {column.name: column for column in summary.columns}

    assert summary.row_count == 4
    assert by_name["age"].column_type == "numeric"
    assert by_name["age"].missing_count == 1
    assert by_name["age"].numeric_stats == {
        "min": 25.0,
        "max": 35.0,
        "mean": 30.0,
        "median": 30.0,
    }
    assert by_name["signup_date"].column_type == "datetime"
    assert by_name["city"].column_type == "categorical"
    assert by_name["city"].top_values[:2] == [("NY", 2), ("LA", 1)]


def test_format_summary_includes_required_statistics(tmp_path: Path) -> None:
    csv_path = tmp_path / "sales.csv"
    csv_path.write_text(
        "category,amount\nA,10\nB,20\nA,30\nC,40\nA,\n",
        encoding="utf-8",
    )

    output = format_summary(analyze_csv(csv_path))

    assert "Column: amount" in output
    assert "Type: numeric" in output
    assert "Missing values: 1" in output
    assert "Min: 10" in output
    assert "Max: 40" in output
    assert "Mean: 25" in output
    assert "Median: 25" in output
    assert "Column: category" in output
    assert "A: 3" in output


def test_top_values_limited_to_five(tmp_path: Path) -> None:
    csv_path = tmp_path / "colors.csv"
    csv_path.write_text(
        "color\nred\nred\nblue\nblue\ngreen\nyellow\nblack\nwhite\n",
        encoding="utf-8",
    )

    color_summary = analyze_csv(csv_path).columns[0]

    assert color_summary.top_values is not None
    assert len(color_summary.top_values) == 5
    assert color_summary.top_values[0] == ("red", 2)


def test_invalid_file_path_raises_clear_error() -> None:
    with pytest.raises(CsvSummaryError, match="File not found"):
        analyze_csv("does-not-exist.csv")


def test_non_csv_extension_raises_clear_error(tmp_path: Path) -> None:
    text_path = tmp_path / "input.txt"
    text_path.write_text("not,csv\n", encoding="utf-8")

    with pytest.raises(CsvSummaryError, match=".csv extension"):
        analyze_csv(text_path)


def test_empty_csv_file_is_handled(tmp_path: Path) -> None:
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("", encoding="utf-8")

    summary = analyze_csv(csv_path)
    output = format_summary(summary)

    assert summary.row_count == 0
    assert summary.columns == []
    assert "CSV file is empty" in output


def test_header_only_csv_is_handled(tmp_path: Path) -> None:
    csv_path = tmp_path / "header_only.csv"
    csv_path.write_text("a,b,c\n", encoding="utf-8")

    summary = analyze_csv(csv_path)
    output = format_summary(summary)

    assert summary.row_count == 0
    assert [column.name for column in summary.columns] == ["a", "b", "c"]
    assert "header but no data rows" in output


def test_cli_outputs_report_and_returns_zero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text("x,y\n1,A\n2,A\n3,B\n", encoding="utf-8")

    exit_code = main([str(csv_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "CSV Summary Report" in captured.out
    assert "Column: x" in captured.out
    assert captured.err == ""


def test_cli_error_returns_nonzero(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main([str(tmp_path / "missing.csv")])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Error: File not found" in captured.err

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from csv_summary import CSVSummaryError, render_summary, summarize_csv
from main import main


def write_csv(tmp_path: Path, content: str, name: str = "data.csv") -> Path:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_numeric_summary_values(tmp_path: Path) -> None:
    path = write_csv(tmp_path, "age,score\n10,1.5\n20,2.5\n30,3.5\n")

    summary = summarize_csv(path)

    assert summary.row_count == 3
    age = summary.columns[0]
    assert age.name == "age"
    assert age.data_type == "numeric"
    assert age.statistics["min"] == 10.0
    assert age.statistics["max"] == 30.0
    assert age.statistics["mean"] == 20.0
    assert age.statistics["median"] == 20.0


def test_missing_values_are_counted(tmp_path: Path) -> None:
    path = write_csv(tmp_path, "name,age\nAlice,10\n,20\nNA,\nBob,null\n")

    summary = summarize_csv(path)

    name = summary.columns[0]
    age = summary.columns[1]
    assert name.missing_count == 2
    assert age.missing_count == 2
    assert age.data_type == "numeric"


def test_categorical_top_five_values(tmp_path: Path) -> None:
    path = write_csv(
        tmp_path,
        "color\nred\nblue\nred\ngreen\nblue\nred\nyellow\nblack\nwhite\n",
    )

    summary = summarize_csv(path)
    color = summary.columns[0]

    assert color.data_type == "categorical"
    assert color.top_values[:3] == [("red", 3), ("blue", 2), ("green", 1)]
    assert len(color.top_values) == 5


def test_datetime_detection_and_statistics(tmp_path: Path) -> None:
    path = write_csv(
        tmp_path,
        "created_at\n2024-01-01\n2024-01-03\n2024-01-05\n",
    )

    summary = summarize_csv(path)
    column = summary.columns[0]
    report = render_summary(summary)

    assert column.data_type == "datetime"
    assert "min: 2024-01-01" in report
    assert "max: 2024-01-05" in report
    assert "median: 2024-01-03" in report


def test_mixed_data_types_are_detected(tmp_path: Path) -> None:
    path = write_csv(
        tmp_path,
        "amount,category,date,mixed\n1,A,2024-01-01,1\n2,A,2024-01-02,two\n3,B,2024-01-03,3\n",
    )

    summary = summarize_csv(path)
    types = {column.name: column.data_type for column in summary.columns}

    assert types == {
        "amount": "numeric",
        "category": "categorical",
        "date": "datetime",
        "mixed": "categorical",
    }


def test_empty_csv_reports_no_data(tmp_path: Path) -> None:
    path = write_csv(tmp_path, "")

    summary = summarize_csv(path)
    report = render_summary(summary)

    assert summary.columns == []
    assert "No data to summarize" in report


def test_missing_file_raises_user_friendly_error(tmp_path: Path) -> None:
    with pytest.raises(CSVSummaryError, match="File not found"):
        summarize_csv(tmp_path / "missing.csv")


def test_non_csv_input_raises_user_friendly_error(tmp_path: Path) -> None:
    path = write_csv(tmp_path, "not,a,csv\n", name="data.txt")

    with pytest.raises(CSVSummaryError, match="does not appear to be a CSV"):
        summarize_csv(path)


def test_invalid_csv_format_raises_user_friendly_error(tmp_path: Path) -> None:
    path = write_csv(tmp_path, 'a,b\n"unterminated,2\n')

    with pytest.raises(CSVSummaryError, match="Invalid CSV format"):
        summarize_csv(path)


def test_cli_prints_report_and_returns_success(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = write_csv(tmp_path, "x,label\n1,a\n2,a\n3,b\n")

    exit_code = main([str(path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "CSV Statistical Summary" in captured.out
    assert "Column: x" in captured.out
    assert "mean: 2" in captured.out
    assert "Column: label" in captured.out
    assert "a: 2" in captured.out
    assert captured.err == ""


def test_cli_prints_error_and_returns_failure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = main([str(tmp_path / "missing.csv")])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Error: File not found" in captured.err

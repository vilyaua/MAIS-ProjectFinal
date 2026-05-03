from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from csv_summary import CSVSummaryError, format_summary, summarize_csv  # noqa: E402
from main import main  # noqa: E402


def write_csv(tmp_path: Path, content: str, name: str = "data.csv") -> Path:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_valid_csv_with_numeric_and_categorical_columns(tmp_path: Path) -> None:
    csv_path = write_csv(
        tmp_path,
        "age,color\n10,red\n20,blue\n30,red\n40,green\n50,red\n",
    )

    summary = summarize_csv(csv_path)

    assert summary.total_rows == 5
    age = summary.columns[0]
    color = summary.columns[1]
    assert age.name == "age"
    assert age.data_type == "numeric"
    assert age.min_value == 10
    assert age.max_value == 50
    assert age.mean_value == 30
    assert age.median_value == 30
    assert color.name == "color"
    assert color.data_type == "categorical"
    assert color.top_values[0] == ("red", 3)


def test_missing_values_are_counted(tmp_path: Path) -> None:
    csv_path = write_csv(
        tmp_path,
        "score,name\n1,Alice\n,\nNA,Bob\n4,null\n",
    )

    summary = summarize_csv(csv_path)
    score = summary.columns[0]
    name = summary.columns[1]

    assert score.missing_count == 2
    assert score.data_type == "numeric"
    assert score.mean_value == 2.5
    assert name.missing_count == 2


def test_top_five_values_are_reported_in_frequency_order(tmp_path: Path) -> None:
    csv_path = write_csv(
        tmp_path,
        "fruit\napple\nbanana\napple\npear\nbanana\napple\nkiwi\nkiwi\nplum\norange\n",
    )

    summary = summarize_csv(csv_path)
    fruit = summary.columns[0]

    assert fruit.data_type == "categorical"
    assert fruit.top_values == [
        ("apple", 3),
        ("banana", 2),
        ("kiwi", 2),
        ("orange", 1),
        ("pear", 1),
    ]


def test_mixed_column_is_handled_gracefully(tmp_path: Path) -> None:
    csv_path = write_csv(tmp_path, "value\n1\ntwo\n3\n\n")

    summary = summarize_csv(csv_path)
    value = summary.columns[0]
    report = format_summary(summary)

    assert value.data_type == "mixed"
    assert value.min_value is None
    assert "Type note: mixed numeric and non-numeric values" in report
    assert "2 numeric, 1 non-numeric" in report


def test_cli_outputs_well_formatted_report(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    csv_path = write_csv(tmp_path, "x,label\n1,a\n2,a\n3,b\n")

    exit_code = main([str(csv_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "CSV Statistical Summary" in captured.out
    assert "Column: x" in captured.out
    assert "Type: numeric" in captured.out
    assert "Mean: 2" in captured.out
    assert "Column: label" in captured.out
    assert "  a: 2" in captured.out
    assert captured.err == ""


def test_missing_file_returns_cli_error(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["does-not-exist.csv"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Error: File not found" in captured.err


def test_empty_csv_raises_clear_error(tmp_path: Path) -> None:
    csv_path = write_csv(tmp_path, "")

    with pytest.raises(CSVSummaryError, match="CSV file is empty"):
        summarize_csv(csv_path)


def test_malformed_csv_with_extra_fields_raises_error(tmp_path: Path) -> None:
    csv_path = write_csv(tmp_path, "a,b\n1,2,3\n")

    with pytest.raises(CSVSummaryError, match="too many fields"):
        summarize_csv(csv_path)

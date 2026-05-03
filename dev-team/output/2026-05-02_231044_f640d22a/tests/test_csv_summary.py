from __future__ import annotations

from pathlib import Path

import pytest
from src.csv_summary import CSVSummaryError, format_report, main, summarize_csv


def write_csv(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_valid_csv_reports_types_stats_missing_and_top_values(tmp_path: Path) -> None:
    csv_path = write_csv(
        tmp_path / "people.csv",
        "age,score,color,comment\n"
        "10,1.5,red,hello\n"
        "20,2.5,blue,world\n"
        "30,3.5,red,hello\n"
        ",4.5,green,unique phrase\n"
        "40,,red,another phrase\n",
    )

    summary = summarize_csv(csv_path)
    report = format_report(summary)

    by_name = {column.name: column for column in summary.columns}
    assert by_name["age"].data_type == "numeric"
    assert by_name["age"].missing_count == 1
    assert by_name["age"].numeric_stats is not None
    assert by_name["age"].numeric_stats.minimum == 10
    assert by_name["age"].numeric_stats.maximum == 40
    assert by_name["age"].numeric_stats.mean == 25
    assert by_name["age"].numeric_stats.median == 25
    assert by_name["color"].data_type == "categorical"
    assert ("red", 3) in by_name["color"].top_values
    assert "CSV Statistical Summary" in report
    assert "Top 5 Values: 'red' (3)" in report


def test_missing_path_displays_error_without_crashing(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["does-not-exist.csv"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Error: File does not exist" in captured.out


def test_non_csv_extension_displays_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = write_csv(tmp_path / "data.txt", "a,b\n1,2\n")

    exit_code = main([str(path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "must have a .csv extension" in captured.out


def test_all_missing_column_has_no_numeric_summary(tmp_path: Path) -> None:
    csv_path = write_csv(
        tmp_path / "missing.csv",
        "id,empty\n1,\n2,NA\n3,null\n",
    )

    summary = summarize_csv(csv_path)
    empty_column = next(column for column in summary.columns if column.name == "empty")

    assert empty_column.data_type == "all_missing"
    assert empty_column.missing_count == 3
    assert empty_column.numeric_stats is None
    assert empty_column.top_values == []
    assert "No non-missing values" in format_report(summary)


def test_non_numeric_columns_skip_numeric_calculations(tmp_path: Path) -> None:
    csv_path = write_csv(
        tmp_path / "text.csv",
        "name,city\nAlice,Paris\nBob,Rome\nCara,Paris\n",
    )

    summary = summarize_csv(csv_path)

    for column in summary.columns:
        assert column.data_type in {"categorical", "string"}
        assert column.numeric_stats is None


def test_empty_csv_file_reports_no_data(tmp_path: Path) -> None:
    csv_path = write_csv(tmp_path / "empty.csv", "")

    with pytest.raises(CSVSummaryError, match="no data"):
        summarize_csv(csv_path)

    exit_code = main([str(csv_path)])
    assert exit_code == 1


def test_header_only_csv_reports_no_data_rows(tmp_path: Path) -> None:
    csv_path = write_csv(tmp_path / "header_only.csv", "a,b,c\n")

    with pytest.raises(CSVSummaryError, match="no data rows"):
        summarize_csv(csv_path)

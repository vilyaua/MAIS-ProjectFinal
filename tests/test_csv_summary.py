from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.csv_summary import (
    CsvParseError,
    FileValidationError,
    main,
    summarize_csv,
)


def write_csv(tmp_path: Path, name: str, content: str) -> Path:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_valid_csv_with_numeric_and_categorical_data(tmp_path: Path) -> None:
    csv_path = write_csv(
        tmp_path,
        "people.csv",
        "name,age,city,score\n"
        "Alice,30,London,88.5\n"
        "Bob,25,Paris,91.5\n"
        "Alice,35,London,95\n"
        "Dana,40,Berlin,85\n",
    )

    summary = summarize_csv(str(csv_path))

    assert summary["row_count"] == 4
    assert summary["column_count"] == 4
    assert summary["columns"]["age"]["type"] == "numeric"
    assert summary["columns"]["age"]["statistics"] == {
        "min": 25.0,
        "max": 40.0,
        "mean": 32.5,
        "median": 32.5,
    }
    assert summary["columns"]["name"]["type"] == "categorical"
    assert summary["columns"]["name"]["top_5_values"][0] == {
        "value": "Alice",
        "count": 2,
    }
    assert summary["columns"]["city"]["missing_count"] == 0


def test_missing_values_are_counted_per_column(tmp_path: Path) -> None:
    csv_path = write_csv(
        tmp_path,
        "missing.csv",
        "id,amount,status\n"
        "1,10,ok\n"
        "2,,NULL\n"
        "3,NA,ok\n"
        "4,20,\n",
    )

    summary = summarize_csv(str(csv_path))

    assert summary["columns"]["amount"]["type"] == "numeric"
    assert summary["columns"]["amount"]["missing_count"] == 2
    assert summary["columns"]["amount"]["statistics"]["mean"] == 15.0
    assert summary["columns"]["status"]["missing_count"] == 2
    assert {"value": "<MISSING>", "count": 2} in summary["columns"]["status"]["top_5_values"]


def test_non_numeric_columns_are_categorical_with_top_values(tmp_path: Path) -> None:
    csv_path = write_csv(
        tmp_path,
        "colors.csv",
        "color,size\nred,small\nblue,large\nred,small\ngreen,small\n",
    )

    summary = summarize_csv(str(csv_path))

    assert summary["columns"]["color"]["type"] == "categorical"
    assert summary["columns"]["color"]["top_5_values"][0] == {
        "value": "red",
        "count": 2,
    }
    assert summary["columns"]["size"]["top_5_values"][0] == {
        "value": "small",
        "count": 3,
    }


def test_nonexistent_file_has_clear_error() -> None:
    with pytest.raises(FileValidationError, match="File not found"):
        summarize_csv("does-not-exist.csv")


def test_non_csv_file_is_rejected(tmp_path: Path) -> None:
    text_path = tmp_path / "data.txt"
    text_path.write_text("a,b\n1,2\n", encoding="utf-8")

    with pytest.raises(FileValidationError, match="must be a CSV file"):
        summarize_csv(str(text_path))


def test_malformed_csv_has_clear_error(tmp_path: Path) -> None:
    csv_path = write_csv(tmp_path, "bad.csv", "a,b\n1,2,3\n")

    with pytest.raises(CsvParseError, match="could not be parsed"):
        summarize_csv(str(csv_path))


def test_empty_csv_is_handled_gracefully(tmp_path: Path) -> None:
    csv_path = write_csv(tmp_path, "empty.csv", "")

    summary = summarize_csv(str(csv_path))

    assert summary["row_count"] == 0
    assert summary["column_count"] == 0
    assert summary["message"] == "No data to process."


def test_cli_outputs_json_for_valid_csv(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    csv_path = write_csv(tmp_path, "data.csv", "x,y\n1,a\n2,a\n3,b\n")

    exit_code = main([str(csv_path)])
    captured = capsys.readouterr()
    output = json.loads(captured.out)

    assert exit_code == 0
    assert output["columns"]["x"]["statistics"]["median"] == 2.0


def test_cli_returns_one_for_user_facing_errors(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["missing.csv"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Error: File not found" in captured.out

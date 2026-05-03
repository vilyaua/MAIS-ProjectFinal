import json
from pathlib import Path

import pytest

from src.csv_summary import (
    MalformedCsvError,
    infer_column_type,
    read_csv,
    summarize_csv,
)


def write_csv(tmp_path: Path, content: str, name: str = "data.csv") -> Path:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_summarizes_numeric_categorical_and_datetime_columns(tmp_path):
    csv_path = write_csv(
        tmp_path,
        "amount,category,created\n"
        "10,A,2024-01-01\n"
        "20,B,2024-01-02\n"
        "30,A,2024-01-03\n",
    )

    summary = summarize_csv(csv_path)

    assert summary["row_count"] == 3
    assert summary["column_count"] == 3
    assert summary["columns"]["amount"]["type"] == "numeric"
    assert summary["columns"]["amount"]["statistics"] == {
        "min": 10,
        "max": 30,
        "mean": 20,
        "median": 20,
    }
    assert summary["columns"]["category"]["type"] == "categorical"
    assert summary["columns"]["created"]["type"] == "datetime"


@pytest.mark.parametrize("missing_token", ["", "NA", "null", " none "])
def test_reports_missing_values(tmp_path, missing_token):
    csv_path = write_csv(
        tmp_path,
        f"name,score\nAlice,10\n{missing_token},20\nBob,{missing_token}\n",
    )

    summary = summarize_csv(csv_path)

    assert summary["columns"]["name"]["missing_values"] == 1
    assert summary["columns"]["score"]["missing_values"] == 1


def test_reports_top_five_frequent_values(tmp_path):
    csv_path = write_csv(
        tmp_path,
        "color\nred\nblue\nred\ngreen\nblue\nred\nyellow\nblack\nwhite\n",
    )

    top_values = summarize_csv(csv_path)["columns"]["color"]["top_values"]

    assert top_values == [
        {"value": "red", "count": 3},
        {"value": "blue", "count": 2},
        {"value": "green", "count": 1},
        {"value": "yellow", "count": 1},
        {"value": "black", "count": 1},
    ]


def test_handles_csv_formatting_variations(tmp_path):
    csv_path = write_csv(
        tmp_path,
        'name;note;value\n"Doe, Jane";"quoted; value";"1,200"\nSmith;plain;3.5\n',
    )

    summary = summarize_csv(csv_path)

    assert summary["columns"]["name"]["top_values"][0] == {
        "value": "Doe, Jane",
        "count": 1,
    }
    assert summary["columns"]["value"]["type"] == "numeric"
    assert summary["columns"]["value"]["statistics"]["max"] == 1200


def test_invalid_file_path_returns_clear_cli_error(tmp_path, capsys):
    from src.csv_summary import main

    exit_code = main([str(tmp_path / "missing.csv")])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Error: File not found" in captured.err


def test_malformed_csv_raises_relevant_error(tmp_path):
    csv_path = write_csv(tmp_path, "a,b\n1,2\n3\n")

    with pytest.raises(MalformedCsvError, match="row 3"):
        read_csv(csv_path)


def test_cli_outputs_json_summary(tmp_path, capsys):
    from src.csv_summary import main

    csv_path = write_csv(tmp_path, "x,y\n1,A\n2,A\n3,B\n")
    exit_code = main([str(csv_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    parsed = json.loads(captured.out)
    assert parsed["columns"]["x"]["statistics"]["median"] == 2
    assert parsed["columns"]["y"]["top_values"][0] == {
        "value": "A",
        "count": 2,
    }


def test_type_inference_avoids_datetime_misclassification_for_numeric_years():
    assert infer_column_type(["2020", "2021", "2022"]) == "numeric"
    assert infer_column_type(["2020-01-01", "2021-01-01"]) == "datetime"
    assert infer_column_type(["001", "002"]) == "numeric"

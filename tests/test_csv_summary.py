from __future__ import annotations

from pathlib import Path

import pytest

from src.csv_summary import CsvSummaryError, format_summary, main, summarise_csv


def write_csv(tmp_path: Path, content: str, name: str = "data.csv") -> Path:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def by_name(summary: list[dict], name: str) -> dict:
    return next(item for item in summary if item["name"] == name)


def test_summarise_csv_detects_types_and_stats(tmp_path: Path) -> None:
    csv_path = write_csv(
        tmp_path,
        "age,city,date\n"
        "10,Paris,2024-01-01\n"
        "20,Paris,2024-01-02\n"
        "30,London,2024-01-03\n"
        ",London,\n",
    )

    summary = summarise_csv(str(csv_path))

    age = by_name(summary, "age")
    city = by_name(summary, "city")
    date = by_name(summary, "date")

    assert age["type"] == "numeric"
    assert age["missing_count"] == 1
    assert age["numeric_stats"] == {
        "min": 10.0,
        "max": 30.0,
        "mean": 20.0,
        "median": 20.0,
    }

    assert city["type"] == "categorical"
    assert city["missing_count"] == 0
    assert city["top_values"][:2] == [("Paris", 2), ("London", 2)]

    assert date["type"] == "datetime"
    assert date["missing_count"] == 1


def test_top_five_values_are_limited(tmp_path: Path) -> None:
    csv_path = write_csv(
        tmp_path,
        "letter\nA\nA\nB\nB\nB\nC\nD\nE\nF\nG\n",
    )

    summary = summarise_csv(str(csv_path))
    letter = by_name(summary, "letter")

    assert len(letter["top_values"]) == 5
    assert letter["top_values"][0] == ("B", 3)


def test_all_missing_and_unique_values_do_not_crash(tmp_path: Path) -> None:
    csv_path = write_csv(
        tmp_path,
        "empty,unique\n"
        ",u1\n"
        "NA,u2\n"
        "null,u3\n"
        "None,u4\n",
    )

    summary = summarise_csv(str(csv_path))
    empty = by_name(summary, "empty")
    unique = by_name(summary, "unique")

    assert empty["type"] == "all_missing"
    assert empty["missing_count"] == 4
    assert empty["numeric_stats"] is None
    assert empty["top_values"] == []

    assert unique["type"] == "categorical"
    assert unique["missing_count"] == 0
    assert len(unique["top_values"]) == 4
    assert all(count == 1 for _, count in unique["top_values"])


def test_invalid_path_raises_meaningful_error(tmp_path: Path) -> None:
    missing = tmp_path / "missing.csv"

    with pytest.raises(CsvSummaryError, match="does not exist"):
        summarise_csv(str(missing))


def test_non_csv_extension_is_rejected(tmp_path: Path) -> None:
    path = write_csv(tmp_path, "a\n1\n", name="data.txt")

    with pytest.raises(CsvSummaryError, match=".csv extension"):
        summarise_csv(str(path))


def test_cli_success_outputs_summary(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    csv_path = write_csv(tmp_path, "num\n1\n2\n3\n")

    exit_code = main([str(csv_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Column: num" in captured.out
    assert "Type: numeric" in captured.out
    assert "median: 2" in captured.out


def test_cli_error_exits_gracefully(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main([str(tmp_path / "missing.csv")])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Error:" in captured.err
    assert "does not exist" in captured.err


def test_format_summary_handles_all_missing() -> None:
    text = format_summary(
        [
            {
                "name": "blank",
                "type": "all_missing",
                "missing_count": 2,
                "total_count": 2,
                "numeric_stats": None,
                "top_values": [],
            }
        ]
    )

    assert "None (no non-missing values)" in text
    assert "N/A" in text

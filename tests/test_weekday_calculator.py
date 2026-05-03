from __future__ import annotations

from datetime import date

import pytest

from src.weekday_calculator import DateParseError, main, parse_date, weekday_name


def test_iso_date_returns_correct_weekday() -> None:
    assert weekday_name("2024-06-10") == "Monday"


def test_day_month_year_format_returns_correct_weekday() -> None:
    assert weekday_name("29 February 2020") == "Saturday"


def test_leap_year_date_is_valid() -> None:
    assert parse_date("2020-02-29") == date(2020, 2, 29)
    assert weekday_name("2020-02-29") == "Saturday"


@pytest.mark.parametrize(
    ("date_text", "expected"),
    [
        ("02/29/2020", date(2020, 2, 29)),
        ("2020/02/29", date(2020, 2, 29)),
        ("29-02-2020", date(2020, 2, 29)),
        ("Feb 29, 2020", date(2020, 2, 29)),
        ("February 29 2020", date(2020, 2, 29)),
    ],
)
def test_supported_free_formats(date_text: str, expected: date) -> None:
    assert parse_date(date_text) == expected


@pytest.mark.parametrize("date_text", ["not a date", "2021-02-29", "", "13/31/2020"])
def test_invalid_dates_raise_clear_error(date_text: str) -> None:
    with pytest.raises(DateParseError, match="date|provided"):
        parse_date(date_text)


def test_cli_outputs_readable_weekday(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["2020-02-29"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == "2020-02-29 is a Saturday."
    assert captured.err == ""


def test_cli_accepts_multi_word_date(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["29", "February", "2020"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Saturday" in captured.out


def test_cli_invalid_input_shows_error(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["2021-02-29"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Error: Invalid or unparseable date" in captured.err


def test_cli_missing_input_shows_usage(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    class NonInteractiveInput:
        def isatty(self) -> bool:
            return False

    monkeypatch.setattr("sys.stdin", NonInteractiveInput())

    exit_code = main([])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "usage:" in captured.err
    assert "missing date input" in captured.err

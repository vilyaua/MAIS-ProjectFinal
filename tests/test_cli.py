"""Tests for the password generator CLI."""

from __future__ import annotations

import re
import string

import pytest

from src.main import main


def _extract_password(output: str) -> str:
    match = re.search(r"^Password: (.+)$", output, re.MULTILINE)
    assert match is not None
    return match.group(1)


def test_cli_generates_password_with_valid_options(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        [
            "--length",
            "16",
            "--no-uppercase",
            "--lowercase",
            "--digits",
            "--no-special",
        ]
    )

    captured = capsys.readouterr()
    password = _extract_password(captured.out)
    assert exit_code == 0
    assert len(password) == 16
    assert all(char in string.ascii_lowercase + string.digits for char in password)
    assert "Strength:" in captured.out


def test_cli_rejects_length_less_than_one(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--length", "0"])

    captured = capsys.readouterr()
    assert exc_info.value.code == 2
    assert "length must be at least" in captured.err
    assert "Password:" not in captured.out


def test_cli_rejects_all_character_types_excluded(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(
            [
                "--no-uppercase",
                "--no-lowercase",
                "--no-digits",
                "--no-special",
            ]
        )

    captured = capsys.readouterr()
    assert exc_info.value.code == 2
    assert "At least one character type" in captured.err
    assert "Password:" not in captured.out


def test_cli_generates_default_password(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main([])

    captured = capsys.readouterr()
    password = _extract_password(captured.out)
    assert exit_code == 0
    assert len(password) == 12
    assert "Strength:" in captured.out


def test_cli_non_integer_length_shows_validation_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--length", "abc"])

    captured = capsys.readouterr()
    assert exc_info.value.code == 2
    assert "invalid int value" in captured.err
    assert "Password:" not in captured.out


def test_cli_conflicting_options_show_error(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--uppercase", "--no-uppercase"])

    captured = capsys.readouterr()
    assert exc_info.value.code == 2
    assert "not allowed with argument" in captured.err

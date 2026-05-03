"""CLI tests for the password generator."""

from __future__ import annotations

import re
import string

from src.main import main


def _extract_generated_password(output: str) -> str:
    match = re.search(r"Generated password: (.+)", output)
    assert match is not None
    return match.group(1).strip()


def test_cli_generates_password_with_valid_arguments(capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = main(
        [
            "--length",
            "10",
            "--no-uppercase",
            "--lowercase",
            "--digits",
            "--no-special",
        ]
    )
    output = capsys.readouterr().out
    password = _extract_generated_password(output)

    assert exit_code == 0
    assert len(password) == 10
    assert set(password).issubset(set(string.ascii_lowercase + string.digits))
    assert "Strength:" in output


def test_cli_rejects_invalid_argument_length(capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = main(["--length", "0", "--lowercase"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "Error: Password length must be greater than zero." in output
    assert "Generated password:" not in output


def test_cli_rejects_no_selected_character_sets(capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = main(
        [
            "--length",
            "12",
            "--no-uppercase",
            "--no-lowercase",
            "--no-digits",
            "--no-special",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "Error: Select at least one character set." in output
    assert "Generated password:" not in output

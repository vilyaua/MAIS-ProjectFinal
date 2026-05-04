"""CLI tests for the password generator."""

from __future__ import annotations

from src.main import run


def test_cli_outputs_password_and_strength(capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = run(["--length", "12", "--lowercase", "--digits"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Generated password:" in captured.out
    assert "Strength:" in captured.out


def test_cli_reports_missing_character_types(capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = None
    try:
        run(["--length", "12"])
    except SystemExit as exc:
        exit_code = exc.code

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Select at least one character type" in captured.err

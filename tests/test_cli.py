"""Tests for the command-line interface."""

from __future__ import annotations

from src.main import main


def test_cli_success_outputs_password_and_strength(capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = main(["--length", "12"])

    captured = capsys.readouterr()
    lines = captured.out.strip().splitlines()
    assert exit_code == 0
    assert len(lines) == 2
    assert lines[0].startswith("Password: ")
    assert len(lines[0].removeprefix("Password: ")) == 12
    assert lines[1] in {"Strength: weak", "Strength: moderate", "Strength: strong"}


def test_cli_invalid_length_outputs_error(capsys) -> None:  # type: ignore[no-untyped-def]
    try:
        main(["--length", "0"])
    except SystemExit as exc:
        assert exc.code == 2

    captured = capsys.readouterr()
    assert "Password length must be between 1 and 128" in captured.err


def test_cli_no_character_sets_outputs_error(capsys) -> None:  # type: ignore[no-untyped-def]
    try:
        main(
            [
                "--length",
                "12",
                "--no-uppercase",
                "--no-lowercase",
                "--no-digits",
                "--no-special",
            ]
        )
    except SystemExit as exc:
        assert exc.code == 2

    captured = capsys.readouterr()
    assert "At least one character set must be selected" in captured.err

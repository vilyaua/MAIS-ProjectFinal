"""Tests for the password generator command line interface."""

from __future__ import annotations

import pytest

from main import build_parser, main, parse_length


def test_main_generates_password_and_strength_output(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main([
        "--length",
        "12",
        "--no-special",
    ])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Generated password:" in captured.out
    assert "Strength:" in captured.out
    password_line = next(
        line for line in captured.out.splitlines()
        if line.startswith("Generated password:")
    )
    password = password_line.split(": ", 1)[1]
    assert len(password) == 12


def test_cli_rejects_no_character_types(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([
            "--length",
            "12",
            "--no-uppercase",
            "--no-lowercase",
            "--no-digits",
            "--no-special",
        ])

    captured = capsys.readouterr()

    assert exc_info.value.code == 2
    assert "At least one character type must be chosen" in captured.err
    assert "usage:" in captured.err


def test_parse_length_rejects_non_integer() -> None:
    with pytest.raises(Exception, match="integer"):
        parse_length("not-a-number")


def test_parse_length_rejects_out_of_range() -> None:
    with pytest.raises(Exception, match="between"):
        parse_length("129")


def test_help_displays_usage(capsys: pytest.CaptureFixture[str]) -> None:
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--help"])

    captured = capsys.readouterr()

    assert exc_info.value.code == 0
    assert "usage:" in captured.out
    assert "--length" in captured.out
    assert "--no-uppercase" in captured.out


def test_interactive_reprompts_for_invalid_length(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    answers = iter(["abc", "4", "10", "y", "n", "y", "n"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))

    exit_code = main([])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Length must be an integer" in captured.out
    assert "Length must be between" in captured.out
    assert "Generated password:" in captured.out

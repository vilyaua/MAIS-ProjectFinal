"""Tests for the command-line interface."""

from __future__ import annotations

from src.main import main


def test_main_valid_argument_prints_ascii_art(capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = main(["Hello"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "ASCII Art:" in captured.out
    assert "#" in captured.out
    assert captured.err == ""


def test_main_empty_argument_reports_error(capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = main(["   "])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Error:" in captured.err
    assert "must not be empty" in captured.err


def test_main_too_long_reports_error(capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = main(["A" * 101])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "shorten" in captured.err


def test_main_unsupported_character_warns_without_crashing(capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = main(["OK🙂"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "ASCII Art:" in captured.out
    assert "Warning:" in captured.err


def test_help_flag_displays_usage(capsys) -> None:  # type: ignore[no-untyped-def]
    try:
        main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0
    captured = capsys.readouterr()

    assert "usage:" in captured.out.lower()
    assert "Generate ASCII art" in captured.out

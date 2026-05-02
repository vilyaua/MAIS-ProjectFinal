"""Tests for the ASCII art generator."""

from __future__ import annotations

import pytest

from src.ascii_art import (
    FontNotFoundError,
    InputValidationError,
    generate_ascii_art,
    main,
    validate_text,
)


def test_generate_ascii_art_valid_text_block_font() -> None:
    art = generate_ascii_art("Hi", font_name="block")

    assert "H   H" in art
    assert "IIIII" in art


def test_empty_input_is_rejected() -> None:
    with pytest.raises(InputValidationError, match="Input cannot be empty"):
        validate_text("   ")


def test_non_printable_input_is_rejected() -> None:
    with pytest.raises(InputValidationError, match="non-printable"):
        validate_text("hello\x00world")


def test_outline_font_differs_from_block_font() -> None:
    block = generate_ascii_art("A", font_name="block")
    outline = generate_ascii_art("A", font_name="outline")

    assert "AAAAA" in block
    assert "__A__" in outline
    assert block != outline


def test_long_input_is_wrapped() -> None:
    art = generate_ascii_art("ABCDEFGHIJK", font_name="block", wrap_width=5)

    assert "\n\n" in art
    assert "  A" in art
    assert "F" in art
    assert "K" in art


def test_unknown_font_raises_user_friendly_error() -> None:
    with pytest.raises(FontNotFoundError, match="Available fonts"):
        generate_ascii_art("Hello", font_name="missing")


def test_main_reads_from_arguments_and_prints(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["Hello", "World", "--font", "block"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "H   H" in captured.out
    assert captured.err == ""


def test_main_reads_from_stdin(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["--font", "outline"], stdin_reader=lambda: "OK")

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "__O__" in captured.out


def test_main_reports_errors_without_traceback(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["   "], stdin_reader=lambda: "")

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Error: Input cannot be empty" in captured.err
    assert "Traceback" not in captured.err

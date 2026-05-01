"""Tests for the ASCII art generator."""

from __future__ import annotations

import pytest
from src.ascii_art import generate_ascii_art, main


def test_generate_ascii_art_for_valid_text() -> None:
    art = generate_ascii_art("Hi")

    assert "#   #" in art
    assert "#####" in art
    assert len(art.splitlines()) == 5


def test_generate_ascii_art_supports_digits_and_spaces() -> None:
    art = generate_ascii_art("A 1")

    assert len(art.splitlines()) == 5
    assert "###" in art
    assert "#####" in art


@pytest.mark.parametrize("text", ["", "   ", "\t\n"])
def test_empty_or_whitespace_input_raises_meaningful_error(text: str) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        generate_ascii_art(text)


def test_non_string_input_raises_type_error() -> None:
    with pytest.raises(TypeError, match="must be a string"):
        generate_ascii_art(123)  # type: ignore[arg-type]


def test_unsupported_characters_are_replaced_with_warning() -> None:
    with pytest.warns(UserWarning, match="Unsupported characters"):
        art = generate_ascii_art("A@")

    assert len(art.splitlines()) == 5
    assert "?" not in art
    assert "###" in art


def test_very_long_input_raises_length_notice() -> None:
    with pytest.raises(ValueError, match="Maximum supported length is 5"):
        generate_ascii_art("ABCDEF", max_length=5)


def test_invalid_max_length_raises_error() -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        generate_ascii_art("A", max_length=0)


def test_cli_prints_art(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["OK"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "#   #" in captured.out
    assert captured.err == ""


def test_cli_reports_validation_error(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["   "])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Error:" in captured.err

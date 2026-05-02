"""Tests for the ASCII art generator."""

from __future__ import annotations

import pytest

from src.ascii_art import (
    AsciiArtError,
    EmptyInputError,
    RenderResult,
    UnsupportedCharacterError,
    render_ascii_art,
)


def test_valid_text_outputs_block_ascii_art() -> None:
    art = render_ascii_art("A1")

    assert isinstance(art, str)
    assert " ### " in art
    assert "#####" in art
    assert len(art.splitlines()) == 5


def test_mixed_case_letters_and_digits_are_rendered() -> None:
    art = render_ascii_art("aZ9")

    assert isinstance(art, str)
    lines = art.splitlines()
    assert len(lines) == 5
    assert any("###" in line for line in lines)
    assert any("####" in line for line in lines)


@pytest.mark.parametrize("value", ["", "   ", None])
def test_empty_input_raises_clear_error(value: str | None) -> None:
    with pytest.raises(EmptyInputError, match="Input cannot be empty"):
        render_ascii_art(value)


def test_unsupported_characters_are_replaced_with_warning() -> None:
    result = render_ascii_art("Hi!", return_warnings=True)

    assert isinstance(result, RenderResult)
    assert "?" not in result.art  # Placeholder is rendered as art, not literal text.
    assert result.warnings == ("Unsupported character '!' replaced with '?'.",)
    assert len(result.art.splitlines()) == 5


def test_strict_mode_raises_for_unsupported_characters() -> None:
    with pytest.raises(UnsupportedCharacterError, match="Unsupported character"):
        render_ascii_art("No!", strict=True)


def test_custom_simple_font_and_size_are_applied() -> None:
    art = render_ascii_art("a1", font="simple", size=2)
    lines = art.splitlines()

    assert len(lines) == 6
    assert lines[0].count("A") == 2
    assert any("111111" in line.replace(" ", "") for line in lines)


def test_invalid_options_raise_clear_errors() -> None:
    with pytest.raises(AsciiArtError, match="Unsupported font"):
        render_ascii_art("Hi", font="fancy")

    with pytest.raises(AsciiArtError, match="positive integer"):
        render_ascii_art("Hi", size=0)

    with pytest.raises(AsciiArtError, match="single character"):
        render_ascii_art("Hi", placeholder="??")

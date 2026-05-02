"""Tests for ASCII art rendering utilities."""

from __future__ import annotations

import pytest

from src.ascii_art import AsciiArtError, GLYPH_HEIGHT, render_ascii_art


def test_render_valid_text_outputs_five_rows() -> None:
    result = render_ascii_art("Hi 123!")

    lines = result.art.splitlines()
    assert len(lines) == GLYPH_HEIGHT
    assert all(line for line in lines)
    assert "#" in result.art
    assert result.warning is None


def test_empty_input_raises_clear_error() -> None:
    with pytest.raises(AsciiArtError, match="must not be empty"):
        render_ascii_art("   ")


def test_too_long_input_raises_clear_error() -> None:
    with pytest.raises(AsciiArtError, match="too long"):
        render_ascii_art("A" * 101)


def test_unsupported_characters_are_skipped_with_warning() -> None:
    result = render_ascii_art("A🙂B")

    assert "#" in result.art
    assert result.warning is not None
    assert "skipped unsupported" in result.warning
    assert "🙂" in result.warning


def test_all_unsupported_characters_raise_error() -> None:
    with pytest.raises(AsciiArtError, match="no supported characters"):
        render_ascii_art("🙂🙂")

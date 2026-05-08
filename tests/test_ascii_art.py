"""Tests for the ASCII art generator."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ascii_art import generate_ascii_art, get_glyph, validate_text  # noqa: E402


def test_generate_ascii_art_for_valid_text() -> None:
    """Valid alphabetic text should render recognizable block glyphs."""
    result = generate_ascii_art("Hi")

    assert "H   H" in result
    assert "IIIII" in result
    assert len(result.splitlines()) == 5


def test_empty_string_raises_user_friendly_error() -> None:
    """Empty input should be rejected with a clear message."""
    with pytest.raises(ValueError, match="Input cannot be empty"):
        generate_ascii_art("")


def test_whitespace_only_string_raises_user_friendly_error() -> None:
    """Whitespace-only input should be treated as empty."""
    with pytest.raises(ValueError, match="Input cannot be empty"):
        validate_text("   ")


def test_special_characters_do_not_crash() -> None:
    """Unsupported characters should be rendered with a fallback glyph."""
    result = generate_ascii_art("A!")

    assert "A" in result
    assert "?" in result
    assert len(result.splitlines()) == 5


def test_spaces_are_reflected_with_spacing() -> None:
    """Spaces should create a visible gap between words."""
    result = generate_ascii_art("A B")
    first_line = result.splitlines()[0]

    assert "  A" in first_line
    assert "     " in first_line
    assert "BBBB" in result


def test_numeric_string_is_rendered() -> None:
    """Numeric strings should use digit glyphs."""
    result = generate_ascii_art("123")

    assert "11111" in result
    assert "22222" in result
    assert "3333" in result


def test_get_glyph_is_case_insensitive() -> None:
    """Lowercase letters should map to the same glyph as uppercase letters."""
    assert get_glyph("a") == get_glyph("A")


def test_non_string_input_is_rejected() -> None:
    """Validation should reject non-string values."""
    with pytest.raises(ValueError, match="Input must be a string"):
        validate_text(123)  # type: ignore[arg-type]

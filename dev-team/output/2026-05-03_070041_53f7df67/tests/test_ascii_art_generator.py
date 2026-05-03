"""Tests for the ASCII Art Generator."""

from __future__ import annotations

import pytest
from src.ascii_art_generator import (
    FONT_HEIGHT,
    generate_ascii_art,
    is_exit_command,
    should_restart,
    validate_text,
)


def test_generate_ascii_art_for_valid_text() -> None:
    art = generate_ascii_art("Hi")

    assert len(art.splitlines()) == FONT_HEIGHT
    assert "# #" in art
    assert "###" in art


def test_empty_input_is_rejected() -> None:
    with pytest.raises(ValueError, match="empty"):
        validate_text("")


def test_non_printable_input_is_rejected() -> None:
    with pytest.raises(ValueError, match="non-printable"):
        validate_text("hello\nworld")


def test_spaces_and_punctuation_are_supported() -> None:
    art = generate_ascii_art("Hi, Bob!")

    assert len(art.splitlines()) == FONT_HEIGHT
    assert "#" in art
    assert art.splitlines()[-1].strip().endswith("#")


def test_mixed_case_uses_same_standard_block_font() -> None:
    upper_art = generate_ascii_art("ABC")
    mixed_art = generate_ascii_art("aBc")

    assert mixed_art == upper_art


def test_exit_and_restart_commands() -> None:
    assert is_exit_command(":exit")
    assert is_exit_command(" Q ")
    assert should_restart("yes")
    assert should_restart(" restart ")
    assert not should_restart("no")

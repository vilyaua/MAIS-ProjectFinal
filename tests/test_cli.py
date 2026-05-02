"""Tests for interactive CLI helpers."""

from __future__ import annotations

from unittest.mock import patch

from src.main import prompt_character_sets, prompt_length


def test_prompt_length_retries_after_invalid_input(capsys) -> None:  # type: ignore[no-untyped-def]
    with patch("builtins.input", side_effect=["abc", "12"]):
        assert prompt_length() == 12

    output = capsys.readouterr().out
    assert "not a valid integer" in output


def test_prompt_character_sets_retries_when_none_selected(capsys) -> None:  # type: ignore[no-untyped-def]
    answers = ["n", "n", "n", "n", "y", "n", "n", "n"]
    with patch("builtins.input", side_effect=answers):
        selected = prompt_character_sets()

    output = capsys.readouterr().out
    assert "Select at least one character set" in output
    assert len(selected) == 1

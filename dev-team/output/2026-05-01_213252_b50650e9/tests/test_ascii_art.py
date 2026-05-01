"""Tests for the ASCII art text generator."""

from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ascii_art import (  # noqa: E402
    AsciiArtError,
    FONT_HEIGHT,
    generate_ascii_art_with_warnings,
    main,
    render_ascii_art,
    sanitize_text,
)


def test_render_valid_text_outputs_ascii_art() -> None:
    art = render_ascii_art("A")

    assert art.splitlines() == [" ###", "#   #", "#####", "#   #", "#   #"]


def test_empty_input_raises_clear_error() -> None:
    with pytest.raises(AsciiArtError, match="Input is required"):
        render_ascii_art("")


def test_whitespace_only_input_raises_clear_error() -> None:
    with pytest.raises(AsciiArtError, match="Input is required"):
        sanitize_text("   ")


def test_unsupported_characters_are_replaced_with_warning() -> None:
    art, warnings = generate_ascii_art_with_warnings("Hi 😀")

    assert warnings
    assert "Unsupported characters replaced" in warnings[0]
    assert len(art.splitlines()) == FONT_HEIGHT
    assert art.splitlines()[0].endswith("###")


def test_multi_word_input_preserves_spacing() -> None:
    single_space_art = render_ascii_art("A B")
    no_space_art = render_ascii_art("AB")

    assert len(single_space_art.splitlines()[0]) > len(no_space_art.splitlines()[0])
    assert "       " in single_space_art.splitlines()[0]


def test_main_prints_art_to_stdout_for_command_line_text(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["OK"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "###" in captured.out
    assert captured.err == ""


def test_main_reports_error_for_empty_input(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO(""))

    exit_code = main([])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Error: Input is required" in captured.err


def test_main_warns_for_unsupported_input(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["A", "😀"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Warning: Unsupported characters" in captured.err
    assert "###" in captured.out

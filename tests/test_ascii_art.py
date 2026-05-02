"""Tests for the ASCII art text generator."""

from __future__ import annotations

from io import StringIO
from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ascii_art import FONT_HEIGHT, main, render_line, render_text  # noqa: E402


def test_render_single_line_text_outputs_expected_height() -> None:
    art = render_text("Hi")

    lines = art.splitlines()
    assert len(lines) == FONT_HEIGHT
    assert "#####" in art
    assert "#   #" in art


def test_empty_input_raises_user_friendly_error() -> None:
    with pytest.raises(ValueError, match="Input cannot be empty"):
        render_text("   \n\t")


def test_multi_line_input_preserves_line_break_between_blocks() -> None:
    art = render_text("A\nB")
    lines = art.splitlines()

    assert len(lines) == FONT_HEIGHT * 2
    assert lines[0].strip() == "###"
    assert lines[FONT_HEIGHT].startswith("####")


def test_blank_line_inside_multi_line_input_is_preserved() -> None:
    art = render_text("A\n\nB")
    lines = art.split("\n")

    assert lines[FONT_HEIGHT] == ""
    assert lines[FONT_HEIGHT + 1].startswith("####")


def test_unsupported_characters_are_replaced_with_placeholder() -> None:
    art = render_line("@").splitlines()

    assert len(art) == FONT_HEIGHT
    assert art[0].strip() == "###"
    assert art[-1].strip() == "#"


def test_cli_uses_command_line_arguments(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["OK"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert "###" in captured.out


def test_cli_reads_standard_input(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main([], stdin=StringIO("A\nB"))
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert len(captured.out.rstrip("\n").splitlines()) == FONT_HEIGHT * 2


def test_cli_reports_empty_input(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main([], stdin=StringIO(""))
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Input cannot be empty" in captured.err
    assert captured.out == ""

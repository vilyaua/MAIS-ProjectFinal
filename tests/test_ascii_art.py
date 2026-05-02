"""Tests for the ASCII art generator."""

from __future__ import annotations

from pathlib import Path

import pytest

import sys

sys.path.insert(0, "src")

from ascii_art import (  # noqa: E402
    FontError,
    InvalidInputError,
    available_fonts,
    generate_ascii_art,
    render_or_save,
)
from main import main  # noqa: E402


def test_single_line_block_output_contains_expected_glyph_rows() -> None:
    art = generate_ascii_art("Hi", font="block")

    assert "#   # #####" in art
    assert "#####   #" in art
    assert len(art.splitlines()) == 5


def test_multiline_input_renders_each_line_as_separate_block() -> None:
    art = generate_ascii_art("A\nB", font="block")
    lines = art.splitlines()

    assert lines[0] == " ###"
    assert lines[5] == ""
    assert lines[6] == "####"
    assert len(lines) == 11


@pytest.mark.parametrize("bad_text", ["", "hello\tworld", "snowman ☃"])
def test_invalid_input_raises_meaningful_error(bad_text: str) -> None:
    with pytest.raises(InvalidInputError, match="Input text|printable ASCII"):
        generate_ascii_art(bad_text)


def test_output_can_be_saved_to_file(tmp_path: Path) -> None:
    output_file = tmp_path / "nested" / "art.txt"

    art = render_or_save("OK", font="star", output_path=output_file)

    assert output_file.exists()
    assert output_file.read_text(encoding="utf-8") == art + "\n"
    assert "*" in art


def test_different_font_styles_change_output() -> None:
    block = generate_ascii_art("A", font="block")
    star = generate_ascii_art("A", font="star")
    outline = generate_ascii_art("A", font="outline")
    simple = generate_ascii_art("A", font="simple")

    assert block != star
    assert star != outline
    assert simple.startswith("+")
    assert set(available_fonts()) == {"block", "star", "outline", "simple"}


def test_unsupported_font_raises_error() -> None:
    with pytest.raises(FontError, match="Unsupported font"):
        generate_ascii_art("A", font="missing")


def test_cli_prints_to_console(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["Hi", "--font", "simple"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "| Hi |" in captured.out
    assert captured.err == ""


def test_cli_reports_invalid_input(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main([""])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Error:" in captured.err

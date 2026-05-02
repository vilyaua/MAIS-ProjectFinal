"""Tests for the ASCII art generator."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

import main as cli_main  # noqa: E402
from ascii_art import (  # noqa: E402
    DEFAULT_FONT,
    InputValidationError,
    get_supported_fonts,
    render_ascii_art,
    validate_text,
)


def test_valid_text_renders_ascii_art() -> None:
    art = render_ascii_art("Hi 2")

    assert "█" in art
    assert len(art.splitlines()) == 7


def test_empty_input_is_rejected() -> None:
    with pytest.raises(InputValidationError, match="text cannot be empty"):
        validate_text("   ")


def test_unsupported_characters_are_reported() -> None:
    with pytest.raises(InputValidationError, match="Unsupported character"):
        validate_text("Hello 😊")


def test_default_font_is_block() -> None:
    art = render_ascii_art("A")

    assert DEFAULT_FONT == "block"
    assert "█" in art


def test_valid_font_style_changes_output() -> None:
    block = render_ascii_art("A", "block")
    star = render_ascii_art("A", "star")

    assert "*" in star
    assert star != block


def test_unsupported_font_is_rejected() -> None:
    with pytest.raises(InputValidationError, match="Unsupported font style"):
        render_ascii_art("A", "unknown")


def test_cli_prints_art_with_selected_font(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli_main.main(["--font", "plain", "OK!"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "#" in captured.out
    assert captured.err == ""


def test_cli_empty_input_displays_error(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli_main.main([])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "text cannot be empty" in captured.err


def test_cli_lists_supported_fonts(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli_main.main(["--list-fonts"])
    captured = capsys.readouterr()

    assert exit_code == 0
    for font in get_supported_fonts():
        assert font in captured.out


def test_cli_unexpected_error_is_user_friendly(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def broken_renderer(text: str, font: str) -> str:
        raise RuntimeError("boom")

    monkeypatch.setattr(cli_main, "render_ascii_art", broken_renderer)

    exit_code = cli_main.main(["Hello"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "unexpected problem" in captured.err
    assert "boom" not in captured.err

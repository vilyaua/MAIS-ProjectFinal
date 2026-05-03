"""Tests for the ASCII art generator."""

from __future__ import annotations

import pytest

from src import ascii_art


def test_render_valid_text_outputs_ascii_art() -> None:
    output = ascii_art.render_text("Hi", "hash")

    assert "#" in output
    assert len(output.splitlines()) == 7


def test_empty_input_raises_clear_error() -> None:
    with pytest.raises(ascii_art.EmptyInputError, match="non-empty text"):
        ascii_art.render_text("   ")


def test_special_supported_character_is_rendered() -> None:
    output = ascii_art.render_text("Hi!", "star")

    assert "*" in output
    assert len(output.splitlines()) == 7


def test_unsupported_special_character_raises_clear_error() -> None:
    with pytest.raises(ascii_art.UnsupportedCharacterError, match="unsupported"):
        ascii_art.render_text("Hello ~")


def test_selected_font_changes_rendering_character() -> None:
    block_output = ascii_art.render_text("A", "block")
    star_output = ascii_art.render_text("A", "star")

    assert "█" in block_output
    assert "*" in star_output
    assert block_output != star_output


def test_multi_word_input_preserves_spacing() -> None:
    one_space_output = ascii_art.render_text("A B", "hash")
    two_space_output = ascii_art.render_text("A  B", "hash")

    assert len(two_space_output.splitlines()[0]) > len(one_space_output.splitlines()[0])


def test_unknown_font_raises_clear_error() -> None:
    with pytest.raises(ascii_art.FontNotFoundError, match="Unknown font"):
        ascii_art.render_text("A", "missing")


def test_cli_outputs_art_to_console(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = ascii_art.main(["--font", "hash", "Hello", "World"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "#" in captured.out
    assert captured.err == ""


def test_cli_empty_input_prints_error(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = ascii_art.main([])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Error:" in captured.err
    assert "non-empty text" in captured.err


def test_cli_backend_conversion_failure_is_meaningful(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fail_render(_text: str, _font_name: str = "block") -> str:
        raise ascii_art.AsciiArtError("simulated backend failure")

    monkeypatch.setattr(ascii_art, "render_text", fail_render)

    exit_code = ascii_art.main(["Hello"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "simulated backend failure" in captured.err


def test_list_fonts(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = ascii_art.main(["--list-fonts"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "block" in captured.out
    assert "hash" in captured.out
    assert "star" in captured.out

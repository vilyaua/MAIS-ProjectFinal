"""Tests for the ASCII art generator."""

from __future__ import annotations

import io
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ascii_art_generator import AsciiArtGenerator, ConsoleOutputSink, run  # noqa: E402


def test_generate_normal_text_default_font_contains_recognizable_letters() -> None:
    generator = AsciiArtGenerator()

    ascii_art, warning = generator.generate("Hi")

    assert warning is None
    assert isinstance(ascii_art, str)
    assert len(ascii_art.strip()) > 0
    assert "_" in ascii_art or "|" in ascii_art


def test_empty_input_raises_expected_error() -> None:
    generator = AsciiArtGenerator()

    with pytest.raises(ValueError, match="Input cannot be empty"):
        generator.generate("   ")


def test_control_sequences_are_sanitized_before_rendering() -> None:
    generator = AsciiArtGenerator()

    sanitized = generator.sanitize_input("Hello\x1b[31m RED\x1b[0m\x00\x07")
    ascii_art, warning = generator.generate("Hello\x1b[31m RED\x1b[0m\x00\x07")

    assert sanitized == "Hello RED"
    assert warning is None
    assert "\x1b" not in ascii_art
    assert "\x00" not in ascii_art


def test_invalid_font_falls_back_and_returns_warning() -> None:
    generator = AsciiArtGenerator()

    ascii_art, warning = generator.generate("Hello", font="definitely_not_a_font")

    assert len(ascii_art.strip()) > 0
    assert warning is not None
    assert "Using default font" in warning


def test_run_prints_error_for_empty_input_without_crashing() -> None:
    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = run("", output_sink=ConsoleOutputSink(stdout), error_stream=stderr)

    assert exit_code == 1
    assert "Input cannot be empty" in stderr.getvalue()
    assert stdout.getvalue() == ""


def test_run_writes_art_and_warning_for_invalid_font() -> None:
    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = run(
        "Test",
        font="missing_font",
        output_sink=ConsoleOutputSink(stdout),
        error_stream=stderr,
    )

    assert exit_code == 0
    assert len(stdout.getvalue().strip()) > 0
    assert "Warning: Font 'missing_font'" in stderr.getvalue()

"""Tests for the ASCII art generator."""

from __future__ import annotations

import pathlib
import subprocess
import sys

import pytest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_PATH))

from ascii_art import generate_ascii_art  # noqa: E402


def test_generate_ascii_art_for_valid_input() -> None:
    """A known valid input should render to the expected block font."""
    expected = " ###\n#   #\n#####\n#   #\n#   #"
    assert generate_ascii_art("A") == expected


def test_generate_ascii_art_handles_lowercase_as_uppercase() -> None:
    """Lowercase text should be represented in the same standard block font."""
    assert generate_ascii_art("a") == generate_ascii_art("A")


def test_empty_input_raises_clear_error() -> None:
    """Empty input should be rejected with a clear message."""
    with pytest.raises(ValueError, match="Input cannot be empty"):
        generate_ascii_art("")


def test_non_printable_input_raises_clear_error() -> None:
    """Non-printable characters should be rejected with a clear message."""
    with pytest.raises(ValueError, match="invalid non-printable"):
        generate_ascii_art("Hello\nWorld")


def test_long_input_wraps_to_avoid_console_overflow() -> None:
    """Long text should render as multiple art blocks within the target width."""
    art = generate_ascii_art("HELLO WORLD", max_width=30)
    assert "\n\n" in art
    for line in art.splitlines():
        assert len(line) <= 30


def test_output_contains_only_ascii_characters() -> None:
    """ASCII art output should contain ASCII characters only."""
    art = generate_ascii_art("Hi! @")
    assert all(ord(char) < 128 for char in art)


def test_cli_prints_art_to_stdout() -> None:
    """The command-line script should print generated art to stdout."""
    result = subprocess.run(
        [sys.executable, str(SRC_PATH / "main.py"), "A"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout.rstrip("\n") == generate_ascii_art("A")
    assert result.stderr == ""


def test_cli_reports_validation_errors() -> None:
    """The command-line script should report validation errors on stderr."""
    result = subprocess.run(
        [sys.executable, str(SRC_PATH / "main.py"), ""],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "Input cannot be empty" in result.stderr

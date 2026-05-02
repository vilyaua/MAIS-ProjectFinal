"""Tests for password generation utilities and CLI."""

from __future__ import annotations

import re
import string
import subprocess
import sys
from pathlib import Path

import pytest

from src.password_generator import (
    MAX_LENGTH,
    MIN_LENGTH,
    SPECIAL_CHARACTERS,
    CharacterOptions,
    PasswordGeneratorError,
    Strength,
    detect_character_variety,
    evaluate_strength,
    generate_password,
)

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "src" / "main.py"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the CLI and capture its output."""
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )


def test_generate_password_matches_length_and_selected_composition() -> None:
    options = CharacterOptions(uppercase=True, lowercase=True, digits=True, special=True)

    password = generate_password(32, options)

    assert len(password) == 32
    assert any(character in string.ascii_uppercase for character in password)
    assert any(character in string.ascii_lowercase for character in password)
    assert any(character in string.digits for character in password)
    assert any(character in SPECIAL_CHARACTERS for character in password)
    assert all(
        character in string.ascii_letters + string.digits + SPECIAL_CHARACTERS
        for character in password
    )


@pytest.mark.parametrize("length", [-1, 0, MIN_LENGTH - 1, MAX_LENGTH + 1])
def test_generate_password_rejects_invalid_lengths(length: int) -> None:
    with pytest.raises(PasswordGeneratorError, match="Length must be between"):
        generate_password(length, CharacterOptions(lowercase=True))


def test_generate_password_rejects_no_character_types() -> None:
    with pytest.raises(PasswordGeneratorError, match="At least one character type"):
        generate_password(MIN_LENGTH, CharacterOptions())


@pytest.mark.parametrize(
    ("password", "expected"),
    [
        ("aaaaaaaa", Strength.WEAK),
        ("Abcdef1234", Strength.MODERATE),
        ("Abcdefgh123456!", Strength.STRONG),
    ],
)
def test_evaluate_strength_predefined_rules(password: str, expected: Strength) -> None:
    assert evaluate_strength(password) == expected


def test_edge_case_minimum_length_only_one_character_type() -> None:
    password = generate_password(MIN_LENGTH, CharacterOptions(digits=True))

    assert len(password) == MIN_LENGTH
    assert password.isdigit()
    assert detect_character_variety(password) == 1
    assert evaluate_strength(password) == Strength.WEAK


def test_edge_case_maximum_length() -> None:
    password = generate_password(MAX_LENGTH, CharacterOptions(lowercase=True, digits=True))

    assert len(password) == MAX_LENGTH
    assert all(character in string.ascii_lowercase + string.digits for character in password)
    assert any(character in string.ascii_lowercase for character in password)
    assert any(character in string.digits for character in password)


def test_cli_valid_output_contains_password_and_strength() -> None:
    result = run_cli(
        "--length",
        "16",
        "--uppercase",
        "--lowercase",
        "--digits",
        "--special",
    )

    assert result.returncode == 0
    assert re.search(r"Generated password: .{16}\n", result.stdout)
    assert re.search(r"Strength: (Weak|Moderate|Strong)\n", result.stdout)
    assert result.stderr == ""


def test_cli_invalid_length_outputs_error_and_no_password() -> None:
    result = run_cli("--length", "0", "--lowercase")

    assert result.returncode != 0
    assert "length must be between" in result.stderr
    assert "usage:" in result.stderr.lower()
    assert "Generated password:" not in result.stdout


def test_cli_no_character_types_outputs_error() -> None:
    result = run_cli("--length", "12")

    assert result.returncode != 0
    assert "At least one character type" in result.stderr
    assert "usage:" in result.stderr.lower()
    assert "Generated password:" not in result.stdout


def test_cli_help_displays_usage() -> None:
    result = run_cli("--help")

    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()
    assert "--length" in result.stdout


def test_cli_invalid_option_displays_usage() -> None:
    result = run_cli("--unknown")

    assert result.returncode != 0
    assert "usage:" in result.stderr.lower()
    assert "unrecognized arguments" in result.stderr

"""Tests for password generation and strength evaluation."""

from __future__ import annotations

import re
import string
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from password_generator import (  # noqa: E402
    SPECIAL_CHARACTERS,
    CharacterSelection,
    PasswordError,
    Strength,
    evaluate_strength,
    format_strength_meter,
    generate_password,
)


def has_any(password: str, characters: str) -> bool:
    """Return whether a password contains any character in a set."""
    return any(character in characters for character in password)


def test_generate_password_contains_all_selected_character_types() -> None:
    """Generated password contains at least one character from every selected type."""
    password = generate_password(
        20,
        CharacterSelection(
            uppercase=True,
            lowercase=True,
            digits=True,
            special=True,
        ),
    )

    assert len(password) == 20
    assert has_any(password, string.ascii_uppercase)
    assert has_any(password, string.ascii_lowercase)
    assert has_any(password, string.digits)
    assert has_any(password, SPECIAL_CHARACTERS)


def test_length_less_than_selected_types_raises_error() -> None:
    """Length shorter than selected character type count is invalid."""
    with pytest.raises(PasswordError, match="too short"):
        generate_password(
            3,
            CharacterSelection(
                uppercase=True,
                lowercase=True,
                digits=True,
                special=True,
            ),
        )


@pytest.mark.parametrize("length", [0, -1, -12])
def test_non_positive_length_raises_error(length: int) -> None:
    """Zero and negative lengths are invalid."""
    with pytest.raises(PasswordError, match="positive integer"):
        generate_password(length, CharacterSelection(lowercase=True))


def test_non_integer_cli_length_displays_validation_error() -> None:
    """Argparse reports an error for non-integer length input."""
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "src" / "main.py"),
            "--length",
            "abc",
            "--lowercase",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "invalid int value" in result.stderr


def test_no_character_types_selected_raises_error() -> None:
    """At least one character type must be selected."""
    with pytest.raises(PasswordError, match="At least one character type"):
        generate_password(12, CharacterSelection())


@pytest.mark.parametrize(
    ("password", "expected"),
    [
        ("abc", Strength.WEAK),
        ("abcdefgh", Strength.WEAK),
        ("abcd1234", Strength.MEDIUM),
        ("Abcd1234!xyz", Strength.STRONG),
    ],
)
def test_evaluate_strength_uses_predefined_criteria(
    password: str, expected: Strength
) -> None:
    """Strength meter classification follows documented criteria."""
    assert evaluate_strength(password) == expected


def test_format_strength_meter_is_clear() -> None:
    """Strength meter includes both visual bars and strength text."""
    assert format_strength_meter(Strength.STRONG) == "[███] strong"


def test_cli_outputs_password_and_strength_meter_clearly() -> None:
    """Successful CLI run prints generated password and strength meter."""
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "src" / "main.py"),
            "--length",
            "16",
            "--uppercase",
            "--lowercase",
            "--digits",
            "--special",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert re.search(r"Generated password: .{16}", result.stdout)
    assert "Strength meter:" in result.stdout

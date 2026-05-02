"""Tests for password generation and strength evaluation."""

from __future__ import annotations

import re
import string

import pytest

from src.password_generator import (
    MAX_LENGTH,
    MIN_LENGTH,
    SPECIAL_CHARACTERS,
    CharacterSetConfig,
    PasswordStrength,
    evaluate_strength,
    generate_password,
)


def test_length_12_all_sets_enabled_includes_every_category() -> None:
    password = generate_password(12, CharacterSetConfig())

    assert len(password) == 12
    assert any(char.isupper() for char in password)
    assert any(char.islower() for char in password)
    assert any(char.isdigit() for char in password)
    assert any(char in SPECIAL_CHARACTERS for char in password)


def test_invalid_length_low_and_high_return_clear_errors() -> None:
    for invalid_length in (0, 200):
        with pytest.raises(ValueError, match=f"between {MIN_LENGTH} and {MAX_LENGTH}"):
            generate_password(invalid_length, CharacterSetConfig())


def test_no_character_set_enabled_returns_clear_error() -> None:
    config = CharacterSetConfig(
        uppercase=False,
        lowercase=False,
        digits=False,
        special=False,
    )

    with pytest.raises(ValueError, match="At least one character set"):
        generate_password(12, config)


def test_strength_meter_categories_are_consistent() -> None:
    assert evaluate_strength("abc") == PasswordStrength.WEAK
    assert evaluate_strength("Abcdef12") == PasswordStrength.MODERATE
    assert evaluate_strength("T9$vQ2@mL8#p") == PasswordStrength.STRONG


def test_minimum_length_one_lowercase_only() -> None:
    password = generate_password(
        1,
        CharacterSetConfig(
            uppercase=False,
            lowercase=True,
            digits=False,
            special=False,
        ),
    )

    assert len(password) == 1
    assert password in string.ascii_lowercase


def test_maximum_length_generation_has_valid_length() -> None:
    password = generate_password(MAX_LENGTH, CharacterSetConfig())

    assert len(password) == MAX_LENGTH


@pytest.mark.parametrize(
    ("config", "allowed_pattern"),
    [
        (
            CharacterSetConfig(True, False, False, False),
            rf"^[{re.escape(string.ascii_uppercase)}]+$",
        ),
        (
            CharacterSetConfig(False, True, False, False),
            rf"^[{re.escape(string.ascii_lowercase)}]+$",
        ),
        (
            CharacterSetConfig(False, False, True, False),
            rf"^[{re.escape(string.digits)}]+$",
        ),
        (
            CharacterSetConfig(False, False, False, True),
            rf"^[{re.escape(SPECIAL_CHARACTERS)}]+$",
        ),
        (
            CharacterSetConfig(True, True, False, False),
            rf"^[{re.escape(string.ascii_letters)}]+$",
        ),
    ],
)
def test_character_set_combinations_only_use_allowed_characters(
    config: CharacterSetConfig,
    allowed_pattern: str,
) -> None:
    password = generate_password(32, config)

    assert re.fullmatch(allowed_pattern, password)

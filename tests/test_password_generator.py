"""Tests for password generation and strength evaluation."""

from __future__ import annotations

import string

import pytest

from src.password_generator import (
    CharacterSetOptions,
    PasswordError,
    StrengthRating,
    build_character_pool,
    character_variety,
    evaluate_strength,
    generate_password,
    parse_positive_length,
)


def test_parse_positive_length_accepts_positive_integer() -> None:
    assert parse_positive_length("12") == 12


@pytest.mark.parametrize("value", ["0", "-1", "abc", "1.5", ""])
def test_parse_positive_length_rejects_invalid_values(value: str) -> None:
    with pytest.raises(PasswordError):
        parse_positive_length(value)


def test_build_character_pool_rejects_no_selection() -> None:
    with pytest.raises(PasswordError, match="Select at least one"):
        build_character_pool(
            CharacterSetOptions(
                uppercase=False, lowercase=False, digits=False, special=False
            )
        )


def test_generate_password_respects_length_and_selected_characters() -> None:
    options = CharacterSetOptions(
        uppercase=False, lowercase=True, digits=True, special=False
    )
    password = generate_password(32, options)
    allowed = set(string.ascii_lowercase + string.digits)

    assert len(password) == 32
    assert set(password).issubset(allowed)


def test_generate_password_rejects_invalid_length() -> None:
    with pytest.raises(PasswordError):
        generate_password(0, CharacterSetOptions())


def test_generated_passwords_vary_randomly() -> None:
    options = CharacterSetOptions()
    passwords = {generate_password(24, options) for _ in range(8)}

    assert len(passwords) > 1


def test_character_variety_counts_categories_present() -> None:
    assert character_variety("Ab1!") == 4
    assert character_variety("abcdef") == 1


@pytest.mark.parametrize(
    ("password", "expected"),
    [
        ("abc", StrengthRating.WEAK),
        ("abcdefgh", StrengthRating.MODERATE),
        ("Abcdef123!@#", StrengthRating.STRONG),
    ],
)
def test_evaluate_strength(password: str, expected: StrengthRating) -> None:
    assert evaluate_strength(password) == expected

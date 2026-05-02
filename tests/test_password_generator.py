"""Tests for password generation and strength evaluation."""

from __future__ import annotations

import string

import pytest

from src.password_generator import (
    CharacterOptions,
    PasswordGeneratorError,
    evaluate_strength,
    generate_password,
)


def test_generate_password_matches_length_and_enabled_criteria() -> None:
    options = CharacterOptions(
        uppercase=True,
        lowercase=False,
        digits=True,
        special=False,
    )

    password = generate_password(20, options)

    assert len(password) == 20
    assert all(char in string.ascii_uppercase + string.digits for char in password)
    assert any(char.isupper() for char in password)
    assert any(char.isdigit() for char in password)
    assert not any(char.islower() for char in password)
    assert not any(char in string.punctuation for char in password)


def test_generate_password_rejects_length_less_than_one() -> None:
    with pytest.raises(PasswordGeneratorError, match="at least"):
        generate_password(0, CharacterOptions())


def test_generate_password_rejects_all_character_types_excluded() -> None:
    options = CharacterOptions(
        uppercase=False,
        lowercase=False,
        digits=False,
        special=False,
    )

    with pytest.raises(PasswordGeneratorError, match="At least one"):
        generate_password(12, options)


@pytest.mark.parametrize(
    ("password", "expected"),
    [
        ("abc", "Very Weak"),
        ("abcdefgh", "Weak"),
        ("Abcdef12", "Moderate"),
        ("Abcdef123456!", "Strong"),
        ("Abcdef123456789!", "Very Strong"),
    ],
)
def test_evaluate_strength(password: str, expected: str) -> None:
    assert evaluate_strength(password) == expected


def test_generate_password_shorter_than_selected_type_count() -> None:
    password = generate_password(2, CharacterOptions())

    assert len(password) == 2
    assert all(
        char in string.ascii_uppercase
        + string.ascii_lowercase
        + string.digits
        + string.punctuation
        for char in password
    )

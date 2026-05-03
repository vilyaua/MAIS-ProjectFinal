"""Tests for password generation and strength evaluation."""

from __future__ import annotations

import random
import string

import pytest

from src.password_generator import (
    MAX_LENGTH,
    SPECIAL_CHARACTERS,
    PasswordGenerationError,
    PasswordOptions,
    character_variety_count,
    evaluate_strength,
    generate_password,
)


def test_generate_password_matches_valid_criteria() -> None:
    options = PasswordOptions(
        length=16,
        uppercase=True,
        lowercase=True,
        digits=True,
        special=True,
    )

    password = generate_password(options, rng=random.Random(1))

    assert len(password) == 16
    assert any(char in string.ascii_uppercase for char in password)
    assert any(char in string.ascii_lowercase for char in password)
    assert any(char in string.digits for char in password)
    assert any(char in SPECIAL_CHARACTERS for char in password)
    assert all(
        char in string.ascii_letters + string.digits + SPECIAL_CHARACTERS
        for char in password
    )


@pytest.mark.parametrize("length", [0, -1])
def test_rejects_non_positive_length(length: int) -> None:
    options = PasswordOptions(length=length, lowercase=True)

    with pytest.raises(PasswordGenerationError, match="positive integer"):
        generate_password(options)


def test_rejects_length_above_reasonable_range() -> None:
    options = PasswordOptions(length=MAX_LENGTH + 1, lowercase=True)

    with pytest.raises(PasswordGenerationError, match="between"):
        generate_password(options)


def test_rejects_no_character_types_selected() -> None:
    options = PasswordOptions(length=12)

    with pytest.raises(PasswordGenerationError, match="at least one character type"):
        generate_password(options)


def test_rejects_too_short_for_selected_character_types() -> None:
    options = PasswordOptions(
        length=2,
        uppercase=True,
        lowercase=True,
        digits=True,
    )

    with pytest.raises(PasswordGenerationError, match="selected character types"):
        generate_password(options)


def test_strength_meter_reflects_length_and_diversity() -> None:
    weak = evaluate_strength("aaaa")
    strong = evaluate_strength("Aa1!Aa1!Aa1!Aa1!")

    assert weak.rating == "Weak"
    assert weak.score < strong.score
    assert strong.score == 100
    assert strong.rating == "Very Strong"
    assert character_variety_count("Aa1!") == 4


def test_password_with_special_option_contains_special_character() -> None:
    options = PasswordOptions(length=8, lowercase=True, special=True)

    password = generate_password(options, rng=random.Random(3))

    assert any(char in SPECIAL_CHARACTERS for char in password)


def test_password_with_digits_option_contains_digit() -> None:
    options = PasswordOptions(length=8, lowercase=True, digits=True)

    password = generate_password(options, rng=random.Random(4))

    assert any(char.isdigit() for char in password)

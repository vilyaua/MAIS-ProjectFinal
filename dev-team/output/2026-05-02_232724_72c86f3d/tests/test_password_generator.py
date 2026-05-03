"""Tests for password generator core behavior."""

from __future__ import annotations

import string

import pytest
from src.password_generator import (
    CHARACTER_SETS,
    MAX_LENGTH,
    MIN_LENGTH,
    PasswordInputError,
    calculate_strength,
    generate_password,
    get_selected_character_sets,
    validate_length,
)


def test_validate_length_accepts_valid_integer() -> None:
    assert validate_length("8") == MIN_LENGTH
    assert validate_length(" 128 ") == MAX_LENGTH


@pytest.mark.parametrize("raw_value", ["", "abc", "7", "129", "10.5"])
def test_validate_length_rejects_invalid_values(raw_value: str) -> None:
    with pytest.raises(PasswordInputError):
        validate_length(raw_value)


def test_generate_password_matches_length_and_selected_characters() -> None:
    selected = get_selected_character_sets(
        uppercase=True,
        lowercase=True,
        digits=False,
        special=False,
    )

    password = generate_password(20, selected)

    assert len(password) == 20
    assert set(password) <= set(string.ascii_uppercase + string.ascii_lowercase)


def test_generate_password_includes_each_selected_set() -> None:
    selected = get_selected_character_sets(
        uppercase=True,
        lowercase=True,
        digits=True,
        special=True,
    )

    password = generate_password(16, selected)

    assert any(char in CHARACTER_SETS["uppercase"] for char in password)
    assert any(char in CHARACTER_SETS["lowercase"] for char in password)
    assert any(char in CHARACTER_SETS["digits"] for char in password)
    assert any(char in CHARACTER_SETS["special"] for char in password)


def test_generate_password_rejects_no_character_sets() -> None:
    with pytest.raises(PasswordInputError, match="at least one character set"):
        generate_password(12, [])


def test_calculate_strength_reflects_complexity() -> None:
    weak = calculate_strength("aaaaaaaa")
    strong = calculate_strength("Aa1!Aa1!Aa1!Aa1!")

    assert weak.label in {"Very Weak", "Weak"}
    assert weak.character_variety == 1
    assert strong.score > weak.score
    assert strong.label in {"Strong", "Very Strong"}
    assert strong.character_variety == 4
    assert strong.entropy_bits > weak.entropy_bits


def test_generate_password_can_avoid_previous_passwords() -> None:
    selected = ["A"]
    first = generate_password(8, selected)

    with pytest.raises(PasswordInputError, match="Unable to generate a unique"):
        generate_password(8, selected, avoid_passwords={first})


def test_repeated_generation_produces_unique_passwords_in_normal_use() -> None:
    selected = get_selected_character_sets(
        uppercase=True,
        lowercase=True,
        digits=True,
        special=True,
    )
    seen: set[str] = set()

    for _ in range(10):
        password = generate_password(16, selected, avoid_passwords=seen)
        assert password not in seen
        seen.add(password)

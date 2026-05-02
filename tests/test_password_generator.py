"""Tests for password generation utilities."""

from __future__ import annotations

import string

import pytest

from password_generator import (
    CHARACTER_SETS,
    MAX_LENGTH,
    MIN_LENGTH,
    PasswordGeneratorError,
    PasswordOptions,
    StrengthLabel,
    calculate_strength,
    generate_password,
    validate_length,
)


ALL_CHARACTERS = set("".join(CHARACTER_SETS.values()))


def test_generate_password_has_requested_length_and_selected_categories() -> None:
    options = PasswordOptions(
        length=16,
        uppercase=True,
        lowercase=False,
        digits=True,
        special=False,
    )

    password = generate_password(options)

    assert len(password) == 16
    assert set(password).issubset(set(string.ascii_uppercase + string.digits))
    assert any(character in string.ascii_uppercase for character in password)
    assert any(character in string.digits for character in password)
    assert not any(character in string.ascii_lowercase for character in password)


@pytest.mark.parametrize("bad_length", [0, 7, 129, 1000])
def test_validate_length_rejects_out_of_range_values(bad_length: int) -> None:
    with pytest.raises(PasswordGeneratorError, match="between"):
        validate_length(bad_length)


def test_generate_password_rejects_no_character_types() -> None:
    options = PasswordOptions(
        length=12,
        uppercase=False,
        lowercase=False,
        digits=False,
        special=False,
    )

    with pytest.raises(PasswordGeneratorError, match="At least one"):
        generate_password(options)


def test_strength_meter_reflects_length_and_variety() -> None:
    weak = calculate_strength("aaaaaaaa")
    strong = calculate_strength("Aa1!" * 8)

    assert weak.score < strong.score
    assert weak.label in {StrengthLabel.VERY_WEAK, StrengthLabel.WEAK}
    assert strong.variety_count == 4
    assert strong.bar.startswith("[") and strong.bar.endswith("]")


def test_repeated_generation_is_random() -> None:
    options = PasswordOptions(length=24)
    passwords = {generate_password(options) for _ in range(5)}

    assert len(passwords) > 1


def test_generates_maximum_length_without_truncation() -> None:
    password = generate_password(PasswordOptions(length=MAX_LENGTH))

    assert len(password) == MAX_LENGTH
    assert set(password).issubset(ALL_CHARACTERS)


def test_boundary_minimum_length_is_allowed() -> None:
    password = generate_password(PasswordOptions(length=MIN_LENGTH))

    assert len(password) == MIN_LENGTH

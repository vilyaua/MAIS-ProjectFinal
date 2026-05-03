"""Tests for password generation and strength evaluation."""

from __future__ import annotations

import string

import pytest
from src.password_generator import (
    CharacterOptions,
    PasswordGeneratorError,
    StrengthRating,
    build_character_pool,
    count_character_variety,
    evaluate_strength,
    generate_password,
)


def test_generate_password_uses_requested_length_and_charset() -> None:
    options = CharacterOptions(
        uppercase=False,
        lowercase=True,
        digits=True,
        special=False,
    )

    password = generate_password(32, options)
    allowed = set(string.ascii_lowercase + string.digits)

    assert len(password) == 32
    assert set(password).issubset(allowed)
    assert any(char.islower() for char in password)
    assert any(char.isdigit() for char in password)


def test_generate_password_rejects_length_less_than_one() -> None:
    with pytest.raises(PasswordGeneratorError, match="at least 1"):
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
    ("password", "expected_rating"),
    [
        ("abc", StrengthRating.WEAK),
        ("abcdefgh1", StrengthRating.MODERATE),
        ("Abcdefgh123!@#$%", StrengthRating.STRONG),
    ],
)
def test_evaluate_strength_outputs_expected_rating(
    password: str,
    expected_rating: StrengthRating,
) -> None:
    result = evaluate_strength(password)

    assert result.rating == expected_rating
    assert 0 <= result.score <= result.max_score
    assert "total=" in result.details


def test_count_character_variety_detects_all_categories() -> None:
    assert count_character_variety("Aa1!") == 4


def test_build_character_pool_requires_at_least_one_type() -> None:
    options = CharacterOptions(False, False, False, False)

    with pytest.raises(PasswordGeneratorError, match="At least one"):
        build_character_pool(options)

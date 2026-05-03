"""Tests for password generation and strength evaluation."""

from __future__ import annotations

import re
import string

import pytest
from src.main import main
from src.password_generator import (
    CharacterOptions,
    PasswordGeneratorError,
    StrengthCategory,
    character_variety_count,
    evaluate_strength,
    generate_password,
    parse_length,
)

SPECIAL_CHARS = "!@#$%^&*()-_=+[]{};:,.<>?/"


def assert_chars_from_pool(password: str, pool: str) -> None:
    assert all(char in pool for char in password)


def test_generate_password_matches_selected_criteria() -> None:
    options = CharacterOptions(
        uppercase=True,
        lowercase=False,
        digits=True,
        special=False,
    )

    password = generate_password(20, options)

    assert len(password) == 20
    assert_chars_from_pool(password, string.ascii_uppercase + string.digits)
    assert any(char in string.ascii_uppercase for char in password)
    assert any(char in string.digits for char in password)
    assert not any(char in string.ascii_lowercase for char in password)
    assert not any(char in SPECIAL_CHARS for char in password)


@pytest.mark.parametrize("invalid_length", ["0", "-1", "257", "abc", "1.5", ""])
def test_invalid_length_returns_clear_error(invalid_length: str) -> None:
    with pytest.raises(PasswordGeneratorError, match="Length must"):
        parse_length(invalid_length)


def test_no_character_types_selected_returns_error() -> None:
    options = CharacterOptions(False, False, False, False)

    with pytest.raises(PasswordGeneratorError, match="At least one character type"):
        generate_password(12, options)


def test_strength_meter_categories() -> None:
    weak, weak_score = evaluate_strength("abc")
    moderate, moderate_score = evaluate_strength("abcd1234")
    strong, strong_score = evaluate_strength("Abcd1234!XyZ")

    assert weak is StrengthCategory.WEAK
    assert moderate is StrengthCategory.MODERATE
    assert strong is StrengthCategory.STRONG
    assert weak_score < moderate_score < strong_score


def test_character_variety_count() -> None:
    assert character_variety_count("abc") == 1
    assert character_variety_count("abc123") == 2
    assert character_variety_count("Abc123!") == 4


def test_multiple_generated_passwords_are_valid_and_random() -> None:
    options = CharacterOptions(True, True, True, True)
    passwords = {generate_password(16, options) for _ in range(20)}

    assert len(passwords) > 1
    for password in passwords:
        assert len(password) == 16
        assert any(char in string.ascii_uppercase for char in password)
        assert any(char in string.ascii_lowercase for char in password)
        assert any(char in string.digits for char in password)
        assert any(char in SPECIAL_CHARS for char in password)


def test_short_password_with_many_selected_groups_still_valid() -> None:
    password = generate_password(2, CharacterOptions(True, True, True, True))

    assert len(password) == 2
    assert_chars_from_pool(
        password,
        string.ascii_uppercase + string.ascii_lowercase + string.digits + SPECIAL_CHARS,
    )


def test_cli_outputs_password_and_strength(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["--length", "12", "--no-special"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert re.search(r"Password: .{12}\n", captured.out)
    assert re.search(r"Strength: (weak|moderate|strong) \(\d+/100\)", captured.out)


def test_cli_errors_when_no_character_types_selected(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(
            [
                "--length",
                "12",
                "--no-uppercase",
                "--no-lowercase",
                "--no-digits",
                "--no-special",
            ]
        )

    captured = capsys.readouterr()
    assert exc_info.value.code == 2
    assert "At least one character type must be selected" in captured.err

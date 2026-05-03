"""Secure password generation and strength scoring utilities."""

from __future__ import annotations

import secrets
import string
from dataclasses import dataclass
from enum import Enum

MIN_LENGTH = 8
MAX_LENGTH = 128

CHARACTER_SETS: dict[str, str] = {
    "uppercase": string.ascii_uppercase,
    "lowercase": string.ascii_lowercase,
    "digits": string.digits,
    "special": "!@#$%^&*()-_=+[]{};:,.<>?/|~",
}


class PasswordGeneratorError(ValueError):
    """Raised when password generation options are invalid."""


class StrengthLabel(str, Enum):
    """Human-friendly password strength labels."""

    VERY_WEAK = "Very Weak"
    WEAK = "Weak"
    FAIR = "Fair"
    GOOD = "Good"
    STRONG = "Strong"
    VERY_STRONG = "Very Strong"


@dataclass(frozen=True)
class PasswordOptions:
    """Options controlling password generation."""

    length: int
    uppercase: bool = True
    lowercase: bool = True
    digits: bool = True
    special: bool = True

    def selected_categories(self) -> list[str]:
        """Return names of enabled character categories."""
        categories: list[str] = []
        if self.uppercase:
            categories.append("uppercase")
        if self.lowercase:
            categories.append("lowercase")
        if self.digits:
            categories.append("digits")
        if self.special:
            categories.append("special")
        return categories


@dataclass(frozen=True)
class StrengthResult:
    """Calculated password strength details."""

    score: int
    label: StrengthLabel
    bar: str
    variety_count: int


def validate_length(length: int) -> None:
    """Validate a password length, raising a clear error when invalid."""
    if not isinstance(length, int):
        raise PasswordGeneratorError("Length must be an integer.")
    if length < MIN_LENGTH or length > MAX_LENGTH:
        raise PasswordGeneratorError(f"Length must be between {MIN_LENGTH} and {MAX_LENGTH}.")


def validate_options(options: PasswordOptions) -> None:
    """Validate password generation options."""
    validate_length(options.length)
    categories = options.selected_categories()
    if not categories:
        raise PasswordGeneratorError("At least one character type must be chosen.")
    if options.length < len(categories):
        raise PasswordGeneratorError(
            "Length is too short to include every selected character type."
        )


def generate_password(options: PasswordOptions) -> str:
    """Generate a secure random password for the given options.

    The password contains only enabled character categories. When multiple
    categories are enabled, at least one character from each category is
    included so that the generated password reflects the requested composition.
    """
    validate_options(options)

    categories = options.selected_categories()
    selected_sets = [CHARACTER_SETS[category] for category in categories]
    all_allowed_characters = "".join(selected_sets)

    password_characters = [secrets.choice(chars) for chars in selected_sets]
    remaining_length = options.length - len(password_characters)
    password_characters.extend(
        secrets.choice(all_allowed_characters) for _ in range(remaining_length)
    )

    secrets.SystemRandom().shuffle(password_characters)
    return "".join(password_characters)


def get_character_variety(password: str) -> int:
    """Count how many supported character categories appear in a password."""
    return sum(
        1
        for character_set in CHARACTER_SETS.values()
        if any(character in character_set for character in password)
    )


def calculate_strength(password: str) -> StrengthResult:
    """Calculate a simple strength score based on length and character variety."""
    length = len(password)
    variety_count = get_character_variety(password)

    length_score = min(50, int((length / MAX_LENGTH) * 50))
    if length >= 8:
        length_score = max(length_score, 15)
    if length >= 12:
        length_score = max(length_score, 25)
    if length >= 16:
        length_score = max(length_score, 35)
    if length >= 24:
        length_score = max(length_score, 45)

    variety_score = variety_count * 12
    bonus = 2 if length >= 12 and variety_count >= 3 else 0
    score = min(100, length_score + variety_score + bonus)

    if score < 25:
        label = StrengthLabel.VERY_WEAK
    elif score < 45:
        label = StrengthLabel.WEAK
    elif score < 65:
        label = StrengthLabel.FAIR
    elif score < 80:
        label = StrengthLabel.GOOD
    elif score < 95:
        label = StrengthLabel.STRONG
    else:
        label = StrengthLabel.VERY_STRONG

    filled_blocks = score // 10
    bar = "[" + "#" * filled_blocks + "-" * (10 - filled_blocks) + "]"
    return StrengthResult(
        score=score,
        label=label,
        bar=bar,
        variety_count=variety_count,
    )

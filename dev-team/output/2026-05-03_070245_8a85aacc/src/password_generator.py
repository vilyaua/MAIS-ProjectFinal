"""Password generation and strength evaluation utilities."""

from __future__ import annotations

import secrets
import string
from dataclasses import dataclass
from enum import Enum


class PasswordGeneratorError(ValueError):
    """Raised when password generation inputs are invalid."""


class StrengthRating(str, Enum):
    """Supported password strength ratings."""

    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"


@dataclass(frozen=True)
class CharacterOptions:
    """Character category switches for password generation."""

    uppercase: bool = True
    lowercase: bool = True
    digits: bool = True
    special: bool = True

    def selected_sets(self) -> list[str]:
        """Return the character sets enabled by the options."""
        sets: list[str] = []
        if self.uppercase:
            sets.append(string.ascii_uppercase)
        if self.lowercase:
            sets.append(string.ascii_lowercase)
        if self.digits:
            sets.append(string.digits)
        if self.special:
            sets.append(string.punctuation)
        return sets

    def selected_count(self) -> int:
        """Return how many character categories are enabled."""
        return len(self.selected_sets())


@dataclass(frozen=True)
class StrengthResult:
    """Password strength evaluation result."""

    rating: StrengthRating
    score: int
    max_score: int
    details: str


MIN_PASSWORD_LENGTH = 1


def validate_length(length: int) -> None:
    """Validate a requested password length.

    Args:
        length: Requested password length.

    Raises:
        PasswordGeneratorError: If the length is below the minimum allowed.
    """
    if length < MIN_PASSWORD_LENGTH:
        raise PasswordGeneratorError(f"Password length must be at least {MIN_PASSWORD_LENGTH}.")


def build_character_pool(options: CharacterOptions) -> str:
    """Build a single character pool from selected character options.

    Args:
        options: Selected character categories.

    Returns:
        Concatenated character pool.

    Raises:
        PasswordGeneratorError: If no character categories are selected.
    """
    selected_sets = options.selected_sets()
    if not selected_sets:
        raise PasswordGeneratorError("At least one character type must be selected.")
    return "".join(selected_sets)


def generate_password(length: int, options: CharacterOptions) -> str:
    """Generate a cryptographically secure random password.

    The generated password uses only the selected character categories. When the
    requested length is at least the number of selected categories, the password
    is guaranteed to contain at least one character from each selected category.

    Args:
        length: Desired password length.
        options: Character categories to include.

    Returns:
        Generated password.

    Raises:
        PasswordGeneratorError: If length or character options are invalid.
    """
    validate_length(length)
    selected_sets = options.selected_sets()
    if not selected_sets:
        raise PasswordGeneratorError("At least one character type must be selected.")

    password_chars: list[str] = []
    if length >= len(selected_sets):
        password_chars.extend(secrets.choice(char_set) for char_set in selected_sets)

    pool = "".join(selected_sets)
    remaining = length - len(password_chars)
    password_chars.extend(secrets.choice(pool) for _ in range(remaining))

    secrets.SystemRandom().shuffle(password_chars)
    return "".join(password_chars)


def count_character_variety(password: str) -> int:
    """Count how many character categories are present in a password."""
    variety = 0
    if any(char.isupper() for char in password):
        variety += 1
    if any(char.islower() for char in password):
        variety += 1
    if any(char.isdigit() for char in password):
        variety += 1
    if any(char in string.punctuation for char in password):
        variety += 1
    return variety


def evaluate_strength(password: str) -> StrengthResult:
    """Evaluate password strength from length and character variety.

    Scoring uses up to four points for length and up to four points for variety:
    - length: 1 point for 1-7 chars, 2 for 8-11, 3 for 12-15, 4 for 16+
    - variety: 1 point for each present category (upper/lower/digit/special)

    Ratings:
    - weak: score 0-3
    - moderate: score 4-6
    - strong: score 7-8
    """
    length = len(password)
    variety = count_character_variety(password)

    if length == 0:
        length_score = 0
    elif length < 8:
        length_score = 1
    elif length < 12:
        length_score = 2
    elif length < 16:
        length_score = 3
    else:
        length_score = 4

    score = length_score + variety
    if score >= 7:
        rating = StrengthRating.STRONG
    elif score >= 4:
        rating = StrengthRating.MODERATE
    else:
        rating = StrengthRating.WEAK

    details = f"length={length} (score {length_score}/4), variety={variety}/4, total={score}/8"
    return StrengthResult(rating=rating, score=score, max_score=8, details=details)

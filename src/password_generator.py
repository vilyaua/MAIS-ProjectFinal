"""Password generation and strength evaluation utilities."""

from __future__ import annotations

import math
import secrets
import string
from dataclasses import dataclass
from enum import Enum
from typing import Sequence


MIN_PASSWORD_LENGTH = 1
MAX_PASSWORD_LENGTH = 256


class PasswordGeneratorError(ValueError):
    """Raised when password generator inputs are invalid."""


class StrengthCategory(str, Enum):
    """Human-readable password strength categories."""

    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"


@dataclass(frozen=True)
class CharacterOptions:
    """Character type selections for generated passwords."""

    uppercase: bool = True
    lowercase: bool = True
    digits: bool = True
    special: bool = True

    def selected_sets(self) -> list[str]:
        """Return all enabled character sets."""
        sets: list[str] = []
        if self.uppercase:
            sets.append(string.ascii_uppercase)
        if self.lowercase:
            sets.append(string.ascii_lowercase)
        if self.digits:
            sets.append(string.digits)
        if self.special:
            sets.append("!@#$%^&*()-_=+[]{};:,.<>?/")
        return sets

    def selected_count(self) -> int:
        """Return the number of enabled character type groups."""
        return len(self.selected_sets())


def parse_length(raw_length: str | int) -> int:
    """Parse and validate a password length value.

    Args:
        raw_length: User-provided length as a string or integer.

    Returns:
        A validated integer length.

    Raises:
        PasswordGeneratorError: If the value is not an integer in range.
    """
    try:
        length = int(raw_length)
    except (TypeError, ValueError) as exc:
        raise PasswordGeneratorError(
            "Length must be a positive integer."
        ) from exc

    if isinstance(raw_length, str) and raw_length.strip() != str(length):
        raise PasswordGeneratorError("Length must be a positive integer.")

    if length < MIN_PASSWORD_LENGTH or length > MAX_PASSWORD_LENGTH:
        raise PasswordGeneratorError(
            f"Length must be between {MIN_PASSWORD_LENGTH} and "
            f"{MAX_PASSWORD_LENGTH}."
        )
    return length


def validate_options(options: CharacterOptions) -> None:
    """Validate that at least one character type was selected."""
    if not options.selected_sets():
        raise PasswordGeneratorError(
            "At least one character type must be selected."
        )


def build_character_pool(options: CharacterOptions) -> str:
    """Build a combined character pool from selected options."""
    validate_options(options)
    return "".join(options.selected_sets())


def generate_password(length: int | str, options: CharacterOptions) -> str:
    """Generate a password matching the requested length and options.

    The generator guarantees that each selected character type appears at least
    once when the requested length is large enough. If the length is smaller
    than the number of selected groups, every character still comes from the
    selected groups, but not every group can be represented.
    """
    validated_length = parse_length(length)
    selected_sets = options.selected_sets()
    validate_options(options)
    pool = "".join(selected_sets)

    password_chars: list[str] = []
    if validated_length >= len(selected_sets):
        password_chars.extend(secrets.choice(char_set) for char_set in selected_sets)

    remaining = validated_length - len(password_chars)
    password_chars.extend(secrets.choice(pool) for _ in range(remaining))

    secrets.SystemRandom().shuffle(password_chars)
    return "".join(password_chars)


def _contains_any(password: str, characters: Sequence[str]) -> bool:
    return any(char in characters for char in password)


def character_variety_count(password: str) -> int:
    """Count the character type groups present in a password."""
    count = 0
    if _contains_any(password, string.ascii_uppercase):
        count += 1
    if _contains_any(password, string.ascii_lowercase):
        count += 1
    if _contains_any(password, string.digits):
        count += 1
    if _contains_any(password, "!@#$%^&*()-_=+[]{};:,.<>?/"):
        count += 1
    return count


def estimate_entropy_bits(password: str) -> float:
    """Estimate password entropy from observed character variety and length."""
    if not password:
        return 0.0

    pool_size = 0
    if _contains_any(password, string.ascii_uppercase):
        pool_size += len(string.ascii_uppercase)
    if _contains_any(password, string.ascii_lowercase):
        pool_size += len(string.ascii_lowercase)
    if _contains_any(password, string.digits):
        pool_size += len(string.digits)
    if _contains_any(password, "!@#$%^&*()-_=+[]{};:,.<>?/"):
        pool_size += len("!@#$%^&*()-_=+[]{};:,.<>?/")

    if pool_size == 0:
        pool_size = len(set(password))
    return len(password) * math.log2(max(pool_size, 1))


def strength_score(password: str) -> int:
    """Calculate a 0-100 password strength score.

    The score considers length, observed character variety, estimated entropy,
    and simple repetition penalties.
    """
    if not password:
        return 0

    length_points = min(len(password) * 3, 40)
    variety_points = character_variety_count(password) * 10
    entropy_points = min(int(estimate_entropy_bits(password) / 2), 20)
    unique_ratio = len(set(password)) / len(password)
    repetition_points = int(unique_ratio * 10)

    score = length_points + variety_points + entropy_points + repetition_points
    return max(0, min(score, 100))


def evaluate_strength(password: str) -> tuple[StrengthCategory, int]:
    """Evaluate a password as weak, moderate, or strong with a score."""
    score = strength_score(password)
    variety = character_variety_count(password)

    if score >= 75 and len(password) >= 12 and variety >= 3:
        return StrengthCategory.STRONG, score
    if score >= 45 and len(password) >= 8 and variety >= 2:
        return StrengthCategory.MODERATE, score
    return StrengthCategory.WEAK, score

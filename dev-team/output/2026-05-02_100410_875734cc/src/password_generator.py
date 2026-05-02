"""Password generation and strength evaluation utilities."""

from __future__ import annotations

import secrets
import string
from dataclasses import dataclass
from enum import Enum


class PasswordError(ValueError):
    """Raised when password generation inputs are invalid."""


class Strength(str, Enum):
    """Supported password strength levels."""

    WEAK = "weak"
    MEDIUM = "medium"
    STRONG = "strong"


@dataclass(frozen=True)
class CharacterSelection:
    """Character type selection for password generation."""

    uppercase: bool = False
    lowercase: bool = False
    digits: bool = False
    special: bool = False

    def selected_sets(self) -> list[str]:
        """Return the character sets selected by the user."""
        sets: list[str] = []
        if self.uppercase:
            sets.append(string.ascii_uppercase)
        if self.lowercase:
            sets.append(string.ascii_lowercase)
        if self.digits:
            sets.append(string.digits)
        if self.special:
            sets.append(SPECIAL_CHARACTERS)
        return sets

    def selected_count(self) -> int:
        """Return the number of selected character types."""
        return len(self.selected_sets())


SPECIAL_CHARACTERS = "!@#$%^&*()-_=+[]{};:,.<>?/|~"


def validate_length(length: int) -> None:
    """Validate that a password length is a positive integer."""
    if not isinstance(length, int):
        raise PasswordError("Password length must be an integer.")
    if length <= 0:
        raise PasswordError("Password length must be a positive integer.")


def validate_generation_options(length: int, selection: CharacterSelection) -> None:
    """Validate generation options and raise PasswordError on invalid input."""
    validate_length(length)
    selected_count = selection.selected_count()
    if selected_count == 0:
        raise PasswordError("At least one character type must be selected.")
    if length < selected_count:
        raise PasswordError(
            "Password length is too short for the selected character types: "
            f"length {length} was provided, but at least {selected_count} "
            "characters are required."
        )


def generate_password(length: int, selection: CharacterSelection) -> str:
    """Generate a password containing at least one character from each selected type."""
    validate_generation_options(length, selection)

    selected_sets = selection.selected_sets()
    required_characters = [secrets.choice(charset) for charset in selected_sets]
    all_characters = "".join(selected_sets)
    remaining_count = length - len(required_characters)
    remaining_characters = [secrets.choice(all_characters) for _ in range(remaining_count)]

    password_characters = required_characters + remaining_characters
    secrets.SystemRandom().shuffle(password_characters)
    return "".join(password_characters)


def character_type_count(password: str) -> int:
    """Count how many supported character types appear in a password."""
    count = 0
    if any(character in string.ascii_uppercase for character in password):
        count += 1
    if any(character in string.ascii_lowercase for character in password):
        count += 1
    if any(character in string.digits for character in password):
        count += 1
    if any(character in SPECIAL_CHARACTERS for character in password):
        count += 1
    return count


def evaluate_strength(password: str) -> Strength:
    """Evaluate password strength using length and character diversity.

    Criteria:
    - strong: length is at least 12 and includes at least 3 character types
    - medium: length is at least 8 and includes at least 2 character types
    - weak: anything below the medium threshold
    """
    diversity = character_type_count(password)
    length = len(password)

    if length >= 12 and diversity >= 3:
        return Strength.STRONG
    if length >= 8 and diversity >= 2:
        return Strength.MEDIUM
    return Strength.WEAK


def format_strength_meter(strength: Strength) -> str:
    """Return a clear text strength meter for CLI output."""
    bars = {
        Strength.WEAK: "[█░░] weak",
        Strength.MEDIUM: "[██░] medium",
        Strength.STRONG: "[███] strong",
    }
    return bars[strength]

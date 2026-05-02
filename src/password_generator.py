"""Password generation and strength evaluation utilities."""

from __future__ import annotations

import math
import secrets
import string
from dataclasses import dataclass
from enum import Enum
from typing import Sequence

MIN_LENGTH = 8
MAX_LENGTH = 128
SPECIAL_CHARACTERS = "!@#$%^&*()-_=+[]{};:,.<>?/|~"


class PasswordGeneratorError(ValueError):
    """Raised when password generation inputs are invalid."""


class Strength(str, Enum):
    """Supported password strength classifications."""

    WEAK = "Weak"
    MODERATE = "Moderate"
    STRONG = "Strong"


@dataclass(frozen=True)
class CharacterOptions:
    """Character classes selected for password generation."""

    uppercase: bool = False
    lowercase: bool = False
    digits: bool = False
    special: bool = False

    def selected_sets(self) -> list[str]:
        """Return the concrete character sets selected by this option group."""
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

    def combined_charset(self) -> str:
        """Return a combined character set for all selected character classes."""
        return "".join(self.selected_sets())

    def selected_count(self) -> int:
        """Return the number of selected character classes."""
        return len(self.selected_sets())


def validate_length(length: int) -> None:
    """Validate password length.

    Args:
        length: Requested password length.

    Raises:
        PasswordGeneratorError: If the length is outside the supported range.
    """
    if not isinstance(length, int):
        raise PasswordGeneratorError("Length must be an integer.")
    if length < MIN_LENGTH or length > MAX_LENGTH:
        raise PasswordGeneratorError(
            f"Length must be between {MIN_LENGTH} and {MAX_LENGTH} characters."
        )


def validate_options(options: CharacterOptions) -> None:
    """Validate selected character type options.

    Args:
        options: Character type selections.

    Raises:
        PasswordGeneratorError: If no character type is selected.
    """
    if options.selected_count() == 0:
        raise PasswordGeneratorError(
            "At least one character type must be selected "
            "(--uppercase, --lowercase, --digits, or --special)."
        )


def _secure_shuffle(characters: Sequence[str]) -> str:
    """Return a securely shuffled string from a character sequence."""
    remaining = list(characters)
    shuffled: list[str] = []
    while remaining:
        index = secrets.randbelow(len(remaining))
        shuffled.append(remaining.pop(index))
    return "".join(shuffled)


def generate_password(length: int, options: CharacterOptions) -> str:
    """Generate a random password matching requested length and character types.

    If multiple character classes are selected, at least one character from each
    selected class is included. Remaining positions are filled from the combined
    selected character set.

    Args:
        length: Desired password length.
        options: Character type selections.

    Returns:
        A generated password.

    Raises:
        PasswordGeneratorError: If length or options are invalid.
    """
    validate_length(length)
    validate_options(options)

    selected_sets = options.selected_sets()
    if length < len(selected_sets):
        raise PasswordGeneratorError(
            "Length is too short for the selected character types."
        )

    required_characters = [charset[secrets.randbelow(len(charset))] for charset in selected_sets]
    combined_charset = options.combined_charset()
    remaining_length = length - len(required_characters)
    remaining_characters = [
        combined_charset[secrets.randbelow(len(combined_charset))]
        for _ in range(remaining_length)
    ]
    return _secure_shuffle(required_characters + remaining_characters)


def detect_character_variety(password: str) -> int:
    """Return the number of character classes present in a password."""
    variety = 0
    if any(character.isupper() for character in password):
        variety += 1
    if any(character.islower() for character in password):
        variety += 1
    if any(character.isdigit() for character in password):
        variety += 1
    if any(character in SPECIAL_CHARACTERS for character in password):
        variety += 1
    return variety


def estimate_charset_size(password: str) -> int:
    """Estimate the generating character-set size from characters present."""
    size = 0
    if any(character.isupper() for character in password):
        size += len(string.ascii_uppercase)
    if any(character.islower() for character in password):
        size += len(string.ascii_lowercase)
    if any(character.isdigit() for character in password):
        size += len(string.digits)
    if any(character in SPECIAL_CHARACTERS for character in password):
        size += len(SPECIAL_CHARACTERS)
    return size


def calculate_entropy_bits(password: str) -> float:
    """Calculate an entropy estimate in bits for a password."""
    if not password:
        return 0.0
    charset_size = estimate_charset_size(password)
    if charset_size <= 1:
        return 0.0
    return len(password) * math.log2(charset_size)


def evaluate_strength(password: str) -> Strength:
    """Evaluate password strength using length, variety, and entropy.

    Rules:
        * Weak: length < 10, fewer than 2 character classes, or entropy < 50 bits.
        * Moderate: length < 14, fewer than 3 character classes, or entropy < 80 bits.
        * Strong: all other generated passwords.
    """
    variety = detect_character_variety(password)
    entropy = calculate_entropy_bits(password)

    if len(password) < 10 or variety < 2 or entropy < 50:
        return Strength.WEAK
    if len(password) < 14 or variety < 3 or entropy < 80:
        return Strength.MODERATE
    return Strength.STRONG

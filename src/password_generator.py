"""Password generation and strength evaluation utilities."""

from __future__ import annotations

import secrets
import string
from dataclasses import dataclass
from typing import Sequence


DEFAULT_LENGTH = 12
MIN_LENGTH = 1
MAX_LENGTH = 1024


@dataclass(frozen=True)
class CharacterOptions:
    """Selection of character classes available for password generation."""

    uppercase: bool = True
    lowercase: bool = True
    digits: bool = True
    special: bool = True

    def selected_sets(self) -> list[str]:
        """Return the enabled character sets as strings."""
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
        """Return the number of enabled character classes."""
        return len(self.selected_sets())


class PasswordGeneratorError(ValueError):
    """Raised when password generation input is invalid."""


def validate_length(length: int) -> None:
    """Validate password length.

    Args:
        length: Requested password length.

    Raises:
        PasswordGeneratorError: If the length is outside the accepted range.
    """
    if length < MIN_LENGTH:
        raise PasswordGeneratorError(
            f"Password length must be at least {MIN_LENGTH} character."
        )
    if length > MAX_LENGTH:
        raise PasswordGeneratorError(
            f"Password length must be no more than {MAX_LENGTH} characters."
        )


def validate_options(options: CharacterOptions) -> None:
    """Validate that at least one character class is enabled."""
    if not options.selected_sets():
        raise PasswordGeneratorError(
            "At least one character type must be selected."
        )


def _choice(characters: Sequence[str]) -> str:
    """Return a cryptographically secure random character from a sequence."""
    return secrets.choice(characters)


def generate_password(length: int, options: CharacterOptions) -> str:
    """Generate a random password using the requested length and character sets.

    The generated password contains only enabled character classes. When the
    requested length is at least the number of selected classes, the password is
    guaranteed to contain at least one character from each selected class.

    Args:
        length: Number of characters to generate.
        options: Character classes to include.

    Returns:
        A generated password string.

    Raises:
        PasswordGeneratorError: If length or options are invalid.
    """
    validate_length(length)
    validate_options(options)

    selected_sets = options.selected_sets()
    all_allowed = "".join(selected_sets)
    password_chars: list[str] = []

    if length >= len(selected_sets):
        password_chars.extend(_choice(char_set) for char_set in selected_sets)
    else:
        password_chars.extend(
            _choice(_choice(selected_sets)) for _ in range(length)
        )

    remaining = length - len(password_chars)
    password_chars.extend(_choice(all_allowed) for _ in range(remaining))

    # Fisher-Yates shuffle using secrets for cryptographic randomness.
    for index in range(len(password_chars) - 1, 0, -1):
        swap_index = secrets.randbelow(index + 1)
        password_chars[index], password_chars[swap_index] = (
            password_chars[swap_index],
            password_chars[index],
        )

    return "".join(password_chars)


def character_variety(password: str) -> int:
    """Return how many character classes are present in a password."""
    checks = (
        any(char.isupper() for char in password),
        any(char.islower() for char in password),
        any(char.isdigit() for char in password),
        any(char in string.punctuation for char in password),
    )
    return sum(checks)


def evaluate_strength(password: str) -> str:
    """Evaluate password strength using length and character diversity.

    Returns one of: ``Very Weak``, ``Weak``, ``Moderate``, ``Strong``, or
    ``Very Strong``.
    """
    length = len(password)
    variety = character_variety(password)
    score = 0

    if length >= 8:
        score += 1
    if length >= 12:
        score += 1
    if length >= 16:
        score += 1

    if variety >= 2:
        score += 1
    if variety >= 3:
        score += 1
    if variety == 4:
        score += 1

    if score == 0:
        return "Very Weak"
    if score <= 2:
        return "Weak"
    if score in (3, 4):
        return "Moderate"
    if score == 5:
        return "Strong"
    return "Very Strong"

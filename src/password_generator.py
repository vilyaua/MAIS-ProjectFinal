"""Password generation and strength evaluation utilities."""

from __future__ import annotations

import random
import secrets
import string
from dataclasses import dataclass
from enum import Enum


MIN_LENGTH = 1
MAX_LENGTH = 128
SPECIAL_CHARACTERS = "!@#$%^&*()-_=+[]{};:,.<>?/|~"


class PasswordGenerationError(ValueError):
    """Raised when password generation inputs are invalid."""


class CharacterType(str, Enum):
    """Supported password character type options."""

    UPPERCASE = "uppercase"
    LOWERCASE = "lowercase"
    DIGITS = "digits"
    SPECIAL = "special"


@dataclass(frozen=True)
class PasswordOptions:
    """User-selected password generation options."""

    length: int
    uppercase: bool = False
    lowercase: bool = False
    digits: bool = False
    special: bool = False

    @property
    def selected_type_count(self) -> int:
        """Return how many character groups are selected."""
        return sum((self.uppercase, self.lowercase, self.digits, self.special))


@dataclass(frozen=True)
class StrengthResult:
    """Password strength score and human-readable rating."""

    score: int
    rating: str
    length_points: int
    variety_points: int


def validate_options(options: PasswordOptions) -> None:
    """Validate password options.

    Raises:
        PasswordGenerationError: If any option is invalid.
    """
    if not isinstance(options.length, int):
        raise PasswordGenerationError("Password length must be an integer.")

    if options.length <= 0:
        raise PasswordGenerationError(
            "Password length must be a positive integer greater than zero."
        )

    if options.length < MIN_LENGTH or options.length > MAX_LENGTH:
        raise PasswordGenerationError(
            f"Password length must be between {MIN_LENGTH} and {MAX_LENGTH}."
        )

    if options.selected_type_count == 0:
        raise PasswordGenerationError(
            "Select at least one character type: uppercase, lowercase, digits, or special."
        )

    if options.length < options.selected_type_count:
        raise PasswordGenerationError(
            "Password length must be at least the number of selected character types "
            f"({options.selected_type_count}) so each selected type can appear."
        )


def _selected_character_sets(options: PasswordOptions) -> list[str]:
    """Return character sets selected in the options."""
    character_sets: list[str] = []
    if options.uppercase:
        character_sets.append(string.ascii_uppercase)
    if options.lowercase:
        character_sets.append(string.ascii_lowercase)
    if options.digits:
        character_sets.append(string.digits)
    if options.special:
        character_sets.append(SPECIAL_CHARACTERS)
    return character_sets


def generate_password(
    options: PasswordOptions,
    rng: random.Random | None = None,
) -> str:
    """Generate a password that matches the selected options.

    The generated password contains at least one character from every selected
    character group, guaranteeing that selected digits/special characters are
    represented when requested.

    Args:
        options: Password length and selected character groups.
        rng: Optional random number generator, primarily for deterministic tests.

    Returns:
        A generated password string.

    Raises:
        PasswordGenerationError: If options are invalid.
    """
    validate_options(options)
    generator = rng if rng is not None else secrets.SystemRandom()

    character_sets = _selected_character_sets(options)
    all_characters = "".join(character_sets)

    password_characters = [generator.choice(charset) for charset in character_sets]
    remaining_length = options.length - len(password_characters)
    password_characters.extend(
        generator.choice(all_characters) for _ in range(remaining_length)
    )
    generator.shuffle(password_characters)
    return "".join(password_characters)


def character_variety_count(password: str) -> int:
    """Return the number of character categories present in a password."""
    return sum(
        (
            any(char.isupper() for char in password),
            any(char.islower() for char in password),
            any(char.isdigit() for char in password),
            any(char in SPECIAL_CHARACTERS for char in password),
        )
    )


def evaluate_strength(password: str) -> StrengthResult:
    """Evaluate password strength based on length and character diversity.

    Scoring is intentionally transparent:
    - Up to 50 points for length, reaching the maximum at 16 characters.
    - Up to 50 points for variety, with 12.5 points per category present.
    """
    if not password:
        return StrengthResult(
            score=0,
            rating="Very Weak",
            length_points=0,
            variety_points=0,
        )

    length_points = min(50, round((len(password) / 16) * 50))
    variety_points = round((character_variety_count(password) / 4) * 50)
    score = min(100, length_points + variety_points)

    if score < 20:
        rating = "Very Weak"
    elif score < 45:
        rating = "Weak"
    elif score < 65:
        rating = "Fair"
    elif score < 85:
        rating = "Strong"
    else:
        rating = "Very Strong"

    return StrengthResult(
        score=score,
        rating=rating,
        length_points=length_points,
        variety_points=variety_points,
    )

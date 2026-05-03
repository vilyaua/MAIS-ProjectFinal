"""Password generation and strength evaluation utilities."""

from __future__ import annotations

import secrets
import string
from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class PasswordError(ValueError):
    """Raised when password generation input is invalid."""


class StrengthRating(str, Enum):
    """Supported password strength ratings."""

    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"


@dataclass(frozen=True)
class CharacterSetOptions:
    """Character sets that may be used when generating a password."""

    uppercase: bool = True
    lowercase: bool = True
    digits: bool = True
    special: bool = True

    def selected_count(self) -> int:
        """Return the number of enabled character set categories."""
        return sum((self.uppercase, self.lowercase, self.digits, self.special))

    def has_any_selected(self) -> bool:
        """Return whether at least one character set category is enabled."""
        return self.selected_count() > 0


def parse_positive_length(value: str) -> int:
    """Parse and validate a positive integer password length.

    Args:
        value: User-provided length text.

    Returns:
        A positive integer length.

    Raises:
        PasswordError: If the value is not an integer greater than zero.
    """
    try:
        length = int(value)
    except (TypeError, ValueError) as exc:
        raise PasswordError("Password length must be a positive integer.") from exc

    if length <= 0:
        raise PasswordError("Password length must be greater than zero.")
    return length


def build_character_pool(options: CharacterSetOptions) -> str:
    """Build the allowed character pool from selected options.

    Args:
        options: Selected character set options.

    Returns:
        A string containing all allowed characters.

    Raises:
        PasswordError: If no character set is selected.
    """
    pool_parts: list[str] = []
    if options.uppercase:
        pool_parts.append(string.ascii_uppercase)
    if options.lowercase:
        pool_parts.append(string.ascii_lowercase)
    if options.digits:
        pool_parts.append(string.digits)
    if options.special:
        pool_parts.append(string.punctuation)

    if not pool_parts:
        raise PasswordError("Select at least one character set.")

    return "".join(pool_parts)


def generate_password(length: int, options: CharacterSetOptions) -> str:
    """Generate a random password matching the requested constraints.

    Args:
        length: Positive password length.
        options: Character set options.

    Returns:
        A randomly generated password.

    Raises:
        PasswordError: If the length is invalid or no character set is selected.
    """
    if not isinstance(length, int):
        raise PasswordError("Password length must be a positive integer.")
    if length <= 0:
        raise PasswordError("Password length must be greater than zero.")

    pool = build_character_pool(options)
    return "".join(secrets.choice(pool) for _ in range(length))


def _contains_any(password: str, characters: Iterable[str]) -> bool:
    character_set = set(characters)
    return any(char in character_set for char in password)


def character_variety(password: str) -> int:
    """Return the number of character categories present in a password."""
    variety = 0
    if _contains_any(password, string.ascii_uppercase):
        variety += 1
    if _contains_any(password, string.ascii_lowercase):
        variety += 1
    if _contains_any(password, string.digits):
        variety += 1
    if _contains_any(password, string.punctuation):
        variety += 1
    return variety


def evaluate_strength(password: str) -> StrengthRating:
    """Evaluate password strength using length and character variety.

    The meter intentionally stays simple and explainable:
    - weak: very short passwords with little variety
    - moderate: reasonable length or some character variety
    - strong: longer passwords with broad character variety

    Args:
        password: Password to evaluate.

    Returns:
        A strength rating.
    """
    length = len(password)
    variety = character_variety(password)

    score = 0
    if length >= 8:
        score += 1
    if length >= 12:
        score += 1
    if variety >= 2:
        score += 1
    if variety >= 3:
        score += 1
    if variety == 4 and length >= 12:
        score += 1

    if score >= 4:
        return StrengthRating.STRONG
    if score >= 1:
        return StrengthRating.MODERATE
    return StrengthRating.WEAK

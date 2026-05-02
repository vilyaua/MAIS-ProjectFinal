"""Password generation and strength evaluation utilities."""

from __future__ import annotations

import math
import secrets
import string
from dataclasses import dataclass
from enum import Enum
from typing import Sequence


MIN_LENGTH = 1
MAX_LENGTH = 128
SPECIAL_CHARACTERS = "!@#$%^&*()-_=+[]{};:,.<>?/|`~"


class PasswordStrength(str, Enum):
    """Supported password strength categories."""

    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"


@dataclass(frozen=True)
class CharacterSetConfig:
    """Configuration describing which character sets are enabled."""

    uppercase: bool = True
    lowercase: bool = True
    digits: bool = True
    special: bool = True

    def enabled_sets(self) -> list[str]:
        """Return the concrete character sets that are enabled."""
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

    def enabled_count(self) -> int:
        """Return the number of enabled character set categories."""
        return len(self.enabled_sets())

    def pool(self) -> str:
        """Return all enabled character sets concatenated into one pool."""
        return "".join(self.enabled_sets())


def validate_options(length: int, config: CharacterSetConfig) -> None:
    """Validate password generation options.

    Args:
        length: Desired password length.
        config: Enabled character set configuration.

    Raises:
        ValueError: If length or character set choices are invalid.
    """
    if not MIN_LENGTH <= length <= MAX_LENGTH:
        raise ValueError(
            f"Password length must be between {MIN_LENGTH} and {MAX_LENGTH} characters."
        )
    if not config.enabled_sets():
        raise ValueError("At least one character set must be selected.")


def generate_password(length: int, config: CharacterSetConfig) -> str:
    """Generate a cryptographically secure password.

    The password is drawn only from selected character sets. When the requested
    length is at least the number of selected character set categories, the
    generated password is guaranteed to include at least one character from each
    selected category.
    """
    validate_options(length, config)

    selected_sets = config.enabled_sets()
    pool = "".join(selected_sets)

    required_chars: list[str] = []
    if length >= len(selected_sets):
        required_chars = [secrets.choice(char_set) for char_set in selected_sets]

    remaining_length = length - len(required_chars)
    password_chars = required_chars + [
        secrets.choice(pool) for _ in range(remaining_length)
    ]
    secrets.SystemRandom().shuffle(password_chars)
    return "".join(password_chars)


def detect_character_variety(password: str) -> int:
    """Count how many supported character categories appear in a password."""
    categories = [
        any(char.isupper() for char in password),
        any(char.islower() for char in password),
        any(char.isdigit() for char in password),
        any(char in SPECIAL_CHARACTERS for char in password),
    ]
    return sum(categories)


def estimate_entropy_bits(password: str) -> float:
    """Estimate password entropy in bits from observed character categories."""
    if not password:
        return 0.0

    pool_size = 0
    if any(char.isupper() for char in password):
        pool_size += len(string.ascii_uppercase)
    if any(char.islower() for char in password):
        pool_size += len(string.ascii_lowercase)
    if any(char.isdigit() for char in password):
        pool_size += len(string.digits)
    if any(char in SPECIAL_CHARACTERS for char in password):
        pool_size += len(SPECIAL_CHARACTERS)

    # Unknown characters still add some uncertainty instead of causing a zero.
    unknown_chars = [
        char
        for char in password
        if not (
            char.isupper()
            or char.islower()
            or char.isdigit()
            or char in SPECIAL_CHARACTERS
        )
    ]
    pool_size += len(set(unknown_chars))

    if pool_size <= 1:
        return 0.0
    return len(password) * math.log2(pool_size)


def has_low_unpredictability(password: str) -> bool:
    """Return True when obvious repetition or sequential patterns are present."""
    if len(password) < 3:
        return False

    unique_ratio = len(set(password)) / len(password)
    if len(password) >= 8 and unique_ratio < 0.35:
        return True

    lowered = password.lower()
    sequential_sources: Sequence[str] = (
        string.ascii_lowercase,
        string.ascii_lowercase[::-1],
        string.digits,
        string.digits[::-1],
    )
    for index in range(len(lowered) - 2):
        chunk = lowered[index : index + 3]
        if any(chunk in source for source in sequential_sources):
            return True

    return False


def evaluate_strength(password: str) -> PasswordStrength:
    """Evaluate password strength as weak, moderate, or strong.

    The score considers length, observed character-set variety, estimated
    entropy, and penalties for predictable repeated/sequential patterns.
    """
    if not password:
        return PasswordStrength.WEAK

    variety = detect_character_variety(password)
    entropy = estimate_entropy_bits(password)
    predictable = has_low_unpredictability(password)

    score = 0
    length = len(password)

    if length >= 12:
        score += 2
    elif length >= 8:
        score += 2
    elif length >= 6:
        score += 1

    if variety >= 4:
        score += 2
    elif variety >= 2:
        score += 1

    if entropy >= 70:
        score += 2
    elif entropy >= 40:
        score += 1

    if predictable:
        score -= 1

    if score >= 5 and length >= 12 and variety >= 3 and not predictable:
        return PasswordStrength.STRONG
    if score >= 3 and length >= 8 and variety >= 2:
        return PasswordStrength.MODERATE
    return PasswordStrength.WEAK

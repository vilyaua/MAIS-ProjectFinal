"""Core password generation and strength calculation utilities."""

from __future__ import annotations

import math
import secrets
import string
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

MIN_LENGTH = 8
MAX_LENGTH = 128

CHARACTER_SETS: Mapping[str, str] = {
    "uppercase": string.ascii_uppercase,
    "lowercase": string.ascii_lowercase,
    "digits": string.digits,
    "special": "!@#$%^&*()-_=+[]{};:,.<>?/~`|\\",
}


class PasswordInputError(ValueError):
    """Raised when password generator input is invalid."""


@dataclass(frozen=True)
class StrengthResult:
    """Human-readable password strength details."""

    score: int
    label: str
    entropy_bits: float
    character_variety: int
    feedback: str

    @property
    def meter(self) -> str:
        """Return a compact text meter with ten positions."""
        filled = "#" * self.score
        empty = "-" * (10 - self.score)
        return f"[{filled}{empty}]"


def validate_length(raw_value: str) -> int:
    """Validate and return a password length from user-provided text.

    Args:
        raw_value: Text entered by a user.

    Raises:
        PasswordInputError: If the value is not an integer in the allowed range.
    """
    value = raw_value.strip()
    if not value:
        raise PasswordInputError(
            f"Password length is required. Enter a number from "
            f"{MIN_LENGTH} to {MAX_LENGTH}."
        )

    try:
        length = int(value)
    except ValueError as exc:
        raise PasswordInputError(
            f"'{raw_value}' is not a valid integer. Enter a number from "
            f"{MIN_LENGTH} to {MAX_LENGTH}."
        ) from exc

    if length < MIN_LENGTH or length > MAX_LENGTH:
        raise PasswordInputError(
            f"Password length must be between {MIN_LENGTH} and {MAX_LENGTH} "
            "characters."
        )
    return length


def get_selected_character_sets(
    *,
    uppercase: bool,
    lowercase: bool,
    digits: bool,
    special: bool,
) -> list[str]:
    """Return selected character-set strings based on boolean options."""
    selected: list[str] = []
    if uppercase:
        selected.append(CHARACTER_SETS["uppercase"])
    if lowercase:
        selected.append(CHARACTER_SETS["lowercase"])
    if digits:
        selected.append(CHARACTER_SETS["digits"])
    if special:
        selected.append(CHARACTER_SETS["special"])
    return selected


def generate_password(
    length: int,
    selected_sets: Sequence[str],
    *,
    avoid_passwords: Iterable[str] | None = None,
) -> str:
    """Generate a random password from selected character sets.

    The generated password contains at least one character from every selected
    set. If ``avoid_passwords`` is supplied, the function attempts to avoid
    returning a password already present in that iterable.

    Args:
        length: Desired password length.
        selected_sets: Sequence of character-set strings to use.
        avoid_passwords: Optional collection of passwords to avoid.

    Raises:
        PasswordInputError: If inputs cannot produce a valid password.
    """
    if length < MIN_LENGTH or length > MAX_LENGTH:
        raise PasswordInputError(
            f"Password length must be between {MIN_LENGTH} and {MAX_LENGTH} "
            "characters."
        )
    if not selected_sets:
        raise PasswordInputError(
            "Select at least one character set: uppercase, lowercase, digits, "
            "or special characters."
        )
    if any(not character_set for character_set in selected_sets):
        raise PasswordInputError("Selected character sets cannot be empty.")
    if length < len(selected_sets):
        raise PasswordInputError(
            "Password length must be at least the number of selected "
            "character sets."
        )

    avoid = set(avoid_passwords or [])
    combined_characters = "".join(selected_sets)
    random = secrets.SystemRandom()

    for _ in range(100):
        required_characters = [random.choice(chars) for chars in selected_sets]
        remaining_count = length - len(required_characters)
        remaining_characters = [
            random.choice(combined_characters) for _ in range(remaining_count)
        ]
        password_characters = required_characters + remaining_characters
        random.shuffle(password_characters)
        password = "".join(password_characters)
        if password not in avoid:
            return password

    raise PasswordInputError(
        "Unable to generate a unique password after several attempts. "
        "Try a longer password or more character sets."
    )


def calculate_strength(password: str) -> StrengthResult:
    """Calculate strength from length, character variety, and entropy."""
    length = len(password)
    variety = _count_detected_character_types(password)
    pool_size = _estimate_pool_size(password)
    entropy_bits = length * math.log2(pool_size) if pool_size else 0.0

    score = _length_points(length) + variety + _entropy_points(entropy_bits)
    score = max(0, min(10, score))
    label = _label_for_score(score)
    feedback = _feedback_for_strength(length, variety, entropy_bits)

    return StrengthResult(
        score=score,
        label=label,
        entropy_bits=entropy_bits,
        character_variety=variety,
        feedback=feedback,
    )


def _count_detected_character_types(password: str) -> int:
    return sum(
        bool(set(password) & set(characters))
        for characters in CHARACTER_SETS.values()
    )


def _estimate_pool_size(password: str) -> int:
    return sum(
        len(characters)
        for characters in CHARACTER_SETS.values()
        if set(password) & set(characters)
    )


def _length_points(length: int) -> int:
    if length >= 16:
        return 3
    if length >= 12:
        return 2
    if length >= MIN_LENGTH:
        return 1
    return 0


def _entropy_points(entropy_bits: float) -> int:
    if entropy_bits >= 80:
        return 3
    if entropy_bits >= 60:
        return 2
    if entropy_bits >= 40:
        return 1
    return 0


def _label_for_score(score: int) -> str:
    if score >= 9:
        return "Very Strong"
    if score >= 7:
        return "Strong"
    if score >= 5:
        return "Moderate"
    if score >= 3:
        return "Weak"
    return "Very Weak"


def _feedback_for_strength(
    length: int,
    character_variety: int,
    entropy_bits: float,
) -> str:
    suggestions: list[str] = []
    if length < 12:
        suggestions.append("use at least 12 characters")
    if character_variety < 3:
        suggestions.append("include more character types")
    if entropy_bits < 60:
        suggestions.append("increase length or character variety for more entropy")

    if not suggestions:
        return "Good complexity for general use."
    return "Consider: " + "; ".join(suggestions) + "."

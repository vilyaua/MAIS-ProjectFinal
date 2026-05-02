"""ASCII art generation utilities.

This module contains a small built-in banner font and rendering logic for
multiple terminal-friendly font styles. It intentionally avoids external
runtime dependencies so the command-line tool works in a basic Python
installation.
"""

from __future__ import annotations

import string
from dataclasses import dataclass


class InputValidationError(ValueError):
    """Raised when text cannot be rendered as ASCII art."""


@dataclass(frozen=True)
class FontStyle:
    """Visual style used to render glyph patterns."""

    name: str
    fill: str
    spacer: str = " "


SUPPORTED_FONTS: dict[str, FontStyle] = {
    "block": FontStyle(name="block", fill="█"),
    "plain": FontStyle(name="plain", fill="#"),
    "star": FontStyle(name="star", fill="*"),
}

DEFAULT_FONT = "block"

# Common punctuation intentionally supported by the validator. Every character
# below also has a glyph in GLYPHS.
SUPPORTED_PUNCTUATION = " .,!?;:'\"-_/@#$%&*+=<>\\|()[]{}"
VALID_CHARACTERS = set(string.ascii_letters + string.digits + SUPPORTED_PUNCTUATION)

GLYPHS: dict[str, tuple[str, ...]] = {
    " ": (
        "     ",
        "     ",
        "     ",
        "     ",
        "     ",
        "     ",
        "     ",
    ),
    "A": (" XXX ", "X   X", "X   X", "XXXXX", "X   X", "X   X", "X   X"),
    "B": ("XXXX ", "X   X", "X   X", "XXXX ", "X   X", "X   X", "XXXX "),
    "C": (" XXX ", "X   X", "X    ", "X    ", "X    ", "X   X", " XXX "),
    "D": ("XXXX ", "X   X", "X   X", "X   X", "X   X", "X   X", "XXXX "),
    "E": ("XXXXX", "X    ", "X    ", "XXXX ", "X    ", "X    ", "XXXXX"),
    "F": ("XXXXX", "X    ", "X    ", "XXXX ", "X    ", "X    ", "X    "),
    "G": (" XXX ", "X   X", "X    ", "X XXX", "X   X", "X   X", " XXX "),
    "H": ("X   X", "X   X", "X   X", "XXXXX", "X   X", "X   X", "X   X"),
    "I": ("XXXXX", "  X  ", "  X  ", "  X  ", "  X  ", "  X  ", "XXXXX"),
    "J": ("XXXXX", "    X", "    X", "    X", "    X", "X   X", " XXX "),
    "K": ("X   X", "X  X ", "X X  ", "XX   ", "X X  ", "X  X ", "X   X"),
    "L": ("X    ", "X    ", "X    ", "X    ", "X    ", "X    ", "XXXXX"),
    "M": ("X   X", "XX XX", "X X X", "X   X", "X   X", "X   X", "X   X"),
    "N": ("X   X", "XX  X", "XX  X", "X X X", "X  XX", "X  XX", "X   X"),
    "O": (" XXX ", "X   X", "X   X", "X   X", "X   X", "X   X", " XXX "),
    "P": ("XXXX ", "X   X", "X   X", "XXXX ", "X    ", "X    ", "X    "),
    "Q": (" XXX ", "X   X", "X   X", "X   X", "X X X", "X  X ", " XX X"),
    "R": ("XXXX ", "X   X", "X   X", "XXXX ", "X X  ", "X  X ", "X   X"),
    "S": (" XXXX", "X    ", "X    ", " XXX ", "    X", "    X", "XXXX "),
    "T": ("XXXXX", "  X  ", "  X  ", "  X  ", "  X  ", "  X  ", "  X  "),
    "U": ("X   X", "X   X", "X   X", "X   X", "X   X", "X   X", " XXX "),
    "V": ("X   X", "X   X", "X   X", "X   X", "X   X", " X X ", "  X  "),
    "W": ("X   X", "X   X", "X   X", "X   X", "X X X", "XX XX", "X   X"),
    "X": ("X   X", "X   X", " X X ", "  X  ", " X X ", "X   X", "X   X"),
    "Y": ("X   X", "X   X", " X X ", "  X  ", "  X  ", "  X  ", "  X  "),
    "Z": ("XXXXX", "    X", "   X ", "  X  ", " X   ", "X    ", "XXXXX"),
    "0": (" XXX ", "X   X", "X  XX", "X X X", "XX  X", "X   X", " XXX "),
    "1": ("  X  ", " XX  ", "  X  ", "  X  ", "  X  ", "  X  ", "XXXXX"),
    "2": (" XXX ", "X   X", "    X", "   X ", "  X  ", " X   ", "XXXXX"),
    "3": (" XXX ", "X   X", "    X", "  XX ", "    X", "X   X", " XXX "),
    "4": ("   X ", "  XX ", " X X ", "X  X ", "XXXXX", "   X ", "   X "),
    "5": ("XXXXX", "X    ", "X    ", "XXXX ", "    X", "X   X", " XXX "),
    "6": (" XXX ", "X   X", "X    ", "XXXX ", "X   X", "X   X", " XXX "),
    "7": ("XXXXX", "    X", "   X ", "  X  ", " X   ", " X   ", " X   "),
    "8": (" XXX ", "X   X", "X   X", " XXX ", "X   X", "X   X", " XXX "),
    "9": (" XXX ", "X   X", "X   X", " XXXX", "    X", "X   X", " XXX "),
    ".": ("     ", "     ", "     ", "     ", "     ", " XX  ", " XX  "),
    ",": ("     ", "     ", "     ", "     ", " XX  ", " XX  ", " X   "),
    "!": ("  X  ", "  X  ", "  X  ", "  X  ", "  X  ", "     ", "  X  "),
    "?": (" XXX ", "X   X", "    X", "   X ", "  X  ", "     ", "  X  "),
    ";": ("     ", " XX  ", " XX  ", "     ", " XX  ", " XX  ", " X   "),
    ":": ("     ", " XX  ", " XX  ", "     ", " XX  ", " XX  ", "     "),
    "'": ("  X  ", "  X  ", " X   ", "     ", "     ", "     ", "     "),
    '"': (" X X ", " X X ", "X X  ", "     ", "     ", "     ", "     "),
    "-": ("     ", "     ", "     ", "XXXXX", "     ", "     ", "     "),
    "_": ("     ", "     ", "     ", "     ", "     ", "     ", "XXXXX"),
    "/": ("    X", "   X ", "   X ", "  X  ", " X   ", " X   ", "X    "),
    "\\": ("X    ", " X   ", " X   ", "  X  ", "   X ", "   X ", "    X"),
    "|": ("  X  ", "  X  ", "  X  ", "  X  ", "  X  ", "  X  ", "  X  "),
    "(": ("   X ", "  X  ", " X   ", " X   ", " X   ", "  X  ", "   X "),
    ")": (" X   ", "  X  ", "   X ", "   X ", "   X ", "  X  ", " X   "),
    "[": (" XXX ", " X   ", " X   ", " X   ", " X   ", " X   ", " XXX "),
    "]": (" XXX ", "   X ", "   X ", "   X ", "   X ", "   X ", " XXX "),
    "{": ("   XX", "  X  ", "  X  ", "XX   ", "  X  ", "  X  ", "   XX"),
    "}": ("XX   ", "  X  ", "  X  ", "   XX", "  X  ", "  X  ", "XX   "),
    "@": (" XXX ", "X   X", "X XXX", "X X X", "X XXX", "X    ", " XXX "),
    "#": (" X X ", " X X ", "XXXXX", " X X ", "XXXXX", " X X ", " X X "),
    "$": ("  X  ", " XXXX", "X X  ", " XXX ", "  X X", "XXXX ", "  X  "),
    "%": ("XX  X", "XX X ", "  X  ", " X   ", "X  XX", "  XX ", "     "),
    "&": (" XX  ", "X  X ", "X X  ", " XX X", "X  X ", "X   X", " XXX "),
    "*": ("     ", "X X X", " XXX ", "XXXXX", " XXX ", "X X X", "     "),
    "+": ("     ", "  X  ", "  X  ", "XXXXX", "  X  ", "  X  ", "     "),
    "=": ("     ", "     ", "XXXXX", "     ", "XXXXX", "     ", "     "),
    "<": ("   X ", "  X  ", " X   ", "X    ", " X   ", "  X  ", "   X "),
    ">": (" X   ", "  X  ", "   X ", "    X", "   X ", "  X  ", " X   "),
}


def get_supported_fonts() -> tuple[str, ...]:
    """Return supported font names in stable display order."""

    return tuple(SUPPORTED_FONTS.keys())


def validate_text(text: str) -> None:
    """Validate user-provided text.

    Args:
        text: Raw text supplied by the user.

    Raises:
        InputValidationError: If text is empty or contains unsupported chars.
    """

    if not text or not text.strip():
        raise InputValidationError("Please provide valid input: text cannot be empty.")

    invalid_characters = sorted({char for char in text if char not in VALID_CHARACTERS})
    if invalid_characters:
        printable = ", ".join(repr(char) for char in invalid_characters)
        raise InputValidationError(f"Unsupported character(s): {printable}")


def normalize_text(text: str) -> str:
    """Normalize text to match the built-in uppercase glyph table."""

    return text.upper()


def render_ascii_art(text: str, font: str = DEFAULT_FONT) -> str:
    """Render text as multi-line ASCII art.

    Args:
        text: Text to render. Letters are rendered case-insensitively.
        font: Name of the style to use. Defaults to ``block``.

    Returns:
        A string containing the rendered ASCII art.

    Raises:
        InputValidationError: If input or font is invalid.
    """

    validate_text(text)

    try:
        style = SUPPORTED_FONTS[font.lower()]
    except KeyError as exc:
        supported = ", ".join(get_supported_fonts())
        raise InputValidationError(
            f"Unsupported font style '{font}'. Supported fonts: {supported}."
        ) from exc

    normalized = normalize_text(text)
    rows: list[str] = [""] * 7

    for character in normalized:
        try:
            glyph = GLYPHS[character]
        except KeyError as exc:
            # Defensive check in case VALID_CHARACTERS and GLYPHS become out of sync.
            raise InputValidationError(f"Unsupported character: {character!r}") from exc

        for index, pattern_row in enumerate(glyph):
            rendered_row = "".join(
                style.fill if pixel == "X" else style.spacer for pixel in pattern_row
            )
            rows[index] += rendered_row + " "

    return "\n".join(row.rstrip() for row in rows)

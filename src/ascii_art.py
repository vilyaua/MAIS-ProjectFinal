"""ASCII art text generation utilities."""

from __future__ import annotations

import string
from dataclasses import dataclass

MAX_LENGTH = 100
GLYPH_HEIGHT = 5


class AsciiArtError(ValueError):
    """Raised when text cannot be converted to ASCII art."""


@dataclass(frozen=True)
class RenderResult:
    """Result of rendering text as ASCII art."""

    art: str
    warning: str | None = None


# A compact 5-row block font. Letters, digits, spaces, and common punctuation
# are intentionally supported so the program works without external packages.
_FONT: dict[str, tuple[str, str, str, str, str]] = {
    "A": (" ### ", "#   #", "#####", "#   #", "#   #"),
    "B": ("#### ", "#   #", "#### ", "#   #", "#### "),
    "C": (" ####", "#    ", "#    ", "#    ", " ####"),
    "D": ("#### ", "#   #", "#   #", "#   #", "#### "),
    "E": ("#####", "#    ", "#### ", "#    ", "#####"),
    "F": ("#####", "#    ", "#### ", "#    ", "#    "),
    "G": (" ####", "#    ", "# ###", "#   #", " ####"),
    "H": ("#   #", "#   #", "#####", "#   #", "#   #"),
    "I": ("#####", "  #  ", "  #  ", "  #  ", "#####"),
    "J": ("#####", "   # ", "   # ", "#  # ", " ##  "),
    "K": ("#   #", "#  # ", "###  ", "#  # ", "#   #"),
    "L": ("#    ", "#    ", "#    ", "#    ", "#####"),
    "M": ("#   #", "## ##", "# # #", "#   #", "#   #"),
    "N": ("#   #", "##  #", "# # #", "#  ##", "#   #"),
    "O": (" ### ", "#   #", "#   #", "#   #", " ### "),
    "P": ("#### ", "#   #", "#### ", "#    ", "#    "),
    "Q": (" ### ", "#   #", "#   #", "#  ##", " ####"),
    "R": ("#### ", "#   #", "#### ", "#  # ", "#   #"),
    "S": (" ####", "#    ", " ### ", "    #", "#### "),
    "T": ("#####", "  #  ", "  #  ", "  #  ", "  #  "),
    "U": ("#   #", "#   #", "#   #", "#   #", " ### "),
    "V": ("#   #", "#   #", "#   #", " # # ", "  #  "),
    "W": ("#   #", "#   #", "# # #", "## ##", "#   #"),
    "X": ("#   #", " # # ", "  #  ", " # # ", "#   #"),
    "Y": ("#   #", " # # ", "  #  ", "  #  ", "  #  "),
    "Z": ("#####", "   # ", "  #  ", " #   ", "#####"),
    "0": (" ### ", "#  ##", "# # #", "##  #", " ### "),
    "1": ("  #  ", " ##  ", "  #  ", "  #  ", " ### "),
    "2": (" ### ", "#   #", "   # ", "  #  ", "#####"),
    "3": ("#### ", "    #", " ### ", "    #", "#### "),
    "4": ("#   #", "#   #", "#####", "    #", "    #"),
    "5": ("#####", "#    ", "#### ", "    #", "#### "),
    "6": (" ####", "#    ", "#### ", "#   #", " ### "),
    "7": ("#####", "   # ", "  #  ", " #   ", "#    "),
    "8": (" ### ", "#   #", " ### ", "#   #", " ### "),
    "9": (" ### ", "#   #", " ####", "    #", " ### "),
    " ": ("   ", "   ", "   ", "   ", "   "),
    ".": ("   ", "   ", "   ", "   ", " # "),
    ",": ("   ", "   ", "   ", " # ", "#  "),
    "!": (" # ", " # ", " # ", "   ", " # "),
    "?": ("### ", "   #", " ## ", "    ", " #  "),
    ":": ("   ", " # ", "   ", " # ", "   "),
    ";": ("   ", " # ", "   ", " # ", "#  "),
    "'": (" # ", " # ", "   ", "   ", "   "),
    '"': ("# #", "# #", "   ", "   ", "   "),
    "-": ("    ", "    ", "####", "    ", "    "),
    "_": ("    ", "    ", "    ", "    ", "####"),
    "/": ("   #", "  # ", " #  ", "#   ", "    "),
    "\\": ("#   ", " #  ", "  # ", "   #", "    "),
    "(": ("  #", " # ", " # ", " # ", "  #"),
    ")": ("#  ", " # ", " # ", " # ", "#  "),
    "[": ("###", "#  ", "#  ", "#  ", "###"),
    "]": ("###", "  #", "  #", "  #", "###"),
    "{": ("  ##", " #  ", "##  ", " #  ", "  ##"),
    "}": ("##  ", "  # ", "  ##", "  # ", "##  "),
    "@": (" ### ", "# ###", "# # #", "#    ", " ### "),
    "#": (" # # ", "#####", " # # ", "#####", " # # "),
    "&": (" ##  ", "#  # ", " ## #", "#  # ", " ## #"),
    "%": ("#   #", "   # ", "  #  ", " #   ", "#   #"),
    "+": ("     ", "  #  ", "#####", "  #  ", "     "),
    "*": ("# # #", " ### ", "#####", " ### ", "# # #"),
    "=": ("     ", "#####", "     ", "#####", "     "),
    "<": ("   #", "  # ", " #  ", "  # ", "   #"),
    ">": ("#   ", " #  ", "  # ", " #  ", "#   "),
    "$": (" ### ", "# #  ", " ### ", "  # #", " ### "),
}

SUPPORTED_CHARACTERS = frozenset(_FONT.keys()) | frozenset(string.ascii_lowercase)


def validate_input(text: str, max_length: int = MAX_LENGTH) -> None:
    """Validate basic input constraints.

    Args:
        text: User-provided text.
        max_length: Maximum allowed input length.

    Raises:
        AsciiArtError: If the text is empty or too long.
    """
    if not text or not text.strip():
        raise AsciiArtError("Invalid input: text must not be empty.")
    if len(text) > max_length:
        raise AsciiArtError(
            f"Invalid input: text is too long ({len(text)} characters). "
            f"Please shorten it to {max_length} characters or fewer."
        )


def _glyph_for(character: str) -> tuple[str, str, str, str, str] | None:
    """Return a glyph for a supported character, or None if unsupported."""
    if character in _FONT:
        return _FONT[character]
    upper_character = character.upper()
    if upper_character in _FONT:
        return _FONT[upper_character]
    return None


def render_ascii_art(text: str, max_length: int = MAX_LENGTH) -> RenderResult:
    """Render text as ASCII art.

    Unsupported characters are skipped and reported in the warning field.

    Args:
        text: Text to render.
        max_length: Maximum allowed input length.

    Returns:
        A RenderResult containing ASCII art and an optional warning.

    Raises:
        AsciiArtError: If the input is empty, too long, or has no renderable
            characters.
    """
    validate_input(text, max_length=max_length)

    rows = [""] * GLYPH_HEIGHT
    unsupported: list[str] = []
    rendered_count = 0

    for character in text:
        glyph = _glyph_for(character)
        if glyph is None:
            if character not in unsupported:
                unsupported.append(character)
            continue
        rendered_count += 1
        for index, row in enumerate(glyph):
            rows[index] += row + "  "

    if rendered_count == 0:
        raise AsciiArtError(
            "Invalid input: no supported characters were provided. "
            "Use letters, numbers, spaces, or common punctuation."
        )

    warning = None
    if unsupported:
        unsupported_display = "".join(unsupported)
        warning = (
            "Warning: skipped unsupported character(s): "
            f"{unsupported_display!r}."
        )

    return RenderResult(art="\n".join(row.rstrip() for row in rows), warning=warning)

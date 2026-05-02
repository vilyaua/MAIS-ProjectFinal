"""ASCII art generation utilities.

This module provides a small, dependency-free ASCII art renderer with a
readable built-in block font and a few rendering styles. It is intentionally
kept simple so it can be used both from the command line and unit tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

FONT_HEIGHT = 5
SPACE_WIDTH = 3
CHAR_SPACING = 1

# Glyphs are five rows tall. The renderer replaces non-space characters in the
# glyph definition with the selected style's drawing character.
GLYPHS: dict[str, tuple[str, ...]] = {
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
    "Q": (" ### ", "#   #", "# # #", "#  # ", " ## #"),
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
    "6": (" ### ", "#    ", "#### ", "#   #", " ### "),
    "7": ("#####", "   # ", "  #  ", " #   ", "#    "),
    "8": (" ### ", "#   #", " ### ", "#   #", " ### "),
    "9": (" ### ", "#   #", " ####", "    #", " ### "),
    "!": ("  #  ", "  #  ", "  #  ", "     ", "  #  "),
    "?": (" ### ", "#   #", "   # ", "     ", "  #  "),
    ".": ("     ", "     ", "     ", "     ", "  #  "),
    ",": ("     ", "     ", "     ", "  #  ", " #   "),
    ":": ("     ", "  #  ", "     ", "  #  ", "     "),
    ";": ("     ", "  #  ", "     ", "  #  ", " #   "),
    "-": ("     ", "     ", "#####", "     ", "     "),
    "_": ("     ", "     ", "     ", "     ", "#####"),
    "+": ("     ", "  #  ", "#####", "  #  ", "     "),
    "=": ("     ", "#####", "     ", "#####", "     "),
    "/": ("    #", "   # ", "  #  ", " #   ", "#    "),
    "\\": ("#    ", " #   ", "  #  ", "   # ", "    #"),
    "'": ("  #  ", "  #  ", "     ", "     ", "     "),
    '"': (" # # ", " # # ", "     ", "     ", "     "),
    "(": ("   # ", "  #  ", "  #  ", "  #  ", "   # "),
    ")": (" #   ", "  #  ", "  #  ", "  #  ", " #   "),
    "[": (" ### ", " #   ", " #   ", " #   ", " ### "),
    "]": (" ### ", "   # ", "   # ", "   # ", " ### "),
    "{": ("   ##", "  #  ", " ##  ", "  #  ", "   ##"),
    "}": ("##   ", "  #  ", "  ## ", "  #  ", "##   "),
    "@": (" ### ", "# ###", "# # #", "# ## ", " ### "),
    "#": (" # # ", "#####", " # # ", "#####", " # # "),
    "$": (" ####", "# #  ", " ### ", "  # #", "#### "),
    "%": ("#   #", "   # ", "  #  ", " #   ", "#   #"),
    "&": (" ##  ", "#  # ", " ##  ", "#  # ", " ## #"),
    "*": ("# # #", " ### ", "#####", " ### ", "# # #"),
    "<": ("   # ", "  #  ", " #   ", "  #  ", "   # "),
    ">": (" #   ", "  #  ", "   # ", "  #  ", " #   "),
    "|": ("  #  ", "  #  ", "  #  ", "  #  ", "  #  "),
}

STYLE_CHARACTERS: dict[str, str] = {
    "block": "#",
    "star": "*",
    "light": "+",
    "dot": ".",
}


@dataclass(frozen=True)
class ArtResult:
    """Result returned by :func:`generate_ascii_art`."""

    art: str
    unsupported_characters: tuple[str, ...]


def available_fonts() -> tuple[str, ...]:
    """Return the names of supported ASCII art styles."""

    return tuple(STYLE_CHARACTERS.keys())


def validate_text(text: str) -> str:
    """Validate and normalize user text input.

    Args:
        text: User-provided text.

    Returns:
        The original text if it contains at least one non-whitespace character.

    Raises:
        ValueError: If text is empty or contains only whitespace.
    """

    if text is None or not text.strip():
        raise ValueError("Please provide a non-empty string.")
    return text


def normalize_font(font: str) -> str:
    """Validate and normalize a font/style name."""

    normalized = font.strip().lower()
    if normalized not in STYLE_CHARACTERS:
        valid = ", ".join(available_fonts())
        raise ValueError(f"Unsupported font style '{font}'. Available styles: {valid}.")
    return normalized


def generate_ascii_art(text: str, font: str = "block") -> ArtResult:
    """Generate ASCII art for text using the requested style.

    Unsupported non-space characters are skipped in the visual output and
    reported in ``ArtResult.unsupported_characters``. Spaces are preserved with
    a fixed-width blank glyph.
    """

    validate_text(text)
    font_name = normalize_font(font)
    draw_char = STYLE_CHARACTERS[font_name]
    rows = [""] * FONT_HEIGHT
    unsupported: list[str] = []

    for character in text:
        if character == " ":
            glyph = tuple(" " * SPACE_WIDTH for _ in range(FONT_HEIGHT))
        else:
            glyph = GLYPHS.get(character.upper())
            if glyph is None:
                if character not in unsupported:
                    unsupported.append(character)
                glyph = tuple(" " * SPACE_WIDTH for _ in range(FONT_HEIGHT))

        rendered_glyph = _render_glyph(glyph, draw_char)
        for index, line in enumerate(rendered_glyph):
            rows[index] += line + (" " * CHAR_SPACING)

    art = "\n".join(row.rstrip() for row in rows)
    return ArtResult(art=art, unsupported_characters=tuple(unsupported))


def save_art_to_file(art: str, filepath: str | Path) -> Path:
    """Save ASCII art to a UTF-8 text file and return the resolved path."""

    path = Path(filepath).expanduser()
    if not str(path):
        raise ValueError("Output file path cannot be empty.")
    if path.exists() and path.is_dir():
        raise ValueError(f"Output path is a directory, not a file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(art + "\n", encoding="utf-8")
    return path


def format_unsupported_warning(characters: Sequence[str]) -> str:
    """Create a user-friendly warning for unsupported characters."""

    if not characters:
        return ""
    shown = ", ".join(repr(character) for character in characters)
    return f"Warning: unsupported character(s) skipped: {shown}"


def _render_glyph(glyph: Iterable[str], draw_char: str) -> tuple[str, ...]:
    """Render a glyph template with the selected drawing character."""

    return tuple(
        "".join(draw_char if cell != " " else " " for cell in row) for row in glyph
    )

"""ASCII art generation utilities.

This module provides a small built-in block font so the application works
without third-party dependencies. Input is validated as printable ASCII and
long text is wrapped at character boundaries to avoid overly wide output.
"""

from __future__ import annotations

from typing import Dict, List, Sequence

FONT_HEIGHT = 5
DEFAULT_MAX_WIDTH = 80
CHAR_SPACING = 1

FONT: Dict[str, Sequence[str]] = {
    "A": (" ### ", "#   #", "#####", "#   #", "#   #"),
    "B": ("#### ", "#   #", "#### ", "#   #", "#### "),
    "C": (" ####", "#    ", "#    ", "#    ", " ####"),
    "D": ("#### ", "#   #", "#   #", "#   #", "#### "),
    "E": ("#####", "#    ", "#### ", "#    ", "#####"),
    "F": ("#####", "#    ", "#### ", "#    ", "#    "),
    "G": (" ####", "#    ", "#  ##", "#   #", " ####"),
    "H": ("#   #", "#   #", "#####", "#   #", "#   #"),
    "I": ("#####", "  #  ", "  #  ", "  #  ", "#####"),
    "J": ("#####", "   # ", "   # ", "#  # ", " ##  "),
    "K": ("#   #", "#  # ", "###  ", "#  # ", "#   #"),
    "L": ("#    ", "#    ", "#    ", "#    ", "#####"),
    "M": ("#   #", "## ##", "# # #", "#   #", "#   #"),
    "N": ("#   #", "##  #", "# # #", "#  ##", "#   #"),
    "O": (" ### ", "#   #", "#   #", "#   #", " ### "),
    "P": ("#### ", "#   #", "#### ", "#    ", "#    "),
    "Q": (" ### ", "#   #", "# # #", "#  ##", " ####"),
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
    " ": ("   ", "   ", "   ", "   ", "   "),
    "!": (" # ", " # ", " # ", "   ", " # "),
    "?": ("### ", "   #", " ## ", "    ", " #  "),
    ".": ("   ", "   ", "   ", "   ", " # "),
    ",": ("   ", "   ", "   ", " # ", "#  "),
    ":": ("   ", " # ", "   ", " # ", "   "),
    ";": ("   ", " # ", "   ", " # ", "#  "),
    "-": ("    ", "    ", "####", "    ", "    "),
    "_": ("    ", "    ", "    ", "    ", "####"),
    "+": ("     ", "  #  ", "#####", "  #  ", "     "),
    "=": ("    ", "####", "    ", "####", "    "),
    "/": ("    #", "   # ", "  #  ", " #   ", "#    "),
    "\\": ("#    ", " #   ", "  #  ", "   # ", "    #"),
    "'": (" # ", " # ", "   ", "   ", "   "),
    '"': ("# #", "# #", "   ", "   ", "   "),
    "(": ("  #", " # ", " # ", " # ", "  #"),
    ")": ("#  ", " # ", " # ", " # ", "#  "),
}


def validate_text(text: str) -> None:
    """Validate that text is non-empty printable ASCII.

    Raises:
        ValueError: If the text is empty or contains non-printable/non-ASCII
            characters.
    """
    if text == "":
        raise ValueError("Input cannot be empty.")

    invalid_chars = [char for char in text if ord(char) < 32 or ord(char) > 126]
    if invalid_chars:
        raise ValueError("Input contains invalid non-printable characters.")


def _fallback_glyph(char: str) -> Sequence[str]:
    """Return a small literal glyph for printable punctuation not in FONT."""
    return ("   ", f" {char} ", "   ", f" {char} ", "   ")


def _glyph_for(char: str) -> Sequence[str]:
    """Return the glyph for a character, using uppercase block letters."""
    return FONT.get(char.upper(), _fallback_glyph(char))


def _glyph_width(char: str) -> int:
    """Return rendered width for a single character glyph."""
    return max(len(row) for row in _glyph_for(char))


def _wrap_text(text: str, max_width: int) -> List[str]:
    """Wrap text into chunks whose rendered width is at most max_width.

    Wrapping happens at spaces where possible, otherwise at character
    boundaries. A single character wider than max_width is still emitted.
    """
    chunks: List[str] = []
    current = ""
    current_width = 0
    last_space_index = -1

    for char in text:
        char_width = _glyph_width(char)
        added_width = char_width if current == "" else char_width + CHAR_SPACING

        if current and current_width + added_width > max_width:
            if last_space_index > 0:
                chunks.append(current[:last_space_index].rstrip())
                remaining = current[last_space_index + 1 :].lstrip()
                current = remaining
                current_width = _rendered_width(current)
                last_space_index = current.rfind(" ")
                added_width = char_width if current == "" else char_width + CHAR_SPACING

                if current and current_width + added_width > max_width:
                    chunks.append(current)
                    current = ""
                    current_width = 0
                    last_space_index = -1
                    added_width = char_width
            else:
                chunks.append(current)
                current = ""
                current_width = 0
                last_space_index = -1
                added_width = char_width

        current += char
        current_width += added_width
        if char == " ":
            last_space_index = len(current) - 1

    if current:
        chunks.append(current.rstrip())

    return [chunk for chunk in chunks if chunk != ""]


def _rendered_width(text: str) -> int:
    """Return the rendered width of text without wrapping."""
    if not text:
        return 0
    return sum(_glyph_width(char) for char in text) + CHAR_SPACING * (len(text) - 1)


def _render_line(text: str) -> List[str]:
    """Render one unwrapped text line into ASCII art rows."""
    rows = [""] * FONT_HEIGHT
    for index, char in enumerate(text):
        glyph = _glyph_for(char)
        width = max(len(row) for row in glyph)
        for row_index in range(FONT_HEIGHT):
            padded_row = glyph[row_index].ljust(width)
            rows[row_index] += padded_row
            if index < len(text) - 1:
                rows[row_index] += " " * CHAR_SPACING
    return [row.rstrip() for row in rows]


def generate_ascii_art(text: str, max_width: int = DEFAULT_MAX_WIDTH) -> str:
    """Generate wrapped ASCII art for printable ASCII text.

    Args:
        text: Input text to render.
        max_width: Maximum target width for each rendered block.

    Returns:
        A string containing ASCII art.

    Raises:
        ValueError: If validation fails or max_width is invalid.
    """
    validate_text(text)
    if max_width < 1:
        raise ValueError("Maximum width must be at least 1.")

    rendered_blocks = ["\n".join(_render_line(chunk)) for chunk in _wrap_text(text, max_width)]
    return "\n\n".join(rendered_blocks)

"""ASCII art generation utilities.

This module provides a small dependency-free ASCII art renderer that can be
used from Python code or by the command-line interface in ``src/main.py``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


class AsciiArtError(ValueError):
    """Base exception raised for user-correctable ASCII art errors."""


class InvalidInputError(AsciiArtError):
    """Raised when input text is empty or contains unsupported characters."""


class FontError(AsciiArtError):
    """Raised when a requested font is not available."""


GLYPH_HEIGHT = 5
Glyph = Tuple[str, str, str, str, str]

_BLOCK_GLYPHS: Dict[str, Glyph] = {
    " ": ("     ", "     ", "     ", "     ", "     "),
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
    "1": ("  #  ", " ##  ", "  #  ", "  #  ", "#####"),
    "2": (" ### ", "#   #", "   # ", "  #  ", "#####"),
    "3": ("#### ", "    #", " ### ", "    #", "#### "),
    "4": ("#   #", "#   #", "#####", "    #", "    #"),
    "5": ("#####", "#    ", "#### ", "    #", "#### "),
    "6": (" ### ", "#    ", "#### ", "#   #", " ### "),
    "7": ("#####", "   # ", "  #  ", " #   ", "#    "),
    "8": (" ### ", "#   #", " ### ", "#   #", " ### "),
    "9": (" ### ", "#   #", " ####", "    #", " ### "),
    ".": ("     ", "     ", "     ", "     ", "  #  "),
    ",": ("     ", "     ", "     ", "  #  ", " #   "),
    "!": ("  #  ", "  #  ", "  #  ", "     ", "  #  "),
    "?": (" ### ", "#   #", "   # ", "     ", "  #  "),
    "-": ("     ", "     ", "#####", "     ", "     "),
    "_": ("     ", "     ", "     ", "     ", "#####"),
    ":": ("     ", "  #  ", "     ", "  #  ", "     "),
    ";": ("     ", "  #  ", "     ", "  #  ", " #   "),
    "'": ("  #  ", "  #  ", "     ", "     ", "     "),
    '"': (" # # ", " # # ", "     ", "     ", "     "),
    "/": ("    #", "   # ", "  #  ", " #   ", "#    "),
    "\\": ("#    ", " #   ", "  #  ", "   # ", "    #"),
    "(": ("   # ", "  #  ", "  #  ", "  #  ", "   # "),
    ")": (" #   ", "  #  ", "  #  ", "  #  ", " #   "),
    "+": ("     ", "  #  ", "#####", "  #  ", "     "),
    "=": ("     ", "#####", "     ", "#####", "     "),
}

_FONT_CHARS = {
    "block": "#",
    "star": "*",
    "outline": "@",
}

_ALLOWED_FONTS = tuple(_FONT_CHARS.keys()) + ("simple",)


def available_fonts() -> Tuple[str, ...]:
    """Return the names of supported font styles."""

    return _ALLOWED_FONTS


def validate_text(text: str) -> str:
    """Validate and normalize text supplied for ASCII art generation.

    Args:
        text: Text to validate. Newline characters are allowed for multi-line
            input. All other characters must be printable 7-bit ASCII.

    Returns:
        The input with CRLF/CR line endings normalized to ``\n``.

    Raises:
        InvalidInputError: If the value is empty or contains non-printable or
            non-ASCII characters.
    """

    if text is None:
        raise InvalidInputError("Input text is required.")

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if normalized == "":
        raise InvalidInputError("Input text must not be empty.")

    for index, char in enumerate(normalized):
        if char == "\n":
            continue
        if not (32 <= ord(char) <= 126):
            raise InvalidInputError(
                "Input text must contain only printable ASCII characters; "
                f"invalid character at position {index}: {char!r}."
            )

    return normalized


def _fallback_glyph(char: str) -> Glyph:
    """Create a readable 5x5 fallback glyph for printable punctuation."""

    if char == " ":
        return _BLOCK_GLYPHS[" "]
    repeated = char * 5
    return (repeated, char + "   " + char, "  " + char + "  ", char + "   " + char, repeated)


def _glyph_for_char(char: str, font: str) -> Glyph:
    lookup_char = char.upper() if char.isalpha() else char
    base_glyph = _BLOCK_GLYPHS.get(lookup_char, _fallback_glyph(char))
    if font == "block":
        return base_glyph

    replacement = _FONT_CHARS[font]
    glyph_char = "#" if lookup_char in _BLOCK_GLYPHS else char
    translated: List[str] = []
    for row in base_glyph:
        translated.append("".join(replacement if item == glyph_char else item for item in row))
    return tuple(translated)  # type: ignore[return-value]


def _render_line(line: str, font: str, spacing: int) -> List[str]:
    rows = [""] * GLYPH_HEIGHT
    spacer = " " * spacing
    glyphs = [_glyph_for_char(char, font) for char in line]
    for row_index in range(GLYPH_HEIGHT):
        rows[row_index] = spacer.join(glyph[row_index] for glyph in glyphs).rstrip()
    return rows


def _render_simple(text: str) -> str:
    lines = text.split("\n")
    rendered: List[str] = []
    for line in lines:
        border = "+" + "-" * (len(line) + 2) + "+"
        rendered.extend([border, f"| {line} |", border])
    return "\n".join(rendered)


def generate_ascii_art(text: str, font: str = "block", spacing: int = 1) -> str:
    """Generate ASCII art from text.

    Args:
        text: Printable ASCII text. Newlines create separate rendered blocks.
        font: One of ``block``, ``star``, ``outline``, or ``simple``.
        spacing: Number of spaces between rendered glyphs for large fonts.

    Returns:
        The rendered ASCII art as a string.

    Raises:
        InvalidInputError: If text is empty or contains non-printable content.
        FontError: If the requested font is unsupported.
        ValueError: If spacing is negative.
    """

    normalized = validate_text(text)
    if font not in _ALLOWED_FONTS:
        supported = ", ".join(_ALLOWED_FONTS)
        raise FontError(f"Unsupported font '{font}'. Supported fonts: {supported}.")
    if spacing < 0:
        raise ValueError("Spacing must be zero or greater.")

    if font == "simple":
        return _render_simple(normalized)

    output_rows: List[str] = []
    lines = normalized.split("\n")
    for line_number, line in enumerate(lines):
        if line == "":
            output_rows.append("")
        else:
            output_rows.extend(_render_line(line, font, spacing))
        if line_number < len(lines) - 1:
            output_rows.append("")
    return "\n".join(output_rows)


def save_ascii_art(art: str, output_path: str | Path) -> None:
    """Save generated ASCII art to a text file.

    Args:
        art: Rendered ASCII art to save.
        output_path: Destination file path.

    Raises:
        OSError: With an augmented message when the file cannot be written.
    """

    path = Path(output_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(art + "\n", encoding="utf-8")
    except OSError as exc:
        raise OSError(f"Could not write ASCII art to '{path}': {exc}") from exc


def render_or_save(
    text: str,
    font: str = "block",
    output_path: Optional[str | Path] = None,
    spacing: int = 1,
) -> str:
    """Generate ASCII art and optionally save it to a file.

    The generated art is always returned, which makes the function convenient
    for tests and for applications that want to decide how to display it.
    """

    art = generate_ascii_art(text=text, font=font, spacing=spacing)
    if output_path is not None:
        save_ascii_art(art, output_path)
    return art

"""ASCII art generation utilities."""

from __future__ import annotations

from typing import Dict, List

Glyph = List[str]

GLYPH_HEIGHT = 5

FONT: Dict[str, Glyph] = {
    "A": ["  A  ", " A A ", "AAAAA", "A   A", "A   A"],
    "B": ["BBBB ", "B   B", "BBBB ", "B   B", "BBBB "],
    "C": [" CCC ", "C   C", "C    ", "C   C", " CCC "],
    "D": ["DDDD ", "D   D", "D   D", "D   D", "DDDD "],
    "E": ["EEEEE", "E    ", "EEEE ", "E    ", "EEEEE"],
    "F": ["FFFFF", "F    ", "FFFF ", "F    ", "F    "],
    "G": [" GGG ", "G    ", "G GGG", "G   G", " GGG "],
    "H": ["H   H", "H   H", "HHHHH", "H   H", "H   H"],
    "I": ["IIIII", "  I  ", "  I  ", "  I  ", "IIIII"],
    "J": ["JJJJJ", "   J ", "   J ", "J  J ", " JJ  "],
    "K": ["K   K", "K  K ", "KKK  ", "K  K ", "K   K"],
    "L": ["L    ", "L    ", "L    ", "L    ", "LLLLL"],
    "M": ["M   M", "MM MM", "M M M", "M   M", "M   M"],
    "N": ["N   N", "NN  N", "N N N", "N  NN", "N   N"],
    "O": [" OOO ", "O   O", "O   O", "O   O", " OOO "],
    "P": ["PPPP ", "P   P", "PPPP ", "P    ", "P    "],
    "Q": [" QQQ ", "Q   Q", "Q   Q", "Q  Q ", " QQ Q"],
    "R": ["RRRR ", "R   R", "RRRR ", "R  R ", "R   R"],
    "S": [" SSS ", "S    ", " SSS ", "    S", "SSSS "],
    "T": ["TTTTT", "  T  ", "  T  ", "  T  ", "  T  "],
    "U": ["U   U", "U   U", "U   U", "U   U", " UUU "],
    "V": ["V   V", "V   V", "V   V", " V V ", "  V  "],
    "W": ["W   W", "W   W", "W W W", "WW WW", "W   W"],
    "X": ["X   X", " X X ", "  X  ", " X X ", "X   X"],
    "Y": ["Y   Y", " Y Y ", "  Y  ", "  Y  ", "  Y  "],
    "Z": ["ZZZZZ", "   Z ", "  Z  ", " Z   ", "ZZZZZ"],
    "0": [" 000 ", "0   0", "0   0", "0   0", " 000 "],
    "1": ["  1  ", " 11  ", "  1  ", "  1  ", "11111"],
    "2": [" 222 ", "2   2", "   2 ", "  2  ", "22222"],
    "3": ["3333 ", "    3", " 333 ", "    3", "3333 "],
    "4": ["4  4 ", "4  4 ", "44444", "   4 ", "   4 "],
    "5": ["55555", "5    ", "5555 ", "    5", "5555 "],
    "6": [" 666 ", "6    ", "6666 ", "6   6", " 666 "],
    "7": ["77777", "   7 ", "  7  ", " 7   ", "7    "],
    "8": [" 888 ", "8   8", " 888 ", "8   8", " 888 "],
    "9": [" 999 ", "9   9", " 9999", "    9", " 999 "],
    "?": ["???? ", "   ? ", "  ?? ", "     ", "  ?  "],
}

SPACE_GLYPH: Glyph = ["     "] * GLYPH_HEIGHT
CHAR_SEPARATOR = "  "


def validate_text(text: str) -> str:
    """Validate and normalize input text.

    Args:
        text: User-provided text.

    Returns:
        The original text when it is a non-empty string.

    Raises:
        ValueError: If text is not a string or contains only whitespace.
    """
    if not isinstance(text, str):
        raise ValueError("Input must be a string.")
    if text.strip() == "":
        raise ValueError("Input cannot be empty.")
    return text


def get_glyph(character: str) -> Glyph:
    """Return a glyph for a character, falling back gracefully for unknowns."""
    if character == " ":
        return SPACE_GLYPH
    return FONT.get(character.upper(), FONT["?"])


def generate_ascii_art(text: str) -> str:
    """Convert text into standard block-style ASCII art.

    Unsupported non-alphanumeric characters are rendered as a question-mark
    glyph so the generator never crashes on special characters.
    """
    valid_text = validate_text(text)
    rows = ["" for _ in range(GLYPH_HEIGHT)]

    for character in valid_text:
        glyph = get_glyph(character)
        for row_index, glyph_row in enumerate(glyph):
            rows[row_index] += glyph_row + CHAR_SEPARATOR

    return "\n".join(row.rstrip() for row in rows)

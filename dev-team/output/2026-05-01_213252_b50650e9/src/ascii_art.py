"""ASCII art text generation utilities and command-line interface."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Iterable, TextIO

FONT_HEIGHT = 5
SPACE_WIDTH = 4

FONT: dict[str, tuple[str, ...]] = {
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
    "!": ("  #  ", "  #  ", "  #  ", "     ", "  #  "),
    "?": (" ### ", "#   #", "   # ", "     ", "  #  "),
    ".": ("     ", "     ", "     ", "     ", "  #  "),
    ",": ("     ", "     ", "     ", "  #  ", " #   "),
    "'": ("  #  ", "  #  ", "     ", "     ", "     "),
    '"': (" # # ", " # # ", "     ", "     ", "     "),
    "-": ("     ", "     ", " ### ", "     ", "     "),
    ":": ("     ", "  #  ", "     ", "  #  ", "     "),
    ";": ("     ", "  #  ", "     ", "  #  ", " #   "),
    "/": ("    #", "   # ", "  #  ", " #   ", "#    "),
    "&": (" ##  ", "#  # ", " ##  ", "#  # ", " ## #"),
}

SPACE_GLYPH = tuple(" " * SPACE_WIDTH for _ in range(FONT_HEIGHT))
UNKNOWN_REPLACEMENT = "?"


@dataclass(frozen=True)
class SanitizedInput:
    """Input text after validation and unsupported-character replacement."""

    text: str
    warnings: tuple[str, ...]


class AsciiArtError(ValueError):
    """Raised when text cannot be converted to ASCII art."""


def is_printable_ascii(character: str) -> bool:
    """Return True when *character* is a printable ASCII character or space."""

    return len(character) == 1 and 32 <= ord(character) <= 126


def sanitize_text(text: str) -> SanitizedInput:
    """Validate text and replace unsupported characters with '?'.

    Empty or whitespace-only input is rejected. Lowercase letters are accepted
    and normalized to uppercase because the built-in font is uppercase.
    Printable ASCII characters without a glyph and non-printable/non-ASCII
    characters are replaced with '?', and warning messages are returned.
    """

    if not text or not text.strip():
        raise AsciiArtError("Input is required. Please provide non-empty text.")

    sanitized: list[str] = []
    warnings: list[str] = []
    unsupported: list[str] = []

    for character in text.rstrip("\n"):
        if character == " ":
            sanitized.append(character)
            continue

        normalized = character.upper()
        if is_printable_ascii(character) and normalized in FONT:
            sanitized.append(normalized)
            continue

        sanitized.append(UNKNOWN_REPLACEMENT)
        unsupported.append(repr(character))

    if unsupported:
        unique_unsupported = sorted(set(unsupported))
        warnings.append(
            "Warning: Unsupported characters replaced with '?': "
            + ", ".join(unique_unsupported)
        )

    return SanitizedInput("".join(sanitized), tuple(warnings))


def render_ascii_art(text: str, *, spacing: int = 1) -> str:
    """Render *text* as ASCII art using the built-in block font."""

    sanitized = sanitize_text(text)
    separator = " " * spacing
    lines = ["" for _ in range(FONT_HEIGHT)]

    for character in sanitized.text:
        glyph = SPACE_GLYPH if character == " " else FONT[character]
        for row_index, glyph_row in enumerate(glyph):
            lines[row_index] += glyph_row + separator

    return "\n".join(line.rstrip() for line in lines)


def generate_ascii_art_with_warnings(text: str) -> tuple[str, tuple[str, ...]]:
    """Return rendered ASCII art and any validation warnings."""

    sanitized = sanitize_text(text)
    art = render_sanitized_text(sanitized.text)
    return art, sanitized.warnings


def render_sanitized_text(text: str, *, spacing: int = 1) -> str:
    """Render already-sanitized text. Intended for internal use and tests."""

    separator = " " * spacing
    lines = ["" for _ in range(FONT_HEIGHT)]
    for character in text:
        glyph = SPACE_GLYPH if character == " " else FONT[character]
        for row_index, glyph_row in enumerate(glyph):
            lines[row_index] += glyph_row + separator
    return "\n".join(line.rstrip() for line in lines)


def read_input(arguments: Iterable[str], stdin: TextIO) -> str:
    """Read text from command-line arguments or standard input."""

    argument_list = list(arguments)
    if argument_list:
        return " ".join(argument_list)

    if stdin.isatty():
        return ""
    return stdin.read()


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""

    parser = argparse.ArgumentParser(
        description="Generate ASCII art from printable text."
    )
    parser.add_argument(
        "text",
        nargs="*",
        help="Text to render. If omitted, text is read from standard input.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the ASCII art command-line program."""

    parser = build_parser()
    parsed_args = parser.parse_args(argv)
    text = read_input(parsed_args.text, sys.stdin)

    try:
        art, warnings = generate_ascii_art_with_warnings(text)
    except AsciiArtError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    for warning in warnings:
        print(warning, file=sys.stderr)
    print(art)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

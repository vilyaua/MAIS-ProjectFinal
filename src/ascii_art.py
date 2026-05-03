"""ASCII art generation utilities and command-line interface."""

from __future__ import annotations

import argparse
import string
import sys
from dataclasses import dataclass
from typing import Iterable, Sequence


class AsciiArtError(Exception):
    """Base exception for ASCII art generation failures."""


class EmptyInputError(AsciiArtError):
    """Raised when the supplied text is empty or whitespace only."""


class UnsupportedCharacterError(AsciiArtError):
    """Raised when the supplied text contains unsupported characters."""


class FontNotFoundError(AsciiArtError):
    """Raised when a requested font is not available."""


@dataclass(frozen=True)
class FontStyle:
    """A renderable font style based on 5x7 bitmap glyphs."""

    name: str
    filled: str
    empty: str = " "
    horizontal_gap: str = " "
    space_width: int = 4


FONT_STYLES: dict[str, FontStyle] = {
    "block": FontStyle(name="block", filled="█"),
    "hash": FontStyle(name="hash", filled="#"),
    "star": FontStyle(name="star", filled="*"),
}

# 5x7 bitmap glyphs. A 1 means filled, 0 means blank.
# Lowercase input is intentionally rendered using the uppercase glyph.
GLYPHS: dict[str, tuple[str, ...]] = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10011", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "J": ("00111", "00010", "00010", "00010", "10010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    ".": ("00000", "00000", "00000", "00000", "00000", "00110", "00110"),
    ",": ("00000", "00000", "00000", "00000", "00110", "00100", "01000"),
    ":": ("00000", "00110", "00110", "00000", "00110", "00110", "00000"),
    ";": ("00000", "00110", "00110", "00000", "00110", "00100", "01000"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "\\": ("10000", "01000", "01000", "00100", "00010", "00010", "00001"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "@": ("01110", "10001", "10111", "10101", "10111", "10000", "01110"),
}

SUPPORTED_CHARACTERS = frozenset(GLYPHS) | {" "}
PRINTABLE_ASCII = set(string.printable) - {"\x0b", "\x0c", "\r", "\n", "\t"}


def available_fonts() -> tuple[str, ...]:
    """Return the names of supported font styles."""

    return tuple(FONT_STYLES)


def validate_text(text: str) -> None:
    """Validate user-provided text before conversion.

    Args:
        text: Text to validate.

    Raises:
        EmptyInputError: If text is empty or whitespace only.
        UnsupportedCharacterError: If text includes non-printable or unsupported
            printable characters.
    """

    if not text or not text.strip():
        raise EmptyInputError("Please provide non-empty text to convert.")

    invalid = sorted({char for char in text if char not in PRINTABLE_ASCII})
    if invalid:
        joined = ", ".join(repr(char) for char in invalid)
        raise UnsupportedCharacterError(
            f"Input contains unsupported non-printable or non-ASCII character(s): {joined}."
        )

    unsupported = sorted({char for char in text.upper() if char not in SUPPORTED_CHARACTERS})
    if unsupported:
        joined = ", ".join(repr(char) for char in unsupported)
        raise UnsupportedCharacterError(
            f"Input contains unsupported character(s): {joined}. "
            f"Supported characters are letters, numbers, spaces, and: "
            f"{''.join(sorted(SUPPORTED_CHARACTERS - set(string.ascii_uppercase) - set(string.digits) - {' '}))}"
        )


def get_font(font_name: str) -> FontStyle:
    """Return a font style by name.

    Args:
        font_name: Name of the requested font.

    Raises:
        FontNotFoundError: If the font is unknown.
    """

    try:
        return FONT_STYLES[font_name]
    except KeyError as exc:
        options = ", ".join(available_fonts())
        raise FontNotFoundError(
            f"Unknown font '{font_name}'. Available fonts: {options}."
        ) from exc


def _render_glyph_row(pattern: str, font: FontStyle) -> str:
    return "".join(font.filled if pixel == "1" else font.empty for pixel in pattern)


def render_text(text: str, font_name: str = "block") -> str:
    """Convert text into multi-line ASCII art.

    Args:
        text: Input text to render. Multi-word input is supported, and spaces are
            preserved as wider blank glyphs.
        font_name: Font style name. See :func:`available_fonts`.

    Returns:
        Rendered ASCII art as a string.

    Raises:
        EmptyInputError: If text is empty.
        UnsupportedCharacterError: If unsupported characters are present.
        FontNotFoundError: If font_name is unknown.
        AsciiArtError: If rendering unexpectedly fails.
    """

    validate_text(text)
    font = get_font(font_name)
    normalized = text.upper()
    rows = ["" for _ in range(7)]

    try:
        for char in normalized:
            if char == " ":
                glyph_rows = tuple("0" * font.space_width for _ in range(7))
            else:
                glyph_rows = GLYPHS[char]
            for index, glyph_row in enumerate(glyph_rows):
                rows[index] += _render_glyph_row(glyph_row, font) + font.horizontal_gap
    except KeyError as exc:
        raise UnsupportedCharacterError(f"No glyph is available for {exc.args[0]!r}.") from exc
    except Exception as exc:
        raise AsciiArtError(f"ASCII art conversion failed: {exc}") from exc

    return "\n".join(row.rstrip() for row in rows)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""

    parser = argparse.ArgumentParser(
        description="Generate ASCII art from command-line text input."
    )
    parser.add_argument(
        "text",
        nargs="*",
        help=(
            "Text to convert. Quote multi-word text, or provide words separated "
            "by spaces; spacing between arguments is preserved as a single space."
        ),
    )
    parser.add_argument(
        "-f",
        "--font",
        default="block",
        help=f"Font style to use. Available: {', '.join(available_fonts())}. Default: block.",
    )
    parser.add_argument(
        "--list-fonts",
        action="store_true",
        help="List available font styles and exit.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the ASCII art generator CLI.

    Args:
        argv: Optional argument list for tests. Defaults to sys.argv.

    Returns:
        Process exit code.
    """

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_fonts:
        print("Available fonts:")
        for font in available_fonts():
            print(f"  - {font}")
        return 0

    text = " ".join(args.text)
    try:
        print(render_text(text, args.font))
    except AsciiArtError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""ASCII art generation utilities.

The module exposes :func:`render_ascii_art` for programmatic use and a
small CLI entry point through :func:`main`.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Iterable


class AsciiArtError(ValueError):
    """Base exception for ASCII art input errors."""


class EmptyInputError(AsciiArtError):
    """Raised when input text is empty or only whitespace."""


class UnsupportedCharacterError(AsciiArtError):
    """Raised when unsupported characters are encountered in strict mode."""


BLOCK_FONT: dict[str, tuple[str, ...]] = {
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
    "6": (" ####", "#    ", "#### ", "#   #", " ### "),
    "7": ("#####", "   # ", "  #  ", " #   ", "#    "),
    "8": (" ### ", "#   #", " ### ", "#   #", " ### "),
    "9": (" ### ", "#   #", " ####", "    #", "#### "),
    "?": (" ### ", "#   #", "  ## ", "     ", "  #  "),
    " ": ("     ", "     ", "     ", "     ", "     "),
}

SUPPORTED_FONTS = {"block", "simple"}


@dataclass(frozen=True)
class RenderResult:
    """Rendered ASCII art and any non-fatal warnings."""

    art: str
    warnings: tuple[str, ...] = ()


def _validate_text(text: str | None) -> str:
    if text is None:
        raise EmptyInputError("Input cannot be empty or null.")
    if not isinstance(text, str):
        raise AsciiArtError("Input must be a string.")
    if text.strip() == "":
        raise EmptyInputError("Input cannot be empty.")
    return text


def _validate_options(font: str, size: int) -> None:
    if font not in SUPPORTED_FONTS:
        valid = ", ".join(sorted(SUPPORTED_FONTS))
        raise AsciiArtError(f"Unsupported font '{font}'. Choose one of: {valid}.")
    if not isinstance(size, int) or size < 1:
        raise AsciiArtError("Size must be a positive integer.")


def _simple_glyph(character: str) -> tuple[str, ...]:
    display = character.upper() if character.isalpha() else character
    return (f" {display} ", f"{display}{display}{display}", f" {display} ")


def _get_glyph(
    character: str,
    font: str,
    placeholder: str,
    strict: bool,
) -> tuple[tuple[str, ...], str | None]:
    if character == " ":
        return BLOCK_FONT[" "] if font == "block" else ("   ", "   ", "   "), None

    if font == "simple" and character.isalnum() and character.isascii():
        return _simple_glyph(character), None

    lookup = character.upper() if character.isalpha() else character
    if lookup in BLOCK_FONT and (lookup.isalnum() or lookup == "?"):
        return BLOCK_FONT[lookup], None

    message = f"Unsupported character '{character}' replaced with '{placeholder}'."
    if strict:
        raise UnsupportedCharacterError(f"Unsupported character: {character!r}")

    replacement = placeholder.upper() if placeholder.isalpha() else placeholder
    glyph = BLOCK_FONT.get(replacement, BLOCK_FONT["?"])
    if font == "simple" and replacement.isalnum() and replacement.isascii():
        glyph = _simple_glyph(replacement)
    return glyph, message


def _scale_glyph(glyph: Iterable[str], size: int) -> tuple[str, ...]:
    scaled_rows: list[str] = []
    for row in glyph:
        horizontal = "".join(char * size for char in row)
        scaled_rows.extend([horizontal] * size)
    return tuple(scaled_rows)


def render_ascii_art(
    text: str | None,
    *,
    font: str = "block",
    size: int = 1,
    placeholder: str = "?",
    strict: bool = False,
    return_warnings: bool = False,
) -> str | RenderResult:
    """Convert text into ASCII art.

    Args:
        text: Text to render. Letters, digits, and spaces are supported.
        font: Font style. Supported values are ``"block"`` and ``"simple"``.
        size: Positive integer scale factor for height and width.
        placeholder: Character used to replace unsupported input in non-strict mode.
        strict: If true, unsupported characters raise an exception.
        return_warnings: If true, return a :class:`RenderResult` with warnings.

    Returns:
        Rendered ASCII art, or ``RenderResult`` when ``return_warnings`` is true.

    Raises:
        EmptyInputError: If text is empty or null.
        AsciiArtError: For invalid options.
        UnsupportedCharacterError: For unsupported characters in strict mode.
    """
    text = _validate_text(text)
    _validate_options(font, size)

    if len(placeholder) != 1:
        raise AsciiArtError("Placeholder must be a single character.")

    glyphs: list[tuple[str, ...]] = []
    warnings: list[str] = []
    for character in text:
        glyph, warning = _get_glyph(character, font, placeholder, strict)
        glyphs.append(_scale_glyph(glyph, size))
        if warning is not None:
            warnings.append(warning)

    height = len(glyphs[0])
    separator = " " * size
    lines = [separator.join(glyph[row] for glyph in glyphs).rstrip() for row in range(height)]
    art = "\n".join(lines)

    if return_warnings:
        return RenderResult(art=art, warnings=tuple(warnings))
    return art


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description="Generate ASCII art from text.")
    parser.add_argument("text", nargs="?", help="Text to convert into ASCII art.")
    parser.add_argument(
        "--font",
        choices=sorted(SUPPORTED_FONTS),
        default="block",
        help="Font style to use (default: block).",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=1,
        help="Positive integer scale factor (default: 1).",
    )
    parser.add_argument(
        "--placeholder",
        default="?",
        help="Single character for unsupported input (default: ?).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail instead of replacing unsupported characters.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the command-line interface."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        result = render_ascii_art(
            args.text,
            font=args.font,
            size=args.size,
            placeholder=args.placeholder,
            strict=args.strict,
            return_warnings=True,
        )
    except AsciiArtError as exc:
        parser.exit(status=1, message=f"Error: {exc}\n")

    assert isinstance(result, RenderResult)
    if result.warnings:
        for warning in result.warnings:
            print(f"Warning: {warning}")
    print(result.art)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

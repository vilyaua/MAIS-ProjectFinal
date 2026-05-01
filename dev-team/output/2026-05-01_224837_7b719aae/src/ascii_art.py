"""ASCII art generation utilities."""

from __future__ import annotations

import argparse
import sys
import warnings
from typing import Dict, List, Sequence

FONT_HEIGHT = 5
DEFAULT_MAX_LENGTH = 100
PLACEHOLDER = "?"

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
    " ": ("     ", "     ", "     ", "     ", "     "),
    "?": (" ### ", "#   #", "   # ", "     ", "  #  "),
}


def _validate_text(text: str, max_length: int) -> str:
    """Validate and normalize input text."""
    if not isinstance(text, str):
        raise TypeError("Input text must be a string.")
    if not isinstance(max_length, int):
        raise TypeError("max_length must be an integer.")
    if max_length <= 0:
        raise ValueError("max_length must be greater than zero.")

    normalized = text.strip()
    if not normalized:
        raise ValueError("Input text must not be empty or whitespace only.")
    if len(normalized) > max_length:
        raise ValueError(
            f"Input text is too long ({len(normalized)} characters). "
            f"Maximum supported length is {max_length}."
        )
    return normalized


def generate_ascii_art(
    text: str,
    *,
    max_length: int = DEFAULT_MAX_LENGTH,
    placeholder: str = PLACEHOLDER,
) -> str:
    """Return a block-letter ASCII art representation of *text*.

    Supported characters are A-Z, 0-9, and spaces. Unsupported characters are
    replaced with the placeholder character and reported via ``warnings.warn``.

    Args:
        text: Text to render.
        max_length: Maximum accepted input length after trimming whitespace.
        placeholder: Single supported font character used for unsupported input.

    Raises:
        TypeError: If text is not a string or max_length is not an integer.
        ValueError: If input is empty, too long, or placeholder is invalid.
    """
    normalized = _validate_text(text, max_length)
    if not isinstance(placeholder, str) or len(placeholder) != 1:
        raise ValueError("placeholder must be a single character string.")
    if placeholder.upper() not in FONT:
        raise ValueError("placeholder must be a supported font character.")

    placeholder_key = placeholder.upper()
    glyph_keys: List[str] = []
    unsupported: List[str] = []

    for character in normalized.upper():
        if character in FONT:
            glyph_keys.append(character)
        else:
            glyph_keys.append(placeholder_key)
            unsupported.append(character)

    if unsupported:
        unique_characters = "".join(dict.fromkeys(unsupported))
        warnings.warn(
            "Unsupported characters were replaced with "
            f"{placeholder_key!r}: {unique_characters!r}",
            UserWarning,
            stacklevel=2,
        )

    rows = []
    for row_index in range(FONT_HEIGHT):
        rows.append("  ".join(FONT[key][row_index] for key in glyph_keys).rstrip())
    return "\n".join(rows)


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(description="Generate ASCII art from text.")
    parser.add_argument("text", nargs="?", help="Text to render as ASCII art.")
    parser.add_argument(
        "--max-length",
        type=int,
        default=DEFAULT_MAX_LENGTH,
        help=f"Maximum input length (default: {DEFAULT_MAX_LENGTH}).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the ASCII art command-line interface."""
    parser = build_parser()
    args = parser.parse_args(argv)

    input_text = args.text
    if input_text is None:
        input_text = input("Enter text to render: ")

    try:
        print(generate_ascii_art(input_text, max_length=args.max_length))
    except (TypeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

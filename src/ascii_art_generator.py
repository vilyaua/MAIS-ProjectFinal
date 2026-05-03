"""ASCII art generation and validation utilities.

This module provides a small built-in block font so the command line program
works without third-party dependencies. It supports printable text, including
spaces, punctuation, numbers, and mixed case letters.
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

FONT_HEIGHT = 5
_SPACE_GLYPH = ("   ", "   ", "   ", "   ", "   ")
_UNKNOWN_GLYPH = ("###", "  #", " # ", "   ", " # ")

# A compact 5-row block font. Lowercase input reuses uppercase glyphs, which is
# a common convention for simple terminal ASCII-art fonts.
_FONT: Dict[str, Tuple[str, ...]] = {
    "A": (" # ", "# #", "###", "# #", "# #"),
    "B": ("## ", "# #", "## ", "# #", "## "),
    "C": (" ##", "#  ", "#  ", "#  ", " ##"),
    "D": ("## ", "# #", "# #", "# #", "## "),
    "E": ("###", "#  ", "## ", "#  ", "###"),
    "F": ("###", "#  ", "## ", "#  ", "#  "),
    "G": (" ##", "#  ", "# #", "# #", " ##"),
    "H": ("# #", "# #", "###", "# #", "# #"),
    "I": ("###", " # ", " # ", " # ", "###"),
    "J": ("  #", "  #", "  #", "# #", " # "),
    "K": ("# #", "# #", "## ", "# #", "# #"),
    "L": ("#  ", "#  ", "#  ", "#  ", "###"),
    "M": ("#   #", "## ##", "# # #", "#   #", "#   #"),
    "N": ("#  #", "## #", "# ##", "#  #", "#  #"),
    "O": (" # ", "# #", "# #", "# #", " # "),
    "P": ("## ", "# #", "## ", "#  ", "#  "),
    "Q": (" # ", "# #", "# #", " ##", "  #"),
    "R": ("## ", "# #", "## ", "# #", "# #"),
    "S": (" ##", "#  ", " # ", "  #", "## "),
    "T": ("###", " # ", " # ", " # ", " # "),
    "U": ("# #", "# #", "# #", "# #", "###"),
    "V": ("# #", "# #", "# #", "# #", " # "),
    "W": ("#   #", "#   #", "# # #", "## ##", "#   #"),
    "X": ("# #", "# #", " # ", "# #", "# #"),
    "Y": ("# #", "# #", " # ", " # ", " # "),
    "Z": ("###", "  #", " # ", "#  ", "###"),
    "0": (" # ", "# #", "# #", "# #", " # "),
    "1": (" # ", "## ", " # ", " # ", "###"),
    "2": ("## ", "  #", " # ", "#  ", "###"),
    "3": ("## ", "  #", " # ", "  #", "## "),
    "4": ("# #", "# #", "###", "  #", "  #"),
    "5": ("###", "#  ", "## ", "  #", "## "),
    "6": (" ##", "#  ", "## ", "# #", " # "),
    "7": ("###", "  #", " # ", "#  ", "#  "),
    "8": (" # ", "# #", " # ", "# #", " # "),
    "9": (" # ", "# #", " ##", "  #", "## "),
    " ": _SPACE_GLYPH,
    ".": ("   ", "   ", "   ", "   ", " # "),
    ",": ("   ", "   ", "   ", " # ", "#  "),
    "!": (" # ", " # ", " # ", "   ", " # "),
    "?": ("## ", "  #", " # ", "   ", " # "),
    ":": ("   ", " # ", "   ", " # ", "   "),
    ";": ("   ", " # ", "   ", " # ", "#  "),
    "'": (" # ", " # ", "   ", "   ", "   "),
    '"': ("# #", "# #", "   ", "   ", "   "),
    "-": ("   ", "   ", "###", "   ", "   "),
    "_": ("   ", "   ", "   ", "   ", "###"),
    "+": ("   ", " # ", "###", " # ", "   "),
    "=": ("   ", "###", "   ", "###", "   "),
    "/": ("  #", "  #", " # ", "#  ", "#  "),
    "\\": ("#  ", "#  ", " # ", "  #", "  #"),
    "|": (" # ", " # ", " # ", " # ", " # "),
    "(": ("  #", " # ", " # ", " # ", "  #"),
    ")": ("#  ", " # ", " # ", " # ", "#  "),
    "[": (" ##", " # ", " # ", " # ", " ##"),
    "]": ("## ", " # ", " # ", " # ", "## "),
    "{": ("  #", " # ", "## ", " # ", "  #"),
    "}": ("#  ", " # ", " ##", " # ", "#  "),
    "<": ("  #", " # ", "#  ", " # ", "  #"),
    ">": ("#  ", " # ", "  #", " # ", "#  "),
    "@": (" # ", "# #", "###", "#  ", " ##"),
    "#": ("# #", "###", "# #", "###", "# #"),
    "$": (" ##", "## ", " # ", " ##", "## "),
    "%": ("# #", "  #", " # ", "#  ", "# #"),
    "^": (" # ", "# #", "   ", "   ", "   "),
    "&": (" # ", "# #", " # ", "# #", " ##"),
    "*": ("# #", " # ", "###", " # ", "# #"),
    "~": ("   ", "   ", "## ", " ##", "   "),
    "`": ("#  ", " # ", "   ", "   ", "   "),
}


def validate_text(text: str) -> None:
    """Validate user text for ASCII-art generation.

    Args:
        text: Text provided by the user.

    Raises:
        ValueError: If text is empty or contains non-printable characters.
    """
    if text == "":
        raise ValueError("Input cannot be empty.")

    invalid_characters = [char for char in text if not char.isprintable()]
    if invalid_characters:
        raise ValueError("Input contains invalid non-printable characters.")


def _glyph_for(char: str) -> Tuple[str, ...]:
    """Return the glyph for a printable character."""
    if char in _FONT:
        return _FONT[char]

    upper_char = char.upper()
    if upper_char in _FONT:
        return _FONT[upper_char]

    return _UNKNOWN_GLYPH


def generate_ascii_art(text: str) -> str:
    """Generate ASCII art for validated printable text.

    Args:
        text: Non-empty printable text.

    Returns:
        A multi-line string containing ASCII art.

    Raises:
        ValueError: If text is empty or contains non-printable characters.
    """
    validate_text(text)
    rows: List[str] = [""] * FONT_HEIGHT

    for char in text:
        glyph = _glyph_for(char)
        for row_index, row in enumerate(glyph):
            rows[row_index] += row + " "

    return "\n".join(row.rstrip() for row in rows)


def is_exit_command(command: str) -> bool:
    """Return True when the command asks the program to exit."""
    return command.strip().lower() in {":exit", ":quit", "exit", "quit", "q"}


def should_restart(answer: str) -> bool:
    """Return True when the user opts to restart/generate another input."""
    return answer.strip().lower() in {"y", "yes", "r", "restart"}


def run_interactive() -> None:
    """Run the interactive command-line input loop."""
    print("ASCII Art Generator")
    print("Enter text to convert, or type ':exit' to quit.")

    while True:
        try:
            user_text = input("Text: ")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            return

        if is_exit_command(user_text):
            print("Goodbye!")
            return

        try:
            art = generate_ascii_art(user_text)
        except ValueError as error:
            print(f"Error: {error}")
            continue

        print(art)

        while True:
            try:
                answer = input("Generate another? [y/N]: ")
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                return

            if should_restart(answer):
                break
            if answer.strip().lower() in {"", "n", "no", "exit", "quit", "q"}:
                print("Goodbye!")
                return
            print("Please enter 'y' to restart or 'n' to exit.")


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point.

    If command-line arguments are supplied, they are joined with spaces and
    converted once. Otherwise, the interactive restart/exit loop is used.
    """
    args = list(argv or [])
    if args:
        text = " ".join(args)
        try:
            print(generate_ascii_art(text))
        except ValueError as error:
            print(f"Error: {error}")
            return 1
        return 0

    run_interactive()
    return 0

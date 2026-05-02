"""ASCII art text generation utilities."""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
import sys
from typing import TextIO

FONT_HEIGHT = 5
PLACEHOLDER = "?"

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
    " ": ("     ", "     ", "     ", "     ", "     "),
    "!": ("  #  ", "  #  ", "  #  ", "     ", "  #  "),
    ".": ("     ", "     ", "     ", "     ", "  #  "),
    ",": ("     ", "     ", "     ", "  #  ", " #   "),
    "?": (" ### ", "#   #", "   # ", "     ", "  #  "),
    "-": ("     ", "     ", " ### ", "     ", "     "),
    ":": ("     ", "  #  ", "     ", "  #  ", "     "),
    "'": ("  #  ", "  #  ", "     ", "     ", "     "),
}


def validate_font(font: dict[str, tuple[str, ...]] = FONT) -> None:
    """Validate that all font glyphs have the expected height and width."""
    for character, glyph in font.items():
        if len(glyph) != FONT_HEIGHT:
            raise ValueError(
                f"Font glyph for {character!r} must have {FONT_HEIGHT} rows."
            )
        widths = {len(row) for row in glyph}
        if len(widths) != 1:
            raise ValueError(f"Font glyph for {character!r} has inconsistent row widths.")


def normalize_character(character: str) -> str:
    """Return a supported font key for *character*, or the placeholder key."""
    normalized = character.upper()
    if normalized in FONT:
        return normalized
    return PLACEHOLDER


def render_line(line: str) -> str:
    """Render a single input line as ASCII art.

    Unsupported characters are replaced with the placeholder glyph, so rendering
    does not fail for special characters or non-ASCII input.
    """
    rows = ["" for _ in range(FONT_HEIGHT)]
    for character in line:
        glyph = FONT[normalize_character(character)]
        for index, glyph_row in enumerate(glyph):
            separator = " " if rows[index] else ""
            rows[index] += f"{separator}{glyph_row}"
    return "\n".join(row.rstrip() for row in rows)


def render_text(text: str) -> str:
    """Render possibly multi-line text as ASCII art.

    Raises:
        ValueError: If *text* is empty or contains only whitespace.
    """
    if not text or not text.strip():
        raise ValueError("Input cannot be empty. Please provide text to render.")

    rendered_lines: list[str] = []
    for line in text.splitlines():
        rendered_lines.append(render_line(line) if line else "")
    return "\n".join(rendered_lines)


def build_parser() -> ArgumentParser:
    """Create and return the command-line argument parser."""
    parser = ArgumentParser(description="Generate readable ASCII art from text.")
    parser.add_argument(
        "text",
        nargs="*",
        help=(
            "Text to render. If omitted, text is read from standard input, "
            "allowing multi-line input."
        ),
    )
    return parser


def read_input(args: Namespace, stdin: TextIO = sys.stdin) -> str:
    """Read input text from command-line arguments or standard input."""
    if args.text:
        return " ".join(args.text)
    return stdin.read()


def main(argv: list[str] | None = None, stdin: TextIO = sys.stdin) -> int:
    """Run the ASCII art command-line interface."""
    parser = build_parser()
    args = parser.parse_args(argv)
    text = read_input(args, stdin)

    try:
        art = render_text(text)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(art)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

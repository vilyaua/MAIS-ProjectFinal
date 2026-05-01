"""ASCII Art Text Generator.

A dependency-free command-line utility that renders text as deterministic ASCII art.
"""

from __future__ import annotations

import argparse
import string
import sys
from typing import Dict, List, Mapping, Sequence, TextIO

DEFAULT_FONT = "block"
SUPPORTED_FONTS = ("block", "simple")

Glyph = Sequence[str]
GlyphMap = Mapping[str, Glyph]

BLOCK_GLYPHS: Dict[str, Glyph] = {
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
    "Q": (" ### ", "#   #", "#   #", "#  ##", " ####"),
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
    ".": ("     ", "     ", "     ", " ##  ", " ##  "),
    ",": ("     ", "     ", "     ", " ##  ", " #   "),
    "!": ("  #  ", "  #  ", "  #  ", "     ", "  #  "),
    "?": (" ### ", "#   #", "   # ", "     ", "  #  "),
    "-": ("     ", "     ", "#####", "     ", "     "),
    "_": ("     ", "     ", "     ", "     ", "#####"),
    "+": ("     ", "  #  ", "#####", "  #  ", "     "),
    "=": ("     ", "#####", "     ", "#####", "     "),
    ":": ("     ", " ##  ", "     ", " ##  ", "     "),
    ";": ("     ", " ##  ", "     ", " ##  ", " #   "),
    "'": ("  #  ", "  #  ", "     ", "     ", "     "),
    '"': (" # # ", " # # ", "     ", "     ", "     "),
    "(": ("  ## ", " #   ", " #   ", " #   ", "  ## "),
    ")": (" ##  ", "   # ", "   # ", "   # ", " ##  "),
    "/": ("    #", "   # ", "  #  ", " #   ", "#    "),
    "\\": ("#    ", " #   ", "  #  ", "   # ", "    #"),
    "@": (" ### ", "# # #", "# ###", "#    ", " ####"),
    "#": (" # # ", "#####", " # # ", "#####", " # # "),
    "$": (" ####", "# #  ", " ### ", "  # #", "#### "),
    "%": ("#   #", "   # ", "  #  ", " #   ", "#   #"),
    "&": (" ##  ", "#  # ", " ##  ", "#  # ", " ## #"),
    "*": ("# # #", " ### ", "#####", " ### ", "# # #"),
    "[": (" ### ", " #   ", " #   ", " #   ", " ### "),
    "]": (" ### ", "   # ", "   # ", "   # ", " ### "),
    "{": ("  ## ", "  #  ", "##   ", "  #  ", "  ## "),
    "}": (" ##  ", "  #  ", "   ##", "  #  ", " ##  "),
    "<": ("   # ", "  #  ", " #   ", "  #  ", "   # "),
    ">": (" #   ", "  #  ", "   # ", "  #  ", " #   "),
    "|": ("  #  ", "  #  ", "  #  ", "  #  ", "  #  "),
    "~": ("     ", " ## #", "# ## ", "     ", "     "),
    "`": (" #   ", "  #  ", "     ", "     ", "     "),
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate ASCII art from a text argument or standard input."
    )
    parser.add_argument(
        "text",
        nargs="?",
        help="Text to render. If omitted, text is read from standard input.",
    )
    parser.add_argument(
        "-f",
        "--font",
        default=DEFAULT_FONT,
        help=f"Font/style to use. Available: {', '.join(SUPPORTED_FONTS)}.",
    )
    return parser.parse_args(argv)


def sanitize_terminal_controls(text: str) -> str:
    """Escape terminal control characters that could corrupt terminal output.

    Newlines are preserved so multi-line input can be rendered. Tabs are expanded
    to spaces. Other C0/C1 control characters are converted to visible escape
    text such as ``\\x1b`` before rendering.
    """
    safe_parts: List[str] = []
    for char in text:
        codepoint = ord(char)
        if char in {"\n", "\r"}:
            safe_parts.append("\n")
        elif char == "\t":
            safe_parts.append("    ")
        elif codepoint < 32 or 127 <= codepoint <= 159:
            safe_parts.append(f"\\x{codepoint:02x}")
        else:
            safe_parts.append(char)
    return "".join(safe_parts)


def validate_font(font: str) -> str:
    """Validate and normalize a font name.

    Raises:
        ValueError: If the font is unsupported.
    """
    normalized = font.lower().strip()
    if normalized not in SUPPORTED_FONTS:
        available = ", ".join(SUPPORTED_FONTS)
        raise ValueError(f"Invalid font/style '{font}'. Available font/styles: {available}.")
    return normalized


def _render_block_line(text: str, glyphs: GlyphMap = BLOCK_GLYPHS) -> str:
    """Render a single line using the block font."""
    rows = [""] * 5
    for char in text:
        glyph_key = char.upper()
        glyph = glyphs.get(glyph_key)
        if glyph is None:
            raise ValueError(
                f"Unsupported character {char!r} (U+{ord(char):04X}) for the "
                "block font. Try using only printable ASCII characters."
            )
        for index, glyph_row in enumerate(glyph):
            rows[index] += glyph_row + " "
    return "\n".join(row.rstrip() for row in rows).rstrip()


def _render_simple_line(text: str) -> str:
    """Render a single line using a dependency-free simple boxed style."""
    allowed = set(string.printable) - {"\x0b", "\x0c"}
    for char in text:
        if char not in allowed or char in {"\n", "\r", "\t"}:
            raise ValueError(
                f"Unsupported character {char!r} (U+{ord(char):04X}) for the simple font."
            )
    if not text:
        return ""
    border = "+" + "-" * (len(text) + 2) + "+"
    return f"{border}\n| {text} |\n{border}"


def generate_ascii_art(text: str, font: str = DEFAULT_FONT) -> str:
    """Generate ASCII art for text.

    Args:
        text: Input text after validation. Terminal controls are sanitized here.
        font: The selected built-in font/style.

    Returns:
        Rendered ASCII art.

    Raises:
        ValueError: If the font or characters are unsupported.
    """
    selected_font = validate_font(font)
    safe_text = sanitize_terminal_controls(text)
    rendered_blocks: List[str] = []
    for line in safe_text.split("\n"):
        if selected_font == "block":
            rendered_blocks.append(_render_block_line(line))
        elif selected_font == "simple":
            rendered_blocks.append(_render_simple_line(line))
        else:  # Defensive only; validate_font should prevent this.
            raise ValueError(f"Unsupported font/style: {font}")
    return "\n".join(rendered_blocks)


def read_input(args: argparse.Namespace, stdin: TextIO) -> str:
    """Read input from an argument or standard input."""
    if args.text is not None:
        return args.text
    if stdin.isatty():
        return ""
    data = stdin.read()
    if data.endswith("\r\n"):
        data = data[:-2]
    elif data.endswith("\n") or data.endswith("\r"):
        data = data[:-1]
    return data


def main(argv: Sequence[str] | None = None) -> int:
    """Run the ASCII art command-line interface."""
    args = parse_args(argv)
    try:
        text = read_input(args, sys.stdin)
        if text == "":
            print(
                "Error: input text is required. Provide a text argument or pipe "
                "non-empty text to standard input.",
                file=sys.stderr,
            )
            return 2
        art = generate_ascii_art(text, args.font)
        print(art)
        return 0
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    except ImportError as error:
        print(
            "Error: an optional ASCII art dependency could not be imported. "
            "This implementation normally uses built-in fonts only; if you "
            f"extended it with a third-party renderer, install it first. Details: {error}",
            file=sys.stderr,
        )
        return 3
    except Exception as error:  # pragma: no cover - defensive CLI guard.
        print(
            f"Error: failed to generate ASCII art due to an unexpected problem. Details: {error}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())

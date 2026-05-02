"""ASCII art generation utilities and command-line interface."""

from __future__ import annotations

import argparse
import sys
import textwrap
from dataclasses import dataclass
from typing import Callable, Mapping, Sequence


class AsciiArtError(Exception):
    """Base exception for user-facing ASCII art errors."""


class InputValidationError(AsciiArtError):
    """Raised when user input is invalid."""


class FontNotFoundError(AsciiArtError):
    """Raised when a requested font is not available."""


@dataclass(frozen=True)
class Font:
    """Represents an ASCII art font style."""

    name: str
    height: int
    renderer: Callable[[str], list[str]]


BLOCK_GLYPHS: Mapping[str, tuple[str, ...]] = {
    "A": ("  A  ", " A A ", "AAAAA", "A   A", "A   A"),
    "B": ("BBBB ", "B   B", "BBBB ", "B   B", "BBBB "),
    "C": (" CCC ", "C   C", "C    ", "C   C", " CCC "),
    "D": ("DDDD ", "D   D", "D   D", "D   D", "DDDD "),
    "E": ("EEEEE", "E    ", "EEEE ", "E    ", "EEEEE"),
    "F": ("FFFFF", "F    ", "FFFF ", "F    ", "F    "),
    "G": (" GGG ", "G    ", "G GGG", "G   G", " GGG "),
    "H": ("H   H", "H   H", "HHHHH", "H   H", "H   H"),
    "I": ("IIIII", "  I  ", "  I  ", "  I  ", "IIIII"),
    "J": ("JJJJJ", "   J ", "   J ", "J  J ", " JJ  "),
    "K": ("K   K", "K  K ", "KKK  ", "K  K ", "K   K"),
    "L": ("L    ", "L    ", "L    ", "L    ", "LLLLL"),
    "M": ("M   M", "MM MM", "M M M", "M   M", "M   M"),
    "N": ("N   N", "NN  N", "N N N", "N  NN", "N   N"),
    "O": (" OOO ", "O   O", "O   O", "O   O", " OOO "),
    "P": ("PPPP ", "P   P", "PPPP ", "P    ", "P    "),
    "Q": (" QQQ ", "Q   Q", "Q   Q", "Q  Q ", " QQ Q"),
    "R": ("RRRR ", "R   R", "RRRR ", "R  R ", "R   R"),
    "S": (" SSS ", "S    ", " SSS ", "    S", " SSS "),
    "T": ("TTTTT", "  T  ", "  T  ", "  T  ", "  T  "),
    "U": ("U   U", "U   U", "U   U", "U   U", " UUU "),
    "V": ("V   V", "V   V", "V   V", " V V ", "  V  "),
    "W": ("W   W", "W   W", "W W W", "WW WW", "W   W"),
    "X": ("X   X", " X X ", "  X  ", " X X ", "X   X"),
    "Y": ("Y   Y", " Y Y ", "  Y  ", "  Y  ", "  Y  "),
    "Z": ("ZZZZZ", "   Z ", "  Z  ", " Z   ", "ZZZZZ"),
    "0": (" 000 ", "0   0", "0   0", "0   0", " 000 "),
    "1": ("  1  ", " 11  ", "  1  ", "  1  ", "11111"),
    "2": (" 222 ", "2   2", "   2 ", "  2  ", "22222"),
    "3": ("3333 ", "    3", " 333 ", "    3", "3333 "),
    "4": ("4  4 ", "4  4 ", "44444", "   4 ", "   4 "),
    "5": ("55555", "5    ", "5555 ", "    5", "5555 "),
    "6": (" 666 ", "6    ", "6666 ", "6   6", " 666 "),
    "7": ("77777", "   7 ", "  7  ", " 7   ", "7    "),
    "8": (" 888 ", "8   8", " 888 ", "8   8", " 888 "),
    "9": (" 999 ", "9   9", " 9999", "    9", " 999 "),
    "!": ("  !  ", "  !  ", "  !  ", "     ", "  !  "),
    "?": (" ??? ", "?   ?", "   ? ", "     ", "  ?  "),
    ".": ("     ", "     ", "     ", "     ", "  .  "),
    ",": ("     ", "     ", "     ", "  ,  ", " ,   "),
    ":": ("     ", "  :  ", "     ", "  :  ", "     "),
    "-": ("     ", "     ", "-----", "     ", "     "),
    "_": ("     ", "     ", "     ", "     ", "_____"),
    " ": ("     ", "     ", "     ", "     ", "     "),
}


def render_block(text: str) -> list[str]:
    """Render text using a five-line block font."""
    lines = ["" for _ in range(5)]
    fallback = ("?????", "?   ?", "  ?? ", "     ", "  ?  ")
    for character in text.upper():
        glyph = BLOCK_GLYPHS.get(character, fallback)
        for index, glyph_line in enumerate(glyph):
            lines[index] += f"{glyph_line} "
    return [line.rstrip() for line in lines]


def render_outline(text: str) -> list[str]:
    """Render text using a compact outlined style."""
    top = ""
    middle = ""
    bottom = ""
    for character in text:
        if character == " ":
            top += "     "
            middle += "     "
            bottom += "     "
        else:
            top += f" __{character}__ "
            middle += f"/  {character}  " + "\\"
            bottom += f"\\__{character}__/"
    return [top.rstrip(), middle.rstrip(), bottom.rstrip()]


FONTS: Mapping[str, Font] = {
    "block": Font(name="block", height=5, renderer=render_block),
    "outline": Font(name="outline", height=3, renderer=render_outline),
}


def validate_text(text: str) -> str:
    """Validate and normalize user-provided text.

    Raises:
        InputValidationError: If text is empty or contains non-printable
            characters.
    """
    normalized = text.strip()
    if not normalized:
        raise InputValidationError("Input cannot be empty.")
    invalid = [character for character in normalized if not character.isprintable()]
    if invalid:
        raise InputValidationError(
            "Input contains non-printable characters; please provide printable text only."
        )
    return normalized


def wrap_text(text: str, width: int) -> list[str]:
    """Wrap text without dropping long words."""
    if width <= 0:
        raise InputValidationError("Wrap width must be a positive integer.")
    return textwrap.wrap(
        text,
        width=width,
        replace_whitespace=False,
        drop_whitespace=False,
        break_long_words=True,
        break_on_hyphens=False,
    ) or [text]


def generate_ascii_art(text: str, font_name: str = "block", wrap_width: int = 20) -> str:
    """Generate ASCII art for validated text.

    Args:
        text: Input text to render.
        font_name: Name of the font in ``FONTS``.
        wrap_width: Maximum text characters per rendered section.

    Returns:
        A console-ready string containing ASCII art.

    Raises:
        InputValidationError: For invalid text or wrap width.
        FontNotFoundError: If the requested font is unknown.
    """
    normalized = validate_text(text)
    try:
        font = FONTS[font_name]
    except KeyError as exc:
        choices = ", ".join(sorted(FONTS))
        raise FontNotFoundError(
            f"Font '{font_name}' was not found. Available fonts: {choices}."
        ) from exc

    rendered_sections: list[str] = []
    for segment in wrap_text(normalized, wrap_width):
        try:
            rendered_sections.append("\n".join(font.renderer(segment)))
        except Exception as exc:  # pragma: no cover - defensive CLI safeguard
            raise AsciiArtError(f"Could not render ASCII art: {exc}") from exc
    return "\n\n".join(rendered_sections)


def read_stdin() -> str:
    """Read all available standard input."""
    return sys.stdin.read()


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate ASCII art from text input.",
    )
    parser.add_argument(
        "text",
        nargs="*",
        help="Text to convert. If omitted, text is read from standard input.",
    )
    parser.add_argument(
        "-f",
        "--font",
        default="block",
        choices=sorted(FONTS),
        help="ASCII art font style to use.",
    )
    parser.add_argument(
        "-w",
        "--wrap-width",
        default=20,
        type=int,
        help="Maximum input characters per rendered line/section.",
    )
    return parser


def main(
    argv: Sequence[str] | None = None,
    stdin_reader: Callable[[], str] = read_stdin,
) -> int:
    """Run the command-line interface."""
    parser = build_parser()
    args = parser.parse_args(argv)
    raw_text = " ".join(args.text) if args.text else stdin_reader()

    try:
        art = generate_ascii_art(raw_text, font_name=args.font, wrap_width=args.wrap_width)
    except AsciiArtError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(art)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

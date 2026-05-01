"""Command-line ASCII art generator using pyfiglet."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from typing import Optional, Protocol, TextIO

import pyfiglet

DEFAULT_FONT = "standard"

# Common ANSI escape sequence patterns, including CSI and OSC sequences.
ANSI_ESCAPE_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1B\\))")
CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]")
WHITESPACE_TO_SPACE_RE = re.compile(r"[\t\r\n]+")


class OutputSink(Protocol):
    """Protocol for future output implementations, such as file saving."""

    def write(self, content: str) -> None:
        """Write generated ASCII art content."""


@dataclass(frozen=True)
class ConsoleOutputSink:
    """Writes ASCII art to a text stream, defaulting to stdout."""

    stream: TextIO = sys.stdout

    def write(self, content: str) -> None:
        """Print content to the configured stream."""
        print(content, file=self.stream)


@dataclass
class AsciiArtGenerator:
    """Generates sanitized ASCII art with graceful font fallback."""

    default_font: str = DEFAULT_FONT

    def sanitize_input(self, text: str) -> str:
        """Remove terminal control sequences and unsafe control characters.

        Args:
            text: User-supplied text.

        Returns:
            Sanitized text safe to render and print to a terminal.
        """
        if text is None:
            return ""

        sanitized = ANSI_ESCAPE_RE.sub("", str(text))
        sanitized = WHITESPACE_TO_SPACE_RE.sub(" ", sanitized)
        sanitized = CONTROL_CHARS_RE.sub("", sanitized)
        return sanitized.strip()

    def resolve_font(self, font: Optional[str]) -> tuple[str, Optional[str]]:
        """Return a usable font name and an optional warning message.

        Args:
            font: Requested font name, if any.

        Returns:
            A tuple of (resolved_font, warning_message). Warning is None when the
            requested font is available or no fallback is needed.
        """
        requested_font = (font or self.default_font).strip() or self.default_font
        try:
            pyfiglet.Figlet(font=requested_font)
            return requested_font, None
        except pyfiglet.FontNotFound:
            warning = (
                f"Warning: Font '{requested_font}' is not available. "
                f"Using default font '{self.default_font}'."
            )
            return self.default_font, warning

    def generate(self, text: str, font: Optional[str] = None) -> tuple[str, Optional[str]]:
        """Generate ASCII art from user text.

        Args:
            text: User-supplied text.
            font: Optional pyfiglet font name.

        Returns:
            A tuple of (ascii_art, warning_message).

        Raises:
            ValueError: If sanitized input is empty.
        """
        sanitized_text = self.sanitize_input(text)
        if not sanitized_text:
            raise ValueError("Input cannot be empty")

        resolved_font, warning = self.resolve_font(font)
        figlet = pyfiglet.Figlet(font=resolved_font)
        return figlet.renderText(sanitized_text), warning


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(description="Generate ASCII art from text using pyfiglet.")
    parser.add_argument(
        "text",
        nargs="*",
        help="Text to convert into ASCII art. If omitted, you will be prompted.",
    )
    parser.add_argument(
        "-f",
        "--font",
        default=None,
        help=f"Optional pyfiglet font name. Defaults to '{DEFAULT_FONT}'.",
    )
    return parser


def get_text_from_args_or_prompt(args: argparse.Namespace) -> str:
    """Get user text from positional arguments or an interactive prompt."""
    if args.text:
        return " ".join(args.text)
    try:
        return input("Enter text for ASCII art: ")
    except EOFError:
        return ""


def run(
    text: str,
    font: Optional[str] = None,
    output_sink: Optional[OutputSink] = None,
    error_stream: TextIO = sys.stderr,
) -> int:
    """Generate and output ASCII art.

    This small orchestration function keeps output handling separate from
    generation, making future file-output support easy to add.

    Args:
        text: User-supplied input text.
        font: Optional font name.
        output_sink: Destination for ASCII art. Defaults to console stdout.
        error_stream: Stream for warnings and errors.

    Returns:
        Process-style exit code: 0 for success, 1 for invalid input/error.
    """
    sink = output_sink or ConsoleOutputSink()
    generator = AsciiArtGenerator()

    try:
        ascii_art, warning = generator.generate(text, font)
    except ValueError as exc:
        print(str(exc), file=error_stream)
        return 1
    except Exception as exc:  # Defensive guard to avoid CLI crashes.
        print(f"Error generating ASCII art: {exc}", file=error_stream)
        return 1

    if warning:
        print(warning, file=error_stream)
    sink.write(ascii_art)
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)
    text = get_text_from_args_or_prompt(args)
    return run(text=text, font=args.font)


if __name__ == "__main__":
    sys.exit(main())

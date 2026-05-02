"""A small Markdown to HTML converter.

The module intentionally implements a practical subset of Markdown without
external dependencies: headings, emphasis, links, inline/fenced/indented code,
and ordered/unordered lists. Input that does not match a supported construct is
escaped and emitted as paragraph text so malformed Markdown remains safe and
non-fatal.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Iterable


class MarkdownConversionError(ValueError):
    """Raised when the converter receives an invalid input type."""


@dataclass(frozen=True)
class _ListMatch:
    """Represents a parsed Markdown list item marker."""

    list_type: str
    content: str


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
_ORDERED_ITEM_RE = re.compile(r"^\s{0,3}\d+[.)]\s+(.+)$")
_UNORDERED_ITEM_RE = re.compile(r"^\s{0,3}[-+*]\s+(.+)$")
_LINK_RE = re.compile(r"\[([^\]\n]+)]\(([^\s)]+)\)")
_INLINE_CODE_RE = re.compile(r"`([^`]+)`")
_STRONG_RE = re.compile(r"(\*\*|__)(?=\S)(.+?)(?<=\S)\1")
_EM_RE = re.compile(r"(?<!\*)\*(?!\s|\*)(.+?)(?<!\s|\*)\*(?!\*)|(?<!_)_(?!\s|_)(.+?)(?<!\s|_)_(?!_)")


def convert(markdown_text: str) -> str:
    """Convert a Markdown-formatted string to HTML.

    Args:
        markdown_text: Markdown source text.

    Returns:
        Converted HTML. Empty or whitespace-only input returns an empty string.

    Raises:
        MarkdownConversionError: If ``markdown_text`` is not a string.
    """
    if not isinstance(markdown_text, str):
        raise MarkdownConversionError("Markdown input must be a string.")

    if markdown_text.strip() == "":
        return ""

    parser = _MarkdownParser(markdown_text)
    return parser.parse()


def markdown_to_html(markdown_text: str) -> str:
    """Alias for :func:`convert` for a descriptive public API."""
    return convert(markdown_text)


class _MarkdownParser:
    """Line-oriented Markdown parser for supported block constructs."""

    def __init__(self, markdown_text: str) -> None:
        self._lines = markdown_text.splitlines()
        self._index = 0
        self._html_parts: list[str] = []

    def parse(self) -> str:
        """Parse all input lines and return HTML."""
        while self._index < len(self._lines):
            line = self._lines[self._index]

            if line.strip() == "":
                self._index += 1
                continue

            if line.lstrip().startswith("```"):
                self._parse_fenced_code_block()
                continue

            if self._is_indented_code_line(line):
                self._parse_indented_code_block()
                continue

            heading_html = self._parse_heading(line)
            if heading_html is not None:
                self._html_parts.append(heading_html)
                self._index += 1
                continue

            list_match = self._match_list_item(line)
            if list_match is not None:
                self._parse_list(list_match.list_type)
                continue

            self._parse_paragraph()

        return "\n".join(self._html_parts)

    def _parse_heading(self, line: str) -> str | None:
        match = _HEADING_RE.match(line)
        if not match:
            return None
        level = len(match.group(1))
        text = _parse_inline(match.group(2))
        return f"<h{level}>{text}</h{level}>"

    def _parse_fenced_code_block(self) -> None:
        opening_line = self._lines[self._index].lstrip()
        fence = opening_line[:3]
        self._index += 1
        code_lines: list[str] = []

        while self._index < len(self._lines):
            line = self._lines[self._index]
            if line.lstrip().startswith(fence):
                self._index += 1
                break
            code_lines.append(line)
            self._index += 1

        code = "\n".join(code_lines)
        self._html_parts.append(f"<pre><code>{html.escape(code)}</code></pre>")

    def _parse_indented_code_block(self) -> None:
        code_lines: list[str] = []

        while self._index < len(self._lines):
            line = self._lines[self._index]
            if line.strip() == "":
                code_lines.append("")
                self._index += 1
                continue
            if not self._is_indented_code_line(line):
                break
            code_lines.append(line[4:] if line.startswith("    ") else line[1:])
            self._index += 1

        while code_lines and code_lines[-1] == "":
            code_lines.pop()

        code = "\n".join(code_lines)
        self._html_parts.append(f"<pre><code>{html.escape(code)}</code></pre>")

    def _parse_list(self, list_type: str) -> None:
        tag = "ul" if list_type == "ul" else "ol"
        items: list[str] = []

        while self._index < len(self._lines):
            line = self._lines[self._index]
            list_match = self._match_list_item(line)
            if list_match is None or list_match.list_type != list_type:
                break
            items.append(f"<li>{_parse_inline(list_match.content)}</li>")
            self._index += 1

        self._html_parts.append(f"<{tag}>\n" + "\n".join(items) + f"\n</{tag}>")

    def _parse_paragraph(self) -> None:
        lines: list[str] = []

        while self._index < len(self._lines):
            line = self._lines[self._index]
            if line.strip() == "":
                break
            if (
                line.lstrip().startswith("```")
                or self._is_indented_code_line(line)
                or self._parse_heading(line) is not None
                or self._match_list_item(line) is not None
            ):
                break
            lines.append(line.strip())
            self._index += 1

        if lines:
            paragraph = " ".join(lines)
            self._html_parts.append(f"<p>{_parse_inline(paragraph)}</p>")
        else:
            self._index += 1

    @staticmethod
    def _is_indented_code_line(line: str) -> bool:
        return line.startswith("    ") or line.startswith("\t")

    @staticmethod
    def _match_list_item(line: str) -> _ListMatch | None:
        ordered_match = _ORDERED_ITEM_RE.match(line)
        if ordered_match:
            return _ListMatch("ol", ordered_match.group(1))

        unordered_match = _UNORDERED_ITEM_RE.match(line)
        if unordered_match:
            return _ListMatch("ul", unordered_match.group(1))

        return None


def _parse_inline(text: str) -> str:
    """Parse supported inline Markdown, escaping all literal HTML first."""
    placeholders: dict[str, str] = {}
    escaped = html.escape(text, quote=True)

    def store(fragment: str) -> str:
        token = f"\u0000{len(placeholders)}\u0000"
        placeholders[token] = fragment
        return token

    def code_replacer(match: re.Match[str]) -> str:
        return store(f"<code>{match.group(1)}</code>")

    def link_replacer(match: re.Match[str]) -> str:
        label = _parse_inline(match.group(1))
        href = html.escape(match.group(2), quote=True)
        return store(f'<a href="{href}">{label}</a>')

    escaped = _INLINE_CODE_RE.sub(code_replacer, escaped)
    escaped = _LINK_RE.sub(link_replacer, escaped)
    escaped = _STRONG_RE.sub(r"<strong>\2</strong>", escaped)

    def em_replacer(match: re.Match[str]) -> str:
        content = match.group(1) if match.group(1) is not None else match.group(2)
        return f"<em>{content}</em>"

    escaped = _EM_RE.sub(em_replacer, escaped)

    for token, fragment in placeholders.items():
        escaped = escaped.replace(token, fragment)

    return escaped


def convert_many(markdown_texts: Iterable[str]) -> list[str]:
    """Convert an iterable of Markdown strings to a list of HTML strings."""
    return [convert(markdown_text) for markdown_text in markdown_texts]


__all__ = [
    "MarkdownConversionError",
    "convert",
    "convert_many",
    "markdown_to_html",
]

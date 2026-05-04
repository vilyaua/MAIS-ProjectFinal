"""A small Markdown to HTML converter library.

The converter intentionally supports a focused subset of Markdown:
headers, emphasis, links, fenced/indented code blocks, and flat ordered
and unordered lists. Unsupported or malformed constructs are preserved as
escaped text so callers receive safe HTML and conversion never crashes for
ordinary string input.
"""

from __future__ import annotations

import html
import re
from typing import Iterable

InlineMatch = re.Match[str]


_HEADER_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_UNORDERED_RE = re.compile(r"^\s*([-+*])\s+(.+)$")
_ORDERED_RE = re.compile(r"^\s*(\d+)\.\s+(.+)$")
_LINK_RE = re.compile(r"\[([^\]\n]+)\]\(([^()\s]+)\)")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_ITALIC_RE = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")


class MarkdownConversionError(ValueError):
    """Raised when converter input is not valid for processing."""


def markdown_to_html(markdown: str) -> str:
    """Convert supported Markdown syntax to HTML.

    Args:
        markdown: Markdown source text.

    Returns:
        HTML with supported Markdown converted. Unsupported or malformed
        Markdown is emitted as escaped text.

    Raises:
        MarkdownConversionError: If ``markdown`` is not a string.
    """
    if not isinstance(markdown, str):
        raise MarkdownConversionError("markdown_to_html expects a string input")

    converter = MarkdownConverter()
    return converter.convert(markdown)


class MarkdownConverter:
    """Converter for a safe, intentionally small Markdown subset."""

    def convert(self, markdown: str) -> str:
        """Convert Markdown text to HTML.

        Args:
            markdown: Markdown source text.

        Returns:
            Converted HTML.
        """
        lines = markdown.splitlines()
        output: list[str] = []
        index = 0

        while index < len(lines):
            line = lines[index]

            if self._is_fenced_code_start(line):
                code_html, index = self._consume_fenced_code(lines, index)
                output.append(code_html)
                continue

            if self._is_indented_code_line(line):
                code_html, index = self._consume_indented_code(lines, index)
                output.append(code_html)
                continue

            unordered_match = _UNORDERED_RE.match(line)
            if unordered_match:
                list_html, index = self._consume_list(lines, index, ordered=False)
                output.append(list_html)
                continue

            ordered_match = _ORDERED_RE.match(line)
            if ordered_match:
                list_html, index = self._consume_list(lines, index, ordered=True)
                output.append(list_html)
                continue

            header_html = self._convert_header(line)
            if header_html is not None:
                output.append(header_html)
            else:
                output.append(self._convert_inline(line))

            index += 1

        return "\n".join(output)

    def _convert_header(self, line: str) -> str | None:
        """Convert one Markdown header line, if valid."""
        match = _HEADER_RE.match(line)
        if not match:
            return None

        level = len(match.group(1))
        content = self._convert_inline(match.group(2))
        return f"<h{level}>{content}</h{level}>"

    def _convert_inline(self, text: str) -> str:
        """Convert supported inline Markdown after escaping source text."""
        escaped = html.escape(text, quote=True)
        with_links = _LINK_RE.sub(self._replace_link, escaped)
        with_bold = _BOLD_RE.sub(r"<strong>\1</strong>", with_links)
        return _ITALIC_RE.sub(r"<em>\1</em>", with_bold)

    def _replace_link(self, match: InlineMatch) -> str:
        """Build a safe anchor tag for a valid Markdown link match."""
        text = match.group(1)
        url = match.group(2)
        return f'<a href="{url}">{text}</a>'

    @staticmethod
    def _is_fenced_code_start(line: str) -> bool:
        """Return True if a line starts a backtick fenced code block."""
        return line.strip().startswith("```")

    @staticmethod
    def _is_indented_code_line(line: str) -> bool:
        """Return True if a line is an indented code block line."""
        return line.startswith("    ") or line.startswith("\t")

    def _consume_fenced_code(self, lines: list[str], start: int) -> tuple[str, int]:
        """Consume a fenced code block and return HTML plus next index.

        If the closing fence is missing, all remaining lines are treated as
        code. This is graceful and safe because the content is escaped.
        """
        code_lines: list[str] = []
        index = start + 1

        while index < len(lines):
            if self._is_fenced_code_start(lines[index]):
                index += 1
                break
            code_lines.append(lines[index])
            index += 1

        return self._code_block(code_lines), index

    def _consume_indented_code(self, lines: list[str], start: int) -> tuple[str, int]:
        """Consume consecutive indented code lines."""
        code_lines: list[str] = []
        index = start

        while index < len(lines) and self._is_indented_code_line(lines[index]):
            line = lines[index]
            if line.startswith("\t"):
                code_lines.append(line[1:])
            else:
                code_lines.append(line[4:])
            index += 1

        return self._code_block(code_lines), index

    @staticmethod
    def _code_block(code_lines: Iterable[str]) -> str:
        """Render escaped code lines inside a pre/code block."""
        code = "\n".join(code_lines)
        escaped_code = html.escape(code, quote=False)
        return f"<pre><code>{escaped_code}</code></pre>"

    def _consume_list(
        self,
        lines: list[str],
        start: int,
        *,
        ordered: bool,
    ) -> tuple[str, int]:
        """Consume consecutive flat list items of the same type."""
        tag = "ol" if ordered else "ul"
        item_re = _ORDERED_RE if ordered else _UNORDERED_RE
        items: list[str] = []
        index = start

        while index < len(lines):
            match = item_re.match(lines[index])
            if not match:
                break
            item_text = match.group(2)
            items.append(f"<li>{self._convert_inline(item_text)}</li>")
            index += 1

        body = "\n".join(items)
        return f"<{tag}>\n{body}\n</{tag}>", index


__all__ = ["MarkdownConversionError", "MarkdownConverter", "markdown_to_html"]

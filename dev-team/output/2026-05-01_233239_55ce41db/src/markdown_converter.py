"""A small Markdown to HTML converter library.

Supports headers, emphasis, links, fenced code blocks, and simple ordered
and unordered lists. The implementation intentionally avoids external
runtime dependencies and focuses on predictable conversion for common
Markdown constructs.
"""

from __future__ import annotations

import html
import re
from typing import Literal

ListType = Literal["ul", "ol"]


class MarkdownConverter:
    """Convert a useful subset of Markdown into HTML."""

    _HEADER_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
    _UNORDERED_RE = re.compile(r"^\s*[-*+]\s+(.+?)\s*$")
    _ORDERED_RE = re.compile(r"^\s*\d+[.)]\s+(.+?)\s*$")
    _LINK_RE = re.compile(r"\[([^\[\]]+)]\(([^\s)]+)\)")
    _BOLD_RE = re.compile(r"(\*\*|__)(.+?)\1")
    _ITALIC_RE = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)|(?<!_)_(?!_)(.+?)(?<!_)_(?!_)")

    def convert(self, markdown: str | None) -> str:
        """Convert Markdown text to HTML.

        Args:
            markdown: Markdown source text. ``None`` and empty strings are
                treated as empty input and return an empty string.

        Returns:
            Converted HTML.

        Raises:
            TypeError: If ``markdown`` is not a string or ``None``.
        """
        if markdown is None:
            return ""
        if not isinstance(markdown, str):
            raise TypeError("markdown input must be a string or None")
        if not markdown.strip():
            return ""

        lines = markdown.splitlines()
        html_lines: list[str] = []
        index = 0
        active_list: ListType | None = None

        while index < len(lines):
            line = lines[index]

            if line.strip().startswith("```"):
                if active_list is not None:
                    html_lines.append(f"</{active_list}>")
                    active_list = None
                code_html, index = self._consume_code_block(lines, index)
                html_lines.append(code_html)
                continue

            if not line.strip():
                if active_list is not None:
                    html_lines.append(f"</{active_list}>")
                    active_list = None
                index += 1
                continue

            list_match = self._match_list_item(line)
            if list_match is not None:
                list_type, item_text = list_match
                if active_list != list_type:
                    if active_list is not None:
                        html_lines.append(f"</{active_list}>")
                    html_lines.append(f"<{list_type}>")
                    active_list = list_type
                html_lines.append(f"<li>{self._convert_inline(item_text)}</li>")
                index += 1
                continue

            if active_list is not None:
                html_lines.append(f"</{active_list}>")
                active_list = None

            header_match = self._HEADER_RE.match(line)
            if header_match:
                level = len(header_match.group(1))
                content = self._convert_inline(header_match.group(2))
                html_lines.append(f"<h{level}>{content}</h{level}>")
            else:
                html_lines.append(f"<p>{self._convert_inline(line.strip())}</p>")
            index += 1

        if active_list is not None:
            html_lines.append(f"</{active_list}>")

        return "\n".join(html_lines)

    def _consume_code_block(self, lines: list[str], start: int) -> tuple[str, int]:
        """Consume a fenced code block beginning at ``start``."""
        code_lines: list[str] = []
        index = start + 1

        while index < len(lines):
            if lines[index].strip().startswith("```"):
                return self._format_code_block(code_lines), index + 1
            code_lines.append(lines[index])
            index += 1

        return self._format_code_block(code_lines), index

    @staticmethod
    def _format_code_block(code_lines: list[str]) -> str:
        escaped_code = html.escape("\n".join(code_lines), quote=False)
        return f"<pre><code>{escaped_code}</code></pre>"

    def _match_list_item(self, line: str) -> tuple[ListType, str] | None:
        unordered_match = self._UNORDERED_RE.match(line)
        if unordered_match:
            return "ul", unordered_match.group(1)

        ordered_match = self._ORDERED_RE.match(line)
        if ordered_match:
            return "ol", ordered_match.group(1)

        return None

    def _convert_inline(self, text: str) -> str:
        """Convert inline Markdown constructs after HTML-escaping text."""
        escaped = html.escape(text, quote=True)

        def replace_link(match: re.Match[str]) -> str:
            label = match.group(1)
            href = match.group(2)
            return f'<a href="{href}">{label}</a>'

        converted = self._LINK_RE.sub(replace_link, escaped)
        converted = self._BOLD_RE.sub(r"<strong>\2</strong>", converted)

        def replace_italic(match: re.Match[str]) -> str:
            content = match.group(1) if match.group(1) is not None else match.group(2)
            return f"<em>{content}</em>"

        return self._ITALIC_RE.sub(replace_italic, converted)


def markdown_to_html(markdown: str | None) -> str:
    """Convert Markdown text to HTML using :class:`MarkdownConverter`."""
    return MarkdownConverter().convert(markdown)

"""A small Markdown to HTML converter library.

The module intentionally implements a focused subset of Markdown without external
runtime dependencies. Supported block features are headings, fenced code blocks,
paragraphs, and flat ordered/unordered lists. Supported inline features are bold,
italic, and hyperlinks.
"""

from __future__ import annotations

import html
import re
from typing import Callable, Match


class MarkdownConversionError(ValueError):
    """Raised when Markdown input cannot be converted safely."""


_HEADER_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_UNORDERED_ITEM_RE = re.compile(r"^\s*[*+-]\s+(.+?)\s*$")
_ORDERED_ITEM_RE = re.compile(r"^\s*\d+[.)]\s+(.+?)\s*$")
_LINK_RE = re.compile(r"\[([^\]\n]+)\]\(([^)\s]+)\)")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_ITALIC_RE = re.compile(r"(?<!\*)\*(?!\s|\*)(.+?)(?<!\s|\*)\*(?!\*)")


def convert_markdown(markdown_text: str | None) -> str:
    """Convert supported Markdown text to well-formed HTML.

    Args:
        markdown_text: Markdown text to convert. ``None`` and empty/whitespace
            strings are handled gracefully and return an empty string.

    Returns:
        HTML generated from the supported Markdown subset.

    Raises:
        TypeError: If ``markdown_text`` is neither a string nor ``None``.

    Supported Markdown features:
        * headings using ``#`` through ``######``
        * bold using ``**text**``
        * italic using ``*text*``
        * links using ``[text](url)``
        * fenced code blocks delimited by triple backticks
        * unordered lists using ``*``, ``-``, or ``+`` markers
        * ordered lists using ``1.`` or ``1)`` style markers

    Malformed or incomplete inline syntax is escaped and emitted literally rather
    than raising an exception. Unclosed code fences are treated as code through
    the end of the document.
    """
    if markdown_text is None:
        return ""
    if not isinstance(markdown_text, str):
        raise TypeError(
            "convert_markdown() expects a string input or None; "
            f"received {type(markdown_text).__name__}."
        )
    if markdown_text.strip() == "":
        return ""

    lines = markdown_text.splitlines()
    html_blocks: list[str] = []
    paragraph_lines: list[str] = []
    list_type: str | None = None
    list_items: list[str] = []
    in_code_block = False
    code_lines: list[str] = []

    def flush_paragraph() -> None:
        if paragraph_lines:
            paragraph_text = " ".join(line.strip() for line in paragraph_lines)
            html_blocks.append(f"<p>{_parse_inline(paragraph_text)}</p>")
            paragraph_lines.clear()

    def flush_list() -> None:
        nonlocal list_type
        if list_type is not None:
            items_html = "".join(f"<li>{item}</li>" for item in list_items)
            html_blocks.append(f"<{list_type}>{items_html}</{list_type}>")
            list_type = None
            list_items.clear()

    def flush_code() -> None:
        if code_lines:
            code_text = "\n".join(code_lines)
            html_blocks.append(f"<pre><code>{html.escape(code_text)}</code></pre>")
            code_lines.clear()
        else:
            html_blocks.append("<pre><code></code></pre>")

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_code_block:
                flush_code()
                in_code_block = False
            else:
                flush_paragraph()
                flush_list()
                in_code_block = True
                code_lines.clear()
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        if stripped == "":
            flush_paragraph()
            flush_list()
            continue

        unordered_match = _UNORDERED_ITEM_RE.match(line)
        ordered_match = _ORDERED_ITEM_RE.match(line)
        if unordered_match or ordered_match:
            flush_paragraph()
            current_type = "ul" if unordered_match else "ol"
            item_text = (unordered_match or ordered_match).group(1)  # type: ignore[union-attr]
            if list_type is not None and list_type != current_type:
                flush_list()
            list_type = current_type
            list_items.append(_parse_inline(item_text))
            continue

        header_match = _HEADER_RE.match(line)
        if header_match:
            flush_paragraph()
            flush_list()
            level = len(header_match.group(1))
            content = _parse_inline(header_match.group(2))
            html_blocks.append(f"<h{level}>{content}</h{level}>")
            continue

        flush_list()
        paragraph_lines.append(line)

    if in_code_block:
        flush_code()
    flush_paragraph()
    flush_list()

    return "\n".join(html_blocks)


def _parse_inline(text: str) -> str:
    """Parse supported inline Markdown while safely escaping raw HTML."""
    escaped = html.escape(text, quote=False)

    def replace_link(match: Match[str]) -> str:
        label = match.group(1)
        url = match.group(2)
        if "&lt;" in url or "&gt;" in url:
            return match.group(0)
        safe_href = html.escape(url, quote=True)
        return f'<a href="{safe_href}">{_parse_emphasis(label)}</a>'

    with_links = _LINK_RE.sub(replace_link, escaped)
    return _parse_emphasis(with_links)


def _parse_emphasis(text: str) -> str:
    """Parse bold and italic markers in already escaped text."""

    def replace_bold(match: Match[str]) -> str:
        return f"<strong>{_parse_italic(match.group(1))}</strong>"

    bolded = _BOLD_RE.sub(replace_bold, text)
    return _parse_italic(bolded)


def _parse_italic(text: str) -> str:
    """Parse italic markers in already escaped text."""

    def replace_italic(match: Match[str]) -> str:
        return f"<em>{match.group(1)}</em>"

    return _ITALIC_RE.sub(replace_italic, text)

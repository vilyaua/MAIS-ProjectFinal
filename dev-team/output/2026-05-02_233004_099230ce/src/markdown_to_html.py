"""A small Markdown to HTML conversion library.

The converter intentionally supports a focused subset of Markdown:
headers, emphasis, links, inline code, fenced code blocks, and simple ordered
and unordered lists. Malformed Markdown is treated as literal text wherever
possible so conversion remains best-effort and non-crashing.
"""

from __future__ import annotations

import html
import re
from typing import Match

_HEADER_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_UNORDERED_ITEM_RE = re.compile(r"^\s*[-*+]\s+(.+)$")
_ORDERED_ITEM_RE = re.compile(r"^\s*\d+[.)]\s+(.+)$")
_LINK_RE = re.compile(r"\[([^\]\n]+)\]\(([^)\n]+)\)")
_BOLD_ASTERISK_RE = re.compile(r"\*\*(.+?)\*\*")
_BOLD_UNDERSCORE_RE = re.compile(r"__(.+?)__")
_ITALIC_ASTERISK_RE = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")
_ITALIC_UNDERSCORE_RE = re.compile(r"(?<!_)_(?!_)(.+?)(?<!_)_(?!_)")


def markdown_to_html(markdown_text: str) -> str:
    """Convert supported Markdown syntax to HTML.

    Args:
        markdown_text: A non-empty string containing Markdown text.

    Returns:
        A string containing well-formed HTML for the supported elements.

    Raises:
        ValueError: If ``markdown_text`` is not a non-empty string.
    """
    _validate_input(markdown_text)

    lines = markdown_text.splitlines()
    output: list[str] = []
    paragraph_lines: list[str] = []
    list_type: str | None = None
    in_code_block = False
    code_lines: list[str] = []

    def flush_paragraph() -> None:
        if paragraph_lines:
            paragraph_text = " ".join(line.strip() for line in paragraph_lines)
            output.append(f"<p>{_parse_inline(paragraph_text)}</p>")
            paragraph_lines.clear()

    def close_list() -> None:
        nonlocal list_type
        if list_type is not None:
            output.append(f"</{list_type}>")
            list_type = None

    for line in lines:
        stripped = line.strip()

        if in_code_block:
            if stripped.startswith("```"):
                escaped_code = html.escape("\n".join(code_lines), quote=False)
                output.append(f"<pre><code>{escaped_code}</code></pre>")
                code_lines.clear()
                in_code_block = False
            else:
                code_lines.append(line)
            continue

        if stripped.startswith("```"):
            flush_paragraph()
            close_list()
            in_code_block = True
            code_lines.clear()
            continue

        if not stripped:
            flush_paragraph()
            close_list()
            continue

        header_match = _HEADER_RE.match(line)
        if header_match:
            flush_paragraph()
            close_list()
            level = len(header_match.group(1))
            content = _parse_inline(header_match.group(2))
            output.append(f"<h{level}>{content}</h{level}>")
            continue

        unordered_match = _UNORDERED_ITEM_RE.match(line)
        ordered_match = _ORDERED_ITEM_RE.match(line)
        if unordered_match or ordered_match:
            flush_paragraph()
            current_type = "ul" if unordered_match else "ol"
            item_text = (unordered_match or ordered_match).group(1)  # type: ignore[union-attr]

            if list_type != current_type:
                close_list()
                output.append(f"<{current_type}>")
                list_type = current_type

            output.append(f"<li>{_parse_inline(item_text)}</li>")
            continue

        close_list()
        paragraph_lines.append(line)

    if in_code_block:
        escaped_code = html.escape("\n".join(code_lines), quote=False)
        output.append(f"<pre><code>{escaped_code}</code></pre>")

    flush_paragraph()
    close_list()
    return "\n".join(output)


def convert(markdown_text: str) -> str:
    """Alias for :func:`markdown_to_html` for convenient public use."""
    return markdown_to_html(markdown_text)


def _validate_input(markdown_text: str) -> None:
    if not isinstance(markdown_text, str):
        raise ValueError("Markdown input must be a non-empty string.")
    if not markdown_text.strip():
        raise ValueError("Markdown input must not be empty.")


def _parse_inline(text: str) -> str:
    """Parse inline Markdown while preserving inline code as literal text."""
    parts = text.split("`")
    rendered_parts: list[str] = []

    for index, part in enumerate(parts):
        if index % 2 == 1:
            rendered_parts.append(f"<code>{html.escape(part, quote=False)}</code>")
        else:
            rendered_parts.append(_parse_inline_without_code(part))

    return "".join(rendered_parts)


def _parse_inline_without_code(text: str) -> str:
    rendered_parts: list[str] = []
    cursor = 0

    for match in _LINK_RE.finditer(text):
        rendered_parts.append(_parse_emphasis(text[cursor : match.start()]))
        label = _parse_inline(match.group(1))
        href = html.escape(match.group(2).strip(), quote=True)
        rendered_parts.append(f'<a href="{href}">{label}</a>')
        cursor = match.end()

    rendered_parts.append(_parse_emphasis(text[cursor:]))
    return "".join(rendered_parts)


def _parse_emphasis(text: str) -> str:
    escaped = html.escape(text, quote=False)
    escaped = _BOLD_ASTERISK_RE.sub(r"<strong>\1</strong>", escaped)
    escaped = _BOLD_UNDERSCORE_RE.sub(r"<strong>\1</strong>", escaped)
    escaped = _ITALIC_ASTERISK_RE.sub(r"<em>\1</em>", escaped)
    escaped = _ITALIC_UNDERSCORE_RE.sub(r"<em>\1</em>", escaped)
    return escaped

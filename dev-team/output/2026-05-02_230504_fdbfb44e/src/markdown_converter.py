"""Markdown to HTML conversion utilities.

This module provides a small, dependency-free Markdown converter supporting
headers, emphasis, links, fenced code blocks, and simple ordered/unordered
lists.
"""

from __future__ import annotations

import html
import re
from typing import List, Optional

_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_BOLD_ASTERISK_PATTERN = re.compile(r"\*\*(.+?)\*\*")
_BOLD_UNDERSCORE_PATTERN = re.compile(r"__(.+?)__")
_ITALIC_ASTERISK_PATTERN = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")
_ITALIC_UNDERSCORE_PATTERN = re.compile(r"(?<!_)_(?!_)(.+?)(?<!_)_(?!_)")
_HEADER_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_UNORDERED_LIST_PATTERN = re.compile(r"^\s*[-+*]\s+(.+?)\s*$")
_ORDERED_LIST_PATTERN = re.compile(r"^\s*\d+[.)]\s+(.+?)\s*$")


class MarkdownConversionError(ValueError):
    """Raised when Markdown input cannot be converted."""


def markdown_to_html(markdown_text: str) -> str:
    """Convert supported Markdown syntax to HTML.

    Args:
        markdown_text: Markdown source text to convert.

    Returns:
        HTML string. Empty or whitespace-only input returns an empty string.

    Raises:
        TypeError: If ``markdown_text`` is not a string.
    """
    if not isinstance(markdown_text, str):
        raise TypeError(
            "markdown_to_html expects a string containing Markdown text; "
            f"received {type(markdown_text).__name__}."
        )

    if markdown_text.strip() == "":
        return ""

    lines = markdown_text.splitlines()
    output: List[str] = []
    in_code_block = False
    code_lines: List[str] = []
    active_list: Optional[str] = None

    for line in lines:
        if line.strip().startswith("```"):
            if in_code_block:
                output.append(_render_code_block(code_lines))
                code_lines = []
                in_code_block = False
            else:
                active_list = _close_list_if_needed(output, active_list)
                in_code_block = True
                code_lines = []
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        if line.strip() == "":
            active_list = _close_list_if_needed(output, active_list)
            continue

        unordered_match = _UNORDERED_LIST_PATTERN.match(line)
        if unordered_match:
            active_list = _ensure_list(output, active_list, "ul")
            output.append(f"<li>{_convert_inline(unordered_match.group(1))}</li>")
            continue

        ordered_match = _ORDERED_LIST_PATTERN.match(line)
        if ordered_match:
            active_list = _ensure_list(output, active_list, "ol")
            output.append(f"<li>{_convert_inline(ordered_match.group(1))}</li>")
            continue

        active_list = _close_list_if_needed(output, active_list)

        header_match = _HEADER_PATTERN.match(line)
        if header_match:
            level = len(header_match.group(1))
            content = _convert_inline(header_match.group(2))
            output.append(f"<h{level}>{content}</h{level}>")
            continue

        output.append(f"<p>{_convert_inline(line.strip())}</p>")

    if in_code_block:
        # Gracefully render an unterminated fenced code block using the content
        # collected so far rather than discarding user data.
        output.append(_render_code_block(code_lines))

    _close_list_if_needed(output, active_list)
    return "\n".join(output)


def _render_code_block(lines: List[str]) -> str:
    """Render collected code lines as an escaped HTML code block."""
    code = "\n".join(lines)
    return f"<pre><code>{html.escape(code, quote=False)}</code></pre>"


def _ensure_list(output: List[str], active_list: Optional[str], list_type: str) -> str:
    """Ensure that the requested list type is open."""
    if active_list == list_type:
        return active_list
    if active_list is not None:
        output.append(f"</{active_list}>")
    output.append(f"<{list_type}>")
    return list_type


def _close_list_if_needed(output: List[str], active_list: Optional[str]) -> Optional[str]:
    """Close any currently active list and return ``None``."""
    if active_list is not None:
        output.append(f"</{active_list}>")
    return None


def _convert_inline(text: str) -> str:
    """Convert supported inline Markdown syntax to HTML."""
    converted_parts: List[str] = []
    last_end = 0

    for match in _LINK_PATTERN.finditer(text):
        converted_parts.append(_convert_emphasis(html.escape(text[last_end : match.start()])))
        link_text = _convert_emphasis(html.escape(match.group(1)))
        href = html.escape(match.group(2).strip(), quote=True)
        converted_parts.append(f'<a href="{href}">{link_text}</a>')
        last_end = match.end()

    converted_parts.append(_convert_emphasis(html.escape(text[last_end:])))
    return "".join(converted_parts)


def _convert_emphasis(escaped_text: str) -> str:
    """Convert bold and italic markers in already escaped text."""
    text = _BOLD_ASTERISK_PATTERN.sub(r"<strong>\1</strong>", escaped_text)
    text = _BOLD_UNDERSCORE_PATTERN.sub(r"<strong>\1</strong>", text)
    text = _ITALIC_ASTERISK_PATTERN.sub(r"<em>\1</em>", text)
    text = _ITALIC_UNDERSCORE_PATTERN.sub(r"<em>\1</em>", text)
    return text

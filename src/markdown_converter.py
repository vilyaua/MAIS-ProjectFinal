"""A small Markdown to HTML converter library.

The converter intentionally implements a focused Markdown subset without external
runtime dependencies. It supports headers, inline emphasis, links, fenced code
blocks, unordered lists, ordered lists, and simple paragraphs.
"""

from __future__ import annotations

import html
import re
from typing import Callable, Match


class MarkdownConversionError(TypeError):
    """Raised when Markdown input is invalid for conversion."""


_HEADER_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_UNORDERED_LIST_RE = re.compile(r"^\s*[-*+]\s+(.*)$")
_ORDERED_LIST_RE = re.compile(r"^\s*\d+\.\s+(.*)$")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+(?:\s+[^)]*)?)\)")
_BOLD_ASTERISK_RE = re.compile(r"\*\*(.+?)\*\*")
_BOLD_UNDERSCORE_RE = re.compile(r"__(.+?)__")
_ITALIC_ASTERISK_RE = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")
_ITALIC_UNDERSCORE_RE = re.compile(r"(?<!\w)_(?!_)(.+?)(?<!_)_(?!\w)")


def convert_markdown(markdown: str) -> str:
    """Convert a supported subset of Markdown to HTML.

    Args:
        markdown: Markdown source text. Must be a string.

    Returns:
        Converted HTML. Empty or whitespace-only Markdown returns an empty
        string.

    Raises:
        MarkdownConversionError: If ``markdown`` is not a string.

    Notes:
        Malformed Markdown is handled conservatively: unmatched delimiters are
        rendered as escaped text, and an unclosed fenced code block is closed in
        the generated HTML at end-of-input.
    """
    if not isinstance(markdown, str):
        raise MarkdownConversionError("Markdown input must be a string.")

    if markdown.strip() == "":
        return ""

    lines = markdown.splitlines()
    html_lines: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]

        if line.strip() == "":
            index += 1
            continue

        if line.lstrip().startswith("```"):
            code_lines: list[str] = []
            index += 1
            while index < len(lines) and not lines[index].lstrip().startswith("```"):
                code_lines.append(lines[index])
                index += 1
            if index < len(lines):
                index += 1
            code = "\n".join(code_lines)
            html_lines.append(
                f"<pre><code>{html.escape(code, quote=False)}</code></pre>"
            )
            continue

        unordered_match = _UNORDERED_LIST_RE.match(line)
        if unordered_match:
            index = _consume_list(
                lines=lines,
                start=index,
                list_pattern=_UNORDERED_LIST_RE,
                list_tag="ul",
                output=html_lines,
            )
            continue

        ordered_match = _ORDERED_LIST_RE.match(line)
        if ordered_match:
            index = _consume_list(
                lines=lines,
                start=index,
                list_pattern=_ORDERED_LIST_RE,
                list_tag="ol",
                output=html_lines,
            )
            continue

        header_match = _HEADER_RE.match(line)
        if header_match:
            level = len(header_match.group(1))
            content = _convert_inline(header_match.group(2).strip())
            html_lines.append(f"<h{level}>{content}</h{level}>")
            index += 1
            continue

        paragraph_lines = [line.strip()]
        index += 1
        while index < len(lines) and _is_paragraph_continuation(lines[index]):
            paragraph_lines.append(lines[index].strip())
            index += 1
        paragraph_text = " ".join(paragraph_lines)
        html_lines.append(f"<p>{_convert_inline(paragraph_text)}</p>")

    return "\n".join(html_lines)


def _consume_list(
    lines: list[str],
    start: int,
    list_pattern: re.Pattern[str],
    list_tag: str,
    output: list[str],
) -> int:
    """Consume consecutive list items and append a complete HTML list."""
    output.append(f"<{list_tag}>")
    index = start
    while index < len(lines):
        match = list_pattern.match(lines[index])
        if not match:
            break
        item_html = _convert_inline(match.group(1).strip())
        output.append(f"<li>{item_html}</li>")
        index += 1
    output.append(f"</{list_tag}>")
    return index


def _is_paragraph_continuation(line: str) -> bool:
    """Return whether a line should continue the current paragraph."""
    if line.strip() == "":
        return False
    if line.lstrip().startswith("```"):
        return False
    if _HEADER_RE.match(line):
        return False
    if _UNORDERED_LIST_RE.match(line) or _ORDERED_LIST_RE.match(line):
        return False
    return True


def _convert_inline(text: str) -> str:
    """Convert supported inline Markdown syntax to HTML."""
    escaped = html.escape(text, quote=True)
    placeholders: dict[str, str] = {}

    def store(fragment: str) -> str:
        key = f"\u0000MDHTML{len(placeholders)}\u0000"
        placeholders[key] = fragment
        return key

    def replace_links(match: Match[str]) -> str:
        label = match.group(1)
        url = match.group(2).strip()
        return store(f'<a href="{url}">{label}</a>')

    escaped = _LINK_RE.sub(replace_links, escaped)
    escaped = _replace_with_placeholder(
        escaped,
        _BOLD_ASTERISK_RE,
        lambda match: store(f"<strong>{match.group(1)}</strong>"),
    )
    escaped = _replace_with_placeholder(
        escaped,
        _BOLD_UNDERSCORE_RE,
        lambda match: store(f"<strong>{match.group(1)}</strong>"),
    )
    escaped = _replace_with_placeholder(
        escaped,
        _ITALIC_ASTERISK_RE,
        lambda match: store(f"<em>{match.group(1)}</em>"),
    )
    escaped = _replace_with_placeholder(
        escaped,
        _ITALIC_UNDERSCORE_RE,
        lambda match: store(f"<em>{match.group(1)}</em>"),
    )

    for key, fragment in placeholders.items():
        escaped = escaped.replace(key, fragment)
    return escaped


def _replace_with_placeholder(
    text: str,
    pattern: re.Pattern[str],
    replacement: Callable[[Match[str]], str],
) -> str:
    """Apply a regex replacement with a typed callback."""
    return pattern.sub(replacement, text)


__all__ = ["MarkdownConversionError", "convert_markdown"]

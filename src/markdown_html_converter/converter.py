"""Markdown to HTML conversion utilities.

This module intentionally implements a small, dependency-free subset of
Markdown. It is designed for applications that need predictable conversion of
common elements without pulling in a full Markdown engine.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Optional

_HEADER_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_UNORDERED_RE = re.compile(r"^(?P<indent>\s*)[-+*]\s+(?P<content>.+?)\s*$")
_ORDERED_RE = re.compile(r"^(?P<indent>\s*)\d+\.\s+(?P<content>.+?)\s*$")


@dataclass(frozen=True)
class _ListItem:
    """Internal representation of a parsed list line."""

    kind: str
    level: int
    content: str


def convert_markdown(markdown: str | bytes | None) -> str:
    """Convert a supported subset of Markdown to HTML.

    Supported block elements are headers (levels 1-6), unordered lists, and
    ordered lists. Supported inline elements are bold, italic, hyperlinks, and
    inline code spans.

    Args:
        markdown: Markdown input as ``str``. ``bytes`` input is decoded as
            UTF-8 with replacement for invalid byte sequences. ``None`` and an
            empty string return an empty string.

    Returns:
        An HTML string. Unsupported or malformed Markdown syntax is preserved as
        escaped text rather than raising an exception.

    Raises:
        TypeError: If ``markdown`` is not ``str``, ``bytes``, or ``None``.
    """
    if markdown is None:
        return ""
    if isinstance(markdown, bytes):
        markdown = markdown.decode("utf-8", errors="replace")
    if not isinstance(markdown, str):
        raise TypeError("markdown input must be a str, bytes, or None")
    if markdown == "":
        return ""

    normalized = markdown.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")
    output: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]

        if line.strip() == "":
            index += 1
            continue

        header_match = _HEADER_RE.match(line)
        if header_match:
            level = len(header_match.group(1))
            content = parse_inline(header_match.group(2))
            output.append(f"<h{level}>{content}</h{level}>")
            index += 1
            continue

        list_item = _parse_list_item(line)
        if list_item is not None:
            html_list, index = _parse_list_block(lines, index)
            output.append(html_list)
            continue

        output.append(parse_inline(line.strip()))
        index += 1

    return "\n".join(output)


def markdown_to_html(markdown: str | bytes | None) -> str:
    """Alias for :func:`convert_markdown` for ergonomic package use."""
    return convert_markdown(markdown)


def parse_inline(text: str) -> str:
    """Convert supported inline Markdown syntax to HTML.

    Malformed constructs are emitted as literal, escaped text. Inline code spans
    are treated as opaque text and are not parsed for nested Markdown.
    """
    return _parse_inline_segment(text, stop_char=None)[0]


def _parse_inline_segment(text: str, stop_char: Optional[str]) -> tuple[str, int]:
    output: list[str] = []
    index = 0

    while index < len(text):
        char = text[index]

        if stop_char is not None and char == stop_char:
            return "".join(output), index + 1

        if char == "`":
            closing = text.find("`", index + 1)
            if closing != -1:
                code = html.escape(text[index + 1 : closing], quote=False)
                output.append(f"<code>{code}</code>")
                index = closing + 1
                continue

        if text.startswith("**", index):
            closing = _find_closing(text, "**", index + 2)
            if closing != -1:
                inner = _parse_inline_segment(text[index + 2 : closing], None)[0]
                output.append(f"<strong>{inner}</strong>")
                index = closing + 2
                continue

        if char == "*":
            # Avoid treating the first star of a bold marker as italic.
            if not text.startswith("**", index):
                closing = _find_closing(text, "*", index + 1)
                if closing != -1:
                    inner = _parse_inline_segment(text[index + 1 : closing], None)[0]
                    output.append(f"<em>{inner}</em>")
                    index = closing + 1
                    continue

        if char == "[":
            link_html, consumed = _try_parse_link(text, index)
            if link_html is not None:
                output.append(link_html)
                index = consumed
                continue

        output.append(html.escape(char, quote=False))
        index += 1

    return "".join(output), index


def _try_parse_link(text: str, start: int) -> tuple[Optional[str], int]:
    label_end = _find_matching_bracket(text, start)
    if label_end == -1 or label_end + 1 >= len(text) or text[label_end + 1] != "(":
        return None, start

    url_end = text.find(")", label_end + 2)
    if url_end == -1:
        return None, start

    label = text[start + 1 : label_end]
    url = text[label_end + 2 : url_end]
    if not label or not url or "\n" in url:
        return None, start

    label_html = _parse_inline_segment(label, None)[0]
    url_html = html.escape(url.strip(), quote=True)
    return f'<a href="{url_html}">{label_html}</a>', url_end + 1


def _find_matching_bracket(text: str, start: int) -> int:
    escaped = False
    for index in range(start + 1, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "]":
            return index
    return -1


def _find_closing(text: str, marker: str, start: int) -> int:
    index = start
    while index < len(text):
        found = text.find(marker, index)
        if found == -1:
            return -1
        if marker == "*" and found + 1 < len(text) and text[found + 1] == "*":
            index = found + 2
            continue
        if marker == "**" and found + 2 < len(text) and text[found + 2] == "*":
            return found + 1
        return found
    return -1


def _parse_list_item(line: str) -> Optional[_ListItem]:
    unordered = _UNORDERED_RE.match(line)
    if unordered:
        return _ListItem(
            kind="ul",
            level=_indent_to_level(unordered.group("indent")),
            content=unordered.group("content"),
        )

    ordered = _ORDERED_RE.match(line)
    if ordered:
        return _ListItem(
            kind="ol",
            level=_indent_to_level(ordered.group("indent")),
            content=ordered.group("content"),
        )

    return None


def _indent_to_level(indent: str) -> int:
    expanded = indent.replace("\t", "    ")
    return len(expanded) // 2


def _parse_list_block(lines: list[str], start: int) -> tuple[str, int]:
    items: list[_ListItem] = []
    index = start

    while index < len(lines):
        item = _parse_list_item(lines[index])
        if item is None:
            break
        items.append(item)
        index += 1

    return _render_list_items(items), index


def _render_list_items(items: list[_ListItem]) -> str:
    if not items:
        return ""

    result: list[str] = []
    stack: list[str] = []
    current_li_open = False

    for item in items:
        target_depth = item.level + 1

        while len(stack) > target_depth:
            if current_li_open:
                result.append("</li>")
                current_li_open = False
            result.append(f"</{stack.pop()}>")
            if stack:
                result.append("</li>")

        if len(stack) == target_depth and stack[-1] != item.kind:
            if current_li_open:
                result.append("</li>")
                current_li_open = False
            result.append(f"</{stack.pop()}>")

        while len(stack) < target_depth:
            result.append(f"<{item.kind}>")
            stack.append(item.kind)
            current_li_open = False

        if current_li_open:
            result.append("</li>")

        result.append(f"<li>{parse_inline(item.content)}")
        current_li_open = True

    while stack:
        if current_li_open:
            result.append("</li>")
            current_li_open = False
        result.append(f"</{stack.pop()}>")
        if stack:
            current_li_open = True

    return "".join(result)

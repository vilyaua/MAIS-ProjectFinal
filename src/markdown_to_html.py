"""A lightweight Markdown to HTML conversion library.

The module intentionally implements a practical subset of Markdown without any
third-party dependencies. It is designed to be forgiving: malformed Markdown is
converted on a best-effort basis and should not crash the converter.
"""

from __future__ import annotations

import html
import re
from typing import Literal

ListType = Literal["ul", "ol"]


class MarkdownConversionError(TypeError):
    """Raised when Markdown input cannot be converted due to invalid type."""


_CODE_PLACEHOLDER = "\u0000CODE{}\u0000"


def convert_markdown(markdown: str) -> str:
    """Convert a Markdown-formatted string to HTML.

    Supported syntax includes headers, emphasis, links, inline code, fenced code
    blocks, and ordered/unordered lists. Invalid or malformed Markdown is handled
    with a best-effort conversion and unmatched markers are left unchanged.

    Args:
        markdown: Markdown-formatted text.

    Returns:
        Converted HTML string.

    Raises:
        MarkdownConversionError: If *markdown* is not a string.
    """
    if not isinstance(markdown, str):
        raise MarkdownConversionError("convert_markdown expects a string input")

    if markdown == "":
        return ""

    try:
        return _convert_blocks(markdown)
    except Exception:
        # Requirement 8: malformed input must not crash conversion. Returning the
        # original input is safer than exposing internal parser failures.
        return markdown


def markdown_to_html(markdown: str) -> str:
    """Alias for :func:`convert_markdown`."""
    return convert_markdown(markdown)


def _convert_blocks(markdown: str) -> str:
    lines = markdown.splitlines()
    output: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if stripped.startswith("```"):
            code_lines: list[str] = []
            opening_remainder = stripped[3:]
            if opening_remainder.endswith("```") and len(opening_remainder) >= 3:
                code_text = opening_remainder[:-3]
                output.append(_render_code_block(code_text))
                index += 1
                continue

            index += 1
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(lines[index])
                index += 1
            if index < len(lines):
                index += 1
            output.append(_render_code_block("\n".join(code_lines)))
            continue

        list_match = _match_list_item(line)
        if list_match is not None:
            list_lines: list[str] = []
            while index < len(lines) and _match_list_item(lines[index]) is not None:
                list_lines.append(lines[index])
                index += 1
            output.append(_convert_list_block(list_lines))
            continue

        header_match = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if header_match:
            level = len(header_match.group(1))
            content = _convert_inline(header_match.group(2))
            output.append(f"<h{level}>{content}</h{level}>")
            index += 1
            continue

        if stripped == "":
            output.append("")
        else:
            output.append(_convert_inline(line))
        index += 1

    return "\n".join(output)


def _render_code_block(code_text: str) -> str:
    return f"<pre><code>{html.escape(code_text)}</code></pre>"


def _match_list_item(line: str) -> tuple[int, ListType, str] | None:
    unordered = re.match(r"^(\s*)[-+*]\s+(.+)$", line)
    if unordered:
        return len(unordered.group(1)), "ul", unordered.group(2)

    ordered = re.match(r"^(\s*)\d+[.)]\s+(.+)$", line)
    if ordered:
        return len(ordered.group(1)), "ol", ordered.group(2)

    return None


def _convert_list_block(lines: list[str]) -> str:
    """Convert a consecutive block of Markdown list items to HTML.

    Basic nested lists are supported by indentation. The generated HTML keeps
    nested list tags inside the preceding list item, which is valid HTML list
    structure.
    """
    html_lines: list[str] = []
    stack: list[tuple[int, ListType, bool]] = []  # indent, type, li_open

    for line in lines:
        match = _match_list_item(line)
        if match is None:
            continue
        indent, list_type, content = match
        item_html = _convert_inline(content)

        while stack and indent < stack[-1][0]:
            _close_current_list(html_lines, stack)

        if not stack or indent > stack[-1][0]:
            if stack and stack[-1][2]:
                # Keep the parent <li> open so the nested list is contained in it.
                html_lines.append(f"<{list_type}>")
            else:
                html_lines.append(f"<{list_type}>")
            stack.append((indent, list_type, False))
        elif stack[-1][1] != list_type:
            _close_current_list(html_lines, stack)
            html_lines.append(f"<{list_type}>")
            stack.append((indent, list_type, False))

        if stack[-1][2]:
            html_lines.append("</li>")
            stack[-1] = (stack[-1][0], stack[-1][1], False)

        html_lines.append(f"<li>{item_html}")
        stack[-1] = (stack[-1][0], stack[-1][1], True)

    while stack:
        _close_current_list(html_lines, stack)

    return "\n".join(html_lines)


def _close_current_list(
    html_lines: list[str], stack: list[tuple[int, ListType, bool]]
) -> None:
    indent, list_type, li_open = stack.pop()
    if li_open:
        html_lines.append("</li>")
    html_lines.append(f"</{list_type}>")

    if stack and stack[-1][2]:
        # A nested list just ended inside the parent <li>. Leave the parent item
        # open so following sibling nested lists or final closure remain valid.
        stack[-1] = (stack[-1][0], stack[-1][1], True)


def _convert_inline(text: str) -> str:
    placeholders: list[str] = []

    def stash_code(match: re.Match[str]) -> str:
        placeholders.append(f"<code>{html.escape(match.group(1))}</code>")
        return _CODE_PLACEHOLDER.format(len(placeholders) - 1)

    # Protect inline code from emphasis/link conversion. Unmatched backticks are
    # left as-is because the regex only matches balanced pairs.
    converted = re.sub(r"`([^`]+)`", stash_code, text)

    converted = _convert_links(converted)
    converted = _convert_emphasis(converted)

    for index, value in enumerate(placeholders):
        converted = converted.replace(_CODE_PLACEHOLDER.format(index), value)

    return converted


def _convert_links(text: str) -> str:
    def replace_link(match: re.Match[str]) -> str:
        label = _convert_emphasis(match.group(1))
        url = html.escape(match.group(2), quote=True)
        return f"<a href='{url}'>{label}</a>"

    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", replace_link, text)


def _convert_emphasis(text: str) -> str:
    # Strong emphasis first so **bold** is not consumed as two italic markers.
    converted = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    converted = re.sub(r"__(.+?)__", r"<strong>\1</strong>", converted)

    # Avoid matching underscores inside words by requiring non-word boundaries.
    converted = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", converted)
    converted = re.sub(r"(?<!\w)_(?!_)(.+?)(?<!_)_(?!\w)", r"<em>\1</em>", converted)
    return converted

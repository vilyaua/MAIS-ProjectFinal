"""A small Markdown to HTML converter library.

The converter intentionally supports a focused subset of Markdown:
headers, emphasis, links, fenced code blocks, and flat ordered/unordered
lists. Unsupported text is emitted as escaped paragraph content.
"""

from __future__ import annotations

import html
import re
from collections.abc import Sequence
from typing import Optional


_HEADER_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_UNORDERED_LIST_RE = re.compile(r"^\s*[-*+]\s+(.+?)\s*$")
_ORDERED_LIST_RE = re.compile(r"^\s*\d+\.\s+(.+?)\s*$")


def convert_markdown_to_html(markdown_text: Optional[str]) -> str:
    """Convert supported Markdown syntax into HTML.

    Args:
        markdown_text: Markdown source text. ``None``, empty strings, and
            non-string values are treated gracefully and return an empty string.

    Returns:
        An HTML string containing converted markup.
    """
    if not isinstance(markdown_text, str) or markdown_text == "":
        return ""

    lines = markdown_text.splitlines()
    output: list[str] = []
    paragraph_lines: list[str] = []
    code_lines: list[str] = []
    in_code_block = False
    open_list_type: Optional[str] = None

    def flush_paragraph() -> None:
        nonlocal paragraph_lines
        if paragraph_lines:
            paragraph_text = " ".join(line.strip() for line in paragraph_lines)
            output.append(f"<p>{_parse_inline(paragraph_text)}</p>")
            paragraph_lines = []

    def close_list() -> None:
        nonlocal open_list_type
        if open_list_type is not None:
            output.append(f"</{open_list_type}>")
            open_list_type = None

    def open_list(list_type: str) -> None:
        nonlocal open_list_type
        if open_list_type != list_type:
            close_list()
            output.append(f"<{list_type}>")
            open_list_type = list_type

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_code_block:
                output.append(
                    f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>"
                )
                code_lines = []
                in_code_block = False
            else:
                flush_paragraph()
                close_list()
                in_code_block = True
                code_lines = []
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        if stripped == "":
            flush_paragraph()
            close_list()
            continue

        header_match = _HEADER_RE.match(line)
        if header_match:
            flush_paragraph()
            close_list()
            level = len(header_match.group(1))
            content = _parse_inline(header_match.group(2).strip())
            output.append(f"<h{level}>{content}</h{level}>")
            continue

        unordered_match = _UNORDERED_LIST_RE.match(line)
        if unordered_match:
            flush_paragraph()
            open_list("ul")
            output.append(f"<li>{_parse_inline(unordered_match.group(1).strip())}</li>")
            continue

        ordered_match = _ORDERED_LIST_RE.match(line)
        if ordered_match:
            flush_paragraph()
            open_list("ol")
            output.append(f"<li>{_parse_inline(ordered_match.group(1).strip())}</li>")
            continue

        close_list()
        paragraph_lines.append(line)

    if in_code_block:
        output.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
    flush_paragraph()
    close_list()

    return "\n".join(output)


def _parse_inline(text: str) -> str:
    """Parse inline links and emphasis in a Markdown text fragment."""
    result: list[str] = []
    position = 0

    while position < len(text):
        link_start = text.find("[", position)
        if link_start == -1:
            result.append(_parse_emphasis(html.escape(text[position:])))
            break

        result.append(_parse_emphasis(html.escape(text[position:link_start])))
        link_text_end = text.find("]", link_start + 1)

        if link_text_end == -1 or link_text_end + 1 >= len(text) or text[link_text_end + 1] != "(":
            result.append(_parse_emphasis(html.escape(text[link_start])))
            position = link_start + 1
            continue

        url_end = text.find(")", link_text_end + 2)
        if url_end == -1:
            result.append(_parse_emphasis(html.escape(text[link_start])))
            position = link_start + 1
            continue

        link_text = text[link_start + 1 : link_text_end]
        url = text[link_text_end + 2 : url_end]
        result.append(
            f'<a href="{html.escape(url, quote=True)}">{_parse_inline(link_text)}</a>'
        )
        position = url_end + 1

    return "".join(result)


def _parse_emphasis(escaped_text: str) -> str:
    """Convert Markdown emphasis markers in already-escaped text."""
    replacements: Sequence[tuple[re.Pattern[str], str]] = (
        (re.compile(r"\*\*(.+?)\*\*"), r"<strong>\1</strong>"),
        (re.compile(r"__(.+?)__"), r"<strong>\1</strong>"),
        (re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)"), r"<em>\1</em>"),
        (re.compile(r"(?<!_)_(?!_)(.+?)(?<!_)_(?!_)"), r"<em>\1</em>"),
    )
    formatted = escaped_text
    for pattern, replacement in replacements:
        formatted = pattern.sub(replacement, formatted)
    return formatted


__all__ = ["convert_markdown_to_html"]

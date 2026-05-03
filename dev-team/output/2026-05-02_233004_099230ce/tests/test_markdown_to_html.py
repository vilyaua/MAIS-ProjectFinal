"""Tests for the Markdown to HTML conversion library."""

from __future__ import annotations

import pytest
from src.markdown_to_html import convert, markdown_to_html


def test_headers_h1_to_h6_with_nested_bold() -> None:
    markdown = "\n".join(
        [
            "# **Title**",
            "## Subtitle",
            "### Third",
            "#### Fourth",
            "##### Fifth",
            "###### Sixth",
        ]
    )

    assert markdown_to_html(markdown) == "\n".join(
        [
            "<h1><strong>Title</strong></h1>",
            "<h2>Subtitle</h2>",
            "<h3>Third</h3>",
            "<h4>Fourth</h4>",
            "<h5>Fifth</h5>",
            "<h6>Sixth</h6>",
        ]
    )


def test_bold_and_italic_text() -> None:
    markdown = "This is **bold**, __also bold__, *italic*, and _also italic_."

    assert markdown_to_html(markdown) == (
        "<p>This is <strong>bold</strong>, <strong>also bold</strong>, "
        "<em>italic</em>, and <em>also italic</em>.</p>"
    )


def test_links_and_nested_formatting_in_link_label() -> None:
    markdown = "Visit [the **docs**](https://example.com?a=1&b=2)."

    assert markdown_to_html(markdown) == (
        '<p>Visit <a href="https://example.com?a=1&amp;b=2">the <strong>docs</strong></a>.</p>'
    )


def test_inline_code_and_fenced_code_block() -> None:
    markdown = "\n".join(
        [
            "Use `x < y` inline.",
            "",
            "```",
            "def hello():",
            "    return '<world>'",
            "```",
        ]
    )

    assert markdown_to_html(markdown) == "\n".join(
        [
            "<p>Use <code>x &lt; y</code> inline.</p>",
            "<pre><code>def hello():\n    return '&lt;world&gt;'</code></pre>",
        ]
    )


def test_ordered_and_unordered_lists_with_links() -> None:
    markdown = "\n".join(
        [
            "- [One](https://one.example)",
            "- **Two**",
            "",
            "1. First",
            "2. `Second`",
        ]
    )

    assert markdown_to_html(markdown) == "\n".join(
        [
            "<ul>",
            '<li><a href="https://one.example">One</a></li>',
            "<li><strong>Two</strong></li>",
            "</ul>",
            "<ol>",
            "<li>First</li>",
            "<li><code>Second</code></li>",
            "</ol>",
        ]
    )


def test_invalid_input_raises_value_error() -> None:
    invalid_values = ["", "   ", None, 123, [], {}]

    for value in invalid_values:
        with pytest.raises(ValueError, match="non-empty string|must not be empty"):
            markdown_to_html(value)  # type: ignore[arg-type]


def test_malformed_markdown_is_best_effort_and_does_not_crash() -> None:
    markdown = "This has **unclosed bold and [broken link]( and `code"

    assert markdown_to_html(markdown) == (
        "<p>This has **unclosed bold and [broken link]( and <code>code</code></p>"
    )


def test_convert_alias() -> None:
    assert convert("# Hello") == "<h1>Hello</h1>"

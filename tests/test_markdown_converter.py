"""Tests for the Markdown to HTML converter."""

from __future__ import annotations

import pytest

from src.markdown_converter import MarkdownConversionError, markdown_to_html


def test_converts_headers() -> None:
    assert markdown_to_html("# Title") == "<h1>Title</h1>"
    assert markdown_to_html("## Subtitle") == "<h2>Subtitle</h2>"
    assert markdown_to_html("### Section") == "<h3>Section</h3>"


def test_header_can_contain_inline_markup() -> None:
    assert markdown_to_html("# **Important**") == "<h1><strong>Important</strong></h1>"


def test_converts_bold_text() -> None:
    assert markdown_to_html("This is **bold** text") == (
        "This is <strong>bold</strong> text"
    )


def test_converts_italic_text() -> None:
    assert markdown_to_html("This is *italic* text") == "This is <em>italic</em> text"


def test_converts_links() -> None:
    assert markdown_to_html("Visit [Example](https://example.com)") == (
        'Visit <a href="https://example.com">Example</a>'
    )


def test_escapes_link_text_and_url() -> None:
    assert markdown_to_html("[<site>](https://example.com?a=1&b=2)") == (
        '<a href="https://example.com?a=1&amp;b=2">&lt;site&gt;</a>'
    )


def test_converts_fenced_code_blocks() -> None:
    markdown = "```\nprint('hello')\nif x < 1:\n    pass\n```"
    assert markdown_to_html(markdown) == (
        "<pre><code>print('hello')\nif x &lt; 1:\n    pass</code></pre>"
    )


def test_unclosed_fenced_code_block_is_escaped_without_crashing() -> None:
    markdown = "```\n**not bold**\n<script>"
    assert markdown_to_html(markdown) == (
        "<pre><code>**not bold**\n&lt;script&gt;</code></pre>"
    )


def test_converts_indented_code_blocks() -> None:
    markdown = "    line 1\n\tline <2>"
    assert markdown_to_html(markdown) == (
        "<pre><code>line 1\nline &lt;2&gt;</code></pre>"
    )


def test_converts_unordered_lists() -> None:
    markdown = "- one\n- **two**\n- three"
    assert markdown_to_html(markdown) == (
        "<ul>\n"
        "<li>one</li>\n"
        "<li><strong>two</strong></li>\n"
        "<li>three</li>\n"
        "</ul>"
    )


def test_converts_ordered_lists() -> None:
    markdown = "1. first\n2. [second](https://example.com)"
    assert markdown_to_html(markdown) == (
        "<ol>\n"
        "<li>first</li>\n"
        '<li><a href="https://example.com">second</a></li>\n'
        "</ol>"
    )


def test_mixed_list_types_are_separate_lists() -> None:
    markdown = "- one\n1. first"
    assert markdown_to_html(markdown) == (
        "<ul>\n<li>one</li>\n</ul>\n"
        "<ol>\n<li>first</li>\n</ol>"
    )


def test_malformed_or_unsupported_markdown_is_preserved_or_escaped() -> None:
    markdown = "#No header\nThis is **not closed\n<script>alert(1)</script>"
    assert markdown_to_html(markdown) == (
        "#No header\n"
        "This is **not closed\n"
        "&lt;script&gt;alert(1)&lt;/script&gt;"
    )


def test_non_string_input_raises_clear_error() -> None:
    with pytest.raises(MarkdownConversionError, match="expects a string"):
        markdown_to_html(123)  # type: ignore[arg-type]

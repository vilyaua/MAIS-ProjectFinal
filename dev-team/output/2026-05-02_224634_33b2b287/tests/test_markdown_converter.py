"""Tests for the Markdown to HTML converter."""

import pytest
from src.markdown_converter import MarkdownConversionError, convert_markdown


def test_header_conversion() -> None:
    html = convert_markdown("# Header")

    assert "<h1>Header</h1>" in html


def test_multiple_header_levels() -> None:
    html = convert_markdown("## Section\n### Subsection")

    assert "<h2>Section</h2>" in html
    assert "<h3>Subsection</h3>" in html


def test_bold_and_italic_conversion() -> None:
    html = convert_markdown("This is **bold** and *italic* text.")

    assert "<strong>bold</strong>" in html
    assert "<em>italic</em>" in html


def test_underscore_bold_and_italic_conversion() -> None:
    html = convert_markdown("This is __bold__ and _italic_ text.")

    assert "<strong>bold</strong>" in html
    assert "<em>italic</em>" in html


def test_link_conversion() -> None:
    html = convert_markdown("Visit [text](https://example.com) now.")

    assert '<a href="https://example.com">text</a>' in html


def test_code_block_conversion_preserves_content() -> None:
    markdown = "```\ndef hello():\n    return '<world>'\n```"

    html = convert_markdown(markdown)

    assert html.startswith("<pre><code>")
    assert html.endswith("</code></pre>")
    assert "def hello():\n    return '&lt;world&gt;'" in html


def test_unclosed_code_block_is_closed_gracefully() -> None:
    markdown = "```\nline one\nline two"

    html = convert_markdown(markdown)

    assert html == "<pre><code>line one\nline two</code></pre>"


def test_unordered_list_conversion() -> None:
    html = convert_markdown("- one\n* two\n+ three")

    assert "<ul>" in html
    assert "<li>one</li>" in html
    assert "<li>two</li>" in html
    assert "<li>three</li>" in html
    assert "</ul>" in html


def test_ordered_list_conversion() -> None:
    html = convert_markdown("1. one\n2. two")

    assert "<ol>" in html
    assert "<li>one</li>" in html
    assert "<li>two</li>" in html
    assert "</ol>" in html


def test_mixed_lists_are_separate_structures() -> None:
    html = convert_markdown("- unordered\n1. ordered")

    assert html == "<ul>\n<li>unordered</li>\n</ul>\n<ol>\n<li>ordered</li>\n</ol>"


def test_empty_input_returns_empty_string() -> None:
    assert convert_markdown("") == ""
    assert convert_markdown("   \n\t") == ""


def test_malformed_markdown_does_not_raise() -> None:
    html = convert_markdown("This **bold is unmatched and [bad link](")

    assert "<p>" in html
    assert "This **bold is unmatched" in html


def test_html_is_escaped_for_plain_text() -> None:
    html = convert_markdown("<script>alert('x')</script>")

    assert "&lt;script&gt;" in html
    assert "<script>" not in html


def test_non_string_input_raises_clear_error() -> None:
    with pytest.raises(MarkdownConversionError, match="must be a string"):
        convert_markdown(None)  # type: ignore[arg-type]

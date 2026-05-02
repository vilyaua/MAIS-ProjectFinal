"""Tests for the Markdown to HTML converter."""

from __future__ import annotations

import pytest
from src import convert_markdown


def test_empty_and_none_inputs_return_empty_string() -> None:
    assert convert_markdown("") == ""
    assert convert_markdown("   \n\t") == ""
    assert convert_markdown(None) == ""


def test_non_string_input_raises_type_error() -> None:
    with pytest.raises(TypeError, match="expects a string"):
        convert_markdown(123)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("markdown", "expected"),
    [
        ("# Heading", "<h1>Heading</h1>"),
        ("## Heading", "<h2>Heading</h2>"),
        ("### Heading", "<h3>Heading</h3>"),
        ("#### Heading", "<h4>Heading</h4>"),
        ("##### Heading", "<h5>Heading</h5>"),
        ("###### Heading", "<h6>Heading</h6>"),
    ],
)
def test_heading_levels(markdown: str, expected: str) -> None:
    assert convert_markdown(markdown) == expected


def test_inline_bold_italic_and_link() -> None:
    markdown = "This is **bold**, *italic*, and [a link](https://example.com)."
    expected = (
        "<p>This is <strong>bold</strong>, <em>italic</em>, and "
        '<a href="https://example.com">a link</a>.</p>'
    )
    assert convert_markdown(markdown) == expected


def test_code_block_escapes_html_and_preserves_content() -> None:
    markdown = "```\nif x < 2:\n    print('ok')\n```"
    expected = "<pre><code>if x &lt; 2:\n    print(&#x27;ok&#x27;)</code></pre>"
    assert convert_markdown(markdown) == expected


def test_unclosed_code_block_falls_back_to_code_until_end() -> None:
    markdown = "```\n**not bold**"
    expected = "<pre><code>**not bold**</code></pre>"
    assert convert_markdown(markdown) == expected


def test_unordered_and_ordered_lists() -> None:
    markdown = "* **bold** item\n* *italic* item\n\n1. first\n2. [second](url)"
    expected = (
        "<ul><li><strong>bold</strong> item</li>"
        "<li><em>italic</em> item</li></ul>\n"
        '<ol><li>first</li><li><a href="url">second</a></li></ol>'
    )
    assert convert_markdown(markdown) == expected


def test_nested_formatting_in_headers_and_links() -> None:
    markdown = "# A **bold** and *italic* [link **label**](https://example.com)"
    expected = (
        "<h1>A <strong>bold</strong> and <em>italic</em> "
        '<a href="https://example.com">link <strong>label</strong></a></h1>'
    )
    assert convert_markdown(markdown) == expected


def test_malformed_markdown_is_escaped_literal_fallback() -> None:
    markdown = "A **broken and [bad](<script>) plus <b>html</b>"
    expected = "<p>A **broken and [bad](&lt;script&gt;) plus &lt;b&gt;html&lt;/b&gt;</p>"
    assert convert_markdown(markdown) == expected


def test_paragraphs_are_well_formed() -> None:
    markdown = "First line\ncontinues\n\nSecond paragraph"
    expected = "<p>First line continues</p>\n<p>Second paragraph</p>"
    assert convert_markdown(markdown) == expected

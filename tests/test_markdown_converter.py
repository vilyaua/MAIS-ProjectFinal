"""Tests for the Markdown to HTML converter."""

import pytest

from src.markdown_converter import markdown_to_html


def test_headers_are_converted_to_matching_html_tags() -> None:
    markdown = "# Heading 1\n## Heading 2\n### Heading 3\n###### Heading 6"

    html = markdown_to_html(markdown)

    assert "<h1>Heading 1</h1>" in html
    assert "<h2>Heading 2</h2>" in html
    assert "<h3>Heading 3</h3>" in html
    assert "<h6>Heading 6</h6>" in html


def test_bold_and_italic_text_are_converted() -> None:
    markdown = "This is **bold**, __also bold__, *italic*, and _also italic_."

    html = markdown_to_html(markdown)

    assert "<strong>bold</strong>" in html
    assert "<strong>also bold</strong>" in html
    assert "<em>italic</em>" in html
    assert "<em>also italic</em>" in html


def test_links_are_converted_to_anchor_tags() -> None:
    markdown = "Visit [Example](https://example.com) now."

    html = markdown_to_html(markdown)

    assert '<a href="https://example.com">Example</a>' in html


def test_code_blocks_are_converted_and_preserve_formatting() -> None:
    markdown = "```\ndef hello():\n    return '<hello>'\n```"

    html = markdown_to_html(markdown)

    assert html.startswith("<pre><code>")
    assert html.endswith("</code></pre>")
    assert "def hello():\n    return '&lt;hello&gt;'" in html


def test_unterminated_code_block_is_rendered_gracefully() -> None:
    markdown = "```\nline one\n  line two"

    html = markdown_to_html(markdown)

    assert html == "<pre><code>line one\n  line two</code></pre>"


def test_unordered_lists_are_converted() -> None:
    markdown = "- First\n- Second with **bold**\n- Third"

    html = markdown_to_html(markdown)

    assert html == (
        "<ul>\n"
        "<li>First</li>\n"
        "<li>Second with <strong>bold</strong></li>\n"
        "<li>Third</li>\n"
        "</ul>"
    )


def test_ordered_lists_are_converted() -> None:
    markdown = "1. First\n2. Second\n3) Third"

    html = markdown_to_html(markdown)

    assert html == (
        "<ol>\n"
        "<li>First</li>\n"
        "<li>Second</li>\n"
        "<li>Third</li>\n"
        "</ol>"
    )


def test_switching_between_list_types_closes_previous_list() -> None:
    markdown = "- Bullet\n1. Number"

    html = markdown_to_html(markdown)

    assert html == "<ul>\n<li>Bullet</li>\n</ul>\n<ol>\n<li>Number</li>\n</ol>"


def test_plain_text_is_wrapped_in_paragraphs() -> None:
    markdown = "Hello **world**"

    html = markdown_to_html(markdown)

    assert html == "<p>Hello <strong>world</strong></p>"


def test_html_is_escaped_outside_code_blocks() -> None:
    markdown = "# <script>alert('x')</script>"

    html = markdown_to_html(markdown)

    assert html == "<h1>&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt;</h1>"


def test_empty_or_whitespace_input_returns_empty_string() -> None:
    assert markdown_to_html("") == ""
    assert markdown_to_html("   \n\t") == ""


@pytest.mark.parametrize("invalid_input", [None, 123, [], {}])
def test_non_string_input_raises_descriptive_error(invalid_input: object) -> None:
    with pytest.raises(TypeError, match="expects a string"):
        markdown_to_html(invalid_input)  # type: ignore[arg-type]

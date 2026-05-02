"""Tests for the Markdown to HTML converter."""

import pytest

from src import MarkdownConversionError, convert, convert_many, markdown_to_html


def test_empty_string_returns_empty_string() -> None:
    assert convert("") == ""
    assert convert("   \n\t  ") == ""


def test_headers_levels_one_to_six() -> None:
    markdown = "\n".join(
        [
            "# Heading 1",
            "## Heading 2",
            "### Heading 3",
            "#### Heading 4",
            "##### Heading 5",
            "###### Heading 6",
        ]
    )

    assert convert(markdown) == "\n".join(
        [
            "<h1>Heading 1</h1>",
            "<h2>Heading 2</h2>",
            "<h3>Heading 3</h3>",
            "<h4>Heading 4</h4>",
            "<h5>Heading 5</h5>",
            "<h6>Heading 6</h6>",
        ]
    )


def test_bold_and_italic_formatting() -> None:
    html = convert("This has **bold** and *italic* text.")
    assert html == "<p>This has <strong>bold</strong> and <em>italic</em> text.</p>"


def test_underscore_bold_and_italic_formatting() -> None:
    html = convert("This has __bold__ and _italic_ text.")
    assert html == "<p>This has <strong>bold</strong> and <em>italic</em> text.</p>"


def test_nested_formatting() -> None:
    html = convert("**bold and *italic* inside**")
    assert html == "<p><strong>bold and <em>italic</em> inside</strong></p>"


def test_links_are_converted() -> None:
    html = convert("Visit [Example](https://example.com) now.")
    assert html == '<p>Visit <a href="https://example.com">Example</a> now.</p>'


def test_link_label_supports_formatting() -> None:
    html = convert("Visit [**Example**](https://example.com).")
    assert html == '<p>Visit <a href="https://example.com"><strong>Example</strong></a>.</p>'


def test_inline_code_is_converted_and_escaped() -> None:
    html = convert("Use `print('<hello>')` here.")
    assert html == "<p>Use <code>print(&#x27;&lt;hello&gt;&#x27;)</code> here.</p>"


def test_fenced_code_block_is_converted() -> None:
    markdown = "```\ndef hello():\n    return '<world>'\n```"
    expected = "<pre><code>def hello():\n    return &#x27;&lt;world&gt;&#x27;</code></pre>"
    assert convert(markdown) == expected


def test_unclosed_fenced_code_block_gracefully_falls_back_to_code_block() -> None:
    markdown = "```\ndef hello():\n    pass"
    expected = "<pre><code>def hello():\n    pass</code></pre>"
    assert convert(markdown) == expected


def test_indented_code_block_is_converted() -> None:
    markdown = "    line 1\n    <line 2>"
    expected = "<pre><code>line 1\n&lt;line 2&gt;</code></pre>"
    assert convert(markdown) == expected


def test_unordered_list_is_converted() -> None:
    markdown = "- first\n- **second**\n- third"
    expected = "<ul>\n<li>first</li>\n<li><strong>second</strong></li>\n<li>third</li>\n</ul>"
    assert convert(markdown) == expected


def test_ordered_list_is_converted() -> None:
    markdown = "1. first\n2. [second](https://example.com)\n3. third"
    expected = (
        "<ol>\n"
        "<li>first</li>\n"
        '<li><a href="https://example.com">second</a></li>\n'
        "<li>third</li>\n"
        "</ol>"
    )
    assert convert(markdown) == expected


def test_mixed_blocks() -> None:
    markdown = "# Title\n\nParagraph with *style*.\n\n- item\n- item two"
    expected = (
        "<h1>Title</h1>\n"
        "<p>Paragraph with <em>style</em>.</p>\n"
        "<ul>\n<li>item</li>\n<li>item two</li>\n</ul>"
    )
    assert convert(markdown) == expected


def test_malformed_markdown_does_not_crash_and_is_escaped() -> None:
    html = convert("This is **not closed and <script>alert(1)</script>")
    assert html == (
        "<p>This is **not closed and "
        "&lt;script&gt;alert(1)&lt;/script&gt;</p>"
    )


def test_non_string_input_raises_meaningful_error() -> None:
    with pytest.raises(MarkdownConversionError, match="must be a string"):
        convert(None)  # type: ignore[arg-type]


def test_alias_and_batch_conversion() -> None:
    assert markdown_to_html("# Hi") == "<h1>Hi</h1>"
    assert convert_many(["# A", "*b*"]) == ["<h1>A</h1>", "<p><em>b</em></p>"]

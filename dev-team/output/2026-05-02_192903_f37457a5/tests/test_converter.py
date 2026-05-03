"""Tests for the Markdown to HTML converter."""

import pytest
from markdown_html_converter import convert_markdown, markdown_to_html
from markdown_html_converter.converter import parse_inline


def test_headers_levels_one_to_six() -> None:
    markdown = "\n".join(f"{'#' * level} Header {level}" for level in range(1, 7))

    html = convert_markdown(markdown)

    for level in range(1, 7):
        assert f"<h{level}>Header {level}</h{level}>" in html


def test_bold_and_italic_conversion() -> None:
    html = convert_markdown("This is **bold** and *italic* text")

    assert "<strong>bold</strong>" in html
    assert "<em>italic</em>" in html


def test_nested_inline_formatting() -> None:
    html = convert_markdown("**bold and *italic***")

    assert html == "<strong>bold and <em>italic</em></strong>"


def test_hyperlink_conversion() -> None:
    html = convert_markdown("Visit [Example](https://example.com?q=1&x=2)")

    assert 'Visit <a href="https://example.com?q=1&amp;x=2">Example</a>' == html


def test_inline_code_conversion_and_escaping() -> None:
    html = convert_markdown("Use `<tag>` and **bold**")

    assert html == "Use <code>&lt;tag&gt;</code> and <strong>bold</strong>"


def test_inline_code_is_not_parsed_for_markdown() -> None:
    html = convert_markdown("Use `**literal**`")

    assert html == "Use <code>**literal**</code>"


def test_unordered_list_conversion() -> None:
    html = convert_markdown("- first\n- **second**")

    assert html == "<ul><li>first</li><li><strong>second</strong></li></ul>"


def test_ordered_list_conversion() -> None:
    html = convert_markdown("1. first\n2. second")

    assert html == "<ol><li>first</li><li>second</li></ol>"


def test_nested_lists() -> None:
    html = convert_markdown("- parent\n  - child\n- sibling")

    assert html == "<ul><li>parent<ul><li>child</li></ul></li><li>sibling</li></ul>"


def test_empty_or_none_input_returns_empty_string() -> None:
    assert convert_markdown("") == ""
    assert convert_markdown(None) == ""


def test_bytes_input_decoded_with_replacement() -> None:
    assert convert_markdown(b"# Hi") == "<h1>Hi</h1>"
    assert "\ufffd" in convert_markdown(b"\xff")


def test_unexpected_input_type_raises_clear_type_error() -> None:
    with pytest.raises(TypeError, match="markdown input must be"):
        convert_markdown(123)  # type: ignore[arg-type]


def test_malformed_markdown_left_as_escaped_text() -> None:
    markdown = "This is **not closed and [bad]( and `code"

    html = convert_markdown(markdown)

    assert html == "This is **not closed and [bad]( and `code"


def test_html_is_escaped_to_prevent_invalid_output() -> None:
    html = convert_markdown("# <script>alert('x')</script>")

    assert html == "<h1>&lt;script&gt;alert('x')&lt;/script&gt;</h1>"


def test_alias_function_matches_converter() -> None:
    assert markdown_to_html("*x*") == convert_markdown("*x*")


def test_parse_inline_public_helper() -> None:
    assert parse_inline("[**x**](url)") == '<a href="url"><strong>x</strong></a>'

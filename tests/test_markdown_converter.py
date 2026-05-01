import pytest

from src.markdown_converter import MarkdownConverter, markdown_to_html


def test_headers_convert_to_html_header_tags():
    markdown = "# Title\n## Subtitle\n### Section"

    html = markdown_to_html(markdown)

    assert "<h1>Title</h1>" in html
    assert "<h2>Subtitle</h2>" in html
    assert "<h3>Section</h3>" in html


def test_bold_and_italic_convert_to_strong_and_em():
    markdown = "This is **bold** and __also bold__ with *italic* and _also italic_."

    html = markdown_to_html(markdown)

    assert "<strong>bold</strong>" in html
    assert "<strong>also bold</strong>" in html
    assert "<em>italic</em>" in html
    assert "<em>also italic</em>" in html


def test_links_convert_to_anchor_tags():
    markdown = "Visit [Example](https://example.com) now."

    html = markdown_to_html(markdown)

    assert '<a href="https://example.com">Example</a>' in html


def test_fenced_code_blocks_convert_to_pre_code():
    markdown = "```\nprint('hello')\nif a < b:\n    pass\n```"

    html = markdown_to_html(markdown)

    assert html == "<pre><code>print('hello')\nif a &lt; b:\n    pass</code></pre>"


def test_unordered_and_ordered_lists_convert_to_html_lists():
    markdown = "- first\n* second\n+ third\n\n1. one\n2. two"

    html = markdown_to_html(markdown)

    assert "<ul>\n<li>first</li>\n<li>second</li>\n<li>third</li>\n</ul>" in html
    assert "<ol>\n<li>one</li>\n<li>two</li>\n</ol>" in html


def test_switching_between_list_types_closes_previous_list():
    markdown = "- item\n1. numbered"

    html = markdown_to_html(markdown)

    assert html == "<ul>\n<li>item</li>\n</ul>\n<ol>\n<li>numbered</li>\n</ol>"


@pytest.mark.parametrize("empty_input", [None, "", "   ", "\n\n"])
def test_null_and_empty_input_returns_empty_string(empty_input):
    assert markdown_to_html(empty_input) == ""


@pytest.mark.parametrize("invalid_input", [123, [], {}, object()])
def test_non_string_input_raises_type_error(invalid_input):
    with pytest.raises(TypeError, match="markdown input must be a string"):
        markdown_to_html(invalid_input)  # type: ignore[arg-type]


def test_converter_class_api():
    converter = MarkdownConverter()

    assert converter.convert("# Hello") == "<h1>Hello</h1>"

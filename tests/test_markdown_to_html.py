import pytest

from src.markdown_to_html import MarkdownConversionError, convert_markdown


def test_headers_are_converted() -> None:
    assert convert_markdown("# Title") == "<h1>Title</h1>"
    assert convert_markdown("### Subtitle") == "<h3>Subtitle</h3>"


def test_bold_and_italic_are_converted() -> None:
    html = convert_markdown("This is **bold**, __strong__, *italic*, and _em_.")
    assert "<strong>bold</strong>" in html
    assert "<strong>strong</strong>" in html
    assert "<em>italic</em>" in html
    assert "<em>em</em>" in html


def test_links_are_converted() -> None:
    assert (
        convert_markdown("Visit [OpenAI](https://openai.com)")
        == "Visit <a href='https://openai.com'>OpenAI</a>"
    )


def test_inline_code_is_converted_and_escaped() -> None:
    assert convert_markdown("Use `<tag>` here") == "Use <code>&lt;tag&gt;</code> here"


def test_code_block_is_converted_and_escaped() -> None:
    markdown = "```\nprint('<hello>')\n```"
    assert (
        convert_markdown(markdown)
        == "<pre><code>print(&#x27;&lt;hello&gt;&#x27;)</code></pre>"
    )


def test_single_line_fenced_code_block_is_converted() -> None:
    assert convert_markdown("```code```") == "<pre><code>code</code></pre>"


def test_unordered_list_is_converted() -> None:
    assert convert_markdown("- one\n- two") == "<ul>\n<li>one\n</li>\n<li>two\n</li>\n</ul>"


def test_ordered_list_is_converted() -> None:
    assert convert_markdown("1. one\n2. two") == "<ol>\n<li>one\n</li>\n<li>two\n</li>\n</ol>"


def test_nested_list_is_contained_in_parent_item() -> None:
    html = convert_markdown("- parent\n  - child")
    assert "<ul>" in html
    assert "<li>parent" in html
    assert "<li>child" in html
    assert html.count("<ul>") == 2


def test_malformed_markdown_does_not_crash() -> None:
    assert convert_markdown("This is **not closed") == "This is **not closed"
    assert convert_markdown("[bad](") == "[bad]("


def test_non_string_input_raises_clear_error() -> None:
    with pytest.raises(MarkdownConversionError, match="expects a string"):
        convert_markdown(123)  # type: ignore[arg-type]

from src.markdown_converter import convert_markdown_to_html


def test_headers_levels_1_to_6():
    markdown = "\n".join(f"{'#' * level} Header {level}" for level in range(1, 7))

    html = convert_markdown_to_html(markdown)

    for level in range(1, 7):
        assert f"<h{level}>Header {level}</h{level}>" in html


def test_bold_and_italic_formatting():
    markdown = "This is **bold** and *italic*, plus __strong__ and _em_."

    html = convert_markdown_to_html(markdown)

    assert "<strong>bold</strong>" in html
    assert "<em>italic</em>" in html
    assert "<strong>strong</strong>" in html
    assert "<em>em</em>" in html


def test_link_conversion():
    markdown = "Visit [Example](https://example.com?a=1&b=2)."

    html = convert_markdown_to_html(markdown)

    assert '<a href="https://example.com?a=1&amp;b=2">Example</a>' in html


def test_fenced_code_block_preserves_formatting_and_escapes_html():
    markdown = "```python\ndef greet():\n    return '<hello>'\n```"

    html = convert_markdown_to_html(markdown)

    assert html == (
        "<pre><code>def greet():\n"
        "    return &#x27;&lt;hello&gt;&#x27;</code></pre>"
    )


def test_unordered_and_ordered_lists():
    markdown = "- apples\n- **bananas**\n\n1. first\n2. second"

    html = convert_markdown_to_html(markdown)

    assert "<ul>\n<li>apples</li>\n<li><strong>bananas</strong></li>\n</ul>" in html
    assert "<ol>\n<li>first</li>\n<li>second</li>\n</ol>" in html


def test_empty_none_and_non_string_input_return_empty_string():
    assert convert_markdown_to_html("") == ""
    assert convert_markdown_to_html(None) == ""
    assert convert_markdown_to_html(123) == ""


def test_complex_markdown_input():
    markdown = """# Title

Intro with **bold**, *italic*, and [link](https://example.com).

- item one
- item two

1. step one
2. step two

```
for i in range(2):
    print(i)
```

###### Done"""

    html = convert_markdown_to_html(markdown)

    assert "<h1>Title</h1>" in html
    assert "<p>Intro with <strong>bold</strong>, <em>italic</em>, and " in html
    assert '<a href="https://example.com">link</a>' in html
    assert "<ul>\n<li>item one</li>\n<li>item two</li>\n</ul>" in html
    assert "<ol>\n<li>step one</li>\n<li>step two</li>\n</ol>" in html
    assert "<pre><code>for i in range(2):\n    print(i)</code></pre>" in html
    assert "<h6>Done</h6>" in html


def test_html_is_escaped_outside_generated_tags():
    markdown = "# <Unsafe>\nA <script>alert('x')</script>"

    html = convert_markdown_to_html(markdown)

    assert "<h1>&lt;Unsafe&gt;</h1>" in html
    assert "&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt;" in html

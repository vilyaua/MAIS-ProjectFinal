# Markdown HTML Converter

A small, dependency-free Python library for converting a supported subset of Markdown to HTML.

## Supported syntax

- Headers (`#` through `######`)
- Bold text (`**text**`)
- Italic text (`*text*`)
- Hyperlinks (`[text](url)`)
- Inline code spans (`` `code` ``)
- Ordered and unordered lists, including simple indentation-based nesting

## Usage

```python
from markdown_html_converter import convert_markdown

html = convert_markdown("# Hello\nThis is **bold**")
print(html)
```

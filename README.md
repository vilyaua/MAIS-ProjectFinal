# Markdown to HTML Converter Library

A dependency-free Python library for converting a practical subset of Markdown to HTML.

## Usage

```python
from src.markdown_converter import markdown_to_html

html = markdown_to_html("# Hello\nThis is **bold** and [linked](https://example.com).")
```

Supported features:

- Headers (`#` through `######`)
- Bold (`**text**` and `__text__`)
- Italic (`*text*` and `_text_`)
- Links (`[text](url)`)
- Fenced code blocks using triple backticks
- Simple ordered and unordered lists

"""Example entry point for the Markdown to HTML converter."""

from markdown_html_converter import convert_markdown

if __name__ == "__main__":
    sample = "# Hello\n\nThis is **bold**, *italic*, and `code`.\n\n- One\n- Two"
    print(convert_markdown(sample))

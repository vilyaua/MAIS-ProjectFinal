# ASCII Art Text Generator

A small Python command-line program that renders text as readable ASCII art.

## Usage

Render text passed as command-line arguments:

```bash
python src/main.py Hello World
```

Render multi-line text from standard input:

```bash
printf 'Hello\nWorld' | python src/main.py
```

Unsupported characters are replaced with a question-mark glyph so generation
continues gracefully.

# ASCII Art Generator

A dependency-free Python command-line tool that converts text into readable ASCII art.

## Usage

Print to the console:

```bash
python src/main.py "Hello, World!"
```

Choose a style:

```bash
python src/main.py "Hello" --font star
```

Save to a file:

```bash
python src/main.py "Hello" --output hello_art.txt
```

If no text argument is supplied, the script prompts for input and asks whether to save the result.

Supported styles are `block`, `star`, `light`, and `dot`.

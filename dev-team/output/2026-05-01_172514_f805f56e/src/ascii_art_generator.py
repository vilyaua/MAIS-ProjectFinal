import sys
from typing import Optional

try:
    import pyfiglet
except ImportError:
    print("Missing required module 'pyfiglet'. Please install it using 'pip install pyfiglet'.")
    sys.exit(1)


def list_fonts() -> None:
    """Print the list of available fonts."""
    fonts = pyfiglet.FigletFont.getFonts()
    print("Available fonts:")
    for font in fonts:
        print(font)


def generate_ascii_art(text: str, font: Optional[str] = None) -> str:
    """Generate ASCII art text with the given font.

    Args:
        text (str): The text to convert.
        font (Optional[str]): The font to use.

    Returns:
        str: ASCII art representation of text.

    Raises:
        ValueError: If the text is empty or contains unsupported characters.
    """
    if not text.strip():
        raise ValueError("Input text cannot be empty.")

    # Validate characters: Allow basic printable ASCII except control chars
    if not all(32 <= ord(ch) <= 126 for ch in text):
        raise ValueError("Text contains unsupported special characters."
                         " Please use printable ASCII characters.")

    figlet = pyfiglet.Figlet(font=font) if font else pyfiglet.Figlet()
    return figlet.renderText(text)


def main() -> None:
    """Main function to run the ASCII art generator."""
    print("ASCII Art Generator")
    print("Enter your text below. To see list of fonts, enter '!fonts'.")

    try:
        user_input = input("Text: ").strip()
        if user_input == "!fonts":
            list_fonts()
            return

        font_choice = input("Enter font name (or press Enter for default): ").strip() or None

        ascii_art = generate_ascii_art(user_input, font_choice)
        print("\nGenerated ASCII Art:\n")
        print(ascii_art)

    except ValueError as ve:
        print(f"Error: {ve}")
    except Exception as e:
        print(f"Unexpected error occurred: {e}")


if __name__ == "__main__":
    main()

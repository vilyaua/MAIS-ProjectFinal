import sys

try:
    from pyfiglet import Figlet, FontNotFound
except ImportError:
    print("Error: pyfiglet package not installed. Please install it with 'pip install pyfiglet'.")
    sys.exit(1)

MAX_INPUT_LENGTH = 100  # Limit to prevent console overflow
FONT = "standard"


def ascii_art_from_text(text: str, font: str = FONT) -> str:
    """
    Converts a string to its ASCII art representation.

    Args:
        text: Input string to be converted.
        font: The pyfiglet font to use.
    Returns:
        An ASCII art string.
    Raises:
        ValueError: On invalid input (empty, non-string, invalid characters, font error).
    """
    if not isinstance(text, str):
        raise ValueError("Input must be a string.")
    if not text.strip():
        raise ValueError("Input text cannot be empty.")

    # Truncate to avoid excessively long output
    if len(text) > MAX_INPUT_LENGTH:
        text = text[:MAX_INPUT_LENGTH] + "..."
    try:
        figlet = Figlet(font=font)
        output = figlet.renderText(text)
    except FontNotFound:
        raise ValueError(f"Font '{font}' is not supported.")
    except Exception as e:
        raise ValueError(f"Failed to generate ASCII art. {e}")
    return output


def main():
    if len(sys.argv) < 2:
        print("Usage: python src/main.py <text to convert>")
        sys.exit(1)
    user_input = " ".join(sys.argv[1:])
    try:
        art = ascii_art_from_text(user_input)
        print(art)
    except ValueError as err:
        print(f"Error: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()

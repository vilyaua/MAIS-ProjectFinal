"""Console entry point for the ASCII art generator."""

from __future__ import annotations

from ascii_art import generate_ascii_art


def main() -> None:
    """Prompt for text and print its ASCII art representation."""
    try:
        user_text = input("Enter text to convert to ASCII art: ")
        ascii_art = generate_ascii_art(user_text)
    except ValueError as error:
        print(f"Error: {error}")
        return

    print(ascii_art)


if __name__ == "__main__":
    main()

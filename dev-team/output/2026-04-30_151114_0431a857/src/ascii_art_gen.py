import argparse
import sys
from typing import List
import string

try:
    from pyfiglet import Figlet
except ImportError:
    print("Error: pyfiglet package is required. Please install it using 'pip install pyfiglet'.")
    sys.exit(1)

def is_printable(s: str) -> bool:
    """Check if the string contains only printable characters."""
    return all(c in string.printable and not c in '\x0b\x0c' for c in s)

def get_available_fonts() -> List[str]:
    f = Figlet()
    return f.getFonts()

def generate_ascii_art(text: str, font: str = 'standard') -> str:
    available_fonts = get_available_fonts()
    if font not in available_fonts:
        raise ValueError(f"Unsupported font: '{font}'. Available fonts: {', '.join([repr(f) for f in available_fonts[:5]])} ...")
    if not text:
        raise ValueError("Input text cannot be empty.")
    if not is_printable(text):
        raise ValueError("Input text contains non-printable characters.")
    f = Figlet(font=font)
    return f.renderText(text)

def main():
    parser = argparse.ArgumentParser(description="ASCII Art Text Generator")
    parser.add_argument('text', nargs='?', help='Input text to convert to ASCII art')
    parser.add_argument('-f', '--font', default='standard', help='ASCII art font to use (default: standard)')
    parser.add_argument('--list-fonts', action='store_true', help='List available fonts and exit')
    args = parser.parse_args()

    if args.list_fonts:
        fonts = get_available_fonts()
        print("Available fonts:")
        for font in fonts:
            print(font)
        sys.exit(0)

    if args.text is None:
        print("Error: No input text provided.")
        parser.print_help()
        sys.exit(1)

    try:
        art = generate_ascii_art(args.text, args.font)
        print(art)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

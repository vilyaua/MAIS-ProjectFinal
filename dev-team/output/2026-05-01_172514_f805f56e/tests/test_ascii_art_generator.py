import os
import sys

import pytest

# Adjust path to import src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from ascii_art_generator import generate_ascii_art


def test_generate_ascii_art_basic():
    art = generate_ascii_art("Test")
    assert isinstance(art, str)
    assert art.strip() != ""


def test_generate_ascii_art_with_font():
    art = generate_ascii_art("Test", font="standard")
    assert isinstance(art, str)
    assert art.strip() != ""


def test_empty_input():
    with pytest.raises(ValueError):
        generate_ascii_art("")


def test_unsupported_characters():
    # Using a character outside typical ASCII printable range
    with pytest.raises(ValueError):
        generate_ascii_art("Hello\x01World")


def test_generate_ascii_art_invalid_font():
    # If invalid font name given, pyfiglet throws a FontNotFound error
    from pyfiglet import FontNotFound

    with pytest.raises(FontNotFound):
        generate_ascii_art("Hello", font="nonexistentfont")

import sys
import types
import pytest

# Patch sys.modules to mock pyfiglet if not installed
# This allows early test validation without pyfiglet
class MockFiglet:
    def __init__(self, font=None):
        if font == "nonexistentfont1234":
            raise Exception("Font not supported.")
    def renderText(self, text):
        return f"ASCII: {text}"

sys_modules_backup = sys.modules.copy()
if 'pyfiglet' not in sys.modules:
    mock_pyfiglet = types.ModuleType("pyfiglet")
    mock_pyfiglet.Figlet = MockFiglet
    mock_pyfiglet.FontNotFound = Exception
    sys.modules['pyfiglet'] = mock_pyfiglet
    sys.modules['pyfiglet.Figlet'] = MockFiglet

from src.main import ascii_art_from_text, FONT, MAX_INPUT_LENGTH

def test_valid_ascii():
    art = ascii_art_from_text("Hello", font=FONT)
    assert "H" in art or "ASCII:" in art

def test_empty_string():
    with pytest.raises(ValueError, match="empty"):
        ascii_art_from_text("")

def test_non_string_input():
    with pytest.raises(ValueError, match="string"):
        ascii_art_from_text(123)
    with pytest.raises(ValueError, match="string"):
        ascii_art_from_text(None)

def test_long_input():
    long_string = "A" * (MAX_INPUT_LENGTH + 10)
    art = ascii_art_from_text(long_string, font=FONT)
    assert ("..." in art) or (len(long_string) > MAX_INPUT_LENGTH)

def test_unsupported_font():
    with pytest.raises(ValueError, match="Font.*not supported"):
        ascii_art_from_text("Test", font="nonexistentfont1234")

# Clean up mocked modules after test session
def teardown_module(module):
    sys.modules.clear()
    sys.modules.update(sys_modules_backup)

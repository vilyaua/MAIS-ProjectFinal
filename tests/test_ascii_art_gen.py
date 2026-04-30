import pytest
from src.ascii_art_gen import generate_ascii_art, get_available_fonts

def test_generate_ascii_art_valid():
    fonts = get_available_fonts()
    font = fonts[0] if fonts else 'standard'
    result = generate_ascii_art('Test', font=font)
    assert isinstance(result, str)
    assert 'Test' not in result  # Should not match plain input
    assert len(result) > 0

def test_generate_ascii_art_invalid_font():
    with pytest.raises(ValueError) as exc_info:
        generate_ascii_art('Hello', font='notafont')
    assert "Unsupported font" in str(exc_info.value)

def test_generate_ascii_art_empty_text():
    with pytest.raises(ValueError) as exc_info:
        generate_ascii_art('', font='standard')
    assert "Input text cannot be empty" in str(exc_info.value)

def test_generate_ascii_art_unprintable():
    with pytest.raises(ValueError) as exc_info:
        generate_ascii_art('Hello\x07', font='standard')
    assert "non-printable characters" in str(exc_info.value)

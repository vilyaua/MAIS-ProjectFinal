from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ascii_art import (  # noqa: E402
    available_fonts,
    format_unsupported_warning,
    generate_ascii_art,
    save_art_to_file,
    validate_text,
)


def test_generate_ascii_art_for_valid_text() -> None:
    result = generate_ascii_art("Hi")

    assert result.unsupported_characters == ()
    assert "#   #" in result.art
    assert "#####" in result.art
    assert len(result.art.splitlines()) == 5


def test_empty_input_is_rejected() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        validate_text("   ")

    with pytest.raises(ValueError, match="non-empty"):
        generate_ascii_art("")


def test_special_characters_are_supported() -> None:
    result = generate_ascii_art("Go!")

    assert result.unsupported_characters == ()
    assert len(result.art.splitlines()) == 5
    assert "# ###" in result.art


def test_unsupported_characters_are_reported_and_skipped() -> None:
    result = generate_ascii_art("A🙂B")

    assert result.unsupported_characters == ("🙂",)
    assert "unsupported" in format_unsupported_warning(result.unsupported_characters)
    assert len(result.art.splitlines()) == 5


def test_save_art_to_file(tmp_path: Path) -> None:
    art = generate_ascii_art("Save me").art
    output_file = tmp_path / "art.txt"

    saved_path = save_art_to_file(art, output_file)

    assert saved_path == output_file
    assert output_file.read_text(encoding="utf-8") == art + "\n"


def test_multiple_font_styles_change_output() -> None:
    assert "star" in available_fonts()

    block = generate_ascii_art("A", font="block").art
    star = generate_ascii_art("A", font="star").art

    assert block != star
    assert "*" in star


def test_spaces_are_preserved() -> None:
    compact = generate_ascii_art("AA").art.splitlines()[0]
    spaced = generate_ascii_art("A A").art.splitlines()[0]

    assert len(spaced) > len(compact)

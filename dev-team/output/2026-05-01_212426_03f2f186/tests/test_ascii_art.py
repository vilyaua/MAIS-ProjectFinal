import io

from src import ascii_art


def test_generate_ascii_art_non_empty_block():
    art = ascii_art.generate_ascii_art("Hi")
    assert "#   #" in art
    assert "#####" in art


def test_generate_ascii_art_simple_font():
    art = ascii_art.generate_ascii_art("Hi!", font="simple")
    assert art == "+-----+\n| Hi! |\n+-----+"


def test_invalid_font_has_clear_message():
    try:
        ascii_art.generate_ascii_art("Hi", font="missing")
    except ValueError as exc:
        assert "Invalid font/style" in str(exc)
        assert "block" in str(exc)
        assert "simple" in str(exc)
    else:
        raise AssertionError("Expected invalid font to raise ValueError")


def test_control_characters_are_sanitized():
    art = ascii_art.generate_ascii_art("A\x1bB")
    assert "A\x1bB" not in art
    assert len(art.splitlines()) == 5


def test_empty_argument_returns_nonzero(capsys):
    exit_code = ascii_art.main([""])
    captured = capsys.readouterr()
    assert exit_code != 0
    assert "input text is required" in captured.err


def test_reads_from_stdin(monkeypatch, capsys):
    stdin = io.StringIO("OK\n")
    stdin.isatty = lambda: False
    monkeypatch.setattr(ascii_art.sys, "stdin", stdin)
    exit_code = ascii_art.main([])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out
    assert captured.err == ""

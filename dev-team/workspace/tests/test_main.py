import sys
import io
import builtins
import pytest
from src import main

def simulate_input_output(inputs):
    inputs_iter = iter(inputs)
    def mock_input(prompt=""):
        print(prompt, end="")
        return next(inputs_iter)
    return mock_input

def test_board_display(capsys):
    board = [["X", "O", "X"], ["", "X", "O"], ["O", "", ""]]
    main.print_board(board)
    captured = capsys.readouterr()
    # Check that the board is printed and all board elements appear
    assert "X" in captured.out
    assert "O" in captured.out

def test_winner_row():
    board = [["X","X","X"],["O","","O"],["","",""]]
    assert main.check_winner(board) == "X"

def test_winner_col():
    board = [["O","X",""] , ["O","X",""] , ["O","",""]]
    assert main.check_winner(board) == "O"

def test_winner_diag():
    board = [["O", "X", "X"], ["", "O", ""], ["", "", "O"]]
    assert main.check_winner(board) == "O"

def test_board_full():
    board = [["X", "O", "X"], ["O", "X", "O"], ["O", "X", "O"]]
    assert main.board_full(board)
    board[0][0] = ""
    assert not main.board_full(board)

def test_get_move_valid(monkeypatch):
    board = [["" for _ in range(3)] for _ in range(3)]
    monkeypatch.setattr('builtins.input', lambda x: "2 3")
    row, col = main.get_move(board, "X")
    assert (row, col) == (1, 2)

def test_get_move_invalid(monkeypatch, capsys):
    board = [["" for _ in range(3)] for _ in range(3)]
    # First move invalid (4 1), then valid (1 2)
    moves = ["4 1", "1 2"]
    monkeypatch.setattr('builtins.input', simulate_input_output(moves))
    row, col = main.get_move(board, "X")
    assert (row, col) == (0, 1)
    captured = capsys.readouterr()
    assert "Numbers must be between 1 and 3" in captured.out

def test_prompt_restart(monkeypatch):
    monkeypatch.setattr('builtins.input', lambda x: "y")
    assert main.prompt_restart() is True
    monkeypatch.setattr('builtins.input', lambda x: "q")
    assert main.prompt_restart() is False
    answers = ["foo", "y"]
    monkeypatch.setattr('builtins.input', simulate_input_output(answers))
    assert main.prompt_restart() is True

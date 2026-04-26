from typing import List, Tuple, Optional

def print_board(board: List[List[str]]) -> None:
    print("\n  1   2   3")
    for idx, row in enumerate(board):
        row_display = " | ".join(cell if cell else ' ' for cell in row)
        print(f"{idx+1} {row_display}")
        if idx < 2:
            print("  ---------")
    print()

def check_winner(board: List[List[str]]) -> Optional[str]:
    # Rows, columns and diagonals to check
    for i in range(3):
        if board[i][0] and all(board[i][j] == board[i][0] for j in range(3)):
            return board[i][0]  # Row
        if board[0][i] and all(board[j][i] == board[0][i] for j in range(3)):
            return board[0][i]  # Column
    # Diagonals
    if board[0][0] and all(board[k][k] == board[0][0] for k in range(3)):
        return board[0][0]
    if board[0][2] and all(board[k][2-k] == board[0][2] for k in range(3)):
        return board[0][2]
    return None

def board_full(board: List[List[str]]) -> bool:
    return all(cell for row in board for cell in row)

def get_move(board: List[List[str]], player: str) -> Tuple[int, int]:
    while True:
        try:
            move_str = input(f"Player {player}, enter your move (row and column, e.g., 1 2): ").strip()
            parts = move_str.split()
            if len(parts) != 2:
                print("Error: Enter exactly two numbers separated by a space.")
                continue
            row_str, col_str = parts
            if not (row_str.isdigit() and col_str.isdigit()):
                print("Error: Both inputs must be numbers from 1 to 3.")
                continue
            row, col = int(row_str) - 1, int(col_str) - 1
            if not (0 <= row <= 2 and 0 <= col <= 2):
                print("Error: Numbers must be between 1 and 3.")
                continue
            if board[row][col]:
                print("Error: Cell already occupied. Choose another.")
                continue
            return row, col
        except Exception:
            print("Error: Invalid input. Please try again.")

def prompt_restart() -> bool:
    while True:
        answer = input("Do you want to play again? (y to restart, q to quit): ").strip().lower()
        if answer == 'y':
            return True
        if answer == 'q':
            return False
        print("Invalid input. Enter 'y' to restart or 'q' to quit.")

def play_game() -> None:
    while True:
        board: List[List[str]] = [["" for _ in range(3)] for _ in range(3)]
        current_player = "X"
        winner: Optional[str] = None
        print("\nWelcome to Tic-Tac-Toe!")
        print_board(board)
        while True:
            row, col = get_move(board, current_player)
            board[row][col] = current_player
            print_board(board)
            winner = check_winner(board)
            if winner:
                print(f"Player {winner} wins! Congratulations!")
                break
            if board_full(board):
                print("It's a draw!")
                break
            current_player = "O" if current_player == "X" else "X"
        if not prompt_restart():
            print("Thanks for playing! Goodbye!")
            break

if __name__ == "__main__":
    play_game()

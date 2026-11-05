"""board_game.py - Step 1: play with a chess board in plain Python.

Run me with:

    python -m bot.board_game

This is the "hello world" of chess. We build a board, print it, play a
couple of moves, and print it again. No internet and no engine needed.
"""
from __future__ import annotations

import chess


def demo() -> None:
    """Create a board, print it, play a few moves, and print the result."""
    board = chess.Board()  # the normal starting position
    print("Start position:\n")
    print(board)  # python-chess draws a nice ASCII board for us

    # It is very easy to ask python-chess questions.
    print("\nWhite has", board.legal_moves.count(), "legal moves at the start.")

    # Let's play 1. e4 e5 2. Nf3
    for uci in ["e2e4", "e7e5", "g1f3"]:
        board.push_uci(uci)
        print(f"\nAfter {uci}:\n")
        print(board)

    side = "White" if board.turn == chess.WHITE else "Black"
    print(f"\nIt is now {side} to move.")
    print("This position as a FEN:", board.fen())


if __name__ == "__main__":
    demo()

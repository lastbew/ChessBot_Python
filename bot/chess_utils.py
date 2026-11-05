"""chess_utils.py - tiny helpers that turn Lichess data into a chess board.

These functions are "pure": given the same input they always return the
same output, and they don't touch the network. That makes them easy to
test (see tests/test_turn_logic.py).
"""
from __future__ import annotations

import chess


def board_from_moves(initial_fen: str | None, moves: str | None) -> chess.Board:
    """Build a python-chess Board from a starting position + a move list.

    Lichess sends moves as one string like "e2e4 e7e5 g1f3" (UCI format).
    initial_fen is "startpos" (or empty) for a normal game, or a custom FEN.
    """
    # "startpos" and blank both mean the standard starting position.
    fen = initial_fen if initial_fen and initial_fen != "startpos" else None
    board = chess.Board(fen) if fen else chess.Board()

    if moves:
        for uci in moves.split():
            # push_uci understands plain moves like "e2e4" and also
            # promotions like "e7e8q" (the trailing letter is the piece).
            board.push_uci(uci)

    return board

"""vision.py - helpers that decide what the Bot Vision window highlights.

Keeping this logic out of the drawing code makes it easy to test and tweak:
  * focus_moves()      - the legal moves of ONE piece (the one being played)
  * threatened_squares() - squares where our pieces are attacked ("threats")
"""
from __future__ import annotations

import chess


def focus_moves(board: chess.Board, chosen: chess.Move | None) -> list[chess.Move]:
    """Legal moves belonging to the single piece that is being played.

    If 'chosen' is the move the bot picked, we highlight all the destinations
    of THAT piece (not every piece on the board). This is what keeps the
    window clean.
    """
    if chosen is None:
        return []
    return [move for move in board.legal_moves if move.from_square == chosen.from_square]


def threatened_squares(board: chess.Board, our_color: chess.Color) -> list[int]:
    """Squares where OUR pieces are attacked by the opponent ('threats')."""
    opponent = not our_color
    harmed: list[int] = []
    for square, piece in board.piece_map().items():
        if piece.color == our_color and board.attackers(opponent, square):
            harmed.append(square)
    return harmed

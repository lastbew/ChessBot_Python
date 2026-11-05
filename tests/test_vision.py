"""Tests for the vision helpers (what the window highlights)."""
import chess

from bot.vision import focus_moves, threatened_squares


def test_focus_moves_only_the_chosen_piece():
    board = chess.Board()
    chosen = chess.Move.from_uci("e2e4")
    moves = focus_moves(board, chosen)

    assert moves, "the e-pawn should have moves"
    assert all(move.from_square == chess.E2 for move in moves)
    assert len(moves) == 2  # e2e3 and e2e4
    assert chosen in moves


def test_focus_moves_empty_when_nothing_chosen():
    assert focus_moves(chess.Board(), None) == []


def test_threatened_squares_flags_attacked_piece():
    # White queen on d4 is attacked by the black pawn on e5.
    board = chess.Board("4k3/8/8/4p3/3Q4/8/8/4K3 w - - 0 1")
    threatened = threatened_squares(board, chess.WHITE)

    assert chess.D4 in threatened
    assert chess.E1 not in threatened  # the king is not attacked here

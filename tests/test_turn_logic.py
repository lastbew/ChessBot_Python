"""Tests for turning a Lichess move-list into a board (our turn logic)."""
import chess

from bot.chess_utils import board_from_moves


def test_start_position_is_white_to_move():
    board = board_from_moves(None, "")
    assert board.turn == chess.WHITE


def test_after_one_move_black_to_move():
    board = board_from_moves(None, "e2e4")
    assert board.turn == chess.BLACK


def test_after_two_moves_white_to_move():
    board = board_from_moves(None, "e2e4 e7e5")
    assert board.turn == chess.WHITE


def test_startpos_keyword_is_handled():
    # Lichess sometimes sends the literal string "startpos".
    board = board_from_moves("startpos", "e2e4")
    assert board.turn == chess.BLACK


def test_promotion_move_is_applied():
    # A promotion like "a7a8q" ends in the piece to promote to.
    # Start from a simple position: white pawn on a7, ready to promote.
    fen = "4k3/P7/8/8/8/8/8/4K3 w - - 0 1"
    board = board_from_moves(fen, "a7a8q")

    # The pawn became a white queen on a8, and now it's Black's move.
    assert board.piece_at(chess.A8) == chess.Piece(chess.QUEEN, chess.WHITE)
    assert board.turn == chess.BLACK

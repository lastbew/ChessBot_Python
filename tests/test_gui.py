"""Smoke tests for the pygame vision window (renders offscreen, no popup)."""
import chess
import pytest

pytest.importorskip("pygame")

from bot.gui import BoardView


def test_render_start_position():
    view = BoardView(headless=True)
    try:
        board = chess.Board()
        alive = view.show(board, list(board.legal_moves), info="test")
        assert alive is True
    finally:
        view.close()


def test_render_with_chosen_move_arrow():
    view = BoardView(headless=True)
    try:
        board = chess.Board()
        chosen = chess.Move.from_uci("e2e4")
        assert view.show(board, list(board.legal_moves), chosen_move=chosen) is True
    finally:
        view.close()


def test_square_coordinates_are_in_bounds():
    view = BoardView(square_size=40, headless=True)
    try:
        for square in chess.SQUARES:
            rect = view._square_to_rect(square)
            assert 0 <= rect.x < view.width
            assert 0 <= rect.y < view.height
    finally:
        view.close()


def test_show_lobby_renders():
    view = BoardView(headless=True)
    try:
        assert view.show_lobby("Waiting for a game...", ["line 1", "line 2"]) is True
    finally:
        view.close()

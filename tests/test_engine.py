"""Tests for the Stockfish engine wrapper (skipped if Stockfish is absent)."""
import chess
import pytest

from bot.engine import Engine, find_stockfish


def _skip_if_no_engine():
    """Skip the test (not fail) if Stockfish hasn't been downloaded."""
    try:
        find_stockfish()
    except FileNotFoundError:
        pytest.skip("Stockfish is not installed in engine/stockfish/")


def test_start_position_returns_a_legal_move():
    _skip_if_no_engine()
    with Engine() as engine:
        move = engine.best_move(None, time_ms=300)

    board = chess.Board()
    assert chess.Move.from_uci(move) in board.legal_moves


def test_finds_mate_in_one():
    _skip_if_no_engine()
    # White to move and mate in one (Re8#).
    fen = "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 1"
    with Engine() as engine:
        move = engine.best_move(fen, time_ms=800)

    board = chess.Board(fen)
    board.push_uci(move)
    assert board.is_checkmate(), f"expected mate, engine played {move}"

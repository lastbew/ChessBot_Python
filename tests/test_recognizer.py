"""Tests for image -> board recognition (deterministic parts + round-trip)."""
from pathlib import Path

import chess
import cv2
import numpy as np
import pytest

from bot.recognizer import build_board, order_corners, split_squares, warp_board

MODEL_PATH = Path(__file__).resolve().parent.parent / "assets" / "model" / "piece_classifier.pt"


def test_order_corners_sorts_into_tl_tr_br_bl():
    points = np.array([[10, 10], [100, 10], [100, 100], [10, 100]], np.float32)
    shuffled = points[[2, 0, 3, 1]]
    ordered = order_corners(shuffled)
    assert tuple(ordered[0]) == (10.0, 10.0)    # top-left
    assert tuple(ordered[1]) == (100.0, 10.0)   # top-right
    assert tuple(ordered[2]) == (100.0, 100.0)  # bottom-right
    assert tuple(ordered[3]) == (10.0, 100.0)   # bottom-left


def test_split_squares_returns_64_tiles():
    warped = np.zeros((128, 128, 3), np.uint8)
    crops = split_squares(warped)
    assert len(crops) == 64
    assert crops[0].size == (16, 16)


def test_build_board_maps_labels_to_correct_squares():
    labels = ["empty"] * 64
    labels[60] = "wK"  # bottom area -> e1
    labels[52] = "wP"  # -> e2
    labels[4] = "bK"   # top area -> e8
    board = build_board(labels, side_to_move=chess.WHITE)

    assert board.piece_at(chess.E1) == chess.Piece(chess.KING, chess.WHITE)
    assert board.piece_at(chess.E2) == chess.Piece(chess.PAWN, chess.WHITE)
    assert board.piece_at(chess.E8) == chess.Piece(chess.KING, chess.BLACK)
    assert board.fen() == "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1"


def test_build_board_rejects_missing_king():
    labels = ["empty"] * 64
    labels[60] = "wK"  # no black king
    with pytest.raises(ValueError):
        build_board(labels)


def test_warp_board_gives_requested_size():
    image = np.zeros((100, 120, 3), np.uint8)
    corners = np.array([[0, 0], [119, 0], [119, 99], [0, 99]], np.float32)
    warped = warp_board(image, corners, size=64)
    assert warped.shape[:2] == (64, 64)


def test_roundtrip_rendered_start_position():
    """End-to-end: draw the start position, then recognise it back."""
    if not MODEL_PATH.exists():
        pytest.skip("model not trained yet (run train_piece_classifier.py)")

    from bot.classifier import load_model
    from bot.dataset import render_board_image
    from bot.recognizer import recognize

    board = chess.Board()
    rgb = np.asarray(render_board_image(board, square=64))
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

    height, width = bgr.shape[:2]
    corners = np.array(
        [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
        np.float32,
    )
    recognised, _labels = recognize(bgr, load_model(MODEL_PATH), corners=corners)

    correct = sum(
        recognised.piece_at(square) == board.piece_at(square)
        for square in chess.SQUARES
    )
    assert correct >= 62, f"only {correct}/64 squares were recognised correctly"

"""recognizer.py - turn a screenshot of a chess board into a chess.Board.

Pipeline:
    image --detect_board--> 4 corners
          --warp_board--->  clean top-down 8x8 square
          --split_squares-> 64 little square images
          --classify------> 64 labels ("wP", "empty", ...)
          --build_board---> a real chess.Board (and its FEN)

OpenCV (cv2) does the image geometry; our CNN classifies each square.
"""
from __future__ import annotations

from pathlib import Path

import chess
import cv2
import numpy as np
from PIL import Image

from .classifier import classify_batch

# Which chess piece type each letter means.
PIECE_TYPE = {
    "P": chess.PAWN, "N": chess.KNIGHT, "B": chess.BISHOP,
    "R": chess.ROOK, "Q": chess.QUEEN, "K": chess.KING,
}


def load_image(path: str | Path) -> np.ndarray:
    """Load an image file as a BGR numpy array (OpenCV's format)."""
    image = cv2.imread(str(path))
    if image is None:
        raise FileNotFoundError(f"Could not read image: {path}")
    return image


def order_corners(points: np.ndarray) -> np.ndarray:
    """Order 4 points as top-left, top-right, bottom-right, bottom-left."""
    points = np.array(points, dtype=np.float32).reshape(4, 2)
    ordered = np.zeros((4, 2), dtype=np.float32)
    sums = points.sum(axis=1)
    differences = np.diff(points, axis=1).ravel()  # x - y
    ordered[0] = points[np.argmin(sums)]        # top-left  (smallest x+y)
    ordered[2] = points[np.argmax(sums)]        # bottom-right (largest x+y)
    ordered[1] = points[np.argmin(differences)]  # top-right (smallest x-y)
    ordered[3] = points[np.argmax(differences)]  # bottom-left (largest x-y)
    return ordered


def detect_board(image: np.ndarray) -> np.ndarray | None:
    """Try to find the 4 corners of the board automatically.

    Returns an ordered (4,2) array of corners, or None if nothing found.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    image_area = image.shape[0] * image.shape[1]
    best = None
    best_area = 0
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < image_area * 0.10:  # ignore tiny shapes
            continue
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
        if len(approx) == 4 and area > best_area:
            best = approx
            best_area = area

    if best is None:
        return None
    return order_corners(best.reshape(4, 2))


def warp_board(image: np.ndarray, corners: np.ndarray, size: int = 512) -> np.ndarray:
    """Apply a perspective transform so the board becomes a square."""
    corners = np.array(corners, dtype=np.float32).reshape(4, 2)
    destination = np.array(
        [[0, 0], [size - 1, 0], [size - 1, size - 1], [0, size - 1]],
        dtype=np.float32,
    )
    matrix = cv2.getPerspectiveTransform(corners, destination)
    return cv2.warpPerspective(image, matrix, (size, size))


def split_squares(warped: np.ndarray) -> list[Image.Image]:
    """Cut the warped board into 64 square images.

    Order is reading order: index 0 is the TOP-LEFT square (rank 8, file a
    when White is at the bottom), index 63 is the BOTTOM-RIGHT.
    """
    height, width = warped.shape[:2]
    cell = min(height, width) // 8
    crops: list[Image.Image] = []
    for row in range(8):
        for col in range(8):
            x0, y0 = col * cell, row * cell
            patch = warped[y0:y0 + cell, x0:x0 + cell]
            rgb = cv2.cvtColor(patch, cv2.COLOR_BGR2RGB)
            crops.append(Image.fromarray(rgb))
    return crops


def classify_squares(model, crops: list[Image.Image]) -> list[str]:
    """Return a label for each of the 64 square images."""
    return classify_batch(model, crops)


def build_board(labels: list[str], side_to_move: int = chess.WHITE,
                flip: bool = False) -> chess.Board:
    """Turn 64 labels into a chess.Board.

    flip=False -> White at the bottom (normal). flip=True -> board is
    rotated 180 degrees (Black at the bottom).
    """
    if len(labels) != 64:
        raise ValueError(f"Expected 64 labels, got {len(labels)}")

    board = chess.Board(None)  # start from an empty board
    for index, label in enumerate(labels):
        if label == "empty":
            continue
        row, col = divmod(index, 8)
        if flip:
            file, rank = 7 - col, row
        else:
            file, rank = col, 7 - row
        square = chess.square(file, rank)
        colour = chess.WHITE if label[0] == "w" else chess.BLACK
        board.set_piece_at(square, chess.Piece(PIECE_TYPE[label[1]], colour))

    board.turn = side_to_move
    _validate_boards(board)
    return board


def _validate_boards(board: chess.Board) -> None:
    """Make sure the recognised position is at least plausible."""
    white_kings = len(board.pieces(chess.KING, chess.WHITE))
    black_kings = len(board.pieces(chess.KING, chess.BLACK))
    if white_kings != 1 or black_kings != 1:
        raise ValueError(
            "Recognised position looks wrong: "
            f"{white_kings} white king(s), {black_kings} black king(s). "
            "Check the image or the model."
        )


def recognize(
    image: np.ndarray,
    model,
    corners: np.ndarray | None = None,
    side_to_move: int = chess.WHITE,
    flip: bool = False,
    size: int = 512,
):
    """Full pipeline: image -> (chess.Board, list_of_64_labels)."""
    if corners is None:
        corners = detect_board(image)
        if corners is None:
            raise ValueError(
                "Could not find the board automatically. Pass corners="
                "[(x,y),(x,y),(x,y),(x,y)] for the 4 board corners."
            )
    warped = warp_board(image, corners, size=size)
    crops = split_squares(warped)
    labels = classify_squares(model, crops)
    board = build_board(labels, side_to_move=side_to_move, flip=flip)
    return board, labels


def pick_corners(image: np.ndarray, max_width: int = 960) -> np.ndarray:
    """Open a window and let the user click the 4 board corners.

    Click in this order: top-left, top-right, bottom-right, bottom-left.
    Press ENTER when all 4 are chosen (or ESC/close to cancel).
    Returns the 4 corners in the ORIGINAL image coordinates.
    """
    import pygame

    height, width = image.shape[:2]
    scale = min(1.0, max_width / width)
    shown = cv2.resize(image, (int(width * scale), int(height * scale)))
    rgb = cv2.cvtColor(shown, cv2.COLOR_BGR2RGB)

    pygame.init()
    screen = pygame.display.set_mode((rgb.shape[1], rgb.shape[0]))
    pygame.display.set_caption(
        "Click 4 corners: top-left, top-right, bottom-right, bottom-left (ENTER to accept)"
    )
    surface = pygame.image.frombuffer(
        rgb.tobytes(), (rgb.shape[1], rgb.shape[0]), "RGB"
    )

    points: list[tuple[int, int]] = []
    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and len(points) == 4:
                    running = False
                elif event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if len(points) < 4:
                    points.append(event.pos)

        screen.blit(surface, (0, 0))
        for point in points:
            pygame.draw.circle(screen, (255, 0, 0), point, 6)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    if len(points) != 4:
        raise ValueError(f"Expected 4 corners, got {len(points)}")
    corners = np.array(points, dtype=np.float32) / scale
    return order_corners(corners)


"""dataset.py - make synthetic "square" images to train the CNN.

Idea: we don't have thousands of labeled screenshots. Instead we *generate*
our own by pasting real piece images onto random board-coloured squares and
then applying random changes (brightness, blur, noise, scale, rotation...).
That teaches the network to recognise pieces across many board themes.

If you add more piece sets (folders) under assets/pieces/<name>/, the
generator will automatically use them too.
"""
from __future__ import annotations

from pathlib import Path

import chess
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from .classifier import CLASSES

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PIECES_DIR = PROJECT_ROOT / "assets" / "pieces"

# A few board colour themes (light square colour, dark square colour).
PALETTES = [
    ((238, 238, 210), (118, 150, 86)),   # lichess green
    ((240, 217, 181), (181, 136, 99)),   # brown
    ((222, 227, 230), (140, 162, 173)),  # blue-grey
    ((255, 255, 255), (200, 200, 200)),  # grey
    ((245, 222, 179), (160, 120, 80)),   # tan
    ((210, 240, 200), (90, 150, 90)),    # green 2
]


def load_piece_sets() -> dict[str, list[Image.Image]]:
    """Load every piece image from assets/pieces/<set>/<wK|bP|...>.png."""
    images: dict[str, list[Image.Image]] = {}
    for png in PIECES_DIR.glob("*/*.png"):
        symbol = png.stem  # e.g. "wK"
        images.setdefault(symbol, []).append(Image.open(png).convert("RGBA"))
    if not images:
        raise FileNotFoundError(
            "No piece images found in assets/pieces/*/.\n"
            "Run: python tools/download_pieces.py"
        )
    return images


def _jitter(color: tuple[int, int, int], rng, amount: int = 10):
    """Nudge each colour channel a little bit (adds variety)."""
    return tuple(
        int(np.clip(channel + rng.integers(-amount, amount + 1), 0, 255))
        for channel in color
    )


def make_square(rng, size: int, symbol: str, piece_images: dict) -> Image.Image:
    """Create one random square image.

    symbol == "empty" -> just a board-coloured square.
    otherwise        -> a piece pasted on a board-coloured square.
    """
    light, dark = PALETTES[int(rng.integers(len(PALETTES)))]
    base = _jitter(dark if rng.integers(2) else light, rng)
    image = Image.new("RGB", (size, size), base)

    if symbol != "empty":
        piece = piece_images[symbol][int(rng.integers(len(piece_images[symbol])))].copy()
        scale = float(rng.uniform(0.60, 0.85))
        piece_size = max(8, int(size * scale))
        piece = piece.resize((piece_size, piece_size), Image.LANCZOS)
        if rng.random() < 0.30:
            piece = piece.rotate(float(rng.uniform(-8, 8)), expand=True,
                                 resample=Image.BICUBIC)

        canvas = image.convert("RGBA")
        room_x = max(0, size - piece.width)
        room_y = max(0, size - piece.height)
        offset_x = int(rng.integers(0, room_x + 1))
        offset_y = int(rng.integers(0, room_y + 1))
        canvas.alpha_composite(piece, (offset_x, offset_y))
        image = canvas.convert("RGB")

    # --- random photo-like changes ---
    image = ImageEnhance.Brightness(image).enhance(float(rng.uniform(0.80, 1.20)))
    image = ImageEnhance.Contrast(image).enhance(float(rng.uniform(0.80, 1.20)))
    if rng.random() < 0.30:
        image = image.filter(ImageFilter.GaussianBlur(float(rng.uniform(0.0, 1.2))))

    if rng.random() < 0.30:  # add a little pixel noise
        array = np.asarray(image, dtype=np.int16)
        noise = rng.integers(-12, 13, array.shape, dtype=np.int16)
        image = Image.fromarray(np.clip(array + noise, 0, 255).astype(np.uint8))

    return image


def build_dataset(samples_per_class: int = 300, size: int = 48, seed: int = 0):
    """Build a balanced dataset of (images, labels).

    Returns:
        X: uint8 array of shape (N, size, size, 3)
        y: int64 array of shape (N,)  -- values are indices into CLASSES
    """
    rng = np.random.default_rng(seed)
    piece_images = load_piece_sets()

    images: list[np.ndarray] = []
    labels: list[int] = []
    for label, symbol in enumerate(CLASSES):
        for _ in range(samples_per_class):
            square = make_square(rng, size, symbol, piece_images)
            images.append(np.asarray(square, dtype=np.uint8))
            labels.append(label)

    X = np.stack(images)
    y = np.array(labels, dtype=np.int64)
    order = rng.permutation(len(X))
    return X[order], y[order]


def render_board_image(board: chess.Board, square: int = 48,
                       palette_index: int = 0) -> Image.Image:
    """Draw a whole board from a chess.Board (used for tests and previews).

    Uses the same orientation the recognizer expects: rank 8 at the top,
    rank 1 at the bottom (White at the bottom).
    """
    light, dark = PALETTES[palette_index]
    piece_images = load_piece_sets()
    size = square * 8
    image = Image.new("RGBA", (size, size), (0, 0, 0, 255))
    draw = ImageDraw.Draw(image)

    # 1) the squares
    for sq in chess.SQUARES:
        file = chess.square_file(sq)
        rank = chess.square_rank(sq)
        colour = dark if (file + rank) % 2 == 0 else light
        x0 = file * square
        y0 = (7 - rank) * square
        draw.rectangle([x0, y0, x0 + square - 1, y0 + square - 1], fill=colour + (255,))

    # 2) the pieces
    for sq, piece in board.piece_map().items():
        key = ("w" if piece.color == chess.WHITE else "b") + piece.symbol().upper()
        art = piece_images[key][0].convert("RGBA")
        target = max(8, int(square * 0.85))
        art = art.resize((target, target), Image.LANCZOS)
        file = chess.square_file(sq)
        rank = chess.square_rank(sq)
        x0 = file * square + (square - target) // 2
        y0 = (7 - rank) * square + (square - target) // 2
        image.alpha_composite(art, (x0, y0))

    return image.convert("RGB")


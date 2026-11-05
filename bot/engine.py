"""engine.py - Step 2: ask Stockfish for the best move.

Stockfish is a free chess engine: a separate .exe program that is extremely
good at chess. python-chess talks to it for us using the "UCI" protocol.

We simply say "here is a position" and it answers "play this move".
"""
from __future__ import annotations

from pathlib import Path

import chess
import chess.engine

# Stockfish was downloaded into the engine/stockfish/ folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STOCKFISH_DIR = PROJECT_ROOT / "engine" / "stockfish"


def find_stockfish() -> Path:
    """Look inside engine/stockfish/ for the Stockfish .exe file."""
    if STOCKFISH_DIR.exists():
        # rglob = search this folder and every sub-folder.
        for exe in STOCKFISH_DIR.rglob("*.exe"):
            return exe
    raise FileNotFoundError(
        "Could not find Stockfish.\n"
        f"  Looked in: {STOCKFISH_DIR}\n"
        "  Download the Windows build from "
        "https://stockfishchess.org/download/ and unzip it there."
    )


class Engine:
    """A friendly wrapper around a running Stockfish process.

    Use it with a `with` block so Stockfish is always shut down cleanly:

        with Engine() as engine:
            move = engine.best_move(fen, time_ms=800)
    """

    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path else find_stockfish()
        # popen_uci starts Stockfish as a background program and shakes hands.
        self._engine = chess.engine.SimpleEngine.popen_uci(str(self.path))

    def best_move(self, fen: str | None, time_ms: int = 800) -> str:
        """Return the best move for a position as a UCI string, e.g. 'e2e4'."""
        board = chess.Board(fen) if fen else chess.Board()
        # Limit(time=...) tells the engine how many SECONDS it may think.
        result = self._engine.play(board, chess.engine.Limit(time=time_ms / 1000.0))
        if result.move is None:
            raise RuntimeError("Stockfish did not return a move.")
        return result.move.uci()

    def close(self) -> None:
        """Shut Stockfish down cleanly."""
        self._engine.quit()

    def __enter__(self) -> "Engine":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

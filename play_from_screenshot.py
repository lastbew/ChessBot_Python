"""play_from_screenshot.py - Feature A: play a position read from an image.

It reads a chess board out of a screenshot, then lets Stockfish play the
position out, move by move, in the "Bot Vision" window.

Usage:
    python play_from_screenshot.py board.png
    python play_from_screenshot.py board.png --flip --turn black
    python play_from_screenshot.py board.png --no-gui
"""
from __future__ import annotations

import argparse
import time

import chess
import numpy as np

from bot.classifier import load_model
from bot.engine import Engine
from bot.recognizer import load_image, recognize
from bot.vision import focus_moves, threatened_squares

MODEL_PATH = "assets/model/piece_classifier.pt"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read a chess board from an image and play it out."
    )
    parser.add_argument("image", help="path to an image/screenshot of a board")
    parser.add_argument("--flip", action="store_true",
                        help="the board is rotated (Black at the bottom)")
    parser.add_argument("--turn", choices=["white", "black"], default="white",
                        help="whose move it is (default: white)")
    parser.add_argument("--time-ms", type=int, default=600,
                        help="thinking time per move in milliseconds")
    parser.add_argument("--delay", type=float, default=0.6,
                        help="seconds to pause between moves on screen")
    parser.add_argument("--moves", type=int, default=0,
                        help="stop after N moves (0 = play until the end)")
    parser.add_argument("--no-gui", action="store_true",
                        help="do not open a window (text only)")
    parser.add_argument("--pick", action="store_true",
                        help="click the 4 board corners with the mouse")
    parser.add_argument("--corners",
                        help="manual corners: x1,y1,x2,y2,x3,y3,x4,y4")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model = load_model(MODEL_PATH)
    image = load_image(args.image)

    side = chess.WHITE if args.turn == "white" else chess.BLACK

    # Work out the board corners: manual numbers > interactive pick > auto.
    corners = None
    if args.corners:
        values = [float(v) for v in args.corners.split(",")]
        if len(values) != 8:
            raise SystemExit(
                "--corners needs 8 numbers: x1,y1,x2,y2,x3,y3,x4,y4"
            )
        corners = np.array(values, dtype=np.float32).reshape(4, 2)
    elif args.pick:
        from bot.recognizer import pick_corners

        corners = pick_corners(image)

    try:
        board, _labels = recognize(
            image, model, corners=corners, side_to_move=side, flip=args.flip
        )
    except ValueError as error:
        raise SystemExit(
            f"Could not read the board: {error}\n"
            "Try again with --pick to click the 4 board corners, or pass "
            '--corners "x1,y1,x2,y2,x3,y3,x4,y4".'
        )

    print("Recognised position (FEN):")
    print("  ", board.fen())
    print(board)
    print(("White" if board.turn == chess.WHITE else "Black") + " to move.")

    view = None
    if not args.no_gui:
        try:
            from bot.gui import BoardView

            view = BoardView(flip=args.flip, title="Playing from screenshot")
        except Exception as error:  # no display / pygame missing
            print(f"(Vision window unavailable: {error})")

    try:
        with Engine() as engine:
            if view is not None:
                view.show(board, [], info="starting position")

            ply = 0
            while not board.is_game_over():
                if args.moves and ply >= args.moves:
                    print(f"Stopping after {args.moves} moves.")
                    break

                move = engine.best_move(board.fen(), args.time_ms)
                chosen = chess.Move.from_uci(move)
                san = board.san(chosen)

                if view is not None:
                    moves = focus_moves(board, chosen)
                    threats = threatened_squares(board, board.turn)
                    if not view.show(
                        board, moves, chosen_move=chosen,
                        info=f"plays {san} ({move})", threat_squares=threats,
                    ):
                        view = None  # window was closed

                print(f"move {ply + 1}: {san}")
                board.push(chosen)
                ply += 1
                time.sleep(args.delay)

            if board.is_game_over():
                result = board.result()
                print("Game over. Result:", result)
                if view is not None:
                    view.show(board, [], info=f"game over: {result}")
                    time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        if view is not None:
            view.close()


if __name__ == "__main__":
    main()

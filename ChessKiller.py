"""ChessKiller.py - the entry point. Run me with:

    python ChessKiller.py            # play a game that's already running
    python ChessKiller.py --watch    # open a lobby; auto-play any new game

It reads your settings from .env, connects to Lichess, and plays chess
using Stockfish. See README.md for how to create a token.
"""
from __future__ import annotations

import argparse

from bot.config import load_config
from bot.game_loop import run_bot


def main() -> None:
    """Load settings and run the bot."""
    parser = argparse.ArgumentParser(
        description="Play chess on Lichess with Stockfish."
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="open a lobby and auto-play any new game you start (loops forever)",
    )
    args = parser.parse_args()

    config = load_config()
    run_bot(config, watch=args.watch)


if __name__ == "__main__":
    main()


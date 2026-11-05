"""The "bot" package - all of our chess-bot code lives in this folder.

A package is just a folder with an __init__.py file inside. It lets us
import our own code with statements like:

    from bot.config import load_config

Each module (file) below has one clear job:
  * config.py       - read settings from .env
  * chess_utils.py  - turn Lichess move lists into a chess board
  * board_game.py   - Step 1 demo: play with a board in the terminal
  * engine.py       - Step 2: ask Stockfish for the best move
  * lichess.py      - Steps 3-4: login + listen to a game
  * game_loop.py    - Steps 5-6: the read -> think -> move loop
"""

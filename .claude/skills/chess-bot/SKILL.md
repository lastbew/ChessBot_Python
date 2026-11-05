---
name: chess-bot
description: Run, test, and maintain the ChessKiller Lichess chess bot in this repo (Python). Use for anything about playing on Lichess, Stockfish, the Bot Vision window, the --watch lobby, or the screenshot/CNN feature.
---

# ChessKiller chess bot

A Python bot that plays Lichess via the Board API with Stockfish, shows a
"Bot Vision" pygame window, and can read a board from a screenshot (CNN).

## Quick start
- Install deps: `python -m pip install -r req.txt`
- Configure token (writes `.env`, needs the `board:play` scope):
  `python setup_env.py`
- Play a game that's already running: `python ChessKiller.py`
- Lobby / auto-play any new game: `python ChessKiller.py --watch`

## Tests
- Full suite: `python -m pytest -q`  (expect ~38 passed)
- One file: `python -m pytest tests/test_vision.py -v`
- Helper: run `scripts/run_tests.ps1`

## Key files
- `bot/engine.py` — Stockfish UCI wrapper (`best_move`).
- `bot/lichess.py` — Board API: auth, game discovery, NDJSON stream, send move.
- `bot/game_loop.py` — read -> think -> move loop, `--watch` lobby, clock-aware time.
- `bot/gui.py` + `bot/vision.py` — the vision window and what it highlights.
- `bot/recognizer.py` + `bot/classifier.py` — screenshot -> FEN (CNN).
- `bot/watcher.py` — game-mode detection + waiting for a new game.

## Conventions / gotchas
- Use `python -m pip` (the bare `pip` launcher is broken on this machine).
- Never hardcode usernames or tokens. Identity comes from `client.get_account()`;
  secrets live in `.env` (gitignored).
- Computer opponents have no `"id"` (they look like `{"aiLevel": 4}`) — use
  `.get("id")` and the `_detect_my_color` helper; never index `["white"]["id"]`.
- Keep functions small and commented; run the tests before finishing.
- `DRY_RUN=1` prints moves without sending — use it for safe testing.

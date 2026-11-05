# ChessKiller — a Lichess chess bot (first-Python-project friendly)

A small Python chess bot that plays on [Lichess](https://lichess.org) using the
free **Stockfish** engine, shows a live **"Bot Vision"** window, and can even
**read a board from a screenshot** and play it out visually. The code is split
into small, heavily commented modules so it doubles as a learning project.

> ⚠️ **Play fair.** Use **unrated games** and, ideally, a **Lichess bot
> account**. Automating rated or human games can break Lichess's rules.

---

## What it does

- **Live Lichess bot** — logs in with a token, finds your game, and plays your
  moves with Stockfish via the official **Board API**.
- **Bot Vision window** — a pygame window showing what the bot sees:
  - the **piece being played** and **only that piece's** possible moves (dots),
  - the chosen move as an **arrow**,
  - **threats**: your pieces the opponent attacks (red rings),
  - the opponent's **move count** in the info strip.
- **Screenshot mode** — reads a chess position from an image (a small CNN
  classifies each square), then lets Stockfish play it out in the window.

## How it works (the whole idea)

1. Log in to Lichess with a personal token.
2. Listen to a game; Lichess streams the moves so far.
3. When it's our turn, rebuild the board and ask Stockfish for a move.
4. Send that move back to Lichess. Repeat.

---

## Requirements

- **Python 3.11+** (this project was built/tested on 3.11.9).
- Packages in `req.txt`: `python-chess`, `requests`, `python-dotenv`, `pytest`,
  `pygame`, `opencv-python`, `Pillow`, `numpy`, `torch`.
- **Stockfish** (a `.exe`) — download instructions below.
- A **Lichess personal access token** with the `board:play` scope.

---

## 1. One-time setup

### Install the Python packages
The plain `pip` command is broken on this machine, so use `python -m pip`:

```powershell
python -m pip install -r req.txt
```

### Get Stockfish
Stockfish picks the moves. It's already downloaded to `engine/stockfish/`.
If you need to redo it: grab the Windows build from
<https://stockfishchess.org/download/>, unzip it, and put the `.exe` anywhere
inside `engine/stockfish/`. The bot auto-finds it there.

### Get a Lichess token
1. Go to <https://lichess.org/account/oauth/token>.
2. Click **"+ New token"**.
3. Name it (e.g. `chessbot`) and enable the **`board:play`** scope.
4. Create it and copy the token (it starts with `lip_`).

### Put the token in `.env` (easiest: the setup script)
Run the friendly setup script and paste your token when prompted (input is
**hidden**):

```powershell
python setup_env.py
```

Or do it by hand:

```powershell
Copy-Item .env.example .env
# then open .env and paste your token after LICHESS_TOKEN=
```

> `.env` is in `.gitignore`. **Never** paste your token into code, chat, or a
> commit. If a token ever leaks, delete it on Lichess and create a new one.

---

## 2. Configuration (`.env`)

| Key | Meaning | Default |
|-----|---------|---------|
| `LICHESS_TOKEN` | Your `lip_...` token (scope `board:play`) | (required) |
| `CHALLENGE_USERNAME` | Opponent to challenge. Blank = resume an ongoing game | blank |
| `CLOCK_MINUTES` | Clock minutes when creating a challenge | `3` |
| `CLOCK_INCREMENT` | Clock increment (seconds) | `2` |
| `DRY_RUN` | `1` = print moves but do **not** send them; `0` = really play | `1` |
| `MOVE_TIME_MS` | How long Stockfish thinks per move (ms) | `800` |
| `SHOW_VISION` | `1` = show the pygame window; `0` = headless | `1` |

---

## 3. Usage

### Play a live game
```powershell
python ChessKiller.py
```

- If `CHALLENGE_USERNAME` is set, the bot **challenges** that player to an
  unrated game and waits for them to accept.
- If it's **blank**, the bot **resumes** any game you already have running
  (e.g. start a game on Lichess vs the computer first, then run the bot).
- The Bot Vision window opens (if `SHOW_VISION=1`).
- Press **Ctrl-C** to stop — the bot resigns so the game doesn't hang.

**First run in dry-run** (`DRY_RUN=1`): it prints `Stockfish plays: e2e4` but
does **not** send anything. Once it looks right, set `DRY_RUN=0` and rerun to
actually play.

Typical console output:
```
Logged in as YourName (id: yourname)
Playing game: https://lichess.org/abcd1234
We are playing as White.
Our turn. Stockfish plays: e2e4
...
Game finished (status: mate).
```

### Watch / lobby mode (auto-start)
Launch first, then start the game — the bot waits in a lobby and starts
automatically:
```powershell
python ChessKiller.py --watch
```
A window opens showing **"Waiting for a game…"**. Start or accept **any** game
on Lichess and the bot will:
- **detect** the new game,
- **read its mode** (speed, rated/unrated, variant, your color, opponent, clock),
- show it briefly, e.g. `Blitz | unrated | you are White | vs Stockfish level 4 | standard`,
- **auto-start playing**, and
- **return to the lobby** after the game ends (it loops).

Details:
- Only **standard** chess is auto-played; other variants are skipped with a message.
- Think time **adapts to the clock** (capped by `MOVE_TIME_MS`) so bullet/blitz
  games don't flag.
- Works headless too (`SHOW_VISION=0`): it prints the detection and plays.
- Stop with **Ctrl-C**.

> Without `--watch` the bot only plays a game that is *already* running (or that
> it challenges via `CHALLENGE_USERNAME`), then exits.

---

### The Bot Vision window (what it shows)
- **Your side:** only the **piece being played** has move dots, plus a gold
  tint on its square and an **arrow** for the chosen move.
- **Opponent:** a **red ring + wash** on any of your pieces they attack
  ("threats"); the info strip also shows their **move count**.
- Info line: `White to move | move 12` and e.g.
  `waiting for opponent (Black has 32 moves)`.

Turn it off with `SHOW_VISION=0` (useful on machines without a display).

### Play a position from a screenshot (Feature A)
One-time — download pieces and train the reader (CPU, a couple of minutes):
```powershell
python tools/download_pieces.py
python train_piece_classifier.py
```
Then:
```powershell
# easiest: click the 4 board corners with the mouse
python play_from_screenshot.py board.png --pick

# or give corners / orientation directly
python play_from_screenshot.py board.png --corners "60,60,571,60,571,571,60,571" --turn black
python play_from_screenshot.py board.png --flip     # board is rotated
python play_from_screenshot.py board.png --no-gui   # text only (prints the FEN)
```
Notes:
- **Manual corners (`--pick` / `--corners`) are the most reliable.** Auto-detect
  works when the board stands out from the background.
- A still image has no "whose turn" → set it with `--turn white|black`.
- Castling rights aren't inferred from a picture (fine for a self-play demo).

---

## 4. How to test it

### Automated tests
Run the whole suite:
```powershell
python -m pytest -q
```
Expected: **`24 passed`** (a deprecation warning from a dependency is harmless).

Run one file, or verbose:
```powershell
python -m pytest tests/test_vision.py -v
python -m pytest tests/test_engine.py -v
```

What the tests cover:
| Test file | Checks |
|-----------|--------|
| `tests/test_engine.py` | Stockfish returns a legal move; finds a mate-in-1 |
| `tests/test_turn_logic.py` | rebuilding a board from a move list; whose turn; promotions |
| `tests/test_lichess_stream.py` | parsing Lichess NDJSON (skips heartbeats; gameFull fields) |
| `tests/test_gui.py` | pygame window renders headless; arrow; square coords |
| `tests/test_classifier.py` | CNN forward-pass shape; image tensor; model load |
| `tests/test_recognizer.py` | corner order; 64-tile split; FEN build; end-to-end round-trip |
| `tests/test_vision.py` | focus-move selection; threat detection |

Some tests **skip gracefully** when their dependency isn't ready:
- engine tests skip if Stockfish isn't in `engine/stockfish/`,
- the recognizer round-trip skips if the CNN model isn't trained yet.

So a clean checkout still runs most tests without errors.

### Manual test checklist (do these once after setup)
1. **Engine works**
   ```powershell
   python -c "from bot.engine import Engine; e=Engine(); print(e.best_move(None,300)); e.close()"
   ```
   → prints a legal move like `e2e4`.
2. **Token works**
   ```powershell
   python -c "from bot.config import load_config; from bot.lichess import LichessClient; print(LichessClient(load_config().token).get_account()['username'])"
   ```
   → prints your Lichess username.
3. **Dry run** (`DRY_RUN=1`): start/keep a game running, run
   `python ChessKiller.py`. It logs in, finds the game, prints moves, sends
   nothing. The Bot Vision window opens.
4. **Live play** (`DRY_RUN=0`): rerun. Open the game on Lichess and watch the
   bot's move appear. Check the window shows the focus-piece dots + red threats.
5. **Screenshot mode**
   ```powershell
   python play_from_screenshot.py someboard.png --no-gui --corners "x1,y1,x2,y2,x3,y3,x4,y4"
   ```
   → prints the recognized FEN. With the GUI it plays moves out.
6. **Board demo** (no network, no engine): `python -m bot.board_game`

### Useful diagnostics
```powershell
python -m pytest -q            # full test suite
python -m bot.board_game       # step-1 board demo
python -c "import bot.gui, bot.recognizer, bot.classifier, bot.vision; print('imports OK')"
```

---

## 5. Troubleshooting

- **"No Lichess token found"** — create `.env` (run `python setup_env.py`).
- **"Login failed (HTTP 401)"** — token is wrong or missing the `board:play`
  scope; regenerate it.
- **"No game to play"** — set `CHALLENGE_USERNAME`, or start a game on Lichess
  and run the bot again.
- **"Could not find Stockfish"** — the `.exe` isn't under `engine/stockfish/`.
- **Bot doesn't move** — not your turn, the game hasn't started, or
  `DRY_RUN=1`.
- **No vision window** — `SHOW_VISION=0`, or no display available (the bot
  keeps playing headless; it prints a note).
- **Screenshot position looks wrong** — use `--pick` / `--corners`, and set the
  correct `--turn`; different board themes may need more training data.

---

## 6. Project layout

```
ChessKiller.py            entry point for live play
play_from_screenshot.py   entry point for the screenshot feature
setup_env.py              friendly .env writer (hidden token input)
train_piece_classifier.py trains the square-reading CNN
req.txt                   dependencies
.env.example              template for your settings (copy to .env)

bot/
  config.py        reads .env settings
  engine.py        Stockfish wrapper (best_move)
  lichess.py       Board API: auth, game discovery, stream, send move
  game_loop.py     the read -> think -> move loop (with vision + dry-run)
  chess_utils.py   build a board from Lichess move lists
  gui.py           pygame "Bot Vision" window (board, moves, threats, arrow)
  vision.py        what to highlight: focus_moves, threatened_squares
  recognizer.py    image -> board (detect/warp/split/classify -> FEN) + pick_corners
  classifier.py    the tiny CNN (13 classes) + helpers
  dataset.py       synthetic training squares + board renderer
  board_game.py    step-1 demo: play with a board in the terminal

tools/
  download_pieces.py   downloads the open-source "cburnett" piece PNGs

assets/
  pieces/…             piece images used for training
  model/piece_classifier.pt   trained CNN weights

tests/                 pytest test suite (24 tests)
engine/stockfish/      the Stockfish binary (auto-detected)
```

### Learning order (read the code in this order)
1. `bot/board_game.py` — using a chess library.
2. `bot/engine.py` — running another program (Stockfish) and getting answers.
3. `bot/lichess.py` — web requests, tokens, JSON, streaming.
4. `bot/game_loop.py` — read → think → move, plus errors and Ctrl-C.
5. `bot/gui.py` + `bot/vision.py` — drawing and what to highlight.
6. `bot/recognizer.py` + `bot/classifier.py` — images → board (the advanced part).

---

## Credits & safety

- **Stockfish** — <https://stockfishchess.org> (GPL).
- **cburnett chess pieces** — from Wikimedia Commons, used for training.
- **python-chess** and **pygame** do a lot of the heavy lifting.

**Keep your token secret**, prefer **unrated / bot** games, and **regenerate the
token** if it is ever exposed.





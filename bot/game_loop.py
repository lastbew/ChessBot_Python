"""game_loop.py - Steps 5 & 6: the heart of the bot.

The loop is simple:
  1. Listen to the game stream from Lichess.
  2. When it is our turn, ask Stockfish for a move.
  3. Send that move to Lichess (or just print it in dry-run mode).
  4. Repeat until the game ends.
"""
from __future__ import annotations

import chess

from .chess_utils import board_from_moves
from .config import Config
from .engine import Engine
from .lichess import LichessClient, LichessError
from .vision import focus_moves, threatened_squares
from .watcher import describe_mode, mode_summary, wait_for_new_game


def run_bot(config: Config, watch: bool = False) -> None:
    """Connect to Lichess and play. watch=True opens a lobby and auto-plays."""
    client = LichessClient(config.token)

    # Step 3: prove the token works and learn our own username/id.
    me = client.get_account()
    my_id = me["id"]
    username = me.get("username", my_id)
    print(f"Logged in as {username} (id: {my_id})")

    # One window is reused for both the lobby and the board.
    view = _make_view(config)

    try:
        with Engine() as engine:
            if watch:
                _run_watch(client, engine, config, my_id, username, view)
            else:
                _run_once(client, engine, config, my_id, view)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        if view is not None:
            view.close()


def _run_once(client, engine, config, my_id, view) -> None:
    """Original behaviour: play a game that is already running / challenged."""
    game_id = _find_game(client, config)
    if not game_id:
        print(
            "No game to play. Set CHALLENGE_USERNAME in .env, start a game on "
            "Lichess, or run with --watch."
        )
        return
    print(f"Playing game: https://lichess.org/{game_id}")
    if config.dry_run:
        print("DRY-RUN mode: the bot will print moves but NOT send them.")
    _play_game(client, engine, config, game_id, my_id, view)


def _find_game(client, config):
    """Challenge someone (and wait), or grab the first ongoing game."""
    if config.challenge_username:
        print(
            f"Challenging {config.challenge_username} "
            "(waiting for them to accept)..."
        )
        client.create_challenge(
            config.challenge_username, config.clock_minutes, config.clock_increment
        )
        return client.wait_for_game()
    games = client.get_ongoing_games()
    return games[0]["gameId"] if games else None


def _run_watch(client, engine, config, my_id, username, view) -> None:
    """Lobby mode: wait for a new game, detect its mode, play it, repeat."""
    seen: set[str] = set()

    def on_poll(active_count: int) -> None:
        nonlocal view
        if view is None:
            return
        lines = [
            f"Signed in as {username}",
            f"{active_count} game(s) in progress",
            "Start or accept a game on Lichess...",
        ]
        if not view.show_lobby("Waiting for a game...", lines):
            view = None

    while True:
        print("Waiting for a new game... (start one on Lichess)")
        game = wait_for_new_game(client, seen, on_poll=on_poll)
        if game is None:
            return

        mode = describe_mode(game)
        seen.add(mode.game_id)
        summary = mode_summary(mode)
        print("Detected:", summary)

        if view is not None:
            if not view.show_lobby("Game detected - starting!", [summary]):
                view = None

        if not mode.is_standard:
            print(f"Skipping variant '{mode.variant}' (only standard is supported).")
            continue

        print(f"Playing game: https://lichess.org/{mode.game_id}")
        if config.dry_run:
            print("DRY-RUN mode: the bot will print moves but NOT send them.")
        _play_game(client, engine, config, mode.game_id, my_id, view)
        print("Game over. Returning to the lobby.\n")


def _make_view(config):
    """Create the optional vision window, or None if it is off/unavailable."""
    if not config.show_vision:
        return None
    try:
        from .gui import BoardView

        return BoardView()
    except Exception as error:  # no display, missing pygame, etc.
        print(f"(Vision window unavailable: {error})")
        return None


def _detect_my_color(game_full: dict, my_id: str) -> chess.Color:
    """Work out our colour from a gameFull event, handling computer opponents.

    A computer player has no "id" (it looks like {"aiLevel": 4}), so we must
    use .get() and fall back sensibly instead of indexing ["id"].
    """
    white = game_full.get("white") or {}
    black = game_full.get("black") or {}

    if white.get("id") == my_id:
        return chess.WHITE
    if black.get("id") == my_id:
        return chess.BLACK

    # Our id wasn't found: trust whichever side actually has an id (the human).
    white_has_id = bool(white.get("id"))
    black_has_id = bool(black.get("id"))
    if white_has_id and not black_has_id:
        return chess.WHITE
    if black_has_id and not white_has_id:
        return chess.BLACK

    # Last resort: a side with an AI level is the opponent.
    if white.get("aiLevel") or white.get("ai"):
        return chess.BLACK
    return chess.WHITE


def _play_game(client, engine, config, game_id, my_id, view) -> None:
    """Follow the game stream and play our moves."""
    my_color: chess.Color | None = None
    initial_fen: str | None = None

    try:
        for event in client.stream_game(game_id):
            kind = event.get("type")

            if kind == "gameFull":
                # The first event: who are we, and what is the start position?
                my_color = _detect_my_color(event, my_id)
                initial_fen = event.get("initialFen")
                side = "White" if my_color == chess.WHITE else "Black"
                print(f"We are playing as {side}.")
                _maybe_move(
                    client, engine, config, event["state"], my_color,
                    initial_fen, game_id, view
                )

            elif kind == "gameState":
                _maybe_move(
                    client, engine, config, event, my_color, initial_fen,
                    game_id, view
                )

    except KeyboardInterrupt:
        # The user pressed Ctrl-C: leave the game politely, then stop.
        print("\nStopping... resigning the game.")
        try:
            client.resign(game_id)
        except Exception:
            pass
        raise


def _think_time(board: chess.Board, state: dict, config) -> int:
    """Pick how long to think (ms) from the clock, capped by MOVE_TIME_MS."""
    white = board.turn == chess.WHITE
    remaining = state.get("wtime") if white else state.get("btime")
    increment = state.get("winc") if white else state.get("binc")
    if remaining is None:
        return config.move_time_ms
    budget = remaining / 30.0 + (increment or 0) * 0.8
    budget = max(120.0, min(budget, float(config.move_time_ms)))
    budget = min(budget, max(120.0, remaining * 0.2))
    return int(budget)


def _maybe_move(
    client, engine, config, state: dict, my_color, initial_fen, game_id, view
) -> None:
    """Play a move only if the game is running AND it is our turn."""
    status = state.get("status", "started")
    if status not in ("created", "started"):
        print(f"Game finished (status: {status}).")
        return

    # Rebuild the current position from Lichess's list of moves so far.
    board = board_from_moves(initial_fen, state.get("moves"))

    if board.is_game_over():
        print("Game is over.")
        _render(view, board, None, "game over", my_color)
        return

    if my_color is None or board.turn != my_color:
        # Keep showing what the bot sees (the opponent's threats) while it waits.
        _render(view, board, None, "waiting for opponent", my_color)
        return

    # Step 5: ask Stockfish what to play.
    _render(view, board, None, "thinking...", my_color)
    fen = board.fen()
    think_ms = _think_time(board, state, config)
    move = engine.best_move(fen, think_ms)
    chosen = chess.Move.from_uci(move)
    print(f"Our turn. Stockfish plays: {move}")
    _render(view, board, chosen, f"plays {move}", my_color)

    if config.dry_run:
        print("  (dry-run: not sending the move)")
        return

    try:
        client.make_move(game_id, move)
    except LichessError as error:
        print(f"  Could not send move: {error}")


def _render(view, board, chosen, info: str, my_color) -> None:
    """Draw one frame: the played piece's moves + threats against us."""
    if view is None:
        return
    try:
        moves = focus_moves(board, chosen)
        threats = threatened_squares(board, my_color) if my_color is not None else []
        side = "White" if board.turn == chess.WHITE else "Black"
        full_info = f"{info}   ({side} has {board.legal_moves.count()} moves)"
        view.show(
            board, moves, chosen_move=chosen, info=full_info, threat_squares=threats
        )
    except Exception as error:
        print(f"(Vision window error: {error})")

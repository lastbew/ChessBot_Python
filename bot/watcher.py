"""watcher.py - "lobby" helpers: wait for a new game and read its mode.

Used by the --watch mode: the bot sits in a lobby until you start/accept a
game on Lichess, then it detects the game and plays it automatically.
"""
from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class GameMode:
    """A tidy summary of a Lichess game's settings."""

    game_id: str
    speed: str
    rated: bool
    variant: str
    color: str
    opponent: str
    is_computer: bool
    is_standard: bool


def _opponent(game: dict) -> tuple[str, bool]:
    """Return (display_name, is_computer) for the opponent."""
    opponent = game.get("opponent") or {}
    ai_level = opponent.get("ai")
    name = opponent.get("username") or opponent.get("id") or "opponent"
    if ai_level:
        return f"Stockfish level {ai_level}", True
    return name, False


def describe_mode(game: dict) -> GameMode:
    """Read the useful fields out of one /api/account/playing entry."""
    opponent_name, is_computer = _opponent(game)
    variant = (game.get("variant") or {}).get("key", "standard")
    return GameMode(
        game_id=game.get("gameId", ""),
        speed=game.get("speed", "?"),
        rated=bool(game.get("rated", False)),
        variant=variant,
        color=game.get("color", "?"),
        opponent=opponent_name,
        is_computer=is_computer,
        is_standard=(variant == "standard"),
    )


def mode_summary(mode: GameMode) -> str:
    """A short human-readable description for the window / console."""
    rated = "rated" if mode.rated else "unrated"
    return (
        f"{mode.speed.capitalize()}  |  {rated}  |  "
        f"you are {mode.color.capitalize()}  |  vs {mode.opponent}  |  {mode.variant}"
    )


def wait_for_new_game(
    client,
    seen: set[str],
    on_poll=None,
    poll_seconds: float = 2.0,
    max_polls: int | None = None,
) -> dict | None:
    """Block until a game id not in 'seen' appears; return its raw dict.

    - on_poll(count) is called each check so a window can show status.
    - max_polls lets tests stop instead of looping forever.
    """
    polls = 0
    while max_polls is None or polls < max_polls:
        games = client.get_ongoing_games()
        for game in games:
            if game.get("gameId") not in seen:
                return game
        if on_poll is not None:
            on_poll(len(games))
        polls += 1
        if max_polls is not None and polls >= max_polls:
            break
        time.sleep(poll_seconds)
    return None

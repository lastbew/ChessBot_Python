"""lichess.py - Steps 3 & 4: talk to the Lichess Board API.

Lichess has an official API for playing games with a program. You need a
personal access token with the "board:play" scope.

We use the 'requests' library to make web requests and to read the game's
live event stream (Lichess sends one JSON object per line = "NDJSON").
"""
from __future__ import annotations

import json
import time
from typing import Iterable, Iterator

import requests

BASE_URL = "https://lichess.org"


class LichessError(Exception):
    """Raised when Lichess returns an error we can't ignore."""


def iter_ndjson(lines: Iterable) -> Iterator[dict]:
    """Turn a stream of text lines into a stream of Python dictionaries.

    Lichess sends one JSON object per line. Blank lines are heartbeats
    (the server saying "still here") and should be skipped.
    """
    for raw in lines:
        # Streamed lines can arrive as bytes; decode them to text.
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")
        text = raw.strip()
        if not text:
            continue  # heartbeat / keep-alive
        yield json.loads(text)


class LichessClient:
    """A thin wrapper around the parts of the Lichess API that we need."""

    def __init__(self, token: str, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        # Every request now carries our secret token in its headers.
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            }
        )

    # -- Step 3: make sure the token works ------------------------------
    def get_account(self) -> dict:
        """Return our account info; raises LichessError if the token is bad."""
        resp = self.session.get(f"{self.base_url}/api/account", timeout=15)
        if resp.status_code != 200:
            raise LichessError(
                f"Login failed (HTTP {resp.status_code}). "
                "Check that your LICHESS_TOKEN has the 'board:play' scope."
            )
        return resp.json()

    # -- Finding a game to play -----------------------------------------
    def get_ongoing_games(self) -> list[dict]:
        """Return the list of games we are currently playing."""
        resp = self.session.get(
            f"{self.base_url}/api/account/playing", timeout=15
        )
        resp.raise_for_status()
        return resp.json().get("nowPlaying", [])

    def create_challenge(
        self, username: str, clock_minutes: int, clock_increment: int
    ) -> dict:
        """Challenge another player to an unrated game."""
        resp = self.session.post(
            f"{self.base_url}/api/challenge/{username}",
            data={
                "rated": "false",
                "clock.limit": str(clock_minutes * 60),  # Lichess uses seconds
                "clock.increment": str(clock_increment),
                "color": "random",
            },
            timeout=15,
        )
        if resp.status_code not in (200, 201):
            raise LichessError(
                f"Could not create challenge (HTTP {resp.status_code}): {resp.text}"
            )
        return resp.json()

    def wait_for_game(self, timeout_seconds: float = 120.0) -> str | None:
        """Wait until a game appears, then return its game id (or None)."""
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            games = self.get_ongoing_games()
            if games:
                return games[0]["gameId"]
            time.sleep(2)  # be polite: check every 2 seconds
        return None

    # -- Step 4: listen to a game ---------------------------------------
    def stream_game(self, game_id: str, timeout: float = 3600) -> Iterator[dict]:
        """Yield game events (gameFull, gameState, chatLine, ...).

        This stays open for the whole game. We yield each event one by one,
        so the caller can react as soon as something happens.
        """
        url = f"{self.base_url}/api/board/game/stream/{game_id}"
        with self.session.get(url, stream=True, timeout=timeout) as resp:
            resp.raise_for_status()
            for event in iter_ndjson(resp.iter_lines()):
                yield event

    # -- Step 5: send our move ------------------------------------------
    def make_move(self, game_id: str, uci_move: str) -> bool:
        """Send a move (like 'e2e4') to the game. Returns True if accepted."""
        resp = self.session.post(
            f"{self.base_url}/api/board/game/{game_id}/move/{uci_move}",
            timeout=15,
        )
        if resp.status_code != 200:
            raise LichessError(
                f"Move {uci_move} rejected (HTTP {resp.status_code}): {resp.text}"
            )
        return bool(resp.json().get("ok"))

    def resign(self, game_id: str) -> None:
        """Resign the game (a handy emergency exit)."""
        self.session.post(
            f"{self.base_url}/api/board/game/{game_id}/resign", timeout=15
        )

"""Tests for the lobby/watcher logic (game-mode detection + new-game polling)."""
from bot.watcher import (
    GameMode,
    describe_mode,
    mode_summary,
    wait_for_new_game,
)


def test_describe_mode_computer_unrated_blitz():
    game = {
        "gameId": "abc123",
        "speed": "blitz",
        "rated": False,
        "variant": {"key": "standard", "name": "Standard"},
        "color": "white",
        "opponent": {"id": "stockfish", "username": "Stockfish level 4", "ai": 4},
    }
    mode = describe_mode(game)
    assert mode.game_id == "abc123"
    assert mode.speed == "blitz"
    assert mode.rated is False
    assert mode.color == "white"
    assert mode.is_computer is True
    assert "Stockfish level 4" in mode.opponent
    assert mode.is_standard is True


def test_describe_mode_human_rated_rapid():
    game = {
        "gameId": "g2",
        "speed": "rapid",
        "rated": True,
        "variant": {"key": "standard"},
        "color": "black",
        "opponent": {"id": "bob", "username": "Bob"},
    }
    mode = describe_mode(game)
    assert mode.rated is True
    assert mode.is_computer is False
    assert mode.opponent == "Bob"
    assert mode.color == "black"


def test_describe_mode_chess960_is_not_standard():
    game = {
        "gameId": "g3",
        "speed": "blitz",
        "rated": False,
        "variant": {"key": "chess960"},
        "color": "white",
        "opponent": {"id": "x", "username": "X"},
    }
    mode = describe_mode(game)
    assert mode.is_standard is False
    assert mode.variant == "chess960"


def test_mode_summary_contains_key_bits():
    mode = GameMode(
        game_id="g",
        speed="blitz",
        rated=False,
        variant="standard",
        color="white",
        opponent="Stockfish level 4",
        is_computer=True,
        is_standard=True,
    )
    summary = mode_summary(mode)
    assert "Blitz" in summary or "blitz" in summary
    assert "unrated" in summary
    assert "White" in summary or "white" in summary


class _FakeClient:
    """Returns a scripted list of 'ongoing games' on each poll."""

    def __init__(self, snapshots):
        self.snapshots = snapshots
        self.calls = 0

    def get_ongoing_games(self):
        index = min(self.calls, len(self.snapshots) - 1)
        self.calls += 1
        return self.snapshots[index]


def test_wait_for_new_game_skips_already_seen():
    client = _FakeClient(
        [
            [{"gameId": "old"}],
            [{"gameId": "old"}, {"gameId": "new"}],
        ]
    )
    game = wait_for_new_game(client, seen={"old"}, poll_seconds=0.0)
    assert game is not None
    assert game["gameId"] == "new"


def test_wait_for_new_game_max_polls_returns_none():
    client = _FakeClient([[{"gameId": "old"}]])
    result = wait_for_new_game(client, seen={"old"}, poll_seconds=0.0, max_polls=2)
    assert result is None

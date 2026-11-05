"""Tests for parsing Lichess's NDJSON game stream (no network needed)."""
from bot.lichess import iter_ndjson


def test_parses_lines_and_skips_blank_heartbeats():
    lines = [
        b'{"type": "gameFull", "id": "abc123"}',
        b"",  # a heartbeat / keep-alive line
        '{"type": "gameState", "moves": "e2e4"}',
    ]
    events = list(iter_ndjson(lines))

    assert len(events) == 2  # blank line was skipped
    assert events[0]["type"] == "gameFull"
    assert events[1]["type"] == "gameState"
    assert events[1]["moves"] == "e2e4"


def test_game_full_has_players_and_state():
    sample = {
        "type": "gameFull",
        "id": "abc123",
        "white": {"id": "me", "name": "Me"},
        "black": {"id": "opponent", "name": "Opponent"},
        "initialFen": "startpos",
        "state": {"moves": "", "status": "started"},
    }
    events = list(iter_ndjson([__import__("json").dumps(sample)]))
    game = events[0]

    assert game["white"]["id"] == "me"
    assert game["black"]["id"] == "opponent"
    assert game["state"]["status"] == "started"

"""Tests for working out our colour from a gameFull event (human or computer)."""
import chess

from bot.game_loop import _detect_my_color

# Neutral, made-up ids - nothing here is tied to a real account.
ME = "alice"
OTHER = "bob"


def test_human_white_vs_computer_black():
    event = {"white": {"id": ME, "name": "Alice"}, "black": {"aiLevel": 4}}
    assert _detect_my_color(event, ME) == chess.WHITE


def test_human_black_vs_computer_white():
    event = {"white": {"aiLevel": 4}, "black": {"id": ME, "name": "Alice"}}
    assert _detect_my_color(event, ME) == chess.BLACK


def test_human_vs_human_white():
    event = {"white": {"id": ME}, "black": {"id": OTHER}}
    assert _detect_my_color(event, ME) == chess.WHITE


def test_human_vs_human_black():
    event = {"white": {"id": OTHER}, "black": {"id": ME}}
    assert _detect_my_color(event, ME) == chess.BLACK


def test_computer_side_without_id_does_not_crash():
    # This used to raise KeyError: black has no "id".
    event = {"white": {"id": ME}, "black": {"aiLevel": 6}}
    assert _detect_my_color(event, ME) == chess.WHITE


def test_any_account_id_works():
    # A completely different account id still works - nothing is hardcoded.
    event = {"white": {"id": "somebody_else"}, "black": {"id": "another_user"}}
    assert _detect_my_color(event, "another_user") == chess.BLACK


def test_empty_event_defaults_to_white():
    assert _detect_my_color({}, ME) == chess.WHITE


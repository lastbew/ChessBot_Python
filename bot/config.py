"""config.py - read the bot's settings from your .env file.

A .env file is just a plain text file full of "KEY=value" lines, e.g.:

    LICHESS_TOKEN=abc123

python-dotenv reads that file for us so we never have to paste the secret
token directly into the source code (which would be unsafe to share).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# The project root is one folder above this file (bot/config.py -> project/).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"


@dataclass
class Config:
    """Every setting the bot needs, grouped into one tidy box.

    A dataclass saves us from writing an __init__ by hand: Python builds
    the constructor for us from these field names and types.
    """

    token: str
    challenge_username: str
    clock_minutes: int
    clock_increment: int
    dry_run: bool
    move_time_ms: int
    show_vision: bool


def _as_int(value: str | None, default: int) -> int:
    """Turn text into a whole number; fall back to 'default' if it's blank."""
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _as_bool(value: str | None, default: bool) -> bool:
    """Turn text like '1', 'true', or 'yes' into True."""
    if value is None or str(value).strip() == "":
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def load_config(require_token: bool = True) -> Config:
    """Read .env (and real environment variables) into a Config object."""
    # load_dotenv fills in any values we haven't already set.
    load_dotenv(ENV_PATH)

    token = os.getenv("LICHESS_TOKEN", "").strip()

    if require_token and not token:
        # SystemExit is a clean way to stop the program with a message.
        raise SystemExit(
            "No Lichess token found.\n"
            f"  1. Copy:  {PROJECT_ROOT / '.env.example'}  ->  {ENV_PATH}\n"
            "  2. Paste a token (scope: board:play) from "
            "https://lichess.org/account/oauth/token\n"
            "  3. Run the bot again."
        )

    return Config(
        token=token,
        challenge_username=os.getenv("CHALLENGE_USERNAME", "").strip(),
        clock_minutes=_as_int(os.getenv("CLOCK_MINUTES"), 3),
        clock_increment=_as_int(os.getenv("CLOCK_INCREMENT"), 2),
        dry_run=_as_bool(os.getenv("DRY_RUN"), True),
        move_time_ms=_as_int(os.getenv("MOVE_TIME_MS"), 800),
        show_vision=_as_bool(os.getenv("SHOW_VISION"), True),
    )

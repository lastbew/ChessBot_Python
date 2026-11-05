"""setup_env.py - friendly one-time setup that writes your .env safely.

Run this in YOUR terminal (not the assistant):

    python setup_env.py

It asks for your Lichess token with HIDDEN input (so it never appears on
screen or in chat), then saves all settings to .env.
"""
from __future__ import annotations

import getpass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
ENV_PATH = PROJECT_ROOT / ".env"

KEY_ORDER = [
    "LICHESS_TOKEN",
    "CHALLENGE_USERNAME",
    "CLOCK_MINUTES",
    "CLOCK_INCREMENT",
    "DRY_RUN",
    "MOVE_TIME_MS",
    "SHOW_VISION",
]
DEFAULTS = {
    "CHALLENGE_USERNAME": "",
    "CLOCK_MINUTES": "3",
    "CLOCK_INCREMENT": "2",
    "DRY_RUN": "1",
    "MOVE_TIME_MS": "800",
    "SHOW_VISION": "1",
}


def read_existing() -> dict[str, str]:
    data: dict[str, str] = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                key, value = line.split("=", 1)
                data[key.strip()] = value.strip()
    return data


def main() -> None:
    settings = {**DEFAULTS, **read_existing()}

    token = settings.get("LICHESS_TOKEN", "").strip()
    if not token.startswith("lip_"):
        print("Paste your Lichess personal access token (input is hidden).")
        print("Create one with scope 'board:play' at:")
        print("  https://lichess.org/account/oauth/token")
        token = getpass.getpass("Token: ").strip()

    if not settings.get("CHALLENGE_USERNAME"):
        name = input(
            "Opponent username to challenge (blank = resume an ongoing game): "
        ).strip()
        settings["CHALLENGE_USERNAME"] = name

    settings["LICHESS_TOKEN"] = token

    lines = ["# Written by setup_env.py - KEEP THIS FILE SECRET!", ""]
    lines += [f"{key}={settings.get(key, '')}" for key in KEY_ORDER]
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"\nSaved to {ENV_PATH}")
    if token.startswith("lip_"):
        print("Token looks plausible (starts with 'lip_').")
    else:
        print("WARNING: token does not start with 'lip_' - double-check it.")


if __name__ == "__main__":
    main()

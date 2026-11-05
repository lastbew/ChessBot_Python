"""Make sure the project root is importable when running pytest.

This lets the tests do `from bot.engine import Engine` no matter which
folder you run pytest from.
"""
import os
import sys
from pathlib import Path

# Make pygame run "headless" during tests (no real window pops up).
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, str(Path(__file__).resolve().parent))

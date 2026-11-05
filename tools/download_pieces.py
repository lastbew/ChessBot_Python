"""download_pieces.py - fetch the open-source "cburnett" chess pieces as PNGs.

The cburnett piece set is a well-known free chess set (used by Wikipedia and
Lichess). We ask Wikimedia for PNG thumbnails of its SVG files, so we don't
need any SVG->PNG tools installed.

Run me with:

    python tools/download_pieces.py

Pieces are saved to:  assets/pieces/cburnett/<wK|wQ|...|bP>.png
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent.parent / "assets" / "pieces" / "cburnett"
API_URL = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "ChessKillerLearningBot/1.0 (educational project)"

# Our symbol -> Wikimedia Commons file name.
# "lt" = light (white), "dt" = dark (black).
FILES = {
    "wK": "Chess_klt45.svg", "wQ": "Chess_qlt45.svg", "wR": "Chess_rlt45.svg",
    "wB": "Chess_blt45.svg", "wN": "Chess_nlt45.svg", "wP": "Chess_plt45.svg",
    "bK": "Chess_kdt45.svg", "bQ": "Chess_qdt45.svg", "bR": "Chess_rdt45.svg",
    "bB": "Chess_bdt45.svg", "bN": "Chess_ndt45.svg", "bP": "Chess_pdt45.svg",
}


def _get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def thumbnail_url(title: str, width: int = 256) -> str:
    """Ask Wikimedia for a PNG thumbnail URL of an SVG file."""
    params = {
        "action": "query",
        "titles": f"File:{title}",
        "prop": "imageinfo",
        "iiprop": "url",
        "iiurlwidth": str(width),
        "format": "json",
    }
    data = json.loads(_get(f"{API_URL}?{urllib.parse.urlencode(params)}"))
    pages = data["query"]["pages"]
    page = next(iter(pages.values()))
    return page["imageinfo"][0]["thumburl"]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for symbol, title in FILES.items():
        dest = OUT_DIR / f"{symbol}.png"
        if dest.exists():
            print(f"skip {symbol} (already downloaded)")
            continue
        url = thumbnail_url(title)
        dest.write_bytes(_get(url))
        print(f"downloaded {symbol} -> {dest.relative_to(OUT_DIR.parents[2])}")


if __name__ == "__main__":
    main()

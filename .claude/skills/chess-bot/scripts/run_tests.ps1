# Run the ChessKiller test suite and a quick import check.
$ErrorActionPreference = "Stop"

Write-Host "== Import check =="
python -c "import bot.game_loop, bot.gui, bot.recognizer, bot.classifier, bot.vision, bot.watcher; print('imports OK')"

Write-Host "== Tests =="
python -m pytest -q

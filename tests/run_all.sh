#!/bin/sh
# Uruchamia wszystkie testy: test DSP w Node i scenariusze w przeglądarce (Playwright + Chrome).
# Testuje to, co jest w katalogu głównym (a nie src/), więc po zmianach w src/
# uruchom wcześniej python3 tools/build.py. Pojedynczy test: python3 tests/test_part_tempo.py
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)
PORT=${LOOPER_PORT:-8765}
export LOOPER_URL=${LOOPER_URL:-http://localhost:$PORT/}
export LOOPER_FIX=${LOOPER_FIX:-/tmp/looper-fixtures}
[ -f "$LOOPER_FIX/legacy-backup.looper" ] || python3 "$ROOT/tests/make_fixtures.py"
python3 "$ROOT/tools/build.py" --check || exit 1
echo "== test DSP"; (cd "$ROOT" && node tests/dsp_test.js) || exit 1
pkill -f "http.server $PORT" 2>/dev/null
(cd "$ROOT" && python3 -m http.server "$PORT" >/tmp/looper-http.log 2>&1 &)
sleep 1
for t in "$ROOT"/tests/test_*.py; do
  echo "== $(basename "$t")"
  timeout 400 python3 "$t" 2>&1 | tail -n 40
done
pkill -f "http.server $PORT" 2>/dev/null
echo "Sprawdź, czy każdy test kończy się pustym ERRS [] i czy wyniki zgadzają się z tests/README.md."

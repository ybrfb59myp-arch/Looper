"""Wspólne ustawienia testów przeglądarkowych (Playwright + Chrome).

LOOPER_URL     adres aplikacji (domyślnie http://localhost:8765/, zob. tests/run_all.sh)
LOOPER_FIX     katalog z plikami testowymi (python3 tests/make_fixtures.py)
LOOPER_OUT     katalog na zrzuty ekranu i pobrane pliki
LOOPER_CHROME  ścieżka do Chrome/Chromium
"""
import os
URL = os.environ.get('LOOPER_URL', 'http://localhost:8765/')
FIX = os.environ.get('LOOPER_FIX', '/tmp/looper-fixtures')
OUT = os.environ.get('LOOPER_OUT', '/tmp/looper-out')
CHROME = os.environ.get('LOOPER_CHROME', '/usr/bin/google-chrome')
os.makedirs(OUT, exist_ok=True)

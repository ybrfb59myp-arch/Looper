#!/usr/bin/env python3
"""Buduje aplikację z plików w src/ do katalogu głównego repozytorium (to, co serwuje GitHub Pages).

  src/looper.html  + src/dsp.js (w miejsce /*DSP*/) + src/mp4audio.js (w miejsce /*MP4*/)  ->  index.html
  src/sw.js (__VERSION__ -> znacznik czasu)                                                ->  sw.js

Nowy znacznik w sw.js sprawia, że zainstalowana aplikacja zauważa aktualizację i pokazuje „Odśwież”.
rec-worklet.js, mp3-worker.js, lame.min.js, manifest i ikony leżą tylko w katalogu głównym i edytuje się je bezpośrednio.

Użycie:  python3 tools/build.py            (wersja = bieżąca data i godzina)
         python3 tools/build.py --check    (sprawdza tylko, czy index.html jest zbudowany z aktualnych źródeł)
"""
import os, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')

def read(name):
    with open(os.path.join(SRC, name), encoding='utf-8') as f:
        return f.read()

def build_index():
    s = read('looper.html')
    for mark in ('/*DSP*/', '/*MP4*/'):
        if s.count(mark) != 1:
            sys.exit('błąd: w src/looper.html musi być dokładnie jedno ' + mark)
    return s.replace('/*DSP*/', read('dsp.js')).replace('/*MP4*/', read('mp4audio.js'))

def main():
    index = build_index()
    out = os.path.join(ROOT, 'index.html')
    if '--check' in sys.argv:
        with open(out, encoding='utf-8') as f:
            same = f.read() == index
        print('index.html aktualny' if same else 'index.html NIEAKTUALNY: uruchom python3 tools/build.py')
        sys.exit(0 if same else 1)
    with open(out, 'w', encoding='utf-8') as f:
        f.write(index)
    ver = time.strftime('%Y%m%d-%H%M%S')
    sw = read('sw.js')
    if '__VERSION__' not in sw:
        sys.exit('błąd: w src/sw.js brakuje __VERSION__')
    with open(os.path.join(ROOT, 'sw.js'), 'w', encoding='utf-8') as f:
        f.write(sw.replace('__VERSION__', ver))
    print('zbudowano wersję', ver)

if __name__ == '__main__':
    main()

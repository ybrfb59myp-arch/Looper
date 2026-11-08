# Testy Loopera

Uruchomienie wszystkiego (ok. 15 minut): `sh tests/run_all.sh` z katalogu głównego repozytorium.
Wymaga: Python 3 z Playwright, Chrome (`LOOPER_CHROME`, domyślnie `/usr/bin/google-chrome`), Node, ffmpeg.
Pliki testowe tworzy `python3 tests/make_fixtures.py` (robi to też `run_all.sh`).

Pojedynczy test: w katalogu głównym `python3 -m http.server 8765 &`, potem np. `python3 tests/test_part_tempo.py`.

Scenariusze nie mają twardych asercji: wypisują wyniki, a na końcu `ERRS [...]` (błędy strony i konsoli),
które **musi być puste**. Poniżej, co powinno wyjść (nazwy sesji i godziny będą inne).

| Test | Co sprawdza | Oczekiwane wyniki |
|---|---|---|
| `dsp_test.js` | zmiana tempa i tonacji (WSOLA + resampling) na sinusach | `f=` zgodne z `exp` co do ok. 0,5 Hz, `rms` stabilne (≈0,35); 3 min przeliczenia poniżej ~1 s |
| `test_recording.py` | nagrywanie (sztuczny mikrofon Chrome), pętla, nagrywanie w pętli, czyszczenie/usuwanie śladu, eksport MP3 i WAV, praca offline, migracja z pierwszej wersji | `after loop rec: … recording? True`, `confirm label: Zastąpić?`, `mp3: … b'\xff\xfb…'`, `offline: … badge True`, `migrated: ['Stare nagranie', 'Stary ślad 2'] \| tempo −10% \| semi +2 półtony \| A 0:00,50` |
| `test_video_sessions.py` | dźwięk z filmów MP4/MOV, film bez dźwięku, kłódka, przesuwanie śladu i nauka poprawki, sesje (nazwa, nowa, kopia, plik, import), migracja v2 | `silent t3: … Ten film nie ma ścieżki dźwiękowej.`, `locked -> loop unchanged`, `imported: … (kopia)`, `migrated v2: Moja sesja … tempo −15% \| t2 off +0,200 s` |
| `test_mixer.py` | mikser na iPadzie i iPhonie: suwak, mute, solo, eksport, zapamiętanie po przeładowaniu | `mute t1: true`, `solo t2 -> t1 off: True`, `after reload solo t2: true` |
| `test_mixer_transport.py` | wyrównanie poziomów (głośny i cichy plik), transport ⏮ −10 −5 +5 +10 w pętli i bez, migracja starych suwaków | oba eksporty ok. `-17.7` dB, `+10 in loop` zostaje w pętli, `after migration faders: ['0 dB', '0 dB']` |
| `test_levels.py` | poziomy eksportu pojedynczo i razem | `loud only: -17.7`, `quiet only: -17.7`, `both: -14.7` |
| `test_faders_collapse.py` | 6 śladów, dymek suwaka, zwijanie karty śladów, czerwone kropki, nagrywanie z kropki z potwierdzeniem | `bubble visible during drag: ~0.9`, `collapsed: True \| dots: 6`, `dot armed: 1`, `after reload collapsed: True` |
| `test_parts_sequence.py` | części A/B/C, koło wyboru, sekwencja, eksport sekwencji, plik sesji z częściami, migracja v3 | `sequence: ['A×2', 'B×3', 'C×1', '+']`, `seq mp3 … duration 11.02`, `imported B tracks: ['screen']`, `migrated v3: Stara v3 ['Nagranie v3'] … A 0:00,50` |
| `test_sequence_timeline.py` | czy widok podąża za grającą częścią (A×1, B×1 w kółko) | `timeline:` naprzemiennie bloki `A` i `B` |
| `test_resume_copy_backup.py` | strażnik „zamrożonego” dźwięku i powrót z tła, kopiowanie części, zwijana karta tempa, kopia zapasowa | `watchdog: contexts 1 -> 2` i ruszająca pozycja, `after return: contexts 2 -> 3`, `confirm label: Zastąpić B?`, `backup magic: b'LOOPERB1'`, `Przywrócono 2 sesje` |
| `test_part_tempo.py` | osobne tempo i tonacja w częściach, sekwencja z różnymi tempami, eksport, zapamiętanie, kopiowanie | `B (new): B \| 0 \| 0 \| bez zmian`, `seq mp3 … duration ≈ expected`, `copied to C: C \| C \| -19 …` |
| `test_layout.py` | menu ☰, chowanie miksera, karta Pętla ze strzałkami, karta części w jednym rzędzie, przewijanie przy zablokowanej pętli (iPhone i iPad) | `parts top row height: 46`, `nudges: ['← 0,1 s', '← 0,01', '0,01 →', '0,1 s →']`, `mixer hidden: True`, `locked canvas touch-action: pan-y`, `tap on locked loop says: Pętla jest zablokowana`, `lock folds loop card: True`, `unlock opens loop card: True` |
| `test_seam.py` | lupa przejścia na iPhonie i iPadzie: wyłączona bez pętli, wartości suwaka, pozycje i **prawdziwy dźwięk** (nagranie wyjścia, sygnał-glissando) tylko w oknach B−h…B i A…A+h, te same punkty pętli co bez lupy | `seam enabled: True`, `small drag +10px: 0,25 s \| +400px: 5,00 s \| -1000px: wyłączona`, `positions in windows: 70/70`, `locked: card folded True \| seam wyłączona`, `unlocked: card open True`, `audio: … in seam windows N/N, … silent windows mid-play 0` |
| `test_backup_reminders.py` | pasek kopii po wyjściu z sesji, kopia sesji (plik `LOOPERS1`), „Nie teraz”, samo słuchanie to nie zmiana, pełna kopia po 7 dniach (dwa kroki, `LOOPERB1`), „Później”, data w Ustawieniach, stare sesje, otwarcie kopii | `nie ma jeszcze kopii`, `session copy: Ćwiczenie.looper b'LOOPERS1'`, `reload after just listening: None`, `full: second step label: Udostępnij kopię (…)`, `settings: Ostatnia: … (dziś).`, `opened copy: Ćwiczenie (z pliku) \| tracks ['test']` |
| `test_seq_pause.py` | sekwencja A×1 B×1 na pauzie: pauza zostawia miejsce, przeskoki zmieniają część, czas i klocek | `paused : part A \| now` ≈ czas z `playing`, `+5` przechodzi do B, przekroczenie końca wraca do A, `-10` od początku zostaje na A |
| `test_legacy_backup.py` | kopia zapasowa ze starej wersji (jedno tempo −12% dla sesji) | A, B i C mają `-12` |

Zachowań typowych dla iOS (usypianie dźwięku po schowaniu aplikacji, wybór mikrofonu, udostępnianie plików)
Chrome nie odtworzy: te rzeczy właściciel sprawdza na iPhonie/iPadzie.

# Looper: notatki projektu dla Claude

Przeczytaj to w całości przed jakąkolwiek pracą nad Looperem. Te notatki zastępują historię
rozmów: aktualizuj je przy każdej zmianie (razem z `CHANGELOG.md`), tak żeby kolejna rozmowa
albo sesja w zakładce Code mogła podjąć pracę bez utraty kontekstu.

## Czym jest Looper

Aplikacja PWA (jedna strona HTML, działa offline) do ćwiczenia na instrumencie z nagraniami
z Dyktafonu na iPhonie i iPadzie. Właściciel to muzyk (saksofon), nie programista.
Najważniejsze funkcje: pętla A–B, tempo −50…+50% bez zmiany wysokości, transpozycja −7…+7 półtonów,
dowolna liczba śladów z nagrywaniem do każdego z nich, mikser (dB, mute, solo), części A/B/C
z sekwencją (np. A×4, B×2), sesje, eksport MP3, kopia zapasowa.

- Adres: https://ybrfb59myp-arch.github.io/Looper/ (zainstalowana na ekranie początkowym iPhone'a i iPada)
- Repozytorium: `ybrfb59myp-arch/Looper`, gałąź `main`, publikowana przez GitHub Pages

## Zasady współpracy z właścicielem (ważne)

- **Odpowiadaj po polsku**, prostym językiem, bez żargonu. Właściciel używa telefonu, często dyktuje głosem.
- **Nic nie zmieniaj, dopóki nie powie „działamy”** (albo równoznacznie: „możesz działać”, „zaczynaj”).
  Gdy opisuje pomysły, najpierw zaproponuj plan i dopytaj o niejasności. Pytania typu „czy da się…?”
  to pytania, nie polecenie zmiany.
- **Nie zakładaj niczego z wcześniejszych rozmów**: rób to, o co prosi teraz.
- Po wdrożeniu powiedz krótko, co się zmieniło, i przypomnij: stuknij **Odśwież** (pasek aktualizacji)
  albo zamknij i otwórz aplikację.
- Lubi obecną kolorystykę (ciemny motyw, żółty akcent z ikony). Nie zmieniaj wyglądu bez prośby.
- Napisy w aplikacji: po polsku, krótko, bez „Ustaw A/B”-podobnych niejasności (patrz decyzje niżej).
- Repozytorium jest publiczne: żadnych danych osobowych w kodzie, notatkach i commitach.

## Publikacja

1. Zmieniaj pliki w `src/` (albo bezpośrednio pliki, które leżą tylko w katalogu głównym, patrz niżej).
2. `python3 tools/build.py`, który składa `index.html` i nadaje nowy numer wersji w `sw.js`.
   **Bez nowej wersji `sw.js` zainstalowane aplikacje nie zauważą aktualizacji.**
3. Testy (patrz niżej), potem commit i `git push origin HEAD:main`.
4. Wdrożenie trwa ok. 30–60 s. Sprawdzenie:
   `gh api "repos/ybrfb59myp-arch/Looper/actions/runs?per_page=1" --jq '.workflow_runs[0] | "\(.head_sha[0:7]) \(.status) \(.conclusion)"'`
5. Aplikacja na urządzeniu sprawdza aktualizację przy starcie i przy każdym powrocie do niej.
   Gdy nowy service worker przejmie stronę, pojawia się pasek z przyciskiem **Odśwież**.

Uwagi: Pages ustawił właściciel ręcznie (deploy from branch `main`, katalog główny). `.nojekyll` wyłącza
Jekyll, więc pliki są serwowane bez przetwarzania. Z sesji Claude API ustawień Pages bywa niedostępne;
w razie potrzeby poproś właściciela o kliknięcie w Settings → Pages.

## Struktura repozytorium

| Ścieżka | Co to jest |
|---|---|
| `src/looper.html` | Cała aplikacja: HTML, CSS i JS (jeden plik, ok. 3500 linii). Zawiera znaczniki `/*DSP*/` i `/*MP4*/`. |
| `src/dsp.js` | Zmiana tempa i tonacji: `resampleLen`, `resampleGen`, `alignCopy`, `wsolaGen`. Wklejane w miejsce `/*DSP*/`. |
| `src/mp4audio.js` | `mp4AacToAdts`: wyciąga dźwięk AAC z filmów MP4/MOV. Wklejane w miejsce `/*MP4*/`. |
| `src/sw.js` | Szablon service workera z `__VERSION__`. |
| `tools/build.py` | Buduje `index.html` i `sw.js` w katalogu głównym. `--check` sprawdza, czy `index.html` jest aktualny. |
| `index.html`, `sw.js` | **Wygenerowane**: nie edytuj ręcznie, zmieniaj `src/` i buduj. |
| `rec-worklet.js` | AudioWorklet nagrywania (edytowany bezpośrednio). |
| `mp3-worker.js`, `lame.min.js` | Kodowanie MP3 w Web Workerze (lamejs, LGPL, `lame.LICENSE.txt`). |
| `manifest.webmanifest`, ikony PNG | PWA. Ikonę dostarczył właściciel (zrobiona w Gemini), PNG są z niej wycięte. |
| `tests/` | Testy, patrz niżej i `tests/README.md`. |
| `CHANGELOG.md` | Dziennik zmian. |

## Testy

- `python3 tests/make_fixtures.py`: tworzy pliki testowe (WAV, filmy przez ffmpeg, stara kopia zapasowa) w `/tmp/looper-fixtures`.
- `sh tests/run_all.sh`: test DSP w Node i wszystkie scenariusze w przeglądarce (Playwright + Chrome, serwer na porcie 8765).
  Pełny przebieg trwa kilkanaście minut; pojedynczy scenariusz: `python3 tests/test_part_tempo.py`
  (przy działającym `python3 -m http.server 8765` w katalogu głównym).
- Scenariusze wypisują wyniki i na końcu `ERRS [...]`: lista musi być pusta. Oczekiwane wyniki są w `tests/README.md`.
- Chrome uruchamiany z `--no-sandbox --autoplay-policy=no-user-gesture-required`; do nagrywania także
  `--use-fake-ui-for-media-stream --use-fake-device-for-media-stream`.
- Po zmianach w UI zrób zrzut ekranu w rozmiarze iPhone'a (390×844) i iPada (820×1180) i obejrzyj go.
- Zachowań typowych dla iOS (usypianie dźwięku w tle, sesja audio, udostępnianie plików) nie da się w pełni
  sprawdzić w Chrome: powiedz właścicielowi, co ma przetestować na urządzeniu.

## Architektura (src/looper.html)

Cały JS jest w jednym IIFE (zmienne nie są dostępne z konsoli/testów). Sekcje w kodzie oznaczone
komentarzami `/* ---------- nazwa ---------- */`.

### Dźwięk
- Jeden `AudioContext` (`getCtx()`), wyjście przez wspólny limiter `master` (DynamicsCompressor: threshold −2,
  knee 2, ratio 20, attack 2 ms, release 120 ms); ten sam limiter w eksporcie (`setupLimiter`).
- Odtwarzanie części: dla każdego śladu `AudioBufferSourceNode` z gotowego renderu (`R.bufs[id]`), pętla przez
  `loop/loopStart/loopEnd`, punkty przyciągane do przejść przez zero (`snapIn`).
- `navigator.audioSession.type`: `'playback'`, a na czas nagrywania `'play-and-record'` (`setSession`).
- Wake lock podczas grania (`keepAwake`).
- **Lupa przejścia** (`seamLen` 0…5 s czasu słuchania, 0 = wył.; `curSeam`): gdy jest włączona pętla w trybie Część,
  `startAt` zamiast jednego źródła na ślad planuje powtórzenia (`seamSchedule`, setInterval 60 ms, horyzont 0,8 s).
  Każde powtórzenie to źródło z tym samym `loop/loopStart/loopEnd` co zwykła pętla, startujące w B−h i grające 2h
  (h = seamLen/2), więc samo przejście B→A jest **identyczne** z prawdziwą pętlą. Tylko skok z A+h z powrotem do
  B−h ma krzyżowe przenikanie 8 ms (`SEAM_X`), bez ciszy. Pętla krótsza niż lupa: gra cała. `pos()` liczy pozycję
  w oknach lupy. Wartość nie jest zapamiętywana: zeruje się w `applyPart` (zmiana części, otwarcie sesji),
  po „Usuń pętlę” i w trybie Sekwencja.
- **Powrót z tła (iOS):** po schowaniu aplikacji odtwarzanie i nagrywanie są zatrzymywane, a stan zapisany.
  Po powrocie (ukrycie > 400 ms) `ctxStale = true`; pierwsze dotknięcie (`wakeAudio`) tworzy nowy kontekst
  (`freshCtx`). Dodatkowo strażnik `watchClock`: jeśli po starcie zegar kontekstu stoi 800 ms, odtwarzanie
  startuje jeszcze raz na nowym kontekście, a gdy to nie pomoże, pojawia się prośba o ponowne ▶.

### Tempo i tonacja (render)
- `renderList(list, alive, label, tp, sm)` przelicza wszystkie ślady części naraz: najpierw zmiana wysokości
  przez resampling o P = 2^(semi/12) (Catmull-Rom), potem WSOLA ze współczynnikiem S = P/T, wspólne
  wyszukiwanie na miksie wszystkich śladów (zgrubnie co 16 próbek, potem dokładnie ±16), okno Hanna,
  N ≈ 40 ms, Δ = 12 ms. Działa w kawałkach z `await nextTick()`, z paskiem postępu.
- Czas w aplikacji (A, B, przesunięcia, pozycja) jest zawsze w **czasie oryginału**; render ma długość D/T.
- **Każda część ma własne `tempoPct` i `semi`** (od 2026-11-08). Globalne `tempoPct/semi` to lustro otwartej
  części (jak `slots`, `R`). Render części k: `ensureRendered(k)` porównuje `R.T/R.P` z `partT(k)/partP(k)`.
- Zmiana suwaka unieważnia render tylko otwartej części (`scheduleRender`).

### Części A/B/C i sekwencja
- `parts[k] = { slots, R, renderDirty, A, B, loopOn, locked, paused, tune, lastRec, tempoPct, semi }`.
  Zmienne globalne (`slots`, `R`, `A`, `B`, …) odzwierciedlają otwartą część: `stashPart()` zapisuje je do
  `parts[curPart]`, `applyPart(k)` wczytuje. Id śladów są unikalne w całej sesji (`nextId`).
- Sekwencja `sequence = [{p:'A', n:4}, …]` (n = 1…32), tryb `playMode` `'part'` albo `'seq'`.
- Silnik sekwencji: planowanie z wyprzedzeniem (setInterval 60 ms, horyzont 0,8 s), jedno źródło na każde
  powtórzenie z obwiednią 2 ms na brzegach, bez przerw. Fragment części = jej pętla A–B (jeśli włączona)
  albo całość. Widok przełącza się na grającą część (`seqFollow`), suwaki tempa pokazują jej ustawienia.
  Zmiana renderu w trakcie: `restartSeqKeepingPlace()` zachowuje miejsce w utworze.
- Kopiowanie części (`copyPart`): ślady (nowe id, te same dane), pętla, mikser, tempo i tonacja.
  Gdy cel ma nagrania, drugie stuknięcie „Zastąpić B?” (4 s).
- Wybór liczby powtórzeń: koło w stylu zegara iOS (`wheelPart`, `wheelCount`, `ITEM_H = 40`).
- **Sekwencja na pauzie:** `pauseSeq` przełącza widok na część, która grała, i ustawia jej `paused` na miejsce
  zatrzymania (`showSeqPlace`). Przeskoki −10/−5/+5/+10 na pauzie liczą miejsce przez `seqLocate(g)` (z pętli i temp,
  bez renderu; powyżej końca sekwencji zawija, poniżej zera staje na początku) i pokazują część, kreskę, czas
  i podświetlony klocek z licznikiem.

### Nagrywanie
- `rec-worklet.js` wysyła paczki po 4096 próbek z numerem ramki; nagranie jest układane na osi czasu
  według ramek, z kompensacją opóźnienia `latencyEstimate()` (outputLatency + latency wejścia) i
  **zapamiętanej poprawki** `learnMs` (localStorage `looper.learnMs`).
- Poprawka uczy się sama: gdy właściciel przesunie strzałkami świeże nagranie (`lastRec`) o ≤ 0,3 s
  (`LEARN_LIMIT`), ta korekta trafia do `learnMs`. W Ustawieniach można ją wyzerować.
- Rozbieg przed nagraniem 0/1/2/4 s (`looper.preroll`). Przy aktywnej pętli nagrywanie rusza przed A
  i kończy się samo po B.
- Nagranie przy zmienionym tempie/tonacji jest przeliczane z powrotem do oryginału (`convertTake`).
- Mikrofon bez echoCancellation/noiseSuppression/autoGainControl. Zalecane słuchawki przewodowe.

### Poziomy i mikser
- Każdy nowy ślad dostaje `trim` z `autoTrim()`: średnia moc (z bramką) sprowadzona do −18 dBFS,
  korekta w granicach −24…+30 dB, szczyt ≤ 2.
- Suwaki w dB: pozycja 0,75 = 0 dB, zakres −48…+12 dB (`posToVol`, `volToPos`, `dbLabel`), dwuklik = 0 dB,
  cały pasek jest uchwytem, zakres ruchu min. 180 px, dymek z wartością. M/S jak w mikserze.
- Przebieg rysowany w rzeczywistej skali (po `trim` i suwaku), żeby różnice głośności były widoczne.
- **Rysowanie (bateria):** `#wave` (ślady, pętla, flagi A/B) jest przerysowywany tylko wtedy, gdy zmieni się jego
  podpis (`layerSig`: rozmiar, widok, A/B, `peaksGen` z `buildPeaks`, mikser, kolory motywu w `themeColors`).
  Kreska pozycji jest na osobnym przezroczystym `#playline` nad przebiegiem (`pointer-events:none`), czyszczonym
  tylko w pasku poprzedniej kreski. Obraz jest identyczny jak dawniej (sprawdzone porównaniem pikseli).

### Dane i pliki
- IndexedDB `petla-ab`, magazyn `kv` (`DB.get/put/del`). Klucze:
  - `sessions` → `{ current, nextSid, list: [{ sid, name, created, updated, tracks }] }`
  - `s<sid>-state` → stan sesji (poniżej)
  - `s<sid>-data-<id>` → nagranie śladu: `{ kind:'file', name, data }` (oryginalny plik) albo
    `{ kind:'pcm', sr, name, data: Int16 }` (nagranie z mikrofonu)
- Stan sesji v4: `{ v:4, nextId, tempoPct, semi, curPart, playMode, sequence, parts: { A|B|C: { A, B, loopOn,
  locked, tempoPct, semi, slots: [{ id, name, vol, trim, offset, has, mute, solo }] } } }`.
  Górne `tempoPct/semi` = otwarta część (zgodność wstecz). **Migracje** (`loadSession`): v1 (`track0/track1/state`),
  v2 (`state2`), v3 (jedna część) i v4 bez tempa w częściach, gdzie każda część dziedziczy wspólne tempo.
- Ustawienia w localStorage: `looper.learnMs`, `looper.preroll`, `looper.fxCollapsed`, `looper.tracksCollapsed`,
  `looper.seqCollapsed`, `looper.loopCollapsed`, `looper.mixHidden`.
- **Przypomnienia o kopiach** (dane w indeksie `sessions`): każda sesja na liście ma `edited` (czas ostatniej prawdziwej
  zmiany: `noteEdits` porównuje skrót `contentSig` stanu, czyli pętle, mikser, tempo, ślady i sekwencję; samo słuchanie,
  zmiana części czy kłódka się nie liczą; `saveSlotData` też ustawia `edited`), `sig`, `copied` (czas kopii, która ją
  obejmuje) i `snoozed` (`edited` w chwili „Nie teraz”). Sesja bez `edited` (sprzed tej wersji) ma zmiany od `updated`.
  `sessions.backup = { lastFull, since, snoozeUntil }`. Pasek `#bkBar` (`offerBackup`): po wyjściu z sesji
  (`switchSession`, `newSession`) i przy starcie dla otwartej sesji, jeśli `needsCopy`; plik sesji jest przygotowywany
  od razu w tle (`sessionFileFromDB`), więc zwykle wystarczy jedno stuknięcie. Jeśli nie ma potrzeby kopii sesji,
  a od `max(lastFull, since)` minęło 7 dni i są zmiany po `lastFull`: pasek pełnej kopii (dwa kroki jak w Ustawieniach,
  „Później” = jutro). Kopia liczy się tylko, gdy udostępnianie się udało (`shareBlob` zwraca `false` po zamknięciu okna);
  „Wyślij sesję jako plik” też ją zalicza. Pełna kopia ustawia `copied` wszystkich sesji. Sesje z pliku, z kopii
  zapasowej i nowe kopie sesji mają `edited = copied`. Data ostatniej pełnej kopii: `#backupLast` w Ustawieniach.
- **Plik sesji** `.looper`: `"LOOPERS1"` + uint32 LE długość JSON + JSON (`format:'looper-session', version:2`,
  części z `tracks` i ich `bytes`) + kolejne dane nagrań.
- **Kopia zapasowa** `.looper`: `"LOOPERB1"` + uint32 + JSON (`format:'looper-backup', version:1, sessions:[{ name,
  created, updated, tracks, state, items:[{ id, kind, sr, name, bytes }] }]`) + dane. Przywracanie dodaje sesje
  (nazwa + „(z kopii)” przy kolizji), niczego nie nadpisuje. `openLooperFile` rozpoznaje typ po nagłówku.
- Udostępnianie plików: Web Share API z plikami wymaga świeżego gestu, dlatego eksport i kopia działają
  w dwóch krokach („Zapisz kopię” → „Udostępnij kopię (X MB)”).
- Filmy: `mp4AacToAdts` (moov/trak/stsd mp4a/esds, także QuickTime `wave`, stco/co64/stsc) → ADTS →
  `decodeAudioData`; awaryjnie dekodowanie całego pliku. Film bez dźwięku → komunikat.
- MP3: `mp3-worker.js`, 160 kb/s mono. Eksport: część (całość albo pętla) albo cała sekwencja (OfflineAudioContext).

### PWA
- `sw.js`: cache-first z wersjonowaną pamięcią `looper-<wersja>`, `skipWaiting` + `clients.claim`, usuwa stare
  pamięci (`looper-*`, dawne `petla-ab-*`). `navigator.storage.persist()` przy starcie.

## Decyzje i ich powody (z rozmów z właścicielem)

- Nazwa **Looper** (nie „Pętla A–B”); bez dużego tytułu na górze.
- Zaznaczanie pętli: przeciągnięcie palcem po przebiegu. Przyciski „Ustaw A/B” były niezrozumiałe, więc wypadły;
  zostało **Dostrój** A/B (precyzyjne przesuwanie punktów) oraz **Pętla wł/wył** i **Usuń pętlę** (w karcie Pętla).
- **Kłódka** blokuje pętlę, bo właściciel przypadkiem przestawiał ją dotykiem. Zamknięcie kłódki zwija kartę Pętla
  i wyłącza lupę (gra cała pętla), otwarcie rozwija kartę (`toggleLock`, życzenie z 2026-11-08). Dotyczy tylko
  stuknięcia kłódki, nie przełączania części.
- Transport: żółty ⏮ (na początek / do A), −10, −5, ▶, +5, +10. Przycisk „Powiększ” usunięty.
- Korekta opóźnienia nagrań: zamiast osobnego suwaka jest przesuwanie śladów 2+ względem śladu 1
  (strzałki w rozwijanych opcjach śladu) i automatyczne zapamiętywanie tej poprawki.
- Bez limitu śladów. Karta śladów zwijana do paska; po zwinięciu przy przebiegach są czerwone kropki nagrywania.
- Duże różnice głośności między nagraniami → automatyczne wyrównanie, suwaki w dB, limiter, przycisk
  „Wyrównaj poziomy” w Ustawieniach.
- Chybienie w suwak zaznaczało tekst (niebieskie ramki): globalne `user-select:none`, `-webkit-touch-callout:none`.
- Karta tempa i tonacji domyślnie zwinięta, z podsumowaniem i literą części; na wąskim ekranie przy zmienionych
  wartościach chowa napis „Tempo i tonacja”, żeby nic się nie ucinało.
- **Ustawienia** i **Jak to działa** są w menu ☰ (prawy górny róg, obok nazwy sesji), nie na dole strony.
  Menu i lista sesji to panele pod paskiem sesji; otwarcie jednego zamyka drugi.
- **Mikser** można schować przyciskiem z suwakami w wierszu z czasem (`#mixToggle`, `looper.mixHidden`);
  przebiegi zajmują wtedy całą szerokość.
- **Karta Pętla** (`#loopCard`, domyślnie zwinięta, `looper.loopCollapsed`): Pętla wł./wył., Usuń pętlę, Dostrój A/B
  i przyciski ze strzałkami „← 0,1 s”, „← 0,01”, „0,01 →”, „0,1 s →” (strzałka = kierunek na osi czasu).
  Na pasku podsumowanie, np. „wł. · 0:01,97–0:07,38”.
- **Karta części na iPhonie**: A/B/C, kopiowanie i Część/Sekwencja w jednym rzędzie (ściśnięte przyciski poniżej
  430 px szerokości); przycisk zwijania sekwencji jest przy klockach, a po zwinięciu zostaje jednolinijkowe
  podsumowanie „Sekwencja: A×2 · B×1 · …”.
- **Zablokowana pętla**: przebieg ma `touch-action: pan-y`, więc ruch palcem w górę i w dół przewija stronę;
  komunikat o blokadzie pojawia się tylko po stuknięciu albo ruchu w bok. Suwaki miksera nadal reagują na
  przeciąganie (żeby przewijać tam, można schować mikser).
- **Lupa przejścia** (2026-11-08, pomysł właściciela): pozioma „pigułka” jak suwak jasności w iOS, w karcie Pętla obok
  Dostrój A/B (strzałki przeszły do osobnego rzędu, także na iPadzie). Bez liczb; skrajnie w lewo = wyłączona,
  przesuwanie dokłada czas płynnie do 5 s (ruch względny, zakres ruchu min. 200 px). Gra połowę sprzed B i połowę od A,
  **bez ciszy** między powtórzeniami (wyraźne życzenie). Działa tylko na otwartej części (nie w Sekwencji).
  Na pasku zwiniętej karty zamiast „wł.” jest „lupa”. Działa też przy zablokowanej pętli (to tylko odsłuch).
- **Kopie zapasowe półautomatycznie** (2026-11-08): w pełni automatyczny zapis do iCloud/Plików nie jest możliwy
  (iOS wymaga stuknięcia, Safari nie ma zapisu plików przez stronę). Właściciel wybrał: kopia **samej opuszczanej
  sesji** przy wyjściu z niej (i przy starcie, zamiast „przy zamknięciu”, którego nie da się obsłużyć) plus
  przypomnienie o pełnej kopii co 7 dni. Automatyczne wysyłanie do Dropboxa/Google Drive omówione, nie wybrane.

## Ograniczenia i odpowiedzi na częste pytania

- Aplikacja nie ma bezpośredniego dostępu do nagrań Dyktafonu (ograniczenie iOS): nagranie → ••• → Udostępnij →
  Zachowaj w Plikach, potem **Wczytaj**. Działa też film z galerii (zostaje dźwięk).
- Usunięcie aplikacji z ekranu początkowego może skasować jej dane (IndexedDB Safari): przed tym **Kopia zapasowa**.
- iPhone i iPad mają osobne dane; sesję przenosi się plikiem `.looper` (AirDrop) albo kopią zapasową.
- Liczba śladów jest ograniczona tylko pamięcią urządzenia (render trzyma wszystkie ślady części w RAM).
- Nagrania nigdzie nie są wysyłane.
- Aplikacja nagrywa z mikrofonu, który iOS wybierze jako wejście (np. podłączony mikrofon USB-C/Lightning).
  Zwykłe mikrofony Bluetooth (słuchawkowe) iOS obsługuje w jakości rozmowy telefonicznej, więc się nie nadają.

## Praca z właścicielem w długiej rozmowie

- Właściciel prosił, żeby mu powiedzieć, kiedy rozmowa robi się za długa. Przy większej zmianie zaproponuj
  nową rozmowę zaczynającą się od „Kontynuujemy Looper, przeczytaj notatki z repozytorium”.
- Często wysyła kilka próśb jedna po drugiej (ze zrzutami ekranu i zielonymi zaznaczeniami): zbierz je,
  zrób razem i opublikuj jedną aktualizacją.

## Plan: druga aktualizacja (uzgodniona 2026-11-08, jeszcze niezrobiona)

Właściciel wybrał z listy propozycji punkty 6, 7, 8, 9, 11 oraz lupę przejścia. Zrobione: 7, 8, 11, lupa.
Zostały (zaczynać po „działamy”):
- **6. Szybsze przeliczanie tempa i tonacji:** po zmianie najpierw przeliczyć tylko to, co zaraz zagra (pętlę albo
  najbliższe ok. 20 s), żeby dźwięk ruszył prawie od razu; resztę w tle i podmienić bez zatrzymywania grania
  (najlepiej przy przejściu pętli). Sekwencja startuje szybciej, bo każda część potrzebuje tylko swojej pętli.
  Nagrywanie i eksport MP3 czekają na całość. Pomiar: 3 min × 2 ślady z transpozycją ≈ 1,2 s na szybkim komputerze.
  Uwaga: WSOLA jest stanowa, więc lepiej osobny krótki render okna pętli (z zapasem), a potem pełny render ciągły,
  niż sklejanie kawałków.
- **9. Powiększanie przebiegu dwoma palcami:** rozsunięcie = powiększenie w tym miejscu, zsunięcie = pomniejszenie;
  przesuwanie powiększonego widoku dwoma palcami w bok; jeden palec działa jak dotąd (pętla, A/B, stuknięcie);
  podczas grania widok jedzie za kreską; przycisk „Całość” w rogu przebiegu, widoczny tylko po powiększeniu;
  działa też przy zablokowanej pętli (uwaga na `touch-action: pan-y`). Właściciel musi sprawdzić gesty na iPhonie.
  W kodzie jest już `zoomed`/`view`/`fitZoom` po dawnym przycisku „Powiększ”.
- Inne propozycje z listy, których nie wybrał (na później): zapisane pętle, trener tempa, strojenie w centach,
  przerwa między powtórzeniami, pedał Bluetooth (strzałki na klawiaturze przesuwają teraz A/B), notatka do sesji.

## Rozważane i odłożone

- **Praca na dwóch urządzeniach naraz** (tablet gra, iPhone nagrywa): odradzone 2026-11-08 jako zbyt
  skomplikowane i kruche (synchronizacja przez Wi-Fi co do milisekund w aplikacji przeglądarkowej na iOS).
  Prostsze drogi przy jednym gnieździe: iPad z osobnym gniazdem słuchawkowym, mikrofon z wyjściem słuchawkowym,
  albo nagranie iPhone'em → AirDrop → **Wczytaj** do śladu i dosunięcie strzałkami.

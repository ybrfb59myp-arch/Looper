# Dziennik zmian

Najnowsze na górze. Daty i godziny według czasu polskiego.

## 2026-11-08
- Źródła, skrypt budujący, testy i notatki projektu (`CLAUDE.md`) trafiły do repozytorium, żeby każda
  nowa rozmowa albo sesja w zakładce Code mogła kontynuować pracę.
- **Osobne tempo i tonacja dla każdej części** (A, B, C). Sekwencja i jej eksport grają każdą część w jej
  ustawieniach; kopiowanie części przenosi też tempo i tonację; starsze sesje: każda część dziedziczy
  dotychczasowe wspólne ustawienie. Na karcie tempa litera części, której dotyczą suwaki.
- Naprawa braku dźwięku po zminimalizowaniu i powrocie do aplikacji (nowy kontekst audio przy powrocie
  i strażnik, który wykrywa „zamrożony” zegar).
- Sprawdzanie nowej wersji przy każdym powrocie do aplikacji.
- Kopiowanie całej części (np. A → B) z potwierdzeniem, gdy cel ma nagrania.
- Zwijana karta tempa i transpozycji z podsumowaniem (domyślnie zwinięta).
- Kopia zapasowa wszystkich sesji w jednym pliku i przywracanie (Ustawienia).
- Części A/B/C z własnymi śladami, pętlą i mikserem; sekwencja (np. A×4, B×2) grana bez przerw, koło
  wyboru powtórzeń 1–32, tryb Część/Sekwencja, eksport całej sekwencji do MP3.
- Bez limitu śladów, wygodniejsze suwaki (cały pasek jest uchwytem, dymek z wartością, brak zaznaczania
  tekstu), zwijana karta śladów z czerwonymi kropkami nagrywania przy przebiegach.

## 2026-11-07
- Wyrównywanie poziomów nagrań, suwaki w dB, limiter na wyjściu, przebieg w rzeczywistej skali,
  przewijanie ±5/±10 s, żółty przycisk „na początek”.
- Mikser przy przebiegu: suwaki głośności, mute i solo.
- Sesje (lista, nazwy, kopie, pliki `.looper`), wczytywanie filmów z galerii (sam dźwięk), kłódka pętli,
  przesuwanie śladów 2+ względem śladu 1 z zapamiętywaną poprawką nagrań.
- Kilka śladów, nagrywanie do każdego śladu, eksport MP3; nazwa Looper i ikona od właściciela.
- Pierwsza wersja „Pętla A–B” jako aplikacja offline: pętla A–B, tempo, transpozycja, dwa ślady, nagrywanie.

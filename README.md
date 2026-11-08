# Looper

Prosta aplikacja do ćwiczenia z nagraniami z Dyktafonu na iPhonie i iPadzie.

- zapętlanie fragmentu A–B (przeciągnięcie palcem po przebiegu), dostrajanie punktów, kłódka blokująca pętlę
- tempo od −50% do +50% bez zmiany wysokości dźwięku, transpozycja od −7 do +7 półtonów
- dowolna liczba śladów: przy każdym **Nagraj**, **Wczytaj**, **Wyczyść**, przesuwanie śladów względem siebie
- mikser przy przebiegu: głośność w dB, mute i solo, automatyczne wyrównanie poziomów
- części A/B/C z własnymi śladami, pętlą, tempem i tonacją oraz sekwencja (np. A×4, B×2, A×4, C×1) grana bez przerw
- **Eksportuj MP3**: część, pętla albo cała sekwencja, np. do wysłania Messengerem
- wczytywanie filmów z galerii (np. nagrania ekranu): zostaje sam dźwięk
- sesje (lista, nazwy, kopie, pliki `.looper`) i kopia zapasowa wszystkich sesji w jednym pliku
- działa offline po dodaniu do ekranu początkowego, pamięta ostatnią sesję

Otwórz: https://ybrfb59myp-arch.github.io/Looper/  
W Safari: Udostępnij → **Do ekranu początkowego**. Na Androidzie w Chrome: **Zainstaluj aplikację**.

Nagrania zostają na urządzeniu. Aplikacja niczego nie wysyła.

Dla rozwijających: notatki projektu w [`CLAUDE.md`](CLAUDE.md), źródła w `src/`, budowanie `python3 tools/build.py`,
testy w `tests/`, historia w [`CHANGELOG.md`](CHANGELOG.md).

Kodowanie MP3: [LAME](https://lame.sourceforge.io/) przez [lamejs](https://github.com/zhuker/lamejs) (LGPL, zob. `lame.LICENSE.txt`).

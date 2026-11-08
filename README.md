# Looper

Prosta aplikacja do ćwiczenia z nagraniami z Dyktafonu na iPhonie i tablecie.

- do 4 śladów: przy każdym **Nagraj**, **Wczytaj**, **Wyczyść** (od drugiego także **Usuń**)
- zapętlanie fragmentu A–B, dostrajanie punktów, powiększanie
- tempo od −50% do +50% bez zmiany wysokości dźwięku, transpozycja od −7 do +7 półtonów
- głośność i przesunięcie każdego śladu, zapis śladu do WAV
- **Eksportuj MP3**: zgranie całości albo pętli do wysłania np. Messengerem
- wczytywanie filmów z galerii (np. nagrania ekranu) — zostaje sam dźwięk
- sesje: lista, nazwy, kopie, przesyłanie sesji jako plik `.looper`
- części A/B/C z własnymi śladami i sekwencja (np. A×4, B×2, A×4, C×1) grana bez przerw, eksport całej sekwencji do MP3
- kłódka blokująca pętlę, przesuwanie śladów 2–4 względem śladu 1 z zapamiętywaną poprawką nagrań
- działa offline po dodaniu do ekranu początkowego, pamięta ostatnią sesję

Otwórz: https://ybrfb59myp-arch.github.io/Looper/  
W Safari: Udostępnij → **Do ekranu początkowego**. Na Androidzie w Chrome: **Zainstaluj aplikację**.

Nagrania zostają na urządzeniu. Aplikacja niczego nie wysyła.

Kodowanie MP3: [LAME](https://lame.sourceforge.io/) przez [lamejs](https://github.com/zhuker/lamejs) (LGPL, zob. `lame.LICENSE.txt`).

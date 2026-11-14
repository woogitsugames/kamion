# STATUS — M60 (cloud p17-dusk-lighting)

- 2026-11-14: GOTOWE do przeglądu. manifest.csv 87 wierszy (niebo 24, ulica 30, okna 19, kadr 14); 24 pliki kadrów (miniatury 1920 px Commons,
  13 113 826 B) przez `fetch.py`; README z tabelą „Do porównania z ADR 0191/0192”; audyt 18/87 (seed 20261114), 0 poprawek po losowaniu.
- Odtworzenie: `python3 build_manifest.py` (manifest), `python3 sun.py table` (zmierzch), `python3 fetch.py` (kadry; Commons dławi - HTTP 429, skrypt ponawia).
- Niekompletne: klasy/wysokości/CCT/próg załączania dla ulic trasy (UNVERIFIED), brak nocnych kadrów Andersa/Maczka/Putry, oryginały zdjęć niepobrane (429).
- NASTĘPNY KROK (lider): `python3 research/cloud/p17-dusk-lighting/fetch.py` i przegląd PR.

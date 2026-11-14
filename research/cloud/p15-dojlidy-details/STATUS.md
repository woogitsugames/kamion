# STATUS — M58 (cloud p15-dojlidy-details)

## 2026-11-14 ~17:50 UTC — WIP 1
- Zrobione: OSM (API 0.6 map bbox 23.155,53.094,23.212,53.114; brak barrier=chain w OSM), AIP VFR EPBK (AD 4 EPBK 2-1, AIRAC AMDT VFR 06/26: RWY 09R/27L 1350×30, LDA 900/640), ortofoto GUGiK 0,05 m (arkusz N-34-107-C-b-3-4, 2025-04-18) — pomiar oznakowania pasa, NMT 1 m (WCS), 31 kadrów Commons obejrzanych (960 px) + 13 w wycinkach 3840 px.
- Blokada: upload.wikimedia.org zwraca 429 (retry-after 600) — oryginały do sha256 pobierane w tle; kadry oglądane przez commons thumb.php.
- Dz.U. 2019 poz. 2311: API Sejmu podaje ten sam plik dla c1 i c2 (525 s., zał. 1) — zał. 4 (U-12b) niedostępny → UNVERIFIED.
- NASTĘPNY KROK: wygenerować manifest.csv (skrypt w scratch), README.md, sources.md, fetch.py, audit_20_percent.json; potem PR.

## 2026-11-14 ~17:50 UTC — GOTOWE do przeglądu
- manifest.csv 80 wierszy (SOURCED 42, ESTIMATED 36, UNVERIFIED 2); 31 kadrów Commons obejrzanych w 960 px, 13 z nich w 26 wycinkach z 3840 px; 12 wycinków ortofoto GUGiK 0,05–0,4 m/px; karta AIP.
- Samokontrola: seed 20261114, 16/80 wierszy, 11 obrazów obejrzanych ponownie, 10 PASS, 6 poprawek.
- fetch.py przetestowany w czystym katalogu: 16/33 plików OK (GUGiK, PAŻP, Dz.U.); 17 plików Commons — HTTP 429 z adresu sesji (w manifeście sha1 z API zamiast sha256).
- NASTĘPNY KROK (lider): `python3 -I research/cloud/p15-dojlidy-details/fetch.py` na własnej maszynie; po pobraniu oryginałów Commons dopisać sha256 (skrypt wypisuje je w każdej linii) i odczytać EXIF ogniskowej kadru 20240623_124644 (metoda A wysokości słupka).
- Otwarte: zał. 4 Dz.U. 2019 poz. 2311 (U-12b) — do pobrania z ISAP z przeglądarki i zacytowania.

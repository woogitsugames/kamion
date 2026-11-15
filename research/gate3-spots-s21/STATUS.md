# STATUS — G3 punkty problemowe trasy C (bramka 3), sesja s21

## 2026-11-15 — GOTOWE (PR do main)
- Punkty a–d zlokalizowane (gate3_cameras.json → WGS84); OSM API 0.6 (2 bbox), ortofoto GUGiK WMS (4 wycinki).
- Manifest: 38 wierszy (30 kadrów: a 6, b 9, c 9, d 6; 4 ortofoto; 4 OSM); files/: 30 kadrów ≤1600 px + 4 ortofoto + 10 wycinków.
- Audyt 20 %: seed 20261115, 8 wierszy, 6 PASS / 2 FIX (poprawione).
- README: odpowiedzi na 4 pytania + co zmienić w grze + pewność; lista UNVERIFIED.

Następny krok (lider): przegląd PR; ewentualnie zadanie na lico muru rampy NW widziane z łącznicy (brak kadru z otwartą
licencją) i na rabaty ronda Bieżeństwa. Odtworzenie manifestu:
`python3 -I research/gate3-spots-s21/tools/build_manifest.py <katalog_pobrań>` (kroki pobierania w sources.md).

## Historia
- krok 1: lokalizacja, OSM, kandydaci (Commons 55, Panoramax 24, KartaView 5 sekwencji).
- krok 2: oględziny kadrów, ortofoto, manifest + pliki (commit WIP).
- krok 3: audyt, README, sources, PR.

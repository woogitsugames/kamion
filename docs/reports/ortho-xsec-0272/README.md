# Przekroje dróg z ortofotomapy GUGiK (ADR 0272) — wyniki pomiaru z 2026-11-15

Narzędzie: `tools/worldgen/qa/ortho_xsec.py` (metoda, adres WMS i progi w nagłówku pliku). Źródło obrazu: GUGiK, WMS
`mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/StandardResolution`, warstwa `Raster`, pobranie 0,05 m/px (serwer
przepróbkowuje arkusze; **rozdzielczość natywna i data arkuszy: UNVERIFIED** — usługa ich nie zwraca w tej skali).
W repo są tylko liczby; obrazy (paski kontrolne `*.jpg`) zostają w `artifacts/rural-xsec-0272/` poza gitem.

Odtworzenie: `uv run --project tools/worldgen python tools/worldgen/qa/ortho_xsec.py measure <region> <waye> <krok> <prefiks>`,
podsumowanie: `… ortho_xsec.py summary docs/reports/ortho-xsec-0272/*.json`. Dokładność odczytu: linia ±0,2 m, krawędź
asfaltu ±0,3 m. „Czysty” przekrój = asfalt 6,0–7,6 m (odrzuca cień drzew, wloty, zatoki).

| plik | region, waye, krok | przekroje / czyste | asfalt mediana (zakres) [m] | obie linie: rozstaw mediana (zakres) [m] |
|---|---|---|---|---|
| `dk65-04_elcka.json` | dk65-04; 1024956365, 41533343, 1243220441; 220 m | 11 / 8 | 6,68 (6,35–7,15) | 3: 6,30 (6,25–6,30) |
| `dk65-05_elcka.json` | dk65-05; 1024956364, 1399803717; 260 m | 10 / 9 | 6,90 (6,20–7,45) | 7: 6,20 (6,00–6,35) |
| Ełcka razem (04 + 05) | — | 21 / 17 | **6,75** (6,20–7,45) | 10: 6,20 (6,00–6,35) |
| `dk65-01_knyszynska.json` | dk65-01; 234919333, 396566354, 1281925347; 120 m | 5 / 5 | 7,15 (6,85–7,40) | 2: 6,20 |
| `dk65-02_knyszynska.json` | dk65-02; 396566354, 716806122, 716806121; 160 m | 6 / 6 | 6,80 (6,65–7,00) | 4: 6,22 (6,00–6,35) |
| `dw671-tykocin-01_dw671.json` | dw671-tykocin-01; 145989268, 286989055; 150 m | 14 / 11 | 6,85 (6,15–7,25) | 2: 6,88 (6,85–6,90) |
| `bialystok-knyszynska_szosa-elcka.json` | bialystok-knyszynska; 303739903; 150 m | 5 / 0 | — (5,95–14,05: zatoki, wloty) | — |

Wnioski użyte w ADR 0272: Ełcka — asfalt 6,75 m przy liniach 6,2 m, czyli przy `width` 6,6 m (D66) zostaje
(6,75 − 6,6) / 2 = 0,08 m asfaltu poza szerokością; różnica jest mniejsza niż dokładność odczytu, więc 0,08 m to
**WORKING_VALUE oparty na pomiarze jednej drogi**, nie pomiar szerokości opaski. Rodzaj pobocza (krawężnik / grunt) i
szerokość pasa żwiru (0,7–1,2 m na Ełckiej) odczytane wzrokowo z pasków kontrolnych — ESTIMATED.

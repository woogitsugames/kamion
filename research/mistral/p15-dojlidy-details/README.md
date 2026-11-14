# P15 — Dojlidy/Krywlany: wygrodzenia U-12b, oznakowanie pasa 09R/27L EPBK, drobne zapory i szlabany (D60)

**Kamion — badanie szczegółów wyposażenia regionu Dojlidy/Krywlany (D60), blok M58.** Stan: 14 listopada 2026, **BADANIE W TOKU** (skeleton commit). Gałąź: `research/mistral-p15-dojlidy-details`, wyjście z najnowszego `origin/main` (34ec02ab). Materiał po polsku. Uzupełnia P11 (kadry) i P12 (landmarki) — nie powtarza ustaleń tam zawartych.

Zakres — trzy wątki:
1. **Słupki biało-czerwone z łańcuchem (U-12b)** przy ul. Adama Mickiewicza / Jacka Kuronia (kadr P11-063) i inne takie wygrodzenia w regionie — wymiary wg Dz.U. 2019 poz. 2311 zał. 4 + odczyt z kadrów (ESTIMATED z metodą).
2. **Pas startowy 09R/27L Krywlany** — oznakowanie wg AIP (PAŻP) i ortofoto GUGiK; werdykt „czy oznakowanie pasa widoczne z drogi publicznej z oka kierowcy ciężarówki (~2,5 m)"; ogrodzenie lotniska od strony dróg.
3. **Inne drobne wygrodzenia** (szlabany z biało-czerwonym ramieniem itp.) — 1–3 przykłady z pozycją i kadrem.

## Metoda i źródła

- **Dz.U. 2019 poz. 2311** (jednolity tekst rozporządzenia MI z 3.07.2003, zał. nr 4 — urządzenia BRD): skany z ELI/Sejm API dekodowane lokalnie (CCITT z PDF, własny dekoder), rysunek U-12b odczytany wzrokowo z kompozycji strony — cytat ≤ 25 słów + numer strony.
- **AIP Polska VFR** AD 4 EPBK (PAŻP, AIRAC 10-26 2026-10-01) — dokument urzędowy; tylko fakty, bez kopiowania map.
- **Ortofoto GUGiK** (WMS StandardResolution) — kadry 0,25–0,75 m/px; opis tego, co widać przy tej rozdzielczości.
- **OSM** (ODbL): geometria dróg (way_id) i pasa 09R/27L (way 958211700; 1350×30 m, asfalt) oraz 09L/27R (way 303368859; 860 m, trawa), poligon lotniska (way 234838628); odległości liczone do osi drogi (przypisanie kadru do drogi tylko przy ≤ 25 m).
- **Wikimedia Commons** (CC0/BY/BY-SA) — kadry Rakoon z 2024-06-23 (seria wzdłuż Mickiewicza/Kuronia), 2023-08-14 (D303), szpital Żurawia 2019-11-10, WSWFiT 2015-08-22 (CC BY-SA 4.0 — referencja, nie tekstura), browar 2012-07-21 (CC BY 3.0).
- Zakazane źródła (Google) — **nieużywane**. Mapillary bez tokenu → UNVERIFIED.
- Statusy: SOURCED (cytat + strona) / ESTIMATED (z metodą) / UNVERIFIED / REJECTED. WGS84 (6 miejsc), JPG ≤ 1600 px.

## Geometria droga↔pas (OSM, obliczenia własne)

| Droga | way_id (najbliższy odcinek) | min. odległość osi drogi od osi pasa 09R/27L | Uwagi |
|---|---|---|---|
| Adama Mickiewicza (odcinek płd.) | 203121432 / 206333509 | ~327 m / ~314 m | odcinki przy lotnisku; Mickiewicza opływa lotnisko od NE |
| Jacka Kuronia | 258564448 / 275237234 | ~650 m / ~551 m | |
| Dywizjonu 303 | 443103344 / 538810157 | ~384 m / ~397 m | uwaga: P12-001 podało „150 m" — patrz sekcja Luki |

Szczegóły, tabele wymiarów, werdykt widoczności i lista kadrów — będą uzupełnione w kolejnych commitach (badanie w toku; pliki robocze poza gitem: `files/` + ZIP przekazywany właścicielowi).

## Luki (stan bieżący)

- Wymiary U-12b z rysunku Dz.U. — w trakcie odczytu ze skanów zał. 4 (odwzorowanie CCITT zakończone; trwa lokalizacja strony rysunku).
- Oznakowanie TRW 09R/27L — AIP VFR AD 4 EPBK nie zawiera opisowej tabeli oznakowania (dane zbiorczo na mapie AD 4.13 — odczyt wizualny w toku); ortofoto w toku.
- Data nalotu ortofoto — skorowidz WMS niedostępny (HTTP 401) → UNVERIFIED jeśli nie uda się odczytać inaczej.

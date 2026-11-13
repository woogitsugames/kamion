# ADR 0167 — P1 budynków w kadrach bramki 3 (cm92458760, cm109685822, wieżowiec przy Kwadracie)

Status: PROPOSED na gałęzi `bldg-0167` (2026-11-13, s17); nie scalone. Liczby w „Walidacja” są zmierzone na świecie
tej gałęzi; ocena `visual-critic` jeszcze wymagana (subagent nie uruchamia subagentów).
Źródło: `docs/reports/visual/REVIEW-2026-11-13-s16b-final.md` (P1 cm92458760: „bezokienny biały prostopadłościan
x 0,1–0,3”, „budynek EC szary zamiast niebieskiego”; P1 cm109685822: „budynek z prawej beżowy 3-kondygnacyjny vs
niebieski biurowiec”), `artifacts/live/p1-0161.md` („Budynki (lider)”). Kryterium: D51 (rozpoznawalność miejsca).

## 1. Ustalenia (dane, nie domysły)

Narzędzia: `artifacts/bldg-0167/tools/map.py` (ortofoto GUGiK 2024-05-27 0,25 m + obrysy + stożek kamery SBS),
`crop.py`. Zdjęcia tylko jako referencja (Commons: Rakoon cm92458760 2020-07-11 CC BY 3.0, cm109685822 2021-09-04
CC0; Mapillary richlv 177786140912399 / 178689077481862 2020-08-15 CC BY-SA 4.0).

| Obiekt | Rekord | Było | Zdjęcie / ortofoto |
|---|---|---|---|
| „biały prostopadłościan” cm924 | `osm:way/591365138`, 34 m², building=service, brak BDOT/LoD1 → wysokość domyślna 6,0 m | biała bezokienna bryła 6 m | półzagłębiona komora: ~1,6 m jasnoszarej ściany z kratkami + ciemna płyta dachu ~0,45 m (ściana 8,0 m = 960 px, ściana 170 px, płyta 50 px) |
| niebieski budynek EC | `bdot:2BE4B431-CA0E-…`, „siedziba firmy”, LoD1 2024 4,45 m, 1 kond. | szary tynk, ciemne okna pasmowe | jasnoniebieski tynk, rząd białych okien dwudzielnych co ~3 m na ścianie NE, ciemniejszy niebieski człon od ulicy |
| akumulator ciepła EC | `osm:way/279896715`, building=industrial, okrąg 21,8 m, brak BDOT/LoD1 → 6,0 m | dysk 6 m (niewidoczny) | zbiornik ~39 m: górna krawędź 310 ±15 px nad linią oka przy f = 1142 px i 148 m → 40 ±2 m nad okiem; kontrola: przesunięcie dachu na ortofoto ~15 m wobec ~14,5 m dla wieżowca 41,81 m (LoD1). Jasny płaszcz, niebieski pas ~9 m pod koroną |
| pawilon z prawej cm109 | `bdot:ffe33067-…`, „obiekt handlowo-usługowy”, 8,57 m, 2 kond. | beżowy tynk, okna punktowe | niebiesko-szara okładzina, witryny na całym parterze od drogi (NW), rząd małych okien piętra, ciemna attyka |
| wieżowiec (177786 / 178689) | `bdot:2BE4B431-CA0F-…`, 41,81 m, 11 kond. | jasnoszary | bladożółty tynk (zdjęcia + elewacja widoczna na ortofoto) |

Wysokość budynku w kadrze cm109 była poprawna (2 kondygnacje wg BDOT, 8,57 m LoD1) — „3-kondygnacyjny” w recenzji
to odczyt rytmu okien generatora; po zmianie parter to witryny, piętro to jeden rząd okien.

## 2. Decyzja

1. `tools/worldgen/streetscape/buildings_mesh.py` `load()`: nowy klucz override'u budynku `height_m` (2 linie) —
   autorska wysokość dla obiektów bez rekordu LoD1/BDOT; rekord `buildings.geojson` nie jest przepisywany.
2. `tools/worldgen/streetscape/materials.py`: jeden nowy materiał `plaster_blue` (albedo 0,09/0,19/0,31 odczytane z
   cm92458760 względem białych ram okien; WORKING_VALUE). Bez wariantu `__far_*` — tylko dla autorskich frontonów.
3. `Data/Regions/bialystok-industrial-c/overrides.yaml` — 5 authored_overrides (przeżywają reimport):
   `g3a-ec-kiosk-height` (2,0 m, płyta dachu), `g3a-ec-blue-office` (fronton niebieski, 11 okien na NE),
   `g3a-ec-heat-accumulator` (39 m, biały płaszcz, niebieski pas 28,5–30,5 m dookoła),
   `g3a-kwadrat-blue-pavilion` (fronton niebieski, witryny NW, pas okien piętra), `g3a-office-tower-colour`
   (`plaster_beige`, wariant dalekiej elewacji istnieje).
4. Bez marek: panel z logo na zbiorniku i szyldy nie są odtwarzane.

Odrzucone: ciemniejszy drugi odcień niebieskiego dla członu od ulicy (`hall_wall_accent_blue` jest zastrzeżony dla
okładzin hal — `frontage.plan` odrzuca `hall_wall_*`; inny materiał = +1 draw na chunk i LOD); grafitowy biurowiec
kadru 326454015490067 (`bdot:2BE4B431-C34C-…`, render jasny, zdjęcie ciemne) — wymaga ciemnego materiału z wariantem
dalekiej elewacji albo frontonu (+2 draw w chunku 2_4): otwarte.

## 3. Walidacja

WALIDACJA_PLACEHOLDER

## 4. Otwarte

- Biurowiec kadru 326454 (jak wyżej).
- Ramy okien frontonu są ciemne (jeden materiał ram w `frontage`); na zdjęciu białe.
- Wysokość zbiornika 39 m i kiosku 2,0 m: WORKING_VALUE (zdjęcie + ortofoto) do sesji zdjęciowej właściciela.
- Pozy kadrów (cm924 B, cm109 C) nie były ruszane — położenie brył w kadrze zależy od nich (zakres 0160/0161).

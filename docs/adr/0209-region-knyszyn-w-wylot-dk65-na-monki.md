# ADR 0209 — region `knyszyn-w`: zachodnia część Knyszyna i wylot DK65 na Mońki (z grubsza, D63/D64)
Status: przyjęty (scalony do main 2026-11-15, `d4914ba6e`; status zaktualizowany 2026-11-16); pierwotnie: Proposed (agent world-builder, s20, gałąź `knyszyn-w-0209`), 2026-11-15. Do scalenia przez lidera.
Powiązane: D63, D64 (`docs/11`), ADR 0203 (siatka kafli), ADR 0204 (`knyszyn`, `knyszyn-s`; otwarte p. 1 = ten kafel),
brief `docs/owner/S20-REGION-RING-BRIEF.md` (DROGI NAJPIERW).

## Kontekst
ADR 0204 zostawił kafel (−9,8) niezbudowany: rondo DK65/DW671 leży 37 m od zachodniej krawędzi `knyszyn`, więc wylot
DK65 na Mońki i DW671 na Tykocin kończyły się zaporą końca świata tuż za rondem.

## Decyzja
1. **Region `knyszyn-w` = kafel (−9,8)** siatki ADR 0203: EPSG:2180 [758539, 611583, 760587, 613631], origin
   (759563, 612607); wspólna krawędź x = 760587 z `knyszyn`. Powiat 2008 w 100 % (relacje OSM: gm. Knyszyn 97,6 %,
   gm. Krypno 2,4 %) — `teryt_powiat_extra` (0208) niepotrzebne. Zawartość: DK65 Obozowa 1,99 km od ramienia ronda do
   północnej krawędzi (dalej Mońki, kafel (−9,9) niezbudowany), DW671 Tykocka 0,6 km (wychodzi południową krawędzią
   do (−9,7)), zachodnie ulice miasta (Legionowa, Kościelna, Zamoyskiego, Junga, Jagiełły, Goniądzka, Polna), cmentarz,
   pola. Graf: 46 węzłów, 47 krawędzi; 371 budynków (BDOT10k + LoD1 2024 / LoD2 2017 powiatu 2008).
2. **Szew z `knyszyn`**: 10 dróg przecina x = 760587 — po obu stronach te same `osm_way`, te same y punktów (0,1 m),
   klasa, liczba pasów, kierunek (test). DK65: ten sam przekrój co w `knyszyn` (override `dk65-carriageway-width`
   2 × 3,4 m + 2 × 0,35 m = 7,5 m) — zmierzony też w tym kaflu na ortofoto 0,1 m 2025 (`tools/profile10.py`):
   linia krawędziowa – linia krawędziowa 6,8 m w dwóch przekrojach (760480 612300; 759650 613425), oś OSM ≤ 1 m od
   linii środkowej na orto (5 przekrojów). DW671: szerokość z BDOT 6,5 m po obu stronach (bez override, jak `knyszyn`).
3. **Teren na szwie: authored pin roku NMT** (`Data/Regions/knyszyn-w/sources.authored.json`, `{"nmt_year": "2022"}`,
   czytany przez `ingest.py` i `build_region.py`; region bez pliku — bez zmian). Najnowszy NMT kafla (2025-05-27)
   różnił się od NMT 2022 kafla `knyszyn` na wspólnej kolumnie: mediana 0,06 m, p95 0,33 m, max 1,31 m, na DK65 0,11 m.
   Z tym samym rokiem kolumna szwu pochodzi z tych samych arkuszy (N-34-106-B-b-1-2/1-4): różnica 0,000 m.
4. **Latarnie**: DK65 w polach (way 232511647) i drogi polne bez latarni — orto 0,1 m 2025 bez słupów (latarnie z
   wysięgnikami tylko przy DK65 w mieście, way 232511646, zostawione regule): reguła 256 → 167 latarni.
5. **Trasa kontrolna** (`route_endpoints.json`): DK65 od węzła brzegowego na szwie (760587, 612073,7) do północnej
   krawędzi (759428,1; 613631), 1989 m. 10 kamer miejsc (`control_cameras_place.authored.json`) + kamery trasy.
   Kamera szwu stoi ~130 m za szwem: zapora końca świata (`WorldEdgeBuilder.ClosureSetbackM` = 60 m) zasłaniała drogę.
6. `graph_filter.authored.json` jak w `knyszyn` (bez zjazdów do posesji `service=driveway`).

## Drogi kontra ortofoto (plan z góry obok orto, `artifacts/knyszyn-w-0209/plan/knyszyn-w/r1/*.jpg`)
| miejsce | zgodne | rozbieżne → co zrobione |
|---|---|---|
| szew / ramię ronda | DK65 i DW671 w punktach szwu `knyszyn` | uliczka przy cmentarzu (way 98072701) ~5 m od jasnego pasa na orto — bez zmiany |
| Legionowa, Kościelna | skrzyżowania T z DK65, położenie ±3 m | na zachód od Kościelnej tylko chodnik (OSM footway) — zgodnie z danymi |
| widełki Goniądzkiej | dwa ramiona + wyspa trójkątna | — |
| Polna + droga polna | T z DK65 ±5 m, droga polna z SE | droga polna na orto żwirowa, u nas asfalt z liniami krawędzi — otwarte |
| DK65 w polach | szerokość, oś | orto: linie krawędziowe i szpalery drzew po obu stronach; u nas tylko oś przerywana i drzewa z generatora — otwarte |

## Budżet (edytor, Low, overcast, `stats.txt`; hipotezy `docs/06` §6: Low ≤ 300–400 draws / ≤ 600 tys. tris)
| | Low |
|---|---|
| WORLD_MEMORY | 53,9 MB (High: 129,2 MB; teren 24,1 / 96,9 MB) |
| draws max (kamery świata) | 202 (`route-s0426`, miasto), 201 (`dk65-koscielna`); w polach 18–64 |
| tris max | 174 tys. (`route-s0426`) |
| `build_world` | 126–158 s; import 8,5–11 min; GLB+import `_Generated/World/knyszyn-w` 516 MB |
Wszystkie kamery Low w hipotezie budżetu (poniżej `knyszyn`: 429 draws). Pomiar na telefonie — lider.

## Walidacja
- `tests/gis/test_region_knyszyn_w_0209.py` (7 testów: siatka, szew drogi/punkty/przekrój, teren szwu identyczny,
  trasa, kamery, override bez stale) + `test_region_knyszyn_0204.py`: 20 passed.
- Rendery: `artifacts/knyszyn-w-0209/vqa/knyszyn-w/r1-Low` (NMT 2025, przed poprawkami), `r2-Low` (stan końcowy).
- Spójność nawierzchni: 4 × `lane_blind_end`, 0 na trasie (Zamoyskiego × Junga; zerowej długości odcinek
  Kościelnej na szwie — ten sam jest w `knyszyn`).
- Ocena `visual-critic` nie wykonana (subagent nie tworzy subagentów) — rendery do przeglądu lidera. Bez telefonu.

## Otwarte
1. Kafle dalej: (−9,9) DK65 na Mońki, (−9,7) DW671 na Tykocin — dziś koniec świata na krawędziach kafla.
2. Linie krawędziowe DK65 (orto: są) — dodać razem w `knyszyn` i `knyszyn-w`, żeby szew został spójny.
3. Szpalery drzew wzdłuż DK65 w polach (orto 0,1 m), cmentarz bez nagrobków (pusta trawa), droga polna żwirowa.
4. Latarnie na DK65 między widełkami Goniądzkiej a Polną (~250 m) — niezweryfikowane.
5. Mechanizm `sources.authored.json` pinuje tylko NMT; ortofoto kafla = 0,1 m 2025 (jak `knyszyn`, `find_manifest`
   bierze ostatni id), co jest zgodne z intencją QA.

## Odtworzenie
```
uv run --project tools/worldgen tools/worldgen/ingest.py --region knyszyn-w --with orto10
uv run --project tools/worldgen tools/worldgen/build_region.py --region knyszyn-w
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region knyszyn-w --context
uv run --project tools/worldgen python scripts/export-route.py --region knyszyn-w
pwsh scripts/import-region.ps1 -Region knyszyn-w
pwsh scripts/visual-qa.ps1 -Scene World_knyszyn-w -Tier Low -Lighting overcast -OutputDir artifacts/knyszyn-w-0209/vqa/knyszyn-w/r2-Low
```

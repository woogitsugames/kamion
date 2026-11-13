# ADR 0164 — tagi limitów ciężarówki w grafie dróg
Status: Proposed (agent geo-worldgen, s16, gałąź `tags-0164`), 2026-11-13. Do scalenia przez lidera; po scaleniu lider
regeneruje dane (sekcja „Co musi zrobić lider”).

## Kontekst
Research G10 (`research/g10-truck-restrictions/README.md`) znalazł lukę w potoku: `tools/worldgen/roadgraph.py` miał białą
listę tagów (`RAW_TAGS` i pętla w `edge_attrs`) bez `maxaxleload`, `maxlength`, `maxweight:hgv`, `hgv:conditional`,
`maxgvweightrating:hgv`; do tego `osm_extract.ROAD_TAGS` w ogóle ich nie czytał z PBF. Format KRTG v2 (ADR 0150, Mistral M21)
ma już pola `maxweight`, `maxaxleload`, `maxheight`, `maxlength` na krawędź, a planer C# (`RoutePlanner.EdgeAllowed`) już
je egzekwuje, więc luka była wyłącznie po stronie danych: pola w pliku były puste, bo graf nie niósł tagów.
Skutek na dziś zerowy (limit 11,5 t = parametr pojazdu), ale po rozszerzeniu regionu 10 t na Szosie Knyszyńskiej/Ełckiej
dałoby trasę przez drogi zakazane dla osi 11,5 t.

## Decyzja
1. **Przepustka tagów.** `roadgraph.TRUCK_LIMIT_TAGS = (maxaxleload, maxlength, maxweight:hgv, hgv:conditional,
   maxgvweightrating:hgv)` dołączone do `RAW_TAGS` i do kopiowania atrybutów krawędzi (provenance `osm`, confidence `high`,
   brak tagu = brak atrybutu, bez wartości domyślnej). Te same klucze w `osm_extract.ROAD_TAGS` (zmiana listy zmienia
   klucz cache `Data/raw/derived`, więc PBF jest parsowany od nowa raz). Test pilnuje zgodności obu list.
2. **Format KRTG bez zmiany wersji.** Pola limitów już istnieją w v2; parser Python i czytnik C# (v1 i v2) bez zmian.
   Normalizacja jednostek jak w M21 (`parse_weight_t`, `parse_length_m`: „10”, „11,5 t”, „10000 kg”, „16.5 m”, `none`/`default`
   = brak limitu); `maxweight:hgv` ma pierwszeństwo przed `maxweight`.
3. **`maxgvweightrating:hgv` tylko w grafie (QA), nie jako limit masy.** To znamionowa masa pojazdu, w Białymstoku występuje
   razem z `hgv=no` i wyjątkiem `none @ delivery`; `hgv=no` już daje `F_NO_TRUCK`. Zamiana na `maxweight` byłaby zgadywaniem.
4. **Nacisk osi pojazdu (C#)**: bez zmian wartości `RoutePlanner.TruckMaxAxleLoadCt = 1150` (11,50 t). Pochodzenie: dane pojazdu
   `tractor_4x2_generic.vehicle.json` oś `rear` `ladenAxleLoadN = 112800` N (wartość projektowa EBS, WORKING_VALUE;
   112800 / 9,80665 = 11,50 t) oraz limit osi napędowej Dyrektywy 96/53/EC cytowany w `docs/VEHICLE_REFERENCE_DATA.md`
   (UNVERIFIED). Rzeczywisty nacisk osi napędowej w `laden40` to 10,76 t. Wybór: limit prawny/projektowy 11,5 t (konserwatywnie);
   w danych występują tylko wartości 10 i 11,5 t, więc dla obu wyborów wynik jest taki sam (10 < 10,76 blokuje, 11,5 przepuszcza).
   Test `TruckAxleLoad_MatchesVehicleData_ADR0164` wiąże stałą z plikiem danych pojazdu (zmiana jednego bez drugiego = czerwony test).
5. **`hgv:conditional`**: `parse_hgv_conditional` rozumie wyłącznie czyste okna godzinowe (`no @ (22:00-06:00)`,
   `destination @ 06:00-08:00`, kilka elementów po `;`). Krawędź z takim warunkiem dostaje flagę **bit7 (128)**
   `F_HGV_TIMED` / `RouteGraph.FlagHgvTimed`, informacyjną: planer nie ma zegara i nie blokuje na jej podstawie (zakaz
   nocny nie może odciąć trasy w dzień). Dni tygodnia, daty, wagi, `yes @ ...` i wszystko inne nie jest kodowane, tylko
   wypisywane w raporcie budowy (`UNPARSED hgv:conditional <edge>: <wartość>`; `t["hgv_conditional_unparsed"]`). Bit to zwykły bit
   bajtu flag: bez zmiany wersji formatu, czytniki maskujące własne bity nie są dotknięte.

## Liczby (pomiar 2026-11-13, PBF `podlaskie-261108`, bbox ekstraktu 22,98–23,32 E / 53,05–53,20 N, 47 179 dróg)
| Tag | way w ekstrakcie | wartości |
|---|---|---|
| `maxaxleload` | 713 | 11,5 t: 687; 10 t: 26 |
| `maxgvweightrating:hgv` | 7 | 8 t: 6; 3,5 t: 1 |
| `maxlength` | 0 | brak |
| `maxweight:hgv` | 0 | brak |
| `hgv:conditional` | 0 | brak (są tylko `maxspeed:hgv:conditional` i `maxgvweightrating:hgv:conditional`, poza zakresem) |
| (dla porównania) `maxweight` / `maxheight` / `hgv` | 173 / 52 / 142 | już przenoszone |

Kafel `bialystok-industrial-c` po regeneracji grafu (skrypt w scratch, ta sama funkcja `roadgraph.build`, `z_terrain`
przepisane z obecnego pliku): 646 krawędzi, **+89 krawędzi z `maxaxleload=11.5`**, 0 krawędzi z innymi nowymi tagami,
**0 innych różnic** w `roads.graph.json` (krawędzie, węzły, atrybuty, nagłówek). W KRTG: 646 krawędzi, jedyna zmiana to
`maxaxleload_c = 1150` na 89 krawędziach (nazwy, węzły, restrykcje, pasy bez zmian).

## Wpływ na trasy (tile `bialystok-industrial-c`)
Porównanie raportów `tools/nav-runner` Runner (36 tras wzorcowych, graf jakości, scenariusze) przed i po regeneracji
`.bytes`: wyjście **identyczne** poza czasem planowania (0,170 vs 0,180 ms). 0 zmian trasy, 0 zmian manewrów. Zgodnie z
oczekiwaniem: 11,5 t = parametr pojazdu, limit równy parametrowi nie blokuje. Planer w żadnej trasie wzorcowej nie omija
krawędzi z limitem 11,5 t.

## Testy
- pytest `tools/worldgen/navgraph/tests`: **51 zielone** (21 dotychczasowych + 30 nowych w `test_truck_tags_0164.py`, w tym
  test na prawdziwych danych: way 249640399 Andersa `maxaxleload=11.5` przez `osm_extract` -> `roadgraph.build` -> KRTG;
  pomijany bez `Data/raw`). Stan danych A (obecne `.bytes`/graf) i B (po regeneracji) oba zielone, poza
  `test_region_file_is_reproducible`, który w stanie B wymaga regeneracji `.bytes` (patrz niżej, w stanie A zielony).
- nav-runner (xUnit, **kompilowany Roslynem z Unity + runtime .NET 8, bo na tej maszynie jest tylko runtime, bez SDK**, wszystkie
  `[Fact]`/`[Theory]` uruchomione prostym runnerem refleksyjnym): **84/84** na zregenerowanych danych, 84/84 na obecnych
  (baseline przed zmianą 81). Nowe: `Synthetic_AxleLoad10Blocks_11_5Allowed`, `Synthetic_HgvTimedFlag_IsInformationalOnly`,
  `TruckAxleLoad_MatchesVehicleData`; poprawiony `Region_LimitsLoadedAndEmptyForCurrentData` (dopuszcza 0 albo 89 krawędzi
  z 11,5 t, żadnych innych limitów). Lustrzane testy NUnit w `game/Assets/_Project/Tests/EditMode/NavTruckLimitsTests.cs`
  (nieuruchamiane: Unity niepotrzebne w tym zadaniu).
- Testy mutacyjne: usunięcie `maxaxleload` z `TRUCK_LIMIT_TAGS` -> **7 testów czerwonych** (pytest); usunięcie warunku osi z
  `RoutePlanner.EdgeAllowed` -> **2 testy czerwone** (nav-runner).
- `tests/gis -k "road or graph or nav"` na obecnych danych: zielone. Po podmianie `roads.graph.json` bez regeneracji raportów
  `test_report_not_stale` (fidelity_qa) słusznie czerwony: dlatego graf i `.bytes` nie są w tym commicie.

## Co musi zrobić lider (nie commitowałem danych)
`Data/**/generated/**` i `.bytes` poza zakresem zadania. Po scaleniu: `uv run tools/worldgen/build_region.py --region
bialystok-industrial-c` (przeparsuje PBF raz, nowy graf z +89 atrybutami `maxaxleload`), raporty QA/fidelity zgodnie z
dotychczasowym przepływem, następnie `uv run --project tools/worldgen tools/worldgen/navgraph/build_route_graph.py --region
bialystok-industrial-c` (nowe `*_route.bytes`; zmiana tylko 89 pól `maxaxleload_c`). Potem `pytest tools/worldgen/navgraph/tests`
(w tym `test_region_file_is_reproducible`) i nav-runner powinny być zielone; trasy wzorcowe bez zmian.

## Ograniczenia i ryzyka
- Nie dodano `maxweight:conditional`, `maxheight:conditional`, `goods`, `toll:hgv` ani `delivery` (poza zakresem; G10 wskazuje
  je jako kolejne).
- Zakazy godzinowe nie wpływają na trasę, bo planer nie zna czasu gry. Gdy pojawi się zegar zleceń, flaga `F_HGV_TIMED` jest
  gotowym wejściem (okna godzinowe trzeba by wtedy zakodować w sekcji v3, na razie 0 takich krawędzi w danych).
- Przy rozszerzaniu regionu: 26 dróg `maxaxleload=10` w ekstrakcie zostanie wykluczonych z tras ciężarówki. To zgodne z OSM, ale
  OSM-only (G10: bez potwierdzenia znakiem), więc przed uznaniem za prawdę drogową zweryfikować zdjęciami (B-18/B-19 UNVERIFIED).
- Wartość 11,5 t jest cytowana, nie zmierzona (UNVERIFIED), jak w `docs/VEHICLE_REFERENCE_DATA.md`.

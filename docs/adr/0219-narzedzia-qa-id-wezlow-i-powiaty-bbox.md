# ADR 0219 — narzędzia QA dla wszystkich regionów: jeden parser id grafu i jeden wybór powiatów dla bbox
Status: Proposed (agent chmury C, s21, gałąź `qa-tools-0219`), 2026-11-15. Do scalenia przez lidera.
Powiązane: ADR 0075 (fidelity), 0085 (far_field), 0070 (lod2_extract), 0204, 0208 („Otwarte” pkt 6), 0210/0213 (woda).

## Kontekst
(a) `tools/worldgen/fidelity/run.py` padał dla `bialystok-dojlidy` w `metrics.node_arm_check`:
`int(str(n).lstrip("n"))` dla węzła `Bw443103344:…`. `lstrip` usuwa **zbiór znaków**, nie prefiks.
(b) ADR 0208 pkt 6: `far_field.py` i `lod2_extract.py` miały powiat 2061 na sztywno, a `water.py` czytał tylko
`region["teryt_powiat"]`, więc część obszaru w drugim powiecie nie dostawała danych BDOT10k / LoD1 / LoD2.

## Ustalenia (policzone na danych w gicie, bez Data/raw)
- **Formaty id węzłów** (wszystkie 15 `Data/Regions/*/roads.graph.json` + `route_start.json`, skrypt w teście):
  `n<osm_node>` (węzeł OSM w kaflu) oraz `B<edge_id>:<k><s|e>`: **syntetyczne cięcie granicą kafla** z
  `roadgraph.build` — początek (`s`) / koniec (`e`) kawałka `k` krawędzi `w<way>:<a>-<b>` przyciętej do kafla;
  węzeł ma `boundary: true` i **nie ma węzła OSM** (leży między węzłami a i b drogi). Krawędzie: `w<way>:<a>-<b>[#k]`.
  Trasa startowa każdego regionu poza C zaczyna i/lub kończy się na takim cięciu (C: 30 węzłów, 0 cięć;
  Dojlidy: 16 + 2; wszystkie regiony w teście).
- **Powiaty (PRG GUGiK, warstwa `A02_Granice_powiatow`)** — udział powierzchni kafla / pierścienia far_field
  (±4200 m od kotwicy; `powiaty.py --report`):
  | region | rejestr | kafel | pierścień far_field |
  |---|---|---|---|
  | bialystok-industrial-c | 2061 | 2061 100 % | 2061 72,07 %, 2002 27,93 % |
  | bialystok-dojlidy | 2061 | 2061 100 % | 2061 66,16 %, 2002 33,84 % |
  | bialystok-maczka | 2061 | 2061 100 % | 2061 69,84 %, 2002 30,16 % |
  | bialystok-kleeberga | 2061 | 2061 100 % | 2061 51,04 %, 2002 48,96 % |
  | bialystok-knyszynska | 2061+2002 | 2002 68,71 %, 2061 31,29 % | 2002 66,37 %, 2061 33,63 % |
  | dk65-01 / dk65-02 | 2002 | 2002 100 % | 2002 83,53 / 89,15 %, 2061 16,47 / 10,85 % |
  | dk65-03…05 | 2002 | 2002 100 % | 2002 100 % |
  | knyszyn / knyszyn-w | 2008 | 2008 100 % | 2008 91,25 / 94,57 %, 2002 8,75 / 5,43 % |
  | **knyszyn-s** | **2008** | **2008 77,13 %, 2002 22,87 %** | 2008 82,95 %, 2002 17,05 % |
  | dk65-monki-01 / dw671-tykocin-01 | 2008 | 2008 100 % | 2008 98,41 / 92,22 %, 2002 1,59 / 7,78 % |
  Skutek starego kodu (manifesty far_field w gicie): `knyszyn`, `knyszyn-s`, `knyszyn-w`, `dk65-monki-01`,
  `dw671-tykocin-01` mają w far_field **0 budynków i 0 lasów** — czytany był tylko BDOT 2061, a OSM tylko w stałym
  oknie Białegostoku 23,08–23,30 E / 53,10–53,24 N. W C pierścień w 2002 (28 %) pochodził wyłącznie z OSM.
  Przyczyna to nie wybór po centroidzie, tylko **stały kod 2061** (far_field, lod2) i **jeden kod z rejestru** (woda).

## Decyzja
1. **Jeden parser id** w `tools/worldgen/roadgraph.py` (tam, gdzie id powstają): `parse_node_id` → `NodeRef`
   (`kind` `osm` / `boundary`, `osm_node`, `osm_way`, `way_nodes`, `piece`, `end`), `edge_osm_way`, oraz
   `osm_node_id` / `boundary_node_id` używane przez `build` (te same napisy co wcześniej). Nieznany format = `ValueError`.
   `fidelity/metrics.way_of` i `edge_sides.py` używają parsera (bez `lstrip`).
2. **Cięcia granicy w `node_arm_check` są pomijane jawnie**: wiersz zostaje w `route_node_arms` z
   `"skipped": "tile_boundary"`, `osm_degree: null`, `osm_way`; log `run.py` podaje liczbę pominiętych.
   Dopasowanie po geometrii odrzucone: cięcie leży w środku drogi OSM (stopień OSM byłby 2 z definicji, a węzeł grafu
   ma stopień 1) — porównanie nic nie mierzy. Wiersze węzłów `n…` są **identyczne** jak przed zmianą (C się nie zmienia).
3. **Jeden wybór powiatów dla bbox**: `tools/worldgen/powiaty.py` — `powiaty_for_bbox(bbox)` (każdy powiat o dodatniej
   wspólnej powierzchni, największy udział pierwszy), `powiat_shares`, `ring_bbox`, `package_files` (ścieżki z
   manifestów), `merge_layers`. Granice: PRG (WFS GUGiK), przycięte do AOI 740000–800000 E × 575000–635000 N,
   uproszczone 2 m (`WORKING_VALUE`), w gicie: `Data/Admin/powiaty_prg.geojson` (139 KB) + manifest
   `Data/SourceManifests/gugik-prg-powiaty.json`. Bbox poza AOI = błąd z komendą ponownego pobrania.
   - `far_field.py`: BDOT10k i LoD1 **każdego powiatu pierścienia**; kolejność = udział, pierwszy powiat czyta jak
     dotąd, następne dokładają tylko nowe `LOKALNYID` / `buildingId`. Brak paczki na dysku → `ring_powiaty_missing`
     w manifeście (nie po cichu). Okno OSM = bbox pierścienia w lon/lat + 0,08° / 0,05° (dla C zawiera stare okno).
     Cache `far-field-gis-cache/12`.
   - `lod2_extract.py`: LoD2 każdego powiatu okna; brak paczki → ostrzeżenie + `powiaty_missing` w JSON.
   - `water.py` (**strefa 0213 — punkt do koordynacji**): zmienione wyłącznie wybranie powiatów w `extract()`
     (pętla po `powiaty_for_bbox` + `merge_layers`); jeden powiat = to samo wywołanie i ten sam wynik.
     Dziś wodę ma tylko `dk65-02` (2002, 100 %) → bez zmiany.
4. `streetscape/sources.py`, `build_region.py`, `ingest.py` nadal czytają rejestr `Region.powiaty` (ADR 0208) — poza
   zakresem; test pilnuje, że rejestr = PRG dla kafla z jednym znanym wyjątkiem (`knyszyn-s`, niżej).

## Konsekwencje
- C: `fidelity_qa.json` bez zmian (wiersze `n…` identyczne, wejścia `inputs_sha256` liczone z `roads/*.py` —
  nie zmienione). **far_field C (i każdego regionu) zmieni się po regeneracji**: BDOT/LoD1 2002 w północnej części
  pierścienia zamiast samego OSM; dla Knyszyna/Mońki/Tykocina pojawią się budynki i lasy. Wymaga budżetu
  (`test_far_field`: Low ≤ 30 000 tris; C dziś 24 548, maczka 25 621) i oględzin kamer — komendy w PR.
- Nie uruchomiono: fidelity, far_field, lod2_extract, water (wymagają Data/raw).

## Walidacja po regeneracji (c-regen-s22, 2026-11-15)
Raport: `docs/reports/INTEGRATION-2026-11-15-c-regen-s22.md`. Uruchomione z Data/raw (paczki 2002 i 2061 na dysku):
- far_field C: `ring_powiaty` [2061, 2002], `ring_powiaty_missing` []; Low 24 548 → 25 389 (limit 30 000),
  High 118 588 → 122 016; przyrost w sektorze N (Low 3 949 → 4 726) i W (3 248 → 3 312). FIX 2 recenzji wykonany.
- far_field Dojlidy: ring [2061, 2002], missing []; Low 20 680 → 23 907, High 99 315 → 119 759.
- fidelity C exit 0: 30 węzłów trasy, 0 cięć; `fidelity_qa.json` różni się tylko `inputs_sha256` (overrides.yaml z
  0216b). fidelity Dojlidy exit 0 (wcześniej wyjątek): 18 węzłów, 2 cięcia `tile_boundary`; nowy `fidelity_qa.json`.
- `frame_estimate` C bez zmian (far_field nie wchodzi do szacunku kamer).
- pytest `tests/gis` pełny: 1496 pass / 1 fail — `…registry…[dk65-09]` (region dodany do main po tej gałęzi: rejestr
  2002, PRG 17,89 % kafla w 2008) → dopisany do `KNOWN_REGISTRY_GAPS`; `test_qa_tools_0219` poza tym zielony.
- Horyzont N w kamerach kontrolnych C zasłania las — zmiana niepotwierdzona wzrokiem (brak kamery).

## Otwarte
1. `knyszyn-s`: rejestr `teryt_powiat="2008"`, PRG: 22,87 % kafla w 2002 (komentarz w `regions.py` to przyznaje) —
   brak `teryt_powiat_extra=("2002",)`; strefa innego agenta, zgłoszone liderowi (test `KNOWN_REGISTRY_GAPS`).
2. Inne miejsca z założeniem „C” lub `lstrip`, poza zakresem: `far_field._road_exit_corridors` (korytarze wylotów z C na sztywno),
   `roads/consistency.py`, `roads/pipeline.py`, `roads/meshing.py` — `split(":")[0].lstrip("w")` na id krawędzi;
   dziś poprawne (id krawędzi zawsze `w<cyfry>:`), do zamiany na `roadgraph.edge_osm_way` przy najbliższej zmianie.
3. Nowy region poza AOI: `uv run --project tools/worldgen python tools/worldgen/powiaty.py --fetch --aoi …`.

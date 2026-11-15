# ADR 0217 — torowisko i przejazdy kolejowe w generatorze świata (opt-in `Region.rail`)
Status: Proposed (chmura C, s20/s21, gałąź `rail-0217`), 2026-11-15. Do scalenia przez lidera.
Powiązane: ADR 0210 (wzorzec etapu opt-in: woda), ADR 0212 „Otwarte 4” (brak przejazdu na DW671), ADR 0205 p. 1
(generator bez torów), K1 `research/dk65-knyszyn-refs/README.md` §(g) (linia nr 38 wzdłuż DK65), docs/06 §6 (budżety).

## Kontekst
Generator (`tools/worldgen/roads/build_world.py`) nie ma torów. Agent 0212 zgłosił, że linia kolejowa przecina DW671
ok. (758830, 610030) — droga jest przejezdna, przejazdu nie ma. K1 podaje linię nr 38 (zelektryfikowana 3 kV) 111–330 m
na L od DK65 w `dk65-01`/`dk65-02`. Etap „automatycznie, gdy są dane” zmieniłby istniejące kafle (jak przy wodzie,
ADR 0210) — odrzucone.

## Decyzja
1. **Opt-in per region**: `Region.rail: bool = False` (`regions.py`). `build_region.py` dopisuje do `region.yaml`
   klucz `rail: {enabled: true, sources: …}` i zapisuje `generated/rail_sources.json` **tylko** przy fladze.
   `build_world` uruchamia etap tylko przy `rail.enabled`. Bez flagi: żadna warstwa nie dostaje części, materiały
   `rail_*`, węzły GLB `rail_*`, klucz manifestu `rail`, pliki `rail_sources.json`/`rail.json` nie powstają.
   **Ta zmiana nie włącza żadnego regionu** (lista włączeń = pusta; test). Kafle zakazane (knyszyn*,
   bialystok-knyszynska, dk65-06…11) — nietknięte.
2. **Źródła** (`streetscape/rail.py`, `extract_osm`, OSM ODbL, kafel + 100 m, mały plik w gicie):
   - drogi `railway=rail` z tagami `gauge` (domyślnie **1435 mm**, `gauge_src: default`; wartość „1435;1520” → pierwsza),
     `tracks` (domyślnie 1, max 6), `service` (siding/yard/spur/crossover — budowane jak tor pojedynczy, zapisane),
     `usage` (main/branch/industrial… — tylko zapisane), `bridge` (profil liniowy między końcami, bez podpór),
     `electrified`, `ref`, `name`;
   - **pomijane z powodem w `skipped`**: `railway=disused|abandoned|construction|proposed|razed|narrow_gauge|
     light_rail|tram|…`, `railway=rail` z `disused=yes`/`abandoned=yes`, `tunnel=yes|building_passage`;
   - węzły `railway=level_crossing` z `crossing:barrier` (no/half/double_half/full/gate/…), `crossing:light`,
     `crossing:bell`, `crossing:saltire`, `supervision`; **`railway=crossing`** (przejście dla pieszych/rowerów)
     zapisane w `skipped` — generator nie ma siatki chodników przez tor.
3. **Profil toru**: główka szyny = wygładzony teren (gauss σ 15 m, WORKING_VALUE) + `TRACK_H` = 0,172 + 0,20 + 0,30 =
   **0,672 m** nad formacją; na przejeździe główka = jezdnia + 0,005 m (płyty), przejście liniowe na 25 m
   (WORKING_VALUE). W strefie płyt główki szyn biorą wysokość jezdni w swoim punkcie (spadek poprzeczny / daszek).
   Teren nie jest wycinany pod podsypkę — skarpa podsypki ciągnie się 0,30 m pod formację (`SKIRT_M`).
4. **Przekrój** (lokalnie, pas boczny w lewo = +):
   | element | wartość | źródło |
   |---|---|---|
   | prześwit toru | 1435 mm (lub `gauge` z OSM) | OSM Key:gauge; tor normalny |
   | szyna 60E1: wysokość / główka | 172 mm / 72 mm (prostopadłościan) | katalog 60E1 (EN 13674-1): 172 mm SOURCED; 72 mm jako szerokość główki **UNVERIFIED** |
   | podkład PS-94: długość | 2,60 m | Plastwil / katalog PS94/SB/60E1 |
   | podkład: szerokość / wysokość widoczna / wystaje nad podsypkę | 0,30 / 0,20 / 0,05 m | WORKING_VALUE |
   | rozstaw podkładów | 0,60 m | WORKING_VALUE (artykuł Baztech: przytwierdzenia PS-94 co 0,6 m; Id-1 nie sprawdzona) |
   | podsypka pod podkładem / ława / skarpa | 0,30 m / 0,40 m / 1:1,5 | WORKING_VALUE (0,30 „zalecane” w jednym źródle, nie Id-1) |
   | rozstaw osi torów (tracks ≥ 2) | 4,00 m | WORKING_VALUE (typowe minimum na szlaku, paragraf **UNVERIFIED**) |
5. **LoD** (warstwy/węzły GLB): `rail_lod0` — podsypka (trapez: korona + 2 skarpy) + podkłady (góra + 2 boki) + szyny
   (góra + 2 boki), stacje co 5 m; `rail_lod1` — podsypka + szyny co 10 m, podkłady jako pasek tekstury (UV0 = (bok m,
   wzdłuż m), co 0,60 m); `rail_lod2` — jeden płaski pas podsypki co 20 m. GLB High: LoD0–2; GLB Low: LoD1–2
   (`LOW_EXCLUDE`). Pod płytami przejazdu podsypki i podkładów nie ma.
6. **Przejazd w poziomie jezdni**: z węzłów `railway=level_crossing` (≤ 8 m od osi toru) + przecięcia osi toru z osiami
   jezdni naziemnych (bez odcinków mostowych; duplikat ≤ 10 m od węzła OSM odrzucany; bez węzła OSM → ostrzeżenie,
   rogatki nieznane, oznakowanie jak kat. D). Strefa płyt = oś toru ∩ (obrys jezdni + 0,5 m). **Płyty** (materiał
   `rail_crossing_panel`, betonowo-gumowe, bez marki): na szerokość podkładu (±1,30 m od osi skrajnego toru),
   siatka co 2 m wzdłuż toru, przerwa 0,07 m + główka przy każdej szynie (żłobek), wysokość = jezdnia + 0,005 m.
7. **Markery** (`generated/rail.json` → `markers`; pozycja E/N/Z lokalnie, `heading_deg` = azymut, w który patrzy
   lico/ramię, zgodnie z ruchem wskazówek od N = obrót Y w Unity), po jednym na wlot:
   - `sign` **G-3** (1 tor) / **G-4** (≥ 2 tory, suma `tracks` wszystkich dróg kolejowych przy przejeździe) — tylko
     gdy brak rogatek (`crossing:barrier` brak/`no`), zgodnie z Dz.U. 2015 poz. 1744 § 5 (G-3/G-4 przed przejazdami
     kat. A bez rogatek, C i D); jawny `crossing:saltire` ma pierwszeństwo. Słupek po prawej stronie wlotu,
     3,0 m przed krawędzią płyt, 1,0 m za krawędzią jezdni (WORKING_VALUE). Ramię 1,20 × 0,20 m, kąt 50°, dolna
     krawędź 1,50 m — **WORKING_VALUE** (rysunku G-3 z rozporządzenia o znakach nie sprawdzono);
   - `barrier`: `half` → 1 ramię na wlot (wjazd, prawy pas, długość ½ jezdni + 0,5 m), `double_half` → 4 (wjazd +
     wyjazd), `full`/`gate` → 1 na wlot przez całą jezdnię; słupek 2,0 m przed płytami (WORKING_VALUE);
   - `light` (`crossing:light=yes`) na słupku znaku każdego wlotu; `bell` — jeden przy przejeździe.
8. **Skrajnia**: uproszczony przekrój (szer. 4,40 m od 0,4 do 4,0 m nad główką, zwężenie do ±1,60 m na 6,0 m) —
   **UNVERIFIED** (do zastąpienia obrysem z PN-K-02057 / Id-1). Zapisana w `rail.json` (`clearance`), używana do QA
   (`min_marker_distance_m` > 2,20 m — test) oraz jako obrys: `Plan.footprint()` = oś ± max(korona + 1 m, skrajnia)
   blokuje drzewa (hook w `streetscape/stage.py`).

## Budżet trójkątów
Wzór (tor bez przejazdów, n torów pod jedną podsypką, Δs = krok stacji LoD, a = 0,60 m rozstaw podkładów):
- LoD0 = (1000/5)·(6 + 6·2n) + (1000/a)·6n → **13 600 / km** (n = 1), 26 000 / km (n = 2)
- LoD1 = (1000/10)·(6 + 6·2n) → **1 800 / km** (n = 1), 3 000 / km (n = 2)
- LoD2 = (1000/20)·2 → **100 / km** (niezależnie od n)
- przejazd: ⌈(B/sinθ + 2·0,5)/2⌉·(2n + 1)·2, B = szer. jezdni → 7 m, 90°, 1 tor: **24**; 2 tory: 40; 10 m pod 60°: 42.
  Szyny w strefie płyt dochodzą (≈ 6 stacji × 6 tris × 2n).
Zmierzone na syntetycznym kaflu (test): 1 km, 1 tor bez przejazdu — LoD0 13 602 (200·18 + 1667·6), LoD1 1 800,
LoD2 100 = wzór (LoD0 ±6 przez liczbę podkładów).

Porównanie z docs/06 §6 (hipoteza Samsung A: ≤ 400–600 tys. tris, ≤ 300–400 draws w kadrze): przy przełączaniu
LoD per chunk 256 m (jak teren) najgorszy kadr wzdłuż toru = 2 chunki LoD0 (512 m) + 2 chunki LoD1 + reszta LoD2:
1 tor ≈ 0,512·13 600 + 0,512·1 800 + 1,5·100 ≈ **8,0 tys.** tris (≤ 2 % dolnej granicy budżetu), 2 tory ≈ 15 tys.
W GLB Low LoD0 nie ma (sam LoD1: 0,512·1 800 ≈ 0,9 tys. na chunk). Draws: ≤ 4 na chunk z torem i przejazdem w LoD0
(podsypka, podkłady, stal, płyty), 3 w LoD1, 1–2 w LoD2. Telefon: nie mierzono.

## Walidacja
- `tests/gis/test_rail_0217.py` (syntetyczne OSM, bez Data/raw): opt-in (żaden region nie włączony, brak kluczy/plików
  w `region.yaml` i `world_manifest.json` wszystkich regionów), strażnicy w build_world/stage/build_region, puste
  warstwy nie zmieniają `assemble`, klasyfikacja tagów (gauge/tracks/service/disused/tunnel, level_crossing vs
  crossing), trójkąty per LoD = wzór (1 i 2 tory), prześwit 1435 mm, trapez 1:1,5, orientacja ścian, płyty na
  wysokości jezdni (ze spadkiem 2 %), szyny zlicowane, brak podsypki pod płytami, G-3 vs G-4 (tracks=2 oraz dwie
  drogi kolejowe), rogatki no/brak/half/double_half/full (0/0/2/4/2 ramion, długości), światła/dzwon, pominięcie
  `railway=abandoned`, footprint blokuje roślinność, próbnik `road_z` poza jezdnią.
- Determinizm: kod etapu jest wyłącznie za `RL.enabled(...)` / `w.rail is not None`; nowe pozycje w `LAYERS`/`NODES`
  dla regionów bez toru są puste, więc GLB i manifest bez zmian. **Nie sprawdzone pełnym build_world** (brak Data/raw
  w chmurze) — komenda dla lidera niżej.
- `test_road_fidelity::test_report_not_stale` pada, bo `fidelity_qa.json` C hashuje `build_world.py` (zmieniony
  tutaj); wynik C się nie zmienia, ale raport trzeba odświeżyć z Data/raw:
  `uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region bialystok-industrial-c`.
- Ocena wizualna: nie wykonana (brak Unity/GPU) — do lidera.

## Integracja z Unity (lider)
Eksport idzie przez istniejące GLB chunków (glTFast), więc w `game/` potrzeba:
1. `RegionImporter.k_HighLayers` += `rail_lod0`, `rail_lod1`, `rail_lod2`, `rail_crossing`; `k_LowLayers` += `rail_lod1`,
   `rail_lod2`, `rail_crossing` (materiały `rail_*` z manifestu idą zwykłą ścieżką PBR — bez osobnego shadera).
2. `WorldSceneBuilder` listy LOD (l. 284–294): LOD0 High `rail_lod0` / Low `rail_lod1` + `rail_crossing`; LOD1 `rail_lod1`
   + `rail_crossing`; LOD2 `rail_lod2` + `rail_crossing`; LOD3 `rail_lod2`. Bez rzucania cieni dla LoD2.
3. Markery `generated/rail.json` → prefaby (krzyż G-3/G-4, rogatka, sygnalizator, dzwon) — nowe zadanie (asset +
   spawner jak instancje); kolizja ze skrajnią opcjonalnie.
4. `Gate3Audit` / `mesh_budget` (streetscape_qa) nie liczą `rail_*` — dopisać.

## Odtworzenie (lider, po włączeniu `rail=True` w wybranym regionie)
```
uv run --project tools/worldgen tools/worldgen/build_region.py --region dw671-tykocin-01
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region dw671-tykocin-01
uv run --project tools/worldgen python scripts/export-route.py --region dw671-tykocin-01
pwsh scripts/import-region.ps1 -Region dw671-tykocin-01 -Build
pwsh scripts/visual-qa.ps1 -Scene World_dw671-tykocin-01 -Tier Low -Lighting clear -OutputDir artifacts/rail-0217/vqa/dw671-tykocin-01/Low
pwsh scripts/visual-qa.ps1 -Scene World_dw671-tykocin-01 -Tier High -Lighting clear -OutputDir artifacts/rail-0217/vqa/dw671-tykocin-01/High
# scena = World_<region> (WorldC to wyłącznie bialystok-industrial-c); kamery przejazdu: -Cameras rail_xing_top,rail_xing_above,...
uv run --project tools/worldgen python -m pytest -q tests/gis/test_rail_0217.py   # po włączeniu: zaktualizować listę `on`
```
Determinizm C/Dojlidy (bez flagi): `build_world` dla `bialystok-industrial-c` i `bialystok-dojlidy` →
`git diff --stat Data/Regions/*/generated` = pusto.

## Otwarte
1. **Włączenie**: proponowane `dw671-tykocin-01` (przejazd DW671 z 0212; kafel spoza listy zakazanej), potem `dk65-01`
   i `dk65-02` (linia 38, K1; w `dk65-02` most kolejowy nad Supraślą = `bridge=yes` bez podpór). Zmienia wynik tych
   kafli (nowa linia bazowa) — decyzja lidera.
2. Wymiary G-3/G-4 i odległości ustawienia, skrajnia, podsypka/rozstaw wg Id-1 — do sprawdzenia w tekstach źródłowych
   (WORKING_VALUE/UNVERIFIED wyżej).
3. Teren pod torem nie jest profilowany (nasyp/przekop); na stromym terenie podsypka może wisieć > 0,3 m — QA po
   pierwszym kaflu (`rail.json` + render).
4. Brak: słupków G-1a…f przed przejazdem, znaków A-9/A-10, linii P-12 przed rogatkami, sieci trakcyjnej (3 kV),
   rozjazdów, peronów, mostów kolejowych z podporami, przejść dla pieszych `railway=crossing`.
5. Bardzo skośne przejazdy: sinθ obcięty do 0,2 (≈ 11,5°) przy liczeniu szerokości jezdni.

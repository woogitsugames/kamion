# ADR 0186 — Dojlidy: zieleń i kadr P11-063 (Mickiewicza / Kuronia)
Status: Proposed (agent world-builder, s20, gałąź `dojgreen-0186` = main + `origin/horizon-0170`), 2026-11-13/14.
Poprzednik: ADR 0179, recenzja `docs/reports/REVIEW-2026-11-13-s19-0179.md` (P11-063: N/P — „inny kadr, brak
zielonej ściany”). Zakres: tylko region `bialystok-dojlidy`; las przy lotnisku (ADR 0187) nietknięty.

## Kontekst
Recenzja s19 0179, kadr P11-063 (CC0, Rakoon 2024-06-23): (1) kępa drzew narożnika to jedna sadzonka, (2) krzewy to
osobne kule liści, przez które widać auta, (3) maszt sygnalizacji stoi w środku kadru, a na zdjęciu przy prawej
krawędzi. Przyczyny znalezione w danych, nie w wyglądzie:
- **Kamera.** ADR 0174/0179 stawiały kamerę w punkcie GPS z Commons (lokalnie −46,5 381,8) i celowały 82° w centroid
  hali Kuronia 2. Punkt GPS leży na pasie rozdziału Mickiewicza. Resekcja z pięciu obiektów kadru (x w kadrze
  1600 px, f = 1255 px dla hFOV 65°) względem ortofoto 2024 / BDOT10k — narożnik W hali Kuronia 2 (47,8 337,4; x 1160),
  szafa sterownicza (−15,3 371,0; x 1102), maszt wysięgnikowy w pasie rozdziału (−35,5 368,0; x 1492), pień bliższego
  drzewa (−13,0 372,5; x 1037), para drzew za nim (−2,0 379,5; x 840) — daje **pozycję −67,0 393,5, azymut 100,0°**,
  reszty ≤ 0,2° (rozwiązanie z trzech pierwszych punktów trafia w oba drzewa na 0,2°). Kamera stała 23 m od
  właściwego miejsca i była obrócona o 18°. Pochylenie 8° (horyzont na y 630/900; było 10°). Pozycja masztu z
  ortofoto ±1,5 m przesuwa wynik o kilka metrów wzdłuż osi widzenia — WORKING_VALUE ±4 m.
- **Maszt w środku kadru** nie istnieje w terenie: reguła `junctions.build_junctions` uznaje skrzyżowanie za
  sterowane, gdy węzeł sygnalizacji OSM leży ≤ 25 m od jego środka. Zawrotka w pasie rozdziału (węzeł OSM
  3541204205) leży 20 m przed linią zatrzymania skrzyżowania z Kuronia, więc dostała 2 maszty i 3 słupy — dokładnie
  tam, gdzie stała kamera. Zdjęcie i ortofoto: przy zawrotce nie ma sygnalizacji.
- **Drzewa narożnika** (`tree_groups`, linia): wszystkie odrzucone przez regułę „3 m od nawierzchni” (trawnik między
  chodnikami); w kadrze została samosiejka 6 m.
- **Krzewy**: dwa rzędy instancji `tree_shrub` co 1,9–2,5 m — z definicji osobne korony na pniach.

## Decyzja
1. **Kamera `photo_P11-063`**: `pos_en [-67.0, 393.5]`, `heading_deg 100`, `pitch_deg 8` (dane; `basis` opisuje
   resekcję; test `test_camera_063_looks_at_the_frame` liczy x pięciu obiektów z pozycji kamery).
2. **`tree_groups.points_en`** (`vegetation.py`, opt-in): pnie wskazane pojedynczo `[E, N]` albo `[E, N, wysokość]`,
   `height_m: [lo, hi]` dla punktów bez własnej wysokości. Odmowa tylko na samej jezdni / nawierzchni / budynku
   (siatka `hard` = maska przed dylatacją 3 m, nowy parametr `place(..., hard=None)`), raport `points_refused`;
   wskazany pień wygrywa przerzedzanie 1,8 m z drzewem reguły. Narożnik: 4 klony/lipy — 10,5 m (zmierzone na
   zdjęciu: 190 px szerokości korony z 58 m ≈ 8 m, wysokość ≈ 10,5 m) i 9,0–9,8 m (WORKING_VALUE, częściowo zasłonięte).
3. **Gatunek nasadzeń `thicket`** (`plantings.SPECIES` + profil `thicket`, opt-in): zarośla jako jedna bryła —
   ciemny rdzeń od gruntu (−5 cm), powłoka liści alfa, krzewy co 1,1–1,7 m jako garby boku 0,4 m, `gap_p = 0`
   (brak brakujących roślin → nic nie prześwituje), zaokrąglony bark, luźne pędy 0,3–0,65 m. Tekstury grabu z
   istniejącego zestawu żywopłotów — **bez nowych materiałów**. Pas krzewów P11-063: 7 zachodzących na siebie
   mas 2,3–3,2 m (oś z ADR 0179, szer. 3,8–4,8 m) jako `kind: plantings` zamiast dwóch rzędów `tree_shrub`.
4. **Nadpisanie węzła `set: {signalized: false | true}`** (`junctions.py`, opt-in) — zawrotka `n3541204205` nie jest
   sterowana. **Maszt w pasie rozdziału** jako `gate3_signal` (−35,5 368,0; ramię nad jezdnią w stronę SW).
5. **Poprawka Round 2 — drzewa `form: kit` i szpaler 31-płatowy**: przejście z drobnych drzew regułowych w narożniku na dojrzałe drzewa `form: kit` (`authored_trees`: 5 drzew narożnych, zamiast zarysowanych w r1 punktów `tree_groups`) oraz z drobnej siatki krzewów z r1 na 31 zachodzących na siebie owalnych płatów `thicket` (`plantings`: `hedges: 31`, `hedge_m2: 728.9`, `shrubs: 0`, `stale: []`, `tris: 20022`).
6. **Poprawka Round 3 — lewa krawędź `photo_P11-063` i `junctions.py`**:
   - W `B-r2` pojedyncze drzewo proceduralne (`tree_maple`, 10,2 m przy `(-23.51, 407.8)`) wyrastało ponad wiatę przystankową przy lewej krawędzi kadru. Dodano wpis `open_ground` `mickiewicza-kuronia-shrub-strip-no-rule-trees` (`area_m2: 837.0`, `trees_removed: 1`), który usuwa regułowe drzewa z pasa krzewów przy narożniku Mickiewicza / Kuronii (po przebudowie `0` instancji drzew w prostokącie `[-60..20, 365..470]`), oraz wpis `kuronia-north-park-skyline-trees` (`authored_trees`, `form: kit`) z liściastym tłem za szpalerem 31-płatowym.
   - W `B-r3` w `streetscape_qa.json`: `authored_trees` = `8` drzew (`tris_high: 320`, `tris_low: 160`, `skipped: {}`), `plantings` = `hedges: 31` (`hedge_m2: 728.9`, `shrubs: 0`, `stale: []`, `tris: 20022`), `vegetation.tree_groups` = `rule_trees_at_kit_stems: 3`; łącznie `-68` drzew regułowych względem stanu `A-r1` sprzed scalenia.
   - W `tools/worldgen/roads/junctions.py` dodano nadpisanie węzła `set: {signalized: false | true}` użyte dla `n3541204205`, zachowując maszt `gate3_signal` (`−35,5 368,0`).
7. **Poprawka Round 4 (`B-r4`) — naprawa 3 problemów P1 z recenzji `REVIEW-ARGON-dojgreen-0186.md`**:
   - **P1-1 (Piczaste „namioty” w górnym obrysie `thicket`)**: w `SPECIES["thicket"]` (`tools/worldgen/streetscape/plantings.py`) zagęszczono próbkowanie obwiedni i wypełnienia wnętrza (`ring_step=0.45`, `fill=(1.2, 0.75)`), włączono lokalną interpolację stropu `local_top=True` oraz spłaszczono relief (`dome=0.24`, `bulge=0.28`). W `Data/Regions/bialystok-dojlidy/overrides.yaml` (`mickiewicza-kuronia-shrub-band`) wygładzono wysokości 31 płatów do łagodnych przejść `2,1–2,75 m` (maks. skok między sąsiednimi płatami w rzędzie `≤ 0,25 m`).
   - **P1-2 (Czarne poziome pasy cienia własnego na `thicket` w High)**: w `SPECIES["thicket"]` oraz `hedge_mass()` zmniejszono rozmiar i zagęszczenie luźnych kart pędów (`sprig=0.70`, `sprig_wh=((0.42, 0.75), (0.38, 0.68))`, `top_sprigs=0.40`) oraz ustawiono bardziej strome pochylenie kart bocznych (`side_tilt=(0.35, 0.80)`, `side_share=0.18`), eliminując poziome „półki” rzucające czarne pasy cienia na High przy zachowaniu pełnej szczelności dolnych 2 m.
   - **P1-3 (Drzewa i krzewy narożnika `mickiewicza-kuronia-corner-trees`, szew `"X"` na Low i kant karty na High)**: w `overrides.yaml` zastąpiono trzy powtarzalne `6,0–6,5 m` drzewka na gołych pniach po lewej stronie krzewami i niskimi formami schodzącymi do gruntu (`[-12.5, 387.8, 2.8, 4.5, berberis_red]` — bordowo-czerwony krzew przy wejściu ścieżki widoczny na `P11-063.jpg`, `[0.6, 381.0, 4.2, 4.2, shrub]` oraz `[-3.2, 378.8, 5.2, 4.4, fruit]`). Dla dojrzałych drzew (`9,2 m` i `10,5 m` `ash` oraz `14,0–15,0 m` `kuronia-north-park-skyline-trees`) w `authored_trees` (`_authored_kit_plant` / `_kit_quad`) zastosowano wielopłatowe, ażurowe korony z 2-trójkątnymi kartami bez wachlarza `occ_mid` `[0,0,1]` i z bocznymi kartami głębi cofniętymi za przednie płaty (`-0.42 r f`), co całkowicie usuwa jasny/ciemny szew `"X"` na Low i pionową kreskę karty ustawionej kantem na High (`authored_trees`: `trees: 8`, `tris_low: 100`, `tris_high: 300`, `rule_trees_at_kit_stems: 3`).

Region C: żadnego z tych wpisów nie ma w jego danych (`test_region_c_uses_none_of_it`), kod bez wpisu idzie starą
ścieżką.

## Budżet i pamięć (Low + High, A/B)
### `WORLD_MEMORY` po imporcie (`-Tiers Low,High`, `materialTier Medium`)
Baza `A-main` z logu `artifacts/lead-s20/import-dojlidy.log` (stan `origin/main` z 0183 i 0196 w głównym repozytorium); gałąź `B-r4` z `artifacts/dojgreen-0186/B-r4/import.log`:

| Tier | Metryka | `A-main` (`origin/main`) | `B-r3` (`dojgreen-0186`) | `B-r4` (`dojgreen-0186`) | Delta (`B-r4 − A-main`) |
|---|---|---|---|---|---|
| Low | `render_meshes` | `64.5 MB` | `65.1 MB` | `65.2 MB` | `+0.7 MB` (zaokr.) |
| Low | `furniture` / `plots` | `7,8 MB` / `2,2 MB` | `8,3 MB` / `2,2 MB` | `8,4 MB` / `2,2 MB` | `+0,6 MB` / `0,0 MB` |
| Low | `instances` / `collision_src` | `18.2 MB` / `15.5 MB` | `18.2 MB` / `15.5 MB` | `18.2 MB` / `15.5 MB` | `0.0 MB` / `0.0 MB` |
| Low | `total` | `98.2 MB` | `98.7 MB` | `98.8 MB` | `+0.6 MB` |
| High | `render_meshes` | `179.8 MB` | `180.3 MB` | `180.5 MB` | `+0.7 MB` |
| High | `furniture` / `plots` | `7,8 MB` / `2,8 MB` | `8,3 MB` / `2,9 MB` | `8,4 MB` / `2,9 MB` | `+0,6 MB` / `+0,1 MB` |
| High | `instances` / `collision_src` | `18.2 MB` / `15.5 MB` | `18.2 MB` / `15.5 MB` | `18.2 MB` / `15.5 MB` | `0.0 MB` / `0.0 MB` |
| High | `total` | `213.5 MB` | `214.0 MB` | `214.1 MB` | `+0.6 MB` |

- `WORLD_TERRAIN_BAND`: bez zmian (`fine fraction Low 31 % High 37 %`). Pozostałe kategorie na obu tierach bez zmian (`terrain 28,6 / 119,6 MB`, `road 9,0 MB`, `markings 1,4 MB`, `paved 2,6 MB`, `buildings 10,7 / 29,9 MB`, `plot_ground 1,1 MB`, `wires 0,1 MB`, `far_field 1,1 / 5,5 MB`).
- `artifacts/world/bialystok-dojlidy-import.json`: `instances: 111077` (w `A-r1` przed scaleniem `origin/main`: `111074`), `prop_colliders: 1641`, `pbr_textures_gpu_bytes_astc: 42611097` (`40,64 MiB` w `44` istniejących zestawach `materials_spec.json`, w tym `hedge_foliage` i `soil_bed` obecne już na `origin/main` po `121 460 B` ASTC mips w `Medium` 256×256, `21 845 B` w `Low`, `622 155 B` w `High`; `0` nowych zestawów tekstur lub materiałów w `dojgreen-0186`).

### Kadry VQA w edytorze Unity (`lighting=overcast`, `1920×1080`)
Dla porównania Low zestawiono `A-r1` (stan worktree przed scaleniem `origin/main`: `artifacts/dojgreen-0186/A-r1/Low-overcast-photo/stats.txt`), `dojind-0196 r4` (stan `origin/main` z `0183` i `0196` przed `0186`: `artifacts/dojind-0196/r4-Low-overcast/stats.txt` w głównym repozytorium) oraz `B-r4` (`artifacts/dojgreen-0186/B-r4/Low/stats.txt`). Dla High podano pełne odczyty `B-r4/High/stats.txt`.

#### Tier Low (`tier=Low msaa=2 renderScale=0.75`)
| Kadr | `A-r1` draws / trisExact (inst draws / tris) | `dojind-0196 r4` (`A-main` Low) draws / trisExact (inst draws / tris) | `B-r4` draws / trisExact (inst draws / inst / cells / HLOD / tris) |
|---|---|---|---|
| `photo-P11-063` | `obj=47`, `drawsEst=262` (`sh=3`), `305 631` (`121` / `21 130`) | `obj=48`, `drawsEst=323` (`sh=3`), `342 810` (`117` / `15 862`) | `obj=49`, `drawsEst=279` (`sh=6`), `339 096` (`116` / `198` / `173` / `38` / `20 775`) |
| `photo-P11-001` | `obj=51`, `drawsEst=335` (`sh=104`), `462 860` (`52` / `9 272`) | `obj=51`, `drawsEst=341` (`sh=109`), `471 466` (`53` / `9 284`) | `obj=51`, `drawsEst=342` (`sh=109`), `464 422` (`53` / `40` / `154` / `10` / `9 296`) |
| `photo-P11-056` | `obj=33`, `drawsEst=125` (`sh=3`), `158 580` (`38` / `2 097`) | `obj=34`, `drawsEst=126` (`sh=3`), `159 781` (`36` / `2 061`) | `obj=34`, `drawsEst=125` (`sh=3`), `159 725` (`35` / `34` / `89` / `9` / `2 037`) |
| `photo-P11-094` | `obj=43`, `drawsEst=195` (`sh=44`), `288 046` (`93` / `16 996`) | `obj=43`, `drawsEst=199` (`sh=45`), `292 547` (`91` / `16 960`) | `obj=43`, `drawsEst=202` (`sh=45`), `293 717` (`92` / `69` / `163` / `47` / `17 032`) |
| `route-s1370` | — | — | `obj=44`, `drawsEst=334` (`sh=74`), `271 259` (`69` / `60` / `200` / `26` / `11 184`) |

Na docelowym kadrze `photo-P11-063` (Low) `B-r4` obniża `drawsEst` z `323` (`dojind-0196 r4`) do `279` (`-44`) i `trisExact` z `342 810` do `339 096` (`-3 714`) przy zachowaniu wszystkich elementów 0183 i 0196 oraz naprawionych wypełnień płotów na Low (`e668a9588`).

#### Tier High (`tier=High msaa=2 renderScale=1`) — `B-r4/High/stats.txt`
| Kadr | `objects` | `drawsEst` (`shadowDrawsEst`) | `trisK` (`trisExact`) | `instanced` (draws / instances / cells / HLOD / `trianglesExact`) |
|---|---|---|---|---|
| `photo-P11-063` | `86` | `461` (`138`) | `753` (`753 627`) | `208` / `492` / `277` / `86` / `92 231` |
| `photo-P11-001` | `76` | `457` (`363`) | `701` (`701 948`) | `139` / `361` / `154` / `10` / `33 038` |
| `photo-P11-056` | `58` | `210` (`18`) | `291` (`291 582`) | `108` / `218` / `95` / `9` / `9 719` |
| `photo-P11-094` | `169` | `513` (`195`) | `878` (`878 031`) | `190` / `387` / `469` / `215` / `68 646` |
| `route-s1370` | `76` | `489` (`360`) | `623` (`623 318`) | `153` / `429` / `203` / `28` / `44 534` |

## Walidacja
- **Build regionu `bialystok-dojlidy`** (`heavy` slot): `uv run --project tools/worldgen python tools/worldgen/roads/build_world.py --region bialystok-dojlidy` → exit `0`, czas `409,2 s` (`artifacts/dojgreen-0186/B-r4/build_world.log`, `plantings.tris = 27 363`, `authored_trees: 8`, `tris_low = 100`, `tris_high = 300`).
- **Testy ukierunkowane**: `uv run --project tools/worldgen python -m pytest tests/gis/test_dojgreen_0186.py tests/gis/test_dojlidy_0179.py -q` → `13 passed`.
- **Pełny `pytest tests/gis -q`** (`heavy` slot, log `artifacts/dojgreen-0186/pytest-gis.log`, czas `1248,77 s`): **`1155 passed, 2 xfailed, 3 failed`**. Wszystkie 3 niepowodzenia to znany stan nieświeżego Regionu C (`bialystok-industrial-c`) w worktree, niezwiązany z kodem `0186`:
  - `tests/gis/test_p1_0161.py::test_ring_mast_survives_the_carriageway_clearing` i `tests/gis/test_world_v31.py::test_forest_trees_reference_their_cell` czytają ignorowane przez Git pliki `Data/raw/derived/bialystok-industrial-c/world/instances_*.json`, nieodświeżone w worktree;
  - `tests/gis/test_road_fidelity.py::test_report_not_stale` zgłasza przestarzały hash `['tools/worldgen/roads/build_world.py', 'tools/worldgen/roads/junctions.py']` względem zacommitowanego `Data/Regions/bialystok-industrial-c/generated/fidelity_qa.json`.
- **Unity EditMode** (`pwsh -NoProfile -File scripts/test.ps1 -Platform EditMode`, `unity` slot, log `artifacts/dojgreen-0186/editmode.log`, wynik `artifacts/tests/editmode-20261114-190417.xml`): **`581 total, 580 passed, 0 failed, 1 skipped`** (`Skipped:Ignored`: `Game.Tests.GardenCanopyWidthTests.ImportedGardenWidthMatchesEverySerializedOptInRecord`).
- **Dowody renderów `B-r4` (Low + High, overcast)** w `artifacts/dojgreen-0186/B-r4/` oraz `artifacts/dojgreen-0186/`:
  - logi: `build_world.log`, `import.log`, `vqa-Low.log`, `vqa-High.log`;
  - statystyki i JPG (`960×540` RGB): `Low/{stats.txt,jpg/photo-P11-{001,056,063,094}.jpg,jpg/route-s1370.jpg}`, `High/{stats.txt,jpg/photo-P11-{001,056,063,094}.jpg,jpg/route-s1370.jpg}`;
  - zestawienia SBS (`1920×540` RGB): `B-r4/sbs-P11-{001,056,063,094}-{Low,High}.jpg` oraz `sbs-P11-063-{Low,High}.jpg`, `sbs-B-r4-{Low,High}.jpg`;
  - zbliżenia kontrolne (`zoom-thicket-{Low,High}.jpg`, `zoom-trees-{Low,High}.jpg`).
  - Oględziny wizualne (`read_file`): w `photo-P11-063` (Low i High) wszystkie 3 problemy P1 z recenzji `REVIEW-ARGON-dojgreen-0186.md` są naprawione — grzbiet `thicket` układa się w miękkie kopuły bez trójkątnych „namiotów” (P1-1), na High zniknęły czarne poziome pasy cienia własnego (P1-2), w narożniku po lewej stronie stoi bordowo-czerwony krzew `berberis_red` oraz niskie/średnie krzewy schodzące do gruntu zamiast „lizaków na patyku”, a dwa dojrzałe drzewa mają ażurowe wielopłatowe korony bez szwu `"X"` na Low i bez pionowej kreski kantu karty na High (P1-3); wypełnienia płotów na Low są widoczne po scaleniu `e668a9588`.

## Otwarte punkty
- Pola oznaczone do weryfikacji terenowej / M63 w `Data/Regions/bialystok-dojlidy/overrides.yaml` (gatunki i dokładna wysokość krzewów w pasie wzdłuż ul. Mickiewicza, dokładne wysokości i liczność drzew narożnych `form: kit` oraz tła `kuronia-north-park-skyline-trees`).
- Po scaleniu `dojgreen-0186` do `main`: regeneracja artefaktów Regionu C (`bialystok-industrial-c`, w tym odświeżenie `fidelity_qa.json` po zmianie `tools/worldgen/roads/junctions.py`) oraz pomiar wydajności na docelowym telefonie (Samsung A).

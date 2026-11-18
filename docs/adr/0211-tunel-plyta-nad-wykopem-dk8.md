# ADR 0211 — tunel / płyta nad wykopem (OSM `tunnel=yes`): rondo Szymańskiego nad DK8, ściany oporowe wykopu
Status: przyjęty (scalony do main 2026-11-15, `1990afc8d`; status zaktualizowany 2026-11-16); pierwotnie: Proposed (agent world-builder, s20–s22, gałąź `tunnel-0211`, baza main a594ef2aa, scalone origin/main 7f830369c; stan r5), 2026-11-15.
Powiązane: ADR 0206 (kafel `bialystok-kleeberga`, `keep_tunnel_cut`, override `bridge` łuków ronda), ADR 0110 (pasy
zieleni scalane z terenem), ADR 0064 (bake oświetlenia gruntu: `bridge` = bryła), ADR 0146 (ściany ramp).

## Kontekst
ADR 0206 przywrócił przejezdność DK8 pod rondem prof. Szymańskiego (teren trzymany pod jezdnią tunelową), ale bez
konstrukcji: wyspa i chodniki ronda były otwarte na wykop, łuki ronda (pomosty) od spodu jednostronne, wykop miał
trawiaste „ściany” z NMT. Pomiary (dev dump, `artifacts/tunnel-0211/probe_*.py`):
- NMT (klasa grunt LiDAR) przechodzi przez całą konstrukcję na poziomie wykopu — w obrysie płyty 75 % węzłów NMT jest
  < 1 m nad jezdnią DK8; wyspa ronda w terenie po conform też jest na dnie wykopu. Powierzchnie na poziomie terenu nad
  płytą (jezdnia ronda, płyty skrzyżowań, chodniki) stoją 5,75–6,2 m nad DK8; skarpy 5,3–5,7 m.
- Ortofoto 2024 0,25 m (`artifacts/tunnel-0211/ortho/rondo_240.jpg`): płyta nad całym skrzyżowaniem, portale przy
  zewnętrznych przejściach, pionowe ściany wykopu (ostry pas cienia) po obu stronach na całej widocznej długości
  (> 120 m od portali), między jezdniami bariera.

## Decyzja
Nowy etap generatora `tools/worldgen/roads/tunnels.py` (wywołany w `build_world` po podporach mostów, przed chunkami
terenu; **zastępuje** `keep_tunnel_cut`). Dla dróg `tunnel` ≠ `no`/`building_passage` (bez service/footway/…):
1. **Płyta**: obrys F = otoczka wypukła pasów jezdni tunelowych od portalu do portalu, do tyłu ścian zewnętrznych
   (tu 1682 m²). Zamknięta bryła w warstwie `bridge` (cień, bake nieba/słońca): wierzch (beton, 0,15 m pod gruntem),
   spód (`bridge_soffit`) na stałym prześwicie nad jezdnią, czoła portali, balustrada stalowa na krawędzi portalu
   (poza jezdniami). Prześwit = min(max(5 percentyl pokrycia − 0,80, 4,70), 5,00) → **4,70 m** (skrajnia pionowa
   4,70 m — rozporządzenie MI z 24.06.2022 w sprawie przepisów techniczno-budowlanych dróg publicznych; paragraf
   UNVERIFIED; grubość 0,80 m WORKING_VALUE).
2. **Grunt na płycie**: wysokość terenu nad F interpolowana (liniowo, poza otoczką najbliższy) z próbek „na poziomie
   terenu” w F + 8 m: pomosty ronda (−0,25 m), inne jezdnie/płyty skrzyżowań (−0,08 m), teren ≥ 4,5 m nad DK8 (górne
   krawędzie skarp); nie niżej niż jezdnia + 4,70 + 0,80; wypełniane tylko węzły poniżej poziomu terenu. Komórki
   terenu 1 m nad F i za ścianami są emitowane jako osobny prymityw `bridge`/`verge_grass` `tunnel:cover` (od r4 **nie**
   scalany z terenem: importer Unity `WorldMeshBake.TerrainBandData` odbudowuje teren bliski z węzłów siatki prymitywu
   terenu — max y na węzeł — i wierzchołki scalonej pokrywy podnosiły obniżone węzły: klif w portalach, „piramidki”
   za licem), z siatką-asekuracją 3 cm pod gruntem wokół pokrywy (szczeliny LOD 2 m); węzły terenu pod nim schodzą na
   dno (jezdnia − 0,35); grunt nad płytą wypełniany do F + 1,5 m; balustrada portalu także nad pasami DK8.
   Kolizja trawy (`collision_grass`) nad F i za ścianami (kolizja terenu jest tam obniżona).
3. **Ściany**: zewnętrzne ściany tunelu (dno → spód płyty + 0,3), ściana środkowa między jezdniami (WORKING_VALUE,
   czoła na portalach), **ściany oporowe wykopu** wzdłuż obu zewnętrznych krawędzi DK8 poza portalami wszędzie, gdzie
   skarpa za licem ≥ 1,0 m nad stopą (przerwy ≤ 14 m domykane; ściana przerywa się tylko na drodze zjeżdżającej do
   wykopu). Lico 0,3 m za końcem profilu pobocza (wygładzone: bez uskoków przy zmianie krawężnik/pobocze), prefabrykaty
   `ramp_wall_panels`, tylna ściana (cień na jezdnię), oczep 0,5 m z kapinosem, balustrada 1,10 m tam, gdzie spadek
   ≥ 1 m, opaska betonowa od profilu pobocza do lica, kolizja `collision_fence`. Grunt za oczepem dociągnięty do
   wierzchu ściany (zasyp skarpy wykopu z NMT na 2 m za licem).
4. **LOD terenu ≥ 4 m** (`terrain_lod2` = kolizja terenu): pas do lico + 4,5 m trzymany na dnie
   (`chunks.build_chunks(low_cut=…)`), żeby trójkąt 4 m kolizji nie tworzył niewidzialnej rampy przed ścianą.
5. Łuki ronda nad F tracą `soffit/fascia/parapet/abutment/pier/screen` (niesie je płyta); instancje pod spodem płyty:
   należące do jezdni tunelowej (src łańcucha lub stoją na jezdni/poboczu) — wysokie (latarnie, drzewa, tablice,
   sygnalizatory, słupki znaków) usuwane; pozostałe (wyspa, chodniki) podnoszone o różnicę gruntu; pod pomostem — usuwane.
6. Regiony bez takich dróg (C, Dojlidy, maczka): `plan` → None, `build` → `({}, None)`, nic się nie zmienia (test).
7. **Wnętrze** (r5, `_dress_inside`): boczne pasy jezdni tunelowych (pobocze gruntowe: żwir + trawa z rowem) pod płytą
   oraz od strony ścian w wykopie stają się opaską brukowaną (`sidewalk_paving`, kolizja `collision_paving`; kształt
   przekroju bez zmian); bariery z reguł `furniture.guardrails` na jezdni tunelowej (reguła „obok obiektu” zostawiała
   8 m bariery z dwoma zakończeniami między ścianami tunelu) są pod płytą usuwane razem z kolizją.

## Budżet (kamery kontrolne kafla, `stats.txt` visual-qa, overcast 1920×1080; A = ADR 0206 r4, B = 0211 r5)
Szacunek edytora przed SRP batching (`drawsEst`, `trisK` w tys.); telefon nie mierzony (zakaz adb dla agentów).

| kamera | Low: draws A → B / tris A → B | High: draws A → B / tris A → B |
|---|---|---|
| `underpass-eb-szymanskiego` | 271 → 277 | 331 → 369 | 728 → 742 | 997 → 1038 |
| `underpass-wb-szymanskiego` | 378 → 391 | 348 → 384 | 597 → 617 | 943 → 984 |
| `produkcyjna-to-rondo-szymanskiego` | 383 → 395 | 408 → 444 | 650 → 671 | 873 → 915 |
| `route-s1110` | 395 → 408 | 346 → 382 | 604 → 624 | 937 → 978 |
| `route-s1427` | 295 → 299 | 221 → 222 | 422 → 431 | 592 → 609 |
| `tertiary-to-rondo-under-kleeberga` | 215 → 220 | 220 → 231 | 425 → 435 | 513 → 532 |
| `tunnel-eb-inside` | – → 275 | – → 325 | – → 679 | – → 908 |
| `tunnel-wb-inside` | – → 423 | – → 394 | – → 603 | – → 1006 |
| `cut-wall-oblique-sw` | – → 213 | – → 363 | – → 692 | – → 874 |
| `rondo-szymanskiego-island-nw` | – → 384 | – → 396 | – → 582 | – → 1100 |

Kamery poza wykopem (`route-s1427`, `tertiary-…`): Low +4…5 draws / +1…11 tys. trójkątów, High +9…10 / +17…19 tys.
Kamery przy tunelu: Low +6…13 draws / +36…38 tys., High +14…21 / +41…42 tys. (płyta, ściany oporowe ~450 m/stronę z
tylną ścianą, oczepy, balustrady, pokrywa gruntu, opaska brukowana). Uwaga: B zawiera też zmiany z main scalone po A
(276af6517, 7f830369c) — różnica A → B nie jest czystym kosztem tunelu (nie rozdzielano). Hipotezy `docs/06` §6: trójkąty w normie
(Low ≤ 400–600 tys., High ≤ 1,5–2 mln); `drawsEst` Low przy tunelu 270–420 wobec hipotezy ≤ 300–400 — kamery trasy były
na tej granicy już w A (378–395). Region C: brak dróg `tunnel` → `plan` = None, `build` = `({}, None)`,
`build_chunks(low_cut=None)` to ścieżka sprzed zmiany — +0 trójkątów z konstrukcji (test
`test_regions_without_tunnel_roads_are_untouched`); C na gałęzi nie był przebudowywany ani renderowany (nie mierzono).

## Walidacja (r5, po scaleniu origin/main 7f830369c)
- Generator: `stats.tunnel.inside` = `{'side_paved_tris': 1026, 'side_paved_collision_tris': 455, 'guardrail_tris': 88, 'guardrail_collision_tris': 80}`; `artifacts/tunnel-0211/dev_qa.py` (siatka 1 m / 2 m / 4 m, obie
  przekątne): teren w wykopie > 0,6 m nad dnem = 0, pokrywa w wykopie poza F / pod stropem = 0.
- `tunnel_sweep.py` (kolizja z GLB): samples 1923, min overhead above road collision 4.70 m, below 4.5 m: 0; min horizontal distance from a lane-edge sample (axis +-3.5 m) to a wall collision: 0.69 m.
- `route_sweep.py`: route 2165 m in tile, samples 5345, no road collision 14, blocked 0, max axis step 0.10 m.
- EditMode: EditMode: 603 total, 602 passed, 0 failed, 1 skipped (Skipped:Ignored). pytest `tests/gis` (`pytest-r5.log`): 1369 passed, 6 failed,
  9 skipped, 5 xfailed; `test_tunnel_0211.py` zielony. Żaden z 6 nie dotyczy kafla ani kodu tej gałęzi (wszystkie
  czytają region C, którego `generated/` jest identyczne z origin/main):
  - znane z main: `test_road_fidelity::test_report_not_stale` (raport fidelity C nieodświeżony po zmianie
    `build_world.py`/`consistency.py`/`tunnels.py` — do odświeżenia przy regeneracji C po scaleniu),
    `test_world_v31::test_frame_budget_with_forest_hlod` oraz `test_hero_bridge::test_asset_lods_and_budget`
    (ta sama przyczyna: `mesh_budget.frame_estimate` C z main, `stretch_04` 2 022 535 > 2 000 000 tris High);
  - nieaktualne lokalne `Data/raw/derived/bialystok-industrial-c/world` w worktree (z 14.11, main przebudował C
    15.11 16:54): `test_far_field::test_generated_far_field_qa_and_manifests`,
    `test_p1_0161::test_ring_mast_survives_the_carriageway_clearing`,
    `test_world_v31::test_forest_trees_reference_their_cell` — po skopiowaniu `world` C z main wszystkie trzy
    zielone (`pytest-r5-recheck.log`: 51 passed, 2 failed = dwa budżetowe powyżej).
- Rendery `artifacts/tunnel-0211/vqa-r5/{Low,High}-overcast/` (portale: `underpass-eb/wb-szymanskiego`, wnętrze:
  `tunnel-eb/wb-inside`, wykop: `cut-wall-oblique-sw`, wyspa na płycie: `rondo-szymanskiego-island-nw`).
- Referencje (Mapillary CC BY-SA 4.0, `Data/raw/mapillary/bialystok-kleeberga/`, arkusze
  `artifacts/tunnel-0211/refs/sheet_*.jpg`): 111496044347413 i 2106529699503974 (picturehoover, 2020-06-27),
  1142430022898855 (gpsmapper, 2019-08-25), 2250499485084897 (szurek, 2017-08-10); ortofoto 2024
  `artifacts/tunnel-0211/ortho/rondo_240.jpg`. Zgodne: płyta nad całym rondem, pionowe ściany wykopu z oczepem i
  balustradą, portal z balustradą nad jezdniami, brak roślinności pod płytą, opaska przy ścianie (r5: bruk zamiast
  trawy/żwiru pod płytą i od strony ścian). Różnice — patrz „Otwarte”.

## Otwarte
- visual-critic nie uruchomiony (subagent nie tworzy subagentów) — do zlecenia przez lidera na `artifacts/tunnel-0211/vqa-*/`.
- Wg zdjęć (wyżej): ściany to gładki beton kremowy z pionowymi dylatacjami i pilastrami oraz zielonym pasem oczepu —
  u nas prefabrykaty `ramp_wall_panels` (szare, układ mijany), WORKING_VALUE; potrzebny osobny materiał/tekstura.
- Wg zdjęć między jezdniami jest powierzchnia wyłączona z ruchu (malowana) i brak ściany środkowej przy portalach —
  u nas pas zieleni z krawężnikami (przekrój z OSM) i ściana środkowa (WORKING_VALUE); do poprawy przez override przekroju.
- Wg zdjęć przy ścianie biegnie opaska z kostki z odwodnieniem liniowym i krawężnikiem — u nas przekrój pobocza
  (rów 0,3 m) wybrukowany; poza odcinkiem pobocza gruntowego (ok. 40 m przed/za portalem) zostaje krawężnik + pas trawy.
- Brak opraw oświetlenia w tunelu (na zdjęciach rząd opraw sodowych pod stropem przy ścianach) i znaków w tunelu.
- `streetscape_qa.json` nadal wymienia przebieg bariery `…:L:structure` (8 m) w tunelu — geometria i kolizja są usuwane
  w `tunnels._dress_inside`; reguła `furniture.guardrails` nie zna tuneli.
- LOD2/3 terenu (300–700 m): pas 4,5 m za ścianami na dnie — z daleka cienka linia (1–2 px).

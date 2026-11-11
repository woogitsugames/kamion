# ADR 0110: Węzły r4 + bariery — trawa za krawężnikiem, barieroporęcz na pomostach, bariery przy wiaduktach, rozdział wsch. geometrią

Status: przyjęty (world-builder, gałąź `junctions-r4`), 2026-11-11. Wynika z `docs/reports/visual/REVIEW-2026-11-11-s10-0100.md`
(„Lista poprawek na węzły r4”) i z `docs/reports/visual/REVIEW-2026-11-11-s10-gpt-JK.md` („Priorytety bramki 3”, pkt 4 bariery).
Powiązane: ADR 0067 (wiadukt hero), 0076/0077 (kołnierze, kliny), 0093, 0095, 0100 (węzły r1–r3), 0102 (meble uliczne, GPT),
0105 (konstrukcja pod pomostem DK8, GPT — nietknięta). Dowody: `artifacts/junctions-r4/` (STATUS.md, REPORT.md, `trace/` =
ortofoto z siatką, `zones0/`, `plan_b*/` = ortofoto | generator, `xsec/`, `renders_b*_{high,low}/`, `view_b*/` ≤ 960 px, `logs/`).

## Kontekst
1. **P0-1**: pole P-21 na północ od wyspy przy n10015785253 było samą ramką: pasy 0,25 / 0,25 m pod 42° w trójkącie 3,2 m² —
   po odrzuceniu fragmentów < 0,35 m zostawał 1 pas; wielokąt 0,5–1 m za wąski od wschodu.
2. **„Wanny” median i murki (P1-1)**: krawężnik bez chodnika kończył się zakopanym kołnierzem 0,5 m, a za nim był tylko teren z
   siatki 1 m, leżący 0,03–0,4 m poniżej korony (węzły pod jezdnią są 0,35 m pod nawierzchnią). Z drugiej jezdni kołnierz czytał
   się jako betonowy mur, a każda mediana jako koryto (`p0_median_slot_eye`, `r2_fork_link_eye`, `eye_putry_n`). Zmierzone
   (`scripts/kerb_back.py`): 63 735 wierzchołków korony kołnierza „krawężnika bez chodnika” miało za sobą tylko teren.
3. **Bariery (bramka 3, pkt 4)**: (a) `hero_bridge.apply` kasował wszystkie części o `src` zaczynającym się od id łańcucha — także
   bariery `streetscape.furniture.guardrails` (`<łańcuch>:<strona>:bridge`). Pomosty wiaduktu Bieżeństwa nie miały żadnej bariery
   drogowej, tylko balustradę szczebelkową z assetu na białej kapie. (b) Reguły barier: most / pas dzielący wiejski / nasyp > 2 m —
   brak reguły dla jezdni biegnącej obok wiaduktu (łącznice przy Rondzie Bieżeństwa). (c) Bieg mostowy, bieg nasypu dojazdu i bieg
   mediany były osobnymi biegami o różnych offsetach: przy E −782 krzyżowały się i dublowały; na pomoście DK8 stały obok siebie
   taśma W, balustrada i słupy ekranu.
4. **Szwy (P1-2)**: 20-metrowy łańcuch między dwiema łatami wylosowany jako „świeży asfalt” (Putry N, N 100–120); łaty skrzyżowań
   nie miały UV1 (eksporter wstawia −1 / 5 m = brak kolein i brudu rynsztoka), więc każda łata w zużytej jezdni była czystsza.
5. **Rozdział jezdni wsch. (P1-3)**: OSM `lanes=3` na łącznicy dawało wstęgę 11,5 m na osi drogi; południowa krawędź leżała
   3–4 m (przy stacji 30: 7 m) za krawężnikiem z ortofoto, a pasmo jodełki było klinem ≤ 1,2 m.
6. **Zatoka s 1060, strzałki n100 (P1-4, P1-5)**: wielokąt `paved_apron` zostawiał 0,9–2 m asfaltu między linią przerywaną a kostką i
   kończył się rogiem przed zatoką generatora (ząb); cztery osierocone łuki farby; strzałki naprowadzające jako glif strzałki na
   wprost obrócony w poprzek pasa („igły”).

## Decyzja
1. **P-21 n100 N** (`overrides.yaml`): wielokąt z ortofoto 120 px/m (`trace/n100n.jpg`), pasy 0,20 / 0,22 m pod 8°, obramowanie
   0,15 m. `p21_hatch`: `border_w_m`, `stripe_min_m` per pole. `roads_qa.painted_zones[]`: `stripes_built`, `stripe_cover`; test:
   ≥ 60 % pasów analitycznych trafia do siatki i pokrycie ≥ 15 % pola.
2. **Trawa za krawężnikiem bez chodnika** (`meshing._emit_verge`, `network.assign_sides` → `side["verge"]`, `network._side_gap`):
   pas trawy od tyłu korony krawężnika, na wysokości korony (+2 % na zewnątrz), 1,0 m (`VERGE_W`), w medianie do 3,0 m
   (`MEDIAN_VERGE_MAX`), nigdy za połowę odstępu do równoległej jezdni (dwa pasy spotykają się w osi mediany); szerokość zmienia się
   najwyżej o 1 m na 2 m; dalej skarpa trawiasta 1 : 2 głęboka 0,5 m zamiast pionowego kołnierza. Także wzdłuż narożników i nosów
   (`build_corner_strips`), z wyjątkiem narożników o skaczącej niwelecie (> 15 %). Po wewnętrznej stronie łuku pas i skarpa są
   ściskane z zachowaniem nachylenia. Pasy nie leżą nad inną jezdnią (ścisłe wycinanie w `cull_sides_on_carriageway`) ani pod wyspą
   autorską / wypełnieniem klina (`gores._drop_verge_in_islands`). **Eksport**: pasy trafiają do prymitywów terenu swojego chunku
   (`build_world.merge_verge_into_terrain`, każdy LOD) — ta sama trawa co obok, bez nowego draw calla (osobny materiał
   `verge_grass` pojawiłby się w 23 chunkach drogi). Nie są footprintem (maska terenu dla nasadzeń / placów bez zmian). Kołnierz
   krawężnika nie jest meszowany tam, gdzie zakrywa go pas; pasy po Douglasie–Peuckerze 2,5 cm (`geom.dp_keep`).
   Kolizja bez zmian (wizualne). `_emit_strip`: `h` stacji wiejskiej w narożniku mieszanym = `KERB_HEIGHT` (był murek 0,6 m).
3. **Nos mediany Putry N**: wyspa autorska `putry-n-median-nose` (kostka, 1,8 m) domyka tępy koniec mediany na łacie przejazdu.
4. **Bariery** (`streetscape/furniture.py`, w miejscu generowania — konflikt z 0102 tylko w `guardrail*`):
   - **barieroporęcz na pomostach** (`guardrail(tall=…)`): słupki do 1,10 m co 2,0 m, taśma W (góra 0,75 m), płaskownik 0,92 m,
     pochwyt 1,10 m; oś 0,40 m od zewnętrznej krawędzi kapy. Wzór: Mapillary 454716650857984, 2948595898752384 (z jezdni),
     500263111404933, 1259231227807789 (od dołu: poziome poręcze, bez szczebelków) — tylko odniesienie, CC BY-SA.
     Wymiary WORKING_VALUE (ortofoto: bariera 0,2–0,4 m od krawędzi pomostu; rozstaw słupków na zdjęciu 1,5–2 m „na oko”).
   - `hero_bridge.apply` zostawia bariery łańcucha; asset `viaduct_biezenstwa` bez balustrady (`rail_h_m` 0, przebudowany
     Blenderem przez `hero_bridge.plan`); konstrukcja pod pomostem (0105) bez zmian.
   - balustrada generyczna (`meshing.build_bridge_extras`) pominięta na krawędzi z ekranem akustycznym.
   - **reguła „structure”**: bariera W przy krawędzi jezdni naziemnej biegnącej ≤ 8 m obok wiaduktu / rampy w murach stojących
     ≥ 1 m wyżej, po stronie konstrukcji (krawędź wiejska: za poboczem; krawężnik bez chodnika: 0,6 m za krawężnikiem). WORKING rule.
   - **jeden bieg na krawędź**: sąsiednie odcinki różnych reguł (most → nasyp → mediana) to jeden bieg, offset i wysokość stopy
     wygładzane 9 m; dedup gruntowy 2,5 m (pomosty 1 m); wolny koniec na gruncie odgięty do ziemi na 4 m; belka i poręcze po
     Douglasie–Peuckerze 1 cm (była siatka co 1 m).
5. **Szwy**: `standards.surface_material` — łańcuch krótszy niż 120 m nie jest „świeżym asfaltem”; `meshing._patch_uv1` — łata
   dostaje UV1 (współrzędna pasa, odległość od krawędzi) w układzie drogi przelotowej (najszersze ramię + ramię naprzeciw).
6. **Rozdział wsch.** (`overrides.yaml`, tylko dane): jezdnia główna `lane_edges` [0,5; 3,95; 6,85] + profil szerokości 10,6 m
   (strefa P-21 i wyspa leżą na niej, więc mają pod sobą asfalt i między wstęgami nie powstaje krawężnik), łącznica = 1 pas
   3,8–4,3 m wzdłuż krawężnika płd. (profil offsetu z ortofoto: krawężnik 5,3 / 2,75 / 2,5 / 0,6 / 0,4 m w prawo od osi OSM na
   stacjach 0 / 29 / 55 / 86 / 108); obie wstęgi wracają na oś OSM i standardową szerokość na styku z wiaduktem (pomost nietknięty).
   Pole P-21 przód: klin 0,75 → 3,0 m; wyspa do E −788 (dryfuje na płd. z łącznicą); pasmo boczne 1 m; linia segregacyjna P-1
   autorska (generator rysował ją na łacie jako ciągłą).
7. **Zatoka s 1060**: `paved_apron` wzdłuż linii przerywanej od E −122 do −98; 4 × `paint_clear` na osierocone łuki.
   **Strzałki n100 płd.**: glif `guide_left` / `guide_right` (`markings.arrow_glyph`) z obrysu na ortofoto 75 px/m: 5,1 × 2,75 m,
   ogon ścięty równolegle do pasa (WORKING_VALUE; wymiary wzoru P-9 z rozporządzenia UNVERIFIED).
8. `terrain_walls_qa.json`: pasy trawy liczone osobno (`verge_strips`), z własnym ratchetem w `tests/gis/test_junctions_r4.py`.
9. Kamery: `r4_*` (9): pozy 5 kadrów side-by-side bramki 3 (pomost, łącznice, filar), n100 N z oczu i z góry, strzałki z góry,
   nos mediany Putry N.

## Wynik
Liczby: sekcja „RAPORT KOŃCOWY” w `artifacts/junctions-r4/STATUS.md` (tabela przed / po z builda końcowego).

## Otwarte
1. **Telefon** — brak zrzutu (agent nie używa adb); budżet zmierzony tylko w edytorze (`stats.txt`) i szacunkiem siatek.
2. **Kapa pomostu**: generowana jezdnia pomostu Bieżeństwa ma 8,0 m + 2 × 1,65 m; ortofoto (`xsec/hero_deck.png`): jezdnia ~6,8 m,
   kapa z barierą ~1,3 m — pomost jest o ~1,5 m za szeroki od strony zewnętrznej, więc bariera stoi 1,25 m od krawędzi jezdni
   (zdjęcie: ~0,9 m). Zwężenie pomostu zmienia spec assetu hero i geometrię 0105 — osobna decyzja.
3. **Słupki barier**: rozstaw 2,0 m i profil belki to WORKING_VALUE; brak stopek / płyt kotwiących na pomoście (zdjęcie je ma),
   brak przejścia taśma W → barieroporęcz kształtką; koniec barieroporęczy przy E −782 kończy się słupkiem.
4. **Jasny prostokąt w `p0_fork_putry_eye`** (P1-2): to nie szew łat, lecz `decal_patch` (łata remontowa „na cały pas”, reguła
   `roads/decals.py`); wygląda płasko, bo materiał dekalu nie ma faktury — runda materiałowa (plik wspólny), nie ruszone.
5. **Nos mediany Putry N**: geometria łaty przejazdu nie przebudowana (mediana generatora sięga 1,7 m dalej na płd. niż na
   ortofoto), nos jest domknięciem, nie odwzorowaniem; wschodnia strona tej mediany dalej jako profil wiejski (pobocze + żwir).
6. **Rozdział wsch.**: odczyty z trzech kadrów ortofoto różnią się o ±0,5 m (WORKING_VALUE); jezdnia główna na pomoście i dalej
   nie przesunięta (oś OSM); separator za E −788 to krawężniki + trawa (na ortofoto betonowy z barierą).
7. **Pasy trawy**: w medianie szerszej niż 6,3 m środek to nadal teren (2–3 cm niżej, skarpa 1 : 2 zakrywa przejście); koniec pasa
   przy łacie bez narożnika kończy się otwartym przekrojem; `verge_strips.steep_grass` > 0 (skręcone trójkąty wybiegu skarpy).
8. Nie ruszone z listy r4: P1-7 separator s 1440 (beton z barierą), P1-8 wzór „W” trawy (shader), P2-1 MA-010 linie prowadzące,
   P2-2 skok linii n100, P2-3 czerwone przejazdy, P2-4 kolor kostki, P2-5 filary / ekrany, P2-6 pasmo s 1380; n100 jezdnia płd.:
   kończący się pas, załom krawężnika, BUS. „Podwójne linie krawędziowe na wiadukcie”: na renderach pomostu
   (`r4_deck_bz_eye`, `p0_lamp_w1101181473_eye`) jest jedna linia na krawędź — nie odtworzone.
9. Ocena `visual-critic` — dla lidera (agent nie tworzy subagentów).

## Pliki wspólne i przewidywane konflikty
- Nie dotknięte: `WorldPbrMaterials.cs`, shadery, `streetscape/materials.py`, `build_world.MATERIALS`, konstrukcja pod pomostem
  (`hero_bridge._apply_underdeck`, `viaduct_underdeck.json`).
- `streetscape/furniture.py`: przepisane `guardrail`, `_dedup_guardrail`, `guardrails` (+ `_structures`, `_beside_structure`);
  reszta pliku (0102: latarnie, znaki, płoty) bez zmian. Konflikt możliwy tylko z inną zmianą barier.
- `streetscape/hero_bridge.py`: `DEFAULTS["rail_h_m"]` = 0, filtr części w `apply` (2 miejsca, addytywnie);
  `tools/blender/world/landmarks/make_viaduct.py`: 2 linie (pominięcie balustrady przy `rail_h_m` < 0,05);
  `art-source/world/landmarks/viaduct_biezenstwa/*` przebudowany.
- `roads/meshing.py`: `_emit_verge`, `_patch_uv1` (nowe), `_emit_strip(noflange=)`, `build_side_strip`, `build_corner_strips`,
  `cull_sides_on_carriageway` (gałąź `:vg`), `build_bridge_extras` (1 warunek). `roads/network.py`: `_side_gap`, `side["verge"]`.
  `roads/gores.py`: `_drop_verge_in_islands`. `roads/build_world.py`: `merge_verge_into_terrain` + 1 linia w `assemble`.
  `terrain_mesh/conform.py`: `terrain_walls` — klucz `verge_strips`. `roads/geom.py`: `dp_keep`. `roads/standards.py`: stałe.
- `Data/Regions/bialystok-industrial-c/overrides.yaml`, `junctions_cameras.json` (+9 kamer), `generated/*` — po scaleniu
  regenerować (build_world → export-route → fidelity).

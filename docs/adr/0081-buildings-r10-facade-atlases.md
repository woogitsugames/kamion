# ADR 0081: Zabudowa r10 — atlasy fasad (LOD0), rzędy kondygnacji (LOD1), prefabrykowany płot betonowy

Status: propozycja (world-builder, gałąź `worktree-agent-ac404823e7d8b56e7`), 2026-11-10. Uzupełnia ADR 0012/0015 (LOD1
zabudowy, „far facade”), ADR 0022 (zestawy PBR), ADR 0063 (skany CC0), ADR 0067 (`set_tile`, atlasy-pasy).

## Kontekst
Runda bazowa r10 (`artifacts/buildings-r10/base/`): okna bloków, biur i domów to jednolite czarne szyby w białej ramie
z geometrii (4 quady ramy + słupek = 20 trójkątów na okno), każde okno identyczne; LOD1 rysował siatkę okien shaderem
z TEXCOORD_1 (jeden prostokąt szkła na przęsło). Balustrady balkonów — jedna szara blacha. Płot betonowy (OSM
`barrier=wall`) — wstęga pochylona po terenie z jedną kafelkowaną teksturą. Zdjęcia CC0 bloku przy Rondzie Putry
(Wikimedia Commons, `artifacts/buildings-r10/refs/cm1215374*.jpg`) pokazują to, czego brakowało: firanki, rolety,
kwiaty, różne balustrady, zabudowy balkonów, anteny, pranie.

## Decyzja
1. **`facade_atlas`** (zestaw PBR 16 × 16 m, kalibrowany, `set_tile`, UV0 w metrach atlasu): 103 komórki — okna z ramą
   i tym, co za szybą, drzwi balkonowe, drzwi wejściowe, bramy garażowe, fronty balustrad, zabudowy balkonów,
   klimatyzatory, czerpnie, skrzynki, próbki kolorów. Układ: `tools/worldgen/streetscape/facade_atlas.py` (czysty
   Python, wspólny kontrakt), malarze: `art-source/world/materials/_src/sets_buildings.py`. Wszystko z kodu, bez
   zdjęć i bez generatorów AI.
2. **LOD0**: wypełnienie otworu = komórka atlasu (`buildings_mesh.cells`), ościeża i parapet zostają geometrią,
   rama i słupki znikają (są w komórce). Balkon: front balustrady z komórki `balf`, 14 % zabudów, 18 % anten,
   30 % prania; klimatyzatory przy 5 % okien bloków i 10 % okien biur (udziały WORKING_VALUE). Hale: czerpnie
   ścienne, jedna drabina z koszem na większą halę (odstępy wg PN-EN ISO 14122-4, wymiary WORKING_VALUE).
3. **LOD1**: `facade_far` (zestaw modulacyjny 24 × 40,2 m, 14 rzędów po 8 przęseł złożonych z tych samych komórek).
   Strefa okien = jeden quad na paczkę kolejnych rzędów (`FA.far_plan`), dwa quady marginesów i attyka dopięta do
   ostatniej paczki; UV0 w metrach atlasu rzędów, bez TEXCOORD_1 i bez shadera siatki. LOD0 czyta **ten sam plan**,
   więc oba LOD-y pokazują te same okna w tych samych miejscach. Parapet i wysokość okna skalują się z wysokością
   kondygnacji (k = sh / 2,8 m) na obu LOD-ach.
4. **Typologia**: biuro ma jedną stolarkę na budynek (biała PVC albo antracyt), bloki mieszają okna jak na zdjęciach;
   balkony od parteru (wysoki parter); kolor akcentu tylko na faktycznych ścianach szczytowych (wcześniej każda
   krawędź < 16 m, przez co bloki ze skokami w rzucie wychodziły całe w kolorze akcentu).
5. **Płot betonowy** (`furniture.concrete_fence`, zestaw `fence_concrete` 16 × 4,5 m, hybryda ze skanem CC0
   „Concrete Floor Worn 001”): przęsła 2,0 m od narożnika do narożnika, każde poziome i schodkowane na słupkach,
   cztery płyty 0,5 m albo panel ramowy (jeden typ na ogrodzenie), inny odlew na każdym licu, słupki 12 × 14 cm
   wystające 8 cm; przęsła ze sprayem / zamalowane rzadko (ok. 1 na 7).
6. **Koszt LOD1**: gzyms attyki LOD1 to jedna pochylona ściana zamiast czoła i wierzchu (−2 trójkąty na krawędź),
   maszynownie bez spodu — płaci za quady rzędów.

7. **Budżet tekstur** (r2): `pbrkit.SurfaceSet.aux_div` — Normal / MaskMap / Var zapisane w 1/aux_div rozdzielczości
   albedo (`aux_res` w `materials_spec.json`, estymata `gpu_bytes_astc_mips` to uwzględnia). `facade_atlas` albedo
   4096 px + reszta 2048 px; `facade_far` albedo 2048 × 3428 + reszta 1/4 (zestaw płaski, bez reliefu);
   `fence_concrete` 2048 × 576 (558 m płotu w regionie nie uzasadnia 4096), skalibrowany do 0,30 po nałożeniu skanu.
8. **Kolor elewacji — `tint_linear`** (r2). Rendery r1 pokazały tynki ciemne i przesycone. Pomiar: `plaster_grey`
   0,36 lin. wychodził na ekranie 0,095, `plaster_cream` [0,55; 0,48; 0,33] → [0,19; 0,15; 0,09], a cokół bez tekstury
   (0,16, URP Lit) był jaśniejszy od ściany 0,36. Przyczyna: `_Tint` w `Kamion/World PBR` jest właściwością `Color`,
   więc Unity linearyzuje wartość zapisaną przez importer drugi raz (≈ kolor^2,2). Materiały z flagą `tint_linear`
   (`materials.py`: tynki, cokół, wielka płyta, cegła, ściany i cokoły hal, dachy, bramy, panel balkonu + warianty
   `__far_*`) dostają w `WorldPbrMaterials.cs` wartość zakodowaną gamma — shader mnoży przez kolor z tabeli.
   Zakres celowo ograniczony do powłoki budynków (to renderuje i ocenia to zadanie).
9. **Cegła `set_tile`**: zestaw NF ma 1,506 m, a był próbkowany co 4 m (domyślny `_Tile`, znany brak z ADR 0067) —
   warstwa cegły wychodziła ok. 20 cm. Cokół `plinth_dark` dostał zestaw `plaster` (był płaskim kolorem).
10. **Zacieki pod attyką na tynku** (flaga `runoff`, LOD0 bloków i biur z dachem płaskim): ta sama warstwa
    `parapet_runoff` co na halach, siła × 0,6 (WORKING_VALUE). LOD1 bez zacieków (strefa okien to atlas rzędów bez UV1).

## Liczby (zmierzone / z generatora; nic z telefonu)
- Pamięć tekstur, zestawy PBR świata razem (estymata ASTC z mipami, `materials_spec.json`), Low / Medium / High:
  main 6,0 / 33,6 / 171,9 MB → r1 8,3 / 46,8 / 239,6 MB → **r2 7,3 / 39,5 / 197,1 MB** (budżet całej gry w
  `docs/PERFORMANCE_BUDGETS.md`: 64 / 96 / 256 MB). `facade_atlas` 39,8 / 7,8 / 1,4 → 17,4 / 3,8 / 0,6 MB (H / M / L),
  `facade_far` 16,7 / 3,3 / 0,6 → 4,9 / 1,6 / 0,6 MB, `fence_concrete` 11,2 / 2,2 / 0,4 → 2,8 / 0,55 / 0,1 MB.
  Estymata jest górną granicą: na Androidzie MaskMap / Var i tak idą w połowie rozdzielczości (ADR 0025).
- Geometria (estymata generatora, 19 kamer r10, baza → r1): Low trójkąty −487..+556 (maks. +0,07 %), materiały Low
  −3..−7, High trójkąty −0,4..−4,4 %. Tabela r2 i `stats.txt` z edytora: `STATUS-buildings-r10.md`.
- Testy: `tests/gis` 222 passed, 3 failed (te same co na main: `test_road_fidelity::test_report_not_stale`,
  `test_route_corridor` × 2 — P0 korytarza, zadanie 0076), `test_cc0_scans` 6/6.

## Znane braki / UNVERIFIED
- Nie zmierzone na telefonie (zakaz adb w tym zadaniu); budżet = estymata generatora + `stats.txt` z edytora.
- Kolory tynków i udziały (zabudowy, anteny, pranie, klimatyzatory) to WORKING_VALUE do sprawdzenia ze zdjęciami
  właściciela.
- Okna LOD0 są płaskie w ościeżu (rama namalowana); z bliska pod ostrym kątem widać brak głębi ramy.
- `facade_far` jest zestawem modulacyjnym: zawartość okien i balustrady lekko przejmują kolor ściany.
- `FarFacadeMaterial` / `window_grid` w `RegionImporter.cs` zostają jako martwa ścieżka (do usunięcia przez lidera).
- **Do decyzji lidera:** podwójna linearyzacja `_Tint` dotyczy wszystkich zestawów modulacyjnych (ogrodzenia, ekrany,
  wiadukt, rekwizyty) i zestawów kalibrowanych z tintem ≠ 1. Te materiały były oceniane wzrokowo z błędem, więc
  globalne włączenie poprawki (zamiana `_Tint` na `Vector` albo zapis gamma dla wszystkich) wymaga osobnej rundy
  przeglądu; tutaj zmieniona jest tylko powłoka budynków. `WorldPbrMaterials.cs` leży poza własnością world-buildera
  (World/Import) — zmiana to 12 linii, do przejrzenia.
- Zacieki na tynku znikają na LOD1 (możliwy „pop” przy przełączeniu LOD); kamera `r10_hall_3` stoi pod terenem
  (błąd generatora kamer, nie zabudowy).

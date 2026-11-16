# 0194 — Plamy i brud na asfalcie sterowane ruchem (olej, łaty, koleiny na płytach, brud placów)

Status: przyjęty (scalony do main 2026-11-15, `5d64bcd92`; status zaktualizowany 2026-11-16); pierwotnie: PROPOSED (gałąź `stains-0194`, po merge `origin/main` `8313ed9ba`). Data: 2026-11-15. Dotyczy: ADR 0019 (decale), 0060 (_GRIME), 0110 (UV1 płyt),
0118 (asphalt_wear / szew łat), 0062/0191 (pule latarni — konflikt opisany niżej).

## Kontekst (REVIEW-2026-11-13-s19-0179, P2)
1. P11-129: plamy na asfalcie to **jasne rozmyte „splaty”** (pomiar przed: plama 91 vs asfalt 66–70 kodu sRGB luma, +34 %).
   Przyczyna (zmierzona na atlasie `oil_stain_alpha`): albedo plamy 0,018 lin. (ciemne, OK), ale Mask.A w rdzeniach 0,43–0,52
   przy płaskiej normalnej decala → przy kącie ślizgowym kierowcy odbija się jasne niebo zachmurzone; asfalt obok ma 0,09.
2. Dojlidy route-after kadr 2 (= kamera `route_s1066`, płyta skrzyżowania Kuronia/Mickiewicza bez linii): gęste ciemne smugi na
   całej szerokości. Przyczyna: `_patch_uv1` (ADR 0110) przenosi współrzędną pasa ramion na płytę, więc koleiny (−42 % albedo w osi
   koleiny przy `wheel_darkening` 0,45) i pas kapania biegną równolegle przez całą płytę, a na płycie nie ma linii, które je porządkują.
3. „Ten sam brud wszędzie”: kałuże/brud `_GRIME` (ADR 0060) mają jeden próg makro na całym placu (chase C), łaty drogowe mają tę
   samą gęstość na każdej klasie drogi i losowe położenie w poprzek jezdni.

## Decyzja
Nowy plik `game/Assets/_Project/Rendering/Shaders/KamionRoadStains.hlsl` (wszystko opt-in, wektor 0 = dokładnie stary wynik):
- **Olej** (`KamionOilStain`, `_OilLook`, dane `decal_oil.oil_look`): gładkość 0,10 (stara plama) … 0,22 (świeży film) zamiast
  ~0,5; gamma pokrycia 0,7 (gęstszy rdzeń, ostrzejszy brzeg). Kratki/włazy Fab (ten sam `_DECAL_ALPHA`) bez zmian.
- **Płyty skrzyżowań** (`KamionPlateWear`): `roads.meshing._patch_uv1` dodaje `PLATE_EDGE_FLAG` (`+20 m` / `d + 25.0`, kodowanie liniowe
  `spread` i `min(edge, 1)`) do UV1.y wierzchołków płyty oraz wygładza `lane` do granicy pasa za `hw`, a `_emit_strip` dla
  `road_asphalt*` ustawia `UV1=(-1, 5)` (brak pasków co 1 m na poboczach). `build_world.assemble()` spawa wierzchołki po `(qp, UV1)`
  z zachowaniem gładkich normalnych `Np` na szwach ramię↔płyta; shader zdejmuje flagę i zostawia 35 % kontrastu kolein i 40 % pasa
  kapania (ruch skręca i się przeplata), eliminując żółto-brązowy pas na zjazdach.
- **Brud placów** (`KamionYardGrimeBias`, `_GrimeTraffic`, dane `grime_traffic` na yard_*): UV1 nawierzchni utwardzonych
  (odl. od krawędzi, odl. od ściany) przesuwa próg kałuż: przy ścianach/dokach (< 18 m) i krawędziach (< 2,5 m) −0,04 (wilgotniej),
  na otwartym środku +0,07 (czyściej). Zero dodatkowych próbek tekstur.
- **Łaty** (`roads.decals`): oczekiwana liczba × klasa drogi (A/S 0,35, GP 0,55, G 0,85, Z 1,0, L 1,2, D 1,3) × strefa wlotu
  (30 m od końca łańcucha przy skrzyżowaniu ×1,8, środek odcinka ×0,75); łaty „w koleinie” i 60 % małych łat w osi koleiny pasa
  (±0,24 szer. pasa, 65 % zewnętrzna). Szew 25 mm i inny odcień/zestaw `asphalt_patch` — bez zmian (ADR 0118), teraz widać je tam,
  gdzie realnie powstają. Wszystkie liczby WORKING_VALUE (porównanie: P11-076 Dywizjonu 303 — prawie bez łat; P11-129 — kilka łat).

### Konflikt z lamppool-0191
0191 zmienia w `WorldPBR.shader` tylko linię oświetlenia (`KamionLampPools(...)` → `KamionLampPoolsLit(...)`, ~l. 986) oraz
`KamionLampPools.hlsl`. 0194 dotyka: include (l. ~108), CBUFFER (`_OilLook, _GrimeTraffic`), Properties (`_GrimeTraffic`, `_OilLook`),
blok `_ROADWEAR` (3 linie), blok `_GRIME` (1 linia), blok `_DECAL_ALPHA` (1 linia). Brak wspólnych linii; przy scaleniu obu
sprawdzić tylko kolejność include w HLSLINCLUDE.

## Budżet A/B (`before` vs `after4`)
Materiały i shader: ten sam zestaw materiałów (0 nowych fetchy, 0 nowych keywordów/wariantów). ALU szacowane: olej +~6, płyta +~4, plac +~10 (tylko materiały z danymi). Liczba łat: Dojlidy `285 → 416`, C `317 → 443` (olej `271` bez zmian).

### `WORLD_MEMORY` (importy `after4` po merge `origin/main` `8313ed9ba`)
- **Dojlidy (`bialystok-dojlidy`)**:
  - `before` Low (`artifacts/stains-0194/before/import-dojlidy.log`): `render_meshes=68.9 MB`, `instances=18.2 MB`, `collision_src=16.7 MB`, `total=103.8 MB` (`road 9,0`, `markings 2,3`, `paved 3,7`).
  - `after4` Low (`artifacts/logs/import-region-bialystok-dojlidy-20261114-220134.log`): `render_meshes=64.6 MB`, `instances=18.2 MB`, `collision_src=15.5 MB`, `total=98.3 MB` (`road 9,1`, `markings 1,4`, `paved 2,6`).
  - `after4` High (ten sam log): `render_meshes=179.9 MB`, `instances=18.2 MB`, `collision_src=15.5 MB`, `total=213.6 MB` (`road 9,1`, `markings 1,4`, `paved 2,6`).
- **Industrial C (`bialystok-industrial-c`)**:
  - `after4` Low (`artifacts/logs/import-region-bialystok-industrial-c-20261114-221656.log`): `render_meshes=83.5 MB`, `instances=22.6 MB`, `collision_src=17.1 MB`, `total=123.2 MB` (`road 11,6`, `markings 2,8`, `paved 3,3`).
  - `after4` High (ten sam log): `render_meshes=226.4 MB`, `instances=22.6 MB`, `collision_src=17.1 MB`, `total=266.1 MB` (`road 11,6`, `markings 2,8`, `paved 3,3`).
  *(Dla porównania w pierwszym `after` przed `origin/main`, log `20261113-235449`: C Low `122.8 MB`, C High `265.8 MB`, `road 11,4`.)*

### `drawsEst` / `trisExact` / `instancedTrisExact` (`stats.txt`)
- **D-Low** (`before/D-Low` i `before/D2-Low` vs `after4/D-Low`, 7 wspólnych kamer; na `route-s0152`/`s0457` spadek z wcześniejszego `origin/main`):
  - `photo-P11-129`: `drawsEst 174 → 174 (+0)`, `trisExact 231790 → 230964 (-826)`, `instTrisExact 18918 → 18946 (+28)`
  - `photo-P11-129b`: `drawsEst 322 → 321 (-1)`, `trisExact 425303 → 424779 (-524)`, `instTrisExact 8339 → 8363 (+24)`
  - `route-s0152`: `drawsEst 146 → 142 (-4)`, `trisExact 187763 → 152957 (-34806)`, `instTrisExact 2374 → 2278 (-96)`
  - `route-s0457`: `drawsEst 203 → 200 (-3)`, `trisExact 180016 → 144024 (-35992)`, `instTrisExact 19837 → 13919 (-5918)`
  - `route-s1066` (vs `D2-Low`): `drawsEst 390 → 393 (+3)`, `trisExact 276582 → 279152 (+2570)`, `instTrisExact 17910 → 9921 (-7989)`
  - `route-s1370` (vs `D2-Low`): `drawsEst 330 → 334 (+4)`, `trisExact 267445 → 271305 (+3860)`, `instTrisExact 11298 → 11208 (-90)`
  - `route-s1675` (vs `D2-Low`): `drawsEst 183 → 182 (-1)`, `trisExact 199432 → 202621 (+3189)`, `instTrisExact 15836 → 16930 (+1094)`
- **D-High** (`after4/D-High`, 12 kamer — brak bazowego `before/D-High`):
  - Wybrane kamery: `photo-P11-129b` (`drawsEst=604`, `trisExact=2030401`, `instTrisExact=39794`), `route-s0457` (`613` / `1061162` / `48585`), `route-s1370` (`504` / `1219821` / `44654`), `route-s0152` (`619` / `1063083` / `52565`).
- **C-Low** (`before/C-Low` vs `after4/C-Low`, 4 wspólne kamery):
  - `chase`: `drawsEst 416 → 417 (+1)`, `trisExact 308005 → 309324 (+1319)`, `instTrisExact 14428 → 14440 (+12)`
  - `route-onramp-andersa`: `drawsEst 387 → 388 (+1)`, `trisExact 249107 → 249154 (+47)`, `instTrisExact 30778 → 30754 (-24)`
  - `route-putry-approach`: `drawsEst 297 → 297 (+0)`, `trisExact 276658 → 277536 (+878)`, `instTrisExact 30806 → 30806 (+0)`
  - `stretch-05-docks`: `drawsEst 254 → 255 (+1)`, `trisExact 237772 → 239174 (+1402)`, `instTrisExact 80618 → 80575 (-43)`
- **C-High** (`before/C-High` vs `after4/C-High`, 4 wspólne kamery):
  - `chase`: `drawsEst 658 → 660 (+2)`, `trisExact 1431013 → 1432895 (+1882)`, `instTrisExact 64366 → 64395 (+29)`
  - `route-onramp-andersa`: `drawsEst 976 → 977 (+1)`, `trisExact 1599892 → 1600136 (+244)`, `instTrisExact 165141 → 165345 (+204)`
  - `route-putry-approach`: `drawsEst 425 → 425 (+0)`, `trisExact 1010822 → 1010843 (+21)`, `instTrisExact 47384 → 47324 (-60)`
  - `stretch-05-docks`: `drawsEst 549 → 550 (+1)`, `trisExact 1182377 → 1183876 (+1499)`, `instTrisExact 316224 → 316097 (-127)`

## Walidacja
- **Visual QA (`after4`, `sbs4/`)**:
  - `artifacts/stains-0194/sbs4/photo_vs_after4_D-High_photo-P11-129b.jpg`: plamy oleju ciemne i ostre (luma w `after1` 62 vs 91 `before`, asfalt 66–70; koniec jasnych rozmytych splatów).
  - `artifacts/stains-0194/sbs4/after3_vs_after4_D-Low_route-s0457.jpg`: usunięte paski/zebra na poboczu `road_asphalt*` (`_emit_strip`).
  - `artifacts/stains-0194/sbs4/after3_vs_after4_D-Low_route-s1370.jpg` i `artifacts/stains-0194/sbs4/photo_vs_after4_C-High_sbs-g3-a-2818555625124739.jpg`: brak skośnych zygzaków kolein na rozszerzeniach zjazdów płyt skrzyżowań i brak żółto-brązowego pasa.
  - `artifacts/stains-0194/sbs4/before_vs_after4_C-Low_chase.jpg`: widoczny gradient brudu/wilgoci na placu (`_GrimeTraffic`) oraz nowe łaty w koleinach drogi dojazdowej.
- **Unity EditMode** (`pwsh scripts/test.ps1 -Platform EditMode`): `584 total, 583 passed, 0 failed, 1 skipped (Skipped:Ignored)` (`artifacts/tests/editmode-20261115-112343.xml`).
- **Pytest (celowane)** (`uv run --project tools/worldgen python -m pytest tests/gis/test_stains_0194.py tests/gis/test_unit_meshing_chunks.py -q`): `14 passed in 0.53s`.
- **Pytest (pełne `tests/gis`)** (`uv run --project tools/worldgen python -m pytest tests/gis -q`): `1157 passed, 2 failed, 2 xfailed` (0:19:30); oba faile to znane upstream faile niezwiązane z 0194:
  - `tests/gis/test_dojbld_0185.py::test_fence_mesh_mips_do_not_preserve_coverage` (brakujące `ti.mipMapsPreserveCoverage` w `InstanceImporter.cs`),
  - `tests/gis/test_road_fidelity.py::test_report_not_stale` (`fidelity_qa.json` nieaktualne dla `build_world.py`, `decals.py`, `meshing.py`).

## Otwarte
- Koleiny na nowych drogach (Dywizjonu 303, P11-076: ledwo widoczne) są w renderze wyraźne — `asphalt_wear.wheel_darkening` 0,45 jest
  wspólne dla `road_asphalt`; kandydat: wiek nawierzchni z danych (oddanie drogi) → osobny materiał, decyzja lidera.
- Pomiar na telefonie przy najbliższym APK (koszt ALU szacowany, nie zmierzony).
- Lider: regeneracja `generated/*` regionów C i Dojlidy po scaleniu (gałąź nie commituje generated).

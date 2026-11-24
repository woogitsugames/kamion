# ADR 0346 — Bele słomy i sianokiszonki na polach mozaiki 0334

Status: Proposed, 2026-11-24 (neon-bales-s24; zamyka otwarty punkt ADR 0334: „bele słomy na ściernisku po prasowaniu — brak modelu”).
Powiązane: ADR 0334 (mozaika upraw lata, `field_layout` / `field_use`), ADR 0166 / 0174 (per-region biblioteka `street_props.glb` i `textures/`), ADR 0221 / 0327 (budżety trójkątów), D68 (lato ~15 sierpnia), `docs/06_GRAFIKA_ANTI_AI_SLOP.md`.

## Kontekst

ADR 0334 wprowadził w shaderze terenu 16 letnich użyć pasów pól (m.in. `stubble`, `stubble_baled`, `meadow_mown`, `meadow_hay`) oraz roślinność miedz i ugorów, zostawiając jako otwarte zadanie brak modelu 3D bel słomy/siana. Na otwartych podlaskich polach z połowy sierpnia (D68, zdjęcia referencyjne CC BY 4.0 `Data/raw/refs/commons-fields-summer/cs157787294.jpg` i `cs158450905.jpg`, `docs/LICENSES.md`) okrągłe bele słomy na ścierniskach i białe bele sianokiszonki owinięte folią na skoszonych łąkach są jednym z najbardziej charakterystycznych akcentów skali i rytmu krajobrazu widzianego z kabiny.

## Decyzja

### 1. Generator 2 wariantów bel i wspólny materiał/atlas (`tools/worldgen/streetscape/field_bales.py`)
- **Dwa prototypy instancjonowane** w `street_props.glb`, współdzielące **jeden nieprzezroczysty materiał** `field_bale` (`rough = 0.80`, bez połysku plastiku, bez testu alfa) i **jeden wspólny atlas 512 × 512 sRGB** `field_bale_atlas.png` (4 ćwiartki po 256 × 256 px z 12 px marginesem krwawienia pod kompresję ASTC i mipmapy; 0 marek/napisów, 100 % deterministyczny generator Python):
  - `bale_straw` — okrągła bela słomy leżąca na boku (`D = 1,38 m`, `L = 1,20 m`, `WORKING_VALUE`; zagłębienie spodu `SINK_M = 0,04 m` + lekkie spłaszczenie pod własnym ciężarem, delikatna asymetria organiczna na LOD0). Atlas: gęste nakładające się źdźbła jasnozłotej słomy (paleta dopasowana do `cs157787294.jpg` i `KamionFieldMosaic.hlsl`), 5 pierścieni sznurka / delikatnej siatki, spiralne styczne źdźbła na ciemniejszych czołach, przyciemnienie kontaktu z gruntem od spodu.
  - `bale_silage` — okrągła bela sianokiszonki owinięta białą/lekko szałwiową folią stretch (`D = 1,26 m`, `L = 1,20 m`, `WORKING_VALUE`; miękkie poduszkowe fazowanie krawędzi, `SINK_M = 0,04 m`). Atlas: nakładające się pasy folii stretch bez przesyconej bieli (nie wypala się w słońcu), miękkie fałdy napięcia i delikatne zakurzenie przy ziemi; na czołach rozeta z 5 obróconych pasów folii.
- **Geometria i LOD:**
  - `LOD0`: **224 trójkąty** (`≤ 300`; 16 segmentów obwodowych × 6 pierścieni osiowych + 2 czoła).
  - `LOD1`: **60 trójkątów** (`~60`; 10 segmentów obwodowych × 2 pierścienie + 2 czoła; kąt między ściankami `36° < 38°` progu `export.crease_normals`, więc cylinder pozostaje gładko cieniowany z dystansu).
  - `.col`: uproszczony 6-boczny cylinder kolizji (`24` trójkąty).
  - **Brak impostora/billboardu LOD2:** mechanizm impostorów w `InstanceImporter.cs` (`trees_lod2.glb` + `Kamion/Vegetation _IMPOSTOR`) jest wyłącznie dla drzew (`tree_*`); dodanie osobnego materiału alfa-test dla bel podbiłoby draw calle i overdraw, podczas gdy nieprzezroczysty `LOD1` ma zaledwie 60 trójkątów na wspólnym materiale.
- **Rejestracja dynamiczna (jak `guide_posts.py`):** `field_bales.PROTOS` jest czyszczone na starcie `place()` i wypełniane tylko na kaflach wiejskich, gdzie faktycznie postawiono bele. Dzięki temu kafel miejski `bialystok-industrial-c` nie dostaje zmian w `art-source/world/props/street_props.glb` ani `props_meta.json`.

### 2. Polityka LOD i budżet draw calli (`InstanceImporter.cs`, `build_world.py`)
- Reguła `bale_*`: `LOD0 = 35 m`, `LOD1 / cull = 340 m` przy `lodBias = 1.0` (High `1.5×`: `52,5 m / 510 m`; Medium `0.8×`: `28 m / 272 m`; Low `0.5×`: `17,5 m / 170 m`; `WORKING_VALUE`).
- Przy 52,5 m na High (1080p, FOV 60°) bela ma ~24 px wysokości — 60-trójkątny gładki `LOD1` jest wizualnie nierozróżnialny od `LOD0`, a cienie rzuca tylko `LOD0` (`shadowLodMask = 0b001`).
- Wspólny materiał (1 submesh na prototyp) + próg `35 m` ograniczają przyrost draw calli instancji do **+≤ 2 na kamerę**.

### 3. Rozmieszczenie deterministyczne (`field_bales.plan_bales` / `place`)
- Wyłącznie **kafle wiejskie** (`not rid.startswith("bialystok-")`), wieloboki BDOT10k `OT_PTTR_A ≥ 2 ha`, ≥ 10 m wewnątrz granicy wieloboku, ≥ 12 m od dróg/placów/budynków, ≥ 4 m od drzew/krzewów, ≥ 3,5 m od miedzy, ≥ 5 m od granicy bloku, nachylenie terenu `≤ 18 %`.
- Siatka odkrywania pasów wyrównana do EPSG:2180 (krok 8 m) + wszystkie decyzje i pozycje liczone z `fid` (`vegetation.field_layout` / `field_use`) → wynik jest w 100 % deterministyczny i spójny na szwie między sąsiednimi kaflami.
- Mapowanie użyć mozaiki 0334 (`WORKING_VALUE`):
  - `stubble_baled` (78 % pasów) i `stubble` (32 % pasów) → `bale_straw`;
  - `meadow_mown` (42 % pasów) i `meadow_hay` (36 % pasów) → `bale_silage`;
  - pozostałe 12 użyć (zboże stojące, kukurydza, okopowe, talerzowane, ugór, pastwisko, nieskoszona łąka itp.) → 0 bel.
- Dwa naturalne układy wybierane per działka (`fid`):
  - **Rzędy wzdłuż ścieżek/przejazdów prasy** (65 % dla słomy, 45 % dla sianokiszonki): aktywne segmenty 140 m (48 % segmentów), co 34 m (±4,5 m jitter, losowe luki 25 %), oś cylindra poprzecznie do kierunku jazdy prasy (jak na `cs157787294.jpg`).
  - **Grupy przy krawędzi pola** (35 % dla słomy, 55 % dla sianokiszonki): zwarte szeregi 3–5 bel z odstępem 0,55 m wzdłuż jednej krawędzi działki.

## Pomiary (prototyp `knyszyn-w`, edytor Win64, visual-qa High 1920×1080 `-Pc`, `lodBias = 1,5`)

### Przebudowa i pamięć kafla `knyszyn-w` (4 km², kafel wiejski)
- `build_world.py --region knyszyn-w --context`: `281,7 s`, `terrain walls > 0,15 m: 0 (max 0,0)`.
- Wygenerowane bele: **244** łącznie (`bale_straw`: **155**, `bale_silage`: **89**; układ `row`: **180**, układ `edge`: **64**; średnio ~61 bel/km²; 0 bel na jezdni w `artifacts/world/knyszyn-w-props-on-road.txt`).
- Metadane `props_meta.json`: `bale_straw` i `bale_silage` — oba `materials: ['field_bale']`, `tris_lod0: 224`, `tris_lod1: 60`.
- `import-region.ps1 -Region knyszyn-w -BuildTarget Win64 -MaterialTier High`: `IMPORT_RESULT: OK`, `sha256 mismatches: 0`, instancje `13 315 → 13 559` (`+244`), prototypy `78 → 80` (`+2`).
- Pamięć świata (`WORLD_MEMORY`, ten sam build `knyszyn-w` bez bel → z belami):
  - `Low`: `56,0 → 56,1 MB` (`+0,1 MB`, `instances 5,7 MB`),
  - `High`: `137,3 → 137,3 MB` (`+0,0 MB`, `instances 5,7 MB`).

### Visual QA High (`-Pc`, 1920×1080, czyste A/B na tym samym buildzie `knyszyn-w`, `clear` i `overcast`)
Pomiar z `stats.txt` (`before_clean` bez bel → `after` z 244 belami; wartości identyczne dla `clear` i `overcast`):

| Kamera | Instanced draws (raw przed→po) | Δ draws samych bel (L0/L1) | Δ instancji (bele / przerzedz. drzew*) | Δ trójkątów exact | Δ shadowCasterDraws |
|---|---:|---:|---:|---:|---:|
| `dk65-fields-nw` | 35 → 36 (`+1`) | **`+1`** (6× `straw` L1) | `-3` (`+6` / `-9`) | `+252` | `+0` |
| `dk65-polna` | 85 → 86 (`+1`) | **`+1`** (3× `straw` L1) | `-4` (`+3` / `-7`) | `+96` | `+0` |
| `tykocka-dw671-out` | 96 → 99 (`+3`*) | **`+2`** (5× `silage` L1 + 1× `straw` L1) | `+11` (`+6` / `+5`) | `+420` | `+0` |
| `dk65-koscielna` | 130 → 130 (`+0`) | **`+2`** (3× `silage` L1 + 7× `straw` L1) | `+4` (`+10` / `-6`) | `+528` | `+0` |
| `dk65-seam-east-out` | 123 → 124 (`+1`) | **`+2`** (3× `silage` L1 + 14× `straw` L1) | `+11` (`+17` / `-6`) | `+948` | `+0` |
| `route-s1846` | 44 → 45 (`+1`) | **`+1`** (14× `straw` L1) | `+13` (`+14` / `-1`) | `+846` | `+0` |
| `route-s0710` | 96 → 96 (`+0`) | **`+1`** (3× `straw` L1) | `-2` (`+3` / `-5`) | `+120` | `+0` |
| `goniadzka-above` | 55 → 54 (`-1`) | **`+0`** (0 bel w kadrze) | `+3` (`0` / `+3`) | `+36` | `+0` |

\* Uwaga pomiarowa: `WorldInstances.cs` (linie 447/456) przerzedza odległe impostory drzew (`12` tris/szt.) testem `(i & (stride - 1)) == 0` po globalnym indeksie w tablicy `matrices[]`. Dopisanie 244 instancji bel przesuwa parzystość indeksów części komórek drzew, wprowadzając szum `±1..2` draw calli impostorów drzew (np. `tykocka-dw671-out`: `+6×60 + 5×12 = +420` tris = **`+2` draw calle bel** + `+1` draw call impostora drzew; `goniadzka-above` z 0 bel: `+3×12 = +36` tris, `-1` draw). **Wkład samych bel mieści się w budżecie `+≤ 2` draw calle na wszystkich 18 kamerach perspektywicznych `knyszyn-w` (maks. `+2`, śr. `+1,25` na 8 kamerach QA, `+0` shadowCasterDraws).**

### Ocena wizualna (`clear` i `overcast`) i testy
- Podgląd 3D w Blender 4.2 Cycles (`preview/bales_blender_preview.png`): czytelna faktura słomy ze sznurkiem i matowo-półmatowej białej folii stretch bez przesycenia, gładki profil `LOD0` i `LOD1`.
- Visual QA Unity High (`sbs_knyszyn-w_{clear,overcast}_part{1,2}.jpg`, zbliżenia `bales_closeup_2x.jpg`):
  - `dk65-koscielna`: białe bele sianokiszonki na skoszonej zielonej łące (60 m i 305–324 m) stabilnie osadzone na gruncie, bez przepalenia bieli w słońcu i bez nadmiernego kontrastu w `overcast`.
  - `route-s1846`: rząd jasnozłotych bel słomy wzdłuż ścieżki na ściernisku (246–413 m) spójny z referencją `cs157787294.jpg` w obu warunkach oświetlenia.
- Zestaw `pytest`: **141 passed** (`test_field_bales_0346.py`, `test_fields_0334.py`, `test_budget_0221.py`, `test_typology_0238.py`, `test_world_v31.py`, `test_hero_bridge.py`, `test_cc0_scans.py`, `test_streetscape.py`).
- Dowody zarchiwizowane w `artifacts/neon-bales-s24/` (zestawienia `sbs_knyszyn-w_{clear,overcast}_part{1,2}.jpg`, zbliżenia `bales_closeup_2x.jpg`, podgląd Blendera `preview/bales_blender_preview.png`, surowe klatki i `stats.txt` w `vqa/{before,before_clean,after}/`).

## Licencje i źródła
- Geometria i atlas `field_bale_atlas.png` w 100 % proceduralne (własny generator Python, brak marek, brak zewnętrznych pikseli w buildzie).
- Referencje wizualne (poza buildem i repo): `Data/raw/refs/commons-fields-summer/cs157787294.jpg` i `cs158450905.jpg` (Aw58, CC BY 4.0 — wpisane w `docs/LICENSES.md`).

## Otwarte
- Przebudowa pozostałych ~50 kafli wiejskich po scaleniu przez lidera (`build_world.py` + import) — kafel `knyszyn-w` jest prototypem tej gałęzi.
- Wariant zielonej folii sianokiszonki (osobny podwariant lub trzeci prototyp tylko jeśli budżet draw calli pozwoli na dodatkowy batch).
- Pomiar playera Windows (`pc-metrics`) na kaflu wiejskim przy kolejnym buildzie lidera.

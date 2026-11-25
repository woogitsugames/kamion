# ADR 0336 — Elewacje małomiasteczkowe Tykocina: stolarka okienna ze szprosami, nadproża, cokoły i zróżnicowanie dachów

Status: Proposed (agent `neon-tykocin-facades-s24`, gałąź `neon-tykocin-facades-s24`), 2026-11-24. Do scalenia przez lidera.
Powiązane: `artifacts/critic-s24-build5/CRITIC.md` (pkt 9; P0 „listopad” odrzucone — D68 lato wszędzie), ADR 0081 (`facade_atlas`, `facade_far`), ADR 0091 (dachy domów), ADR 0097 (paleta sąsiedztwa domów), ADR 0124 (okna LOD1), ADR 0238 (typologia zabudowy, bit-identyczność C/Dojlidy), ADR 0295 (domy drewniane Podlasia), ADR 0316 (stara dachówka i karpiówka), ADR 0320 / 0325 (Plac Stefana Czarnieckiego w Tykocinie).

## Kontekst
W krytyce buildu #5 (`CRITIC.md` pkt 9, klatki `t3441`, `t3371`) oraz na ujęciach kontrolnych `before` (`look_tykocin_rynek_n`, `look_tykocin_rynek_s`, `look_tykocin_zlota`, `look_tykocin_roofs_above`) zabudowa Tykocina miała trzy widoczne defekty:
1. **Okna czytały się jako czarne kwadraty bez ram i podziałów:**
   - niskie/spadziste budynki publiczne i usługowe przy Rynku (klasa `office`, m.in. Urząd Miasta / Biblioteka) dostawały antracytową stolarkę korporacyjną `office_d` i płaskie dachy (kod LoD2 `1130` nie był w `LOD2_PITCHED`);
   - domy (`house`) losowały niezależnie 4 komórki `facade_atlas`, w tym zamkniętą szarą roletę zewnętrzną (`i=2`) oraz ciemnozieloną/ciemną stolarkę (`i=1,3`) w głębokim glifie `REVEAL_ETICS = 0,22 m` rzucającym mocny cień;
   - brakowało nadproży i opasek okiennych, a na LOD1 okna domów nie miały widocznej ramy.
2. **Brak czytelnych cokołów:** stały `PLINTH_H["house"] = 0,25 m` względem `zref` znikał pod terenem po wyższej stronie spadku; brakowało też charakterystycznych dla Podlasia cokołów z kamienia polnego (`fieldstone_plinth`) oraz pasa cokołu na LOD1 domów.
3. **Powtarzalne dachy:** dominowała 3-pozycyjna paleta (`roof_tiles_red`, `roof_tiles_brown`, `roof_metal_graphite`), stały kąt domyślny dla dachów bez danych LoD2 oraz długie puste połacie bez lukarn.

Referencje (wyłącznie otwarte źródła lokalne, bez pikseli w zasobach, bez Google): zdjęcia Wikimedia Commons w `Data/raw/refs/tykocin-rynek-commons/` — m.in. `cs202183366.jpg` i `cs202183436.jpg` (Krzysztof Popławski, CC BY 4.0), `cs153250600.jpg` (Krzysztof Popławski, CC BY 4.0), `cs21721113.jpg` (Andwieczor, CC BY-SA 3.0 pl).

## Decyzja

### 1. Tryb `small_town` jako jawny override regionu (opt-in)
W `Data/Regions/tykocin/overrides.yaml` dodano wpis `tykocin-small-town-facades-0336` (`kind: facade_rules`, `small_town: true`). `streetscape.buildings_mesh.load()` ustawia flagę `small_town` wyłącznie na kaflach z takim wpisem — kafle Białegostoku (`bialystok-industrial-c`, `bialystok-dojlidy`) pozostają bit-identyczne z bazą ADR 0238.

### 2. Stolarka okienna ze szprosami, parapety i nadproża
- **Atlas `facade_atlas`** (`art-source/world/materials/_src/sets_buildings.py`, `_resid` dla `kind == "house"`):
  - 4 komórki `house` podzielone na dwie spójne pary kolorystyczne stolarki: biała malowana/PVC (`0, 2`, liniowe `0.76, 0.76, 0.73`) oraz ciepły brązowy drewniany lakier (`1, 3`, `0.26/0.145/0.08` i `0.22/0.12/0.065`) — `WORKING_VALUE`;
  - szersze ramy (`fw=0.072`, `sw=0.058`) i wyraźne szprosy: krzyżowy podział 4-szybowy (`muntins=(1, 2)`, półszerokość `mw=0.024 m`) w wariantach `0, 1` oraz klasyczne polskie nadświetle z poziomą belką (`transom=0.68`) w wariantach `2, 3`;
  - usunięta pełna szara roleta zewnętrzna z wariantu `2`; wszystkie 4 warianty mają firanki/zasłony/kwiaty w oknie oraz lekkie odbicie nieba na odsłoniętych szybach, żeby okno nie zapadało się w czerń z 30–60 m.
- **Spójność stolarki per budynek i budynki Rynku** (`buildings_mesh.py`):
  - każdy dom i niski/spadzisty budynek usługowy/publiczny (`office`, nie-pawilon, spadzisty lub ≤ 2 kondygnacje) dostaje deterministycznie **jedną** paletę stolarki na cały budynek: białą (`0, 2`) lub brązową (`1, 3`; udział brązowej 45 % dla 1-kondygnacyjnych/drewnianych, 30 % dla wyższych, `WORKING_VALUE`);
  - niskie/spadziste budynki `office` w trybie `small_town` rezygnują z `office_d` i okien wstęgowych zarówno na LOD0 (używają komórek `house`), jak i na LOD1 (jasna grupa `office`);
  - płytszy glif muru historycznego `REVEAL_SMALL_TOWN = 0,13 m` (zamiast `0,22 m` ocieplenia ETICS, `WORKING_VALUE`);
  - pogrubione/szersze parapety (`bold_sill`, te same 4 trójkąty, 0 nowych draw calli) oraz nadproża i opaski okienne 3D (`facade_kit.window_trim`, 6 trójkątów nadproża + opcjonalnie 4 trójkąty pionowych opasek u 55 % budynków murowanych, materiał `reveal_plaster` — 0 nowych materiałów);
  - okna LOD1 domów dostają cienką ramę `SMALL_TOWN_LOD1_FRAME_M = 0,10 m` w istniejącym materiale z tego samego chunku (0 nowych draw calli).

### 3. Cokoły (38–60 cm, odporne na spadek, tynk + kamień polny)
- W trybie `small_town` domy i budynki `office` (bez witryn) dostają cokół o deterministycznej wysokości `SMALL_TOWN_PLINTH_HS = (0.38, 0.45, 0.52, 0.60) m` (`WORKING_VALUE`), podniesiony co najmniej do `zg85 + 0,35 m` (85. percentyl rzędnych terenu na obrysie, ograniczony pod okapem), dzięki czemu cokół pozostaje widoczny również na pochyłych działkach.
- ~45 % domów 1-kondygnacyjnych / drewnianych i ~25 % wyższych domów dostaje istniejący materiał `fieldstone_plinth` (kamień polny, 0 nowych zestawów PBR), pozostałe `plinth_dark` (ciemny tynk).
- Pitched `house` dostaje również pas cokołu `plinth_dark` na LOD1 (`lod1_wall`), żeby cokół nie znikał na średnim dystansie i na tierze Low.

### 4. Dachy: paleta 7 pokryć, kąt połaci, kod LoD2 `1130` i lukarny
- **Paleta 7 materiałów** (`SMALL_TOWN_ROOFS`, `SMALL_TOWN_ROOFS_PITCHED`, `roof_variant` w `buildings_mesh.py`): deterministyczny dobór z unikaniem powtórzeń u sąsiadów z użyciem wyłącznie istniejących zestawów PBR — `roof_tiles_red` (28 %, rozdzielane dalej na standardową, `roof_karp_red` 22 % i `roof_tiles_old` 24 %), `roof_tiles_brown` (18 %), `roof_metal_graphite` (16 %), `roof_cement_grey` (15 %), `roof_sheet_grey` (14 %), `roof_tiles_old` (9 %) (`WORKING_VALUE`). Na LOD1 warianty `roof_karp_red` i `roof_tiles_old` mapują się na `roof_tiles_red` (`ROOF_LOD1_SMALL_TOWN`), ograniczając liczbę submeshy Low.
- **Kod LoD2 `1130`:** w trybie `small_town` `typology.LOD2_PITCHED_SMALL_TOWN` dopuszcza kod `1130` jako dach dwuspadowy dla `office`/`block`, o ile zmierzone wzniesienie LoD2 wynosi ≥ `1,5 m`.
- **Rozrzut kąta połaci LoD1** (`roofs.SMALL_TOWN_PITCH`): gdy brak wysokości LoD2, deterministyczny kąt per budynek zamiast jednej stałej (`gable`: 33°–47°, `hip`: 24°–36°, `mono`: 14°–24°, `WORKING_VALUE`).
- **Lukarny dwuspadowe** (`roofs.dormer_spots`, `facade_kit.dormer`): na kwalifikujących się dachach dwuspadowych (`slope ≥ 32°`, wzniesienie ≥ 2,25 m, kalenica ≥ 8,5 m, udział 48 %, preferowana połać od ulicy), z kontrolą zawierania w obrysie, omijaniem kominów (≥ 1,7 m) i skrzydeł `MultiRoof`. Tylko LOD0, ~34 trójkąty na lukarnę, 0 nowych materiałów.

## Wyniki i budżety (zmierzone)

### Generator (`tykocin`, przebudowa `build_world.py --region tykocin --context`, 594,7 s, `terrain_walls = 0`)
- Budynki w trybie `small_town`: **482** (stolarka biała **309**, brązowa **173**), cokoły kamienne `fieldstone_plinth`: **108**, lukarny dwuspadowe: **170**, nadproża/opaski okienne: **50 764** trójkątów LOD0.
- Rozkład materiałów dachów (7 pokryć): `roof_tiles_brown` 82, `roof_tiles_red` 74, `roof_metal_graphite` 61, `roof_cement_grey` 50, `roof_sheet_grey` 47, `roof_tiles_old` 40, `roof_karp_red` 32.
- Dachy spadziste budynków niemieszkalnych (kod LoD2 `1130` w `small_town`): `biurowiec:gable:lod2_rise` **4 → 13** (+9), `pawilon:gable:lod2_rise` **1 → 7** (+6).
- Okna LOD1 domów z ramami (`lod1_house_openings_framed`): **0 / 5 416 → 5 171 / 5 196** (fallback mat = 0).
- Manifest kafla `tykocin` (`41b5956dd` → `HEAD`):
  - wszystkie warstwy: `13 088 973 → 13 180 440` (**+91 467**, **+0,70 %**);
  - `buildings` (LOD0): `416 418 → 463 850` (+47 432, +11,39 %);
  - `buildings_lod1` (LOD1): `65 286 → 109 220` (+43 934, +67,29 % — ramy okien i cokoły LOD1 domów);
  - unikalne materiały regionu: **375 → 375** (+0 nowych materiałów); submeshe per chunk: `1 502 → 1 551` (+49);
  - GLB High: `518,98 → 523,93 MB` (+4,94 MB); GLB Low: `206,69 → 207,54 MB` (+0,85 MB);
  - tekstury PBR `facade_atlas` (estymata ASTC z mipami, `materials_spec.json`): High `17 420 342 B`, Medium `3 809 826 B`, Low `611 669 B` (**+0 B**).

### Import Unity Win64 i visual-qa przed | po (`artifacts/neon-tykocin-facades-s24/`)
- Import `tykocin` Win64 (`RegionImporter.ImportBatch`, `-tiers Low,High -materialTier Medium`): `IMPORT_RESULT: OK region=tykocin chunks=64 corridor=36 tiers=Low+High`.
- Pamięć zaimportowanego świata (`WORLD_MEMORY`):
  - Low: `83,0 → 86,6 MB` (+3,6 MB; `buildings 17,0 → 20,6 MB`);
  - High: `184,1 → 189,0 MB` (+4,9 MB; `buildings 26,2 → 31,1 MB`).
- Visual-qa (21 klatek przed i 21 klatek po: 9 kamer `High-clear`, 9 `High-overcast`, 3 `Low-clear`; arkusze porównawcze w `sbs/`):
  - **High** (9 kamer, `stats.txt` przed SRP batching): `drawsEst` `3 482 → 3 492` (**+10** łącznie, zakres **−6…+14** na kamerę; `look-tykocin-rynek-n` `304 → 300`, `look-tykocin-zlota` `394 → 393`, `look-tykocin-plaza-se` `409 → 410`), trójkąty `9 633 515 → 9 785 715` (**+1,58 %**, maks. `route-s1121` `1 512 061` < 2 M).
  - **Low** (3 kamery): `drawsEst` `727 → 747` (**+20** łącznie, 170–300/kamerę), trójkąty `724 511 → 774 332` (**+6,88 %**, maks. `route-s1441` `294 549`).
  - Ocena wzrokowa przed | po (clear + overcast + Low): czarne kwadraty okien `office_d` przy Rynku (`look-tykocin-rynek-n`, `look-tykocin-plaza-se`) i szare rolety (`look-tykocin-zlota`) zniknęły; czytelna biała i brązowa stolarka ze szprosami/nadświetlami, nadproża i parapety, cokoły tynkowe i z kamienia polnego (`route-s1441`, `look-tykocin-zlota`, `look-tykocin-rynek-n`), 7 pokryć dachów i lukarny bez artefaktów czy przenikań (`look-tykocin-roofs-above`).

### Testy automatyczne (`pytest`)
- `tests/gis/test_tykocin_facades_0336.py` (5 testów: override opt-in, dach `1130`, spójność stolarki i brak `office_d`, cokoły kamienne/LOD1/nadproża, 7 pokryć/kąty/lukarny bez zdegenerowanych trójkątów).
- Testy budżetowe i typologii (`test_budget_0221.py`, `test_typology_0238.py`, `test_world_v31.py`, `test_hero_bridge.py`): zielone.
- Poprawki po scaleniu fali 8 (`neon-testfix-s24`): `test_dom_klattow_0305.py::test_materials_and_sets` zaktualizowany pod obecność `roof_tiles_old` w `BM.ROOF_OVERRIDES` (wymagane przez `SMALL_TOWN_ROOFS` i `house_roof_material`; `log_wall_white` nadal poza `HOUSE_WALL_OVERRIDES`), `test_ring_0231.py::test_authored_files_present_and_consistent` rozszerzony o schemat reguł na poziomie regionu (`facade_rules`/`building_rules`/`lamp_policy` bez `target`/`set`), oraz `test_tykocin_facades_0336.py` i `test_wood_house_p1_s24.py` dostosowane do 5-krotki `Acc.d` (`V, T, UV, UV1, COL`) wprowadzonej przez `neon-bronze-s24`.

## Otwarte / UNVERIFIED
- Wartości proporcji i udziałów (`SMALL_TOWN_PLINTH_HS`, `REVEAL_SMALL_TOWN`, `SMALL_TOWN_PITCH`, `DORMER_*`, udziały kolorów stolarki i dachów) są `WORKING_VALUE` — dobrane na podstawie zdjęć Commons, nie z inwentaryzacji każdego domu.
- Pomiar czasu klatki i pamięci w buildzie Windows (`pc-metrics.ps1`) pozostaje po stronie lidera po scaleniu; w niniejszym zadaniu zmierzono wyłącznie pamięć importu oraz estymaty kamer w edytorze (`stats.txt`).
- Tryb `small_town` włączony jest na razie wyłącznie dla `tykocin` — ewentualne rozszerzenie na `knyszyn` / `monki` wymaga osobnej decyzji i weryfikacji wizualnej.

# ADR 0344 — Deska rozdzielcza kabiny TRAKT: jasne przedmioty kierowcy dla fizycznego odbicia w przedniej szybie

Status: Proposed (`neon-dash-items-s24`, 2026-11-24; numer zarezerwowany przez lidera).
Uzupełnia: ADR 0341 (szyba: odbicie deski z wypieczonej panoramy), `docs/06` (anti-slop, §4 „odbicia deski”), `docs/07` (budżety kabiny TRAKT, brak obcych marek), `DRAFT-d84` (kabina PC). Wartości albedo i rozmieszczenia przedmiotów: `WORKING_VALUE`.

## Kontekst
ADR 0341 dodał w shaderze `Kamion/Truck Glass` (`MI_Ext_Glass`) warstwę odbicia kabiny z wypieczonej panoramy z oka lustrzanego (`T_CabWindscreenReflection.png`). Przy zatwierdzonej czarnej desce (albedo 0,035–0,045) odbicie było jednak fizycznie niewidoczne na tle drogi (`p50 = 0,00`, poniżej 1 kodu sRGB), tak jak w prawdziwej pustej ciężarówce. Zgodnie z ADR 0341 nie podbijamy wzmocnienia shadera ponad fizyczny Fresnel pojedynczej powierzchni (`F1 ≈ 0,045`) — zamiast tego realistyczny, subtelny refleks w dolnej strefie szyby dają typowe jasne przedmioty kierowcy leżące na desce.

## Decyzja
1. **Generator przedmiotów na desce (`build_dash_items` w `tools/blender/truck/interior/build_interior.py`):**
   Dodano 4 typowe, bezmarkowe (fikcyjna ciężarówka TRAKT) przedmioty kierowcy, dopasowane do krzywizny deski (`dash_surface_z`) i ukształtowane proceduralnie z lekką asymetrią (bez sterylnej symetrii i bez nieczytelnego tekstu AI):
   - **Podkładka/teczka + 2 kartki dokumentów przewozowych (CMR/WZ) + klips** w środkowej tacce (`x ∈ [0,00; 0,38]`): granatowa podkładka (`folder_cover`), dwie lekko skręcone i delikatnie pofałdowane biało-kremowe kartki (`paper_doc`, albedo liniowe `(0,84; 0,81; 0,75)` `WORKING_VALUE`) z subtelnymi poziomymi pasmami cieniowania wierzchołkowego oraz metalowy klips sprężynowy (`satin`).
   - **Wydruk z tachografu (pasek papieru termicznego 57 mm)** między daszkiem zegarów a środkową tacką (`x ≈ -0,172`): lekko asymetrycznie podwinięty pasek (lewy koniec +13 mm, prawy +5,5 mm; `paper_tacho`, albedo liniowe `(0,86; 0,87; 0,85)` `WORKING_VALUE`) z delikatnymi poprzecznymi pasmami nadruku w kolorze wierzchołków.
   - **Niski uchwyt przyssawkowy z czarnym telefonem (poziomo)** przy lewym słupku A (`x = -0,89; y = 1,155`): podstawa gumowa wpuszczona w spadek deski (brak lewitacji), krótkie ramię, uchwyt i czarny smartfon 146×71 mm z wyłączonym ekranem (`rubber`, `dash_dark`, `dash_mid`, `metal_dark`, `piano`), skierowany ku `EYE_POINT` na tyle nisko (~9,5 cm nad deską), by nie zasłaniał drogi, lusterek ani zegarów.
   - **Złożona ściereczka z mikrofibry** w tacce pasażera (`x ≈ 0,570`): dwie nakładające się warstwy ze stopniem na krawędzi złożenia i lekkim pofałdowaniem (`dash_cloth`, albedo liniowe `(0,42; 0,49; 0,54)` `WORKING_VALUE`).
2. **Poprawka próbkowania AO dla obiektów `INHERIT_AO`:**
   `dash_tray_lip_*` oraz `dash_item_doc_clip` otrzymały jawny punkt `ao_probe` poza cieniem kontaktowym przedmiotów w tacce, dzięki czemu ramki tacek i klips nie czernieją po wypieku atlasu AO.
3. **Wspólne sloty materiałowe i redukcja LOD (`tools/blender/truck/interior/a6_export.py`):**
   - **0 nowych slotów materiałowych i 0 nowych tekstur runtime**: `paper_doc`, `paper_tacho`, `folder_cover` mapowane na istniejący slot `MI_Cab_Plastic`, a `dash_cloth` na `MI_Cab_Fabric`; wszystkie `dash_item_*` dostały wagę wysokiej gęstości w atlasie AO (`texel_weight`).
   - Na `LOD2` odrzucane są drobne detale (`dash_item_doc_clip`, `dash_item_doc_sheet_1`, `dash_item_phone_jaw_`, `dash_item_phone_arm`) w `LOD2_DROP`, aby utrzymać limit 22 000 trójkątów.
4. **Ponowny wypiek panoramy odbicia (`bake_windscreen_reflection.py`):**
   Wygenerowano nową panoramę `game/Assets/_Project/Rendering/Textures/Truck/T_CabWindscreenReflection.png` (1024×512) z nowego `SM_CabInterior_LOD1.fbx` i `T_Cab_AO_LOD1.png`. Maksymalna wartość liniowa w panoramie wzrosła do `0,565` (p99 wnętrza `0,352`) wobec `0,035–0,045` samej czarnej deski.

## Zmierzone
1. **Budżet geometrii i walidacja eksportu (`check_export.py` — `CHECK PASS`):**
   - `LOD0`: `105 163 → 106 130` / `120 000` tris (`+967`, `+0,92 %`), 22 meshe, 0 nowych slotów.
   - `LOD1`: `44 003 → 44 457` / `45 000` tris (`+454`, `+1,03 %`), 22 meshe.
   - `LOD2`: `21 557 → 21 787` / `22 000` tris (`+230`, `+1,07 %`), 20 meshy.
2. **Widoczność zegarów i ekranu (`sightline_test.py` — `SIGHTLINE PASS`):**
   - `0,0 %` zasłonięcia zestawu wskaźników (`cluster:*`) i ekranu nawigacji (`info:whole_screen`) zarówno dla nominalnego `EYE_POINT`, jak i w całym `headbox`.
   - Z kamer `cab-driver` droga, pasy, pachołki oraz lewe lusterko pozostają w 100 % niezasłonięte.
3. **Pętla wizualna `visual-qa` (`DrivingLab`, PC High, 2340×1080, `cab-driver` i `cab-dash`, `clear`, `lowsun`, `overcast`, przed = `main 71336ba56`, po = ta gałąź + `rq_glassdbg=2`):**
   - **Czytelność drogi zachowana (`windscreen_measure.py`):** kontrast drogi (`hp-sigma`) `×1,00` we wszystkich 6 kadrach; mediana dodanego światła na całej szybie `p50 = 0,00` (zero mlecznej zasłony).
   - **Odbicie w dolnej strefie szyby nad przedmiotami** (orientacja i kształt potwierdzone w `after2-dbg2` ×8 oraz na wycinkach 1:1 `inspect2/refl_crop_*`):
     - `cab-driver` (strefa szyby nad paskiem/dokumentami/ściereczką `x∈[1260,2260], y∈[640,790]`): przyrost p99 liniowy `×100` = `+0,21` (`clear`), `+0,35` (`lowsun`), `+0,35` (`overcast`); top 5 % strefy względem jasności tła asfaltu: **`+2,7 %` (`clear`)**, **`+7,5 %` (`lowsun`)**, **`+6,6 %` (`overcast`)** (`+1,0..+2,7` kodów sRGB 8-bit — subtelny, fizyczny refleks bez sztucznego wzmocnienia).
     - `cab-dash` (strefa szyby `x∈[1080,2200], y∈[350,480]`): przyrost p99 liniowy `×100` = `+0,41` (`clear`), `+0,49` (`lowsun`), `+0,52` (`overcast`); top 5 % względem tła: **`+16,8 %` (`clear`)**, **`+40,6 %` (`lowsun`)**, **`+39,6 %` (`overcast`)** (`windscreen_measure.py` `pane p99`: `0,73→1,35` clear, `0,79→1,45` lowsun, `0,67→2,08` overcast).
4. **Testy automatyczne:**
   - Unity EditMode Win64 (`editmode-20261124-180411.xml`): **1429 passed, 0 failed, 121 skipped** (1550 total).
   - Testy budżetowe GIS (`test_budget_0221.py`, `test_typology_0238.py`, `test_world_v31.py`, `test_hero_bridge.py`): **62 passed, 0 failed**.
   - Wydajność runtime w playerze Windows / Android: `UNVERIFIED` (0 nowych draw calli/materiałów/tekstur, `+967` tris na LOD0 w kabinie).

## Odrzucone / otwarte
- **Podbicie `_CabReflectionGain` ponad fizykę (`> 1,0`):** odrzucone zgodnie z ADR 0341 i `docs/06` — w jasny dzień na jasnym asfalcie odbicie papieru na prawie pionowej szybie (`1,5°`, `F1 ≈ 0,045`) jest z natury subtelne, a mocniej ujawnia się w `lowsun`, `overcast` i na tle ciemnych obiektów (drzewa, cienie na trasie).
- **Własny atlas/tekstura z nadrukiem tabeli CMR lub podświetlonym ekranem telefonu:** odrzucone w tej iteracji (0 nowych tekstur/draw calli, ekran telefonu wyłączony, brak ryzyka artefaktów tekstu).
- **`SM_CabInterior_LOD0.fbx` poza gitem** (znane z `DRAFT-d84`): lider po scaleniu w `main` musi wyeksportować `LOD0` (`blender -b --factory-startup --python tools/blender/truck/interior/a6_export.py -- --lods 0 --keep-leather-maps`) albo skopiować `SM_CabInterior_LOD0.fbx` z worktree przed uruchomieniem `TruckAssetBuilder.BuildBatch`.

## Dowody
`artifacts/neon-dash-items-s24/`: `before/`, `after2/`, `after2-dbg2/`, `compare2/` (`measure.txt`, `pair_*`, `diff_*`), `inspect2/` (zrzuty 960 px + 1:1 wycinki strefy odbicia `refl_crop_*` + `T_CabWindscreenReflection_960.jpg`), `blender_check/`.

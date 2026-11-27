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

## Dopisek (2026-11-25, `neon-wheel-s24`) — weryfikacja spójności przycisków kierownicy (`CRITIC.md` build #8 pkt 10)
- **Diagnoza:** Raport `artifacts/critic-s24-build8/CRITIC.md` pkt 10 wskazał: „kierownica z przyciskami tylko w t1380 i t3330, w pozostałych klatkach gładka”. Analiza 31 klatek nagrania (`critic_wheel_sheet.jpg`), geometrii (`build_interior.py`, `a6_export.py`) oraz rigu (`TruckAssetBuilder.cs`, `TruckVisualRig.cs`) wykluczyła błąd LOD, osobny mesh przycisków lub culling:
  - Wszystkie elementy kierownicy (wieniec `MI_Cab_Leather`, ramiona i przyciski `MI_Cab_Plastic`, piktogramy `MI_Cab_Decal`) są eksportowane w **jednym** meshu i rendererze `STEERING_WHEEL_LOD0` (14 302 tris, 5 submeshy; +0 dodatkowych draw calli).
  - `TruckVisualRig.InteriorLodFor(tier)` używa `LOD0` na wszystkich tierach (`Low`..`Ultra`) z jednym poziomem w `interiorGroup` (`interiorCull = 0,12`).
  - Przyczyną obserwacji z build #8 jest wyłącznie kąt skrętu kierownicy względem zatwierdzonego kadru `cab-driver` (ADR 0294: pionowe FOV `70°`, wzrok `6°` w dół): boczne ramiona z przyciskami są opuszczone o `SPOKE_ANG = -14°` (`r_c = 0,150 m`, by nie zasłaniać zegarów — `sightline_test.py = 0,0 %`), więc przy jeździe na wprost (`0°`, 29/31 klatek) środek piasty leży na `NDC_Y = -1,043`, a pody przycisków na `NDC_Y = -1,181` (górna krawędź `-1,095`, poniżej dolnej krawędzi kadru). Przy skręcie w prawo (`+35°`, jak w `t3330`) lewy panel obraca się w górę do kadru (`NDC_Y ≈ -0,86`), a na rondzie (`+180°`, jak w `t1380`) oba panele wchodzą w kadr (`NDC_Y ≈ -0,91`) wraz z dolnymi ramionami V u góry.
- **Zmiany i weryfikacja (bez zmian geometrii/kadru ADR 0294 i bez zmian `ProjectSettings`):**
  - Dodano parametr `-SteerDeg` (`-qaSteerDeg`) w `scripts/visual-qa.ps1` i `VisualQaRunner.cs` do deterministycznego renderowania kabiny pod zadanym kątem kierownicy.
  - Dodano testy regresyjne EditMode `SteeringWheelVisibilityTests.cs` (jeden renderer z wieńcem/przyciskami/piktogramami, aktywność i brak cullingu dla kątów `-540°…+540°` i tierów `Low`..`Ultra` z zapasem `0,6×` `lodBias`, oraz projekcja podów przy `0°`, `+35°`, `+180°`): **16/16 passed** (z `TruckCabGlassTierTests`, `CabInteriorRimAoTests`, `CabInteriorWearTests`).
  - Pętla `visual-qa` (`DrivingLab`, High PC, 1920×1080, `clear` i `overcast`, kamery `cab-driver` i `cab-hub`, kąty `0° / +35° / +180°`): identyczny budżet dla wszystkich kątów (`cab-driver`: `127` obiektów, `147` `drawsEst`, `173 847` tris; `cab-hub`: `21` obiektów, `42` `drawsEst`, `171 727` tris; `+0` draw calli). Dowody w `artifacts/neon-wheel-s24/`.


## Dopisek (2026-11-27, `mirror-housing-s24`) — kartki z załamaniami i niższym albedo; kafel ostrzeżenia jako lampka

Źródło: krytyk build #10 („biała kartka na desce”, papiery „jak biała płyta bez załamań”, plakietka POSTOJOWY „płaska jak naklejka
UI”). Status: Proposed, ocenia `visual-critic`. Wartości `WORKING_VALUE`.

1. **Albedo papieru:** `paper_doc` liniowo (0,84; 0,81; 0,75) → (0,585; 0,565; 0,520) (sRGB ≈ 0,78), `paper_tacho` (0,86; 0,87; 0,85)
   → (0,60; 0,605; 0,59). Dotyczy wszystkich LOD (kolor wierzchołków). Panorama odbicia w szybie wypieczona ponownie
   (`bake_windscreen_reflection.py`) — jasne kształty są ciemniejsze o ten sam czynnik (~0,69), czyli refleks z ADR 0344 słabnie
   proporcjonalnie; nie mierzono ponownie `windscreen_measure.py` (`UNVERIFIED`).
2. **Załamania (tylko LOD0; LOD1/LOD2 mają stare siatki):** obie kartki CMR to arkusze złożone „na trzy” i rozłożone — linie zgięcia
   mają własne kolumny wierzchołków (wąskie V, dolina przy u = −0,34, grzbiet przy +0,31), panele leżą pod różnymi kątami, górna
   kartka ma dodatkowe zgięcie poprzeczne i odstający prawy koniec; nadruk formularza (dwa pola nagłówka, wiersze, blok pieczęci)
   i przybrudzone krawędzie w tincie wierzchołków, bez tekstu. Pasek tachografu: jedno ostre zgięcie i gęstsze pasma wydruku.
   Cień kontaktowy kartek pochodzi z atlasu AO (wypieczony ponownie, 4096 spp). Zero nowych tekstur, slotów i draw calli.
3. **Kafel ostrzeżeń HUD (monitor)** — `DrivingHud.TelltaleLens()`: 9-slice 64 px, biały (kolor kafla go barwi): ciemna ramka z
   zaokrągleniem i światłem na górnej krawędzi, soczewka cofnięta w ramce (cień pod górną krawędzią, odblask przy dolnej),
   podświetlenie jaśniejsze w środku niż przy brzegu, miękki cień na panelu. Tekst i kolory z `UiPalette` bez zmian. Dowód kadru:
   `KAMION_QA_PARK=1` zapala kafel w kamerach kontrolnych (edytor nie ma żywego pojazdu).
4. **Eksport na maszynie z blokadą SAC:** `a6_export.py --keep-plastic-maps` (analogicznie do `--keep-leather-maps`) zostawia
   zatwierdzone `T_Cab_Plastic_*` bajt w bajt, gdy krok `plastic_grain.py` przez `uv` nie może wystartować (os error 4551, 27.11).

**Zmierzone (budżet kabiny, docs/07 §3 — osobny budżet wnętrza, limity z `check_export.py`):** LOD0 106 130 → **107 305** / 120 000
(+1 175, +1,1 %), LOD1 44 457 → 44 457 / 45 000, LOD2 21 787 → 21 787 / 22 000; 22 / 22 / 20 meshy, 0 nowych slotów. `CHECK PASS`,
`SIGHTLINE PASS`. Kamery kabiny (edytor, PC High, 1920 × 1080, clear) przed | po: `cab-driver` 236 | 236 `drawsEst`, 176 279 | 177 455
trójkątów; `cab-hub` 43 | 43, 171 755 | 172 931; `cab-dash` 240 | 240, 176 437 | 177 613.
**Dowody:** `artifacts/mirrors-trailer-s24/r2/` — `cmp_cab-dash.jpg`, `cmp_cab-driver.jpg`, `dash_before_zoom.jpg` | `dash_after_zoom.jpg`, `iter2/tile.jpg` (kafel ×2).
**Otwarte:** nadruk w tincie ma rozdzielczość siatki (6-10 mm) — z fotela czyta się jako szare wiersze, nie jako formularz; ostry
druk wymaga pasma w atlasie decali (osobna runda); ocena jasności papieru w słońcu na buildzie Windows.

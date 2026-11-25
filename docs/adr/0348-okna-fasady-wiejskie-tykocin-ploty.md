# ADR 0348 — Okna i fasady domów wiejskich / Tykocina (wnęka 8–12 cm, rama 3D, parapet, odbicie nieba, cokół, 2–3 odcienie tynku) oraz warianty płotów bez powtarzalnego żółtego płotka

Status: Proposed (agent `neon-windows-s24`, gałąź `neon-windows-s24`), 2026-11-25. Do scalenia przez lidera.
Powiązane: `artifacts/critic-s24-build8/CRITIC.md` (pkt 9, klatki `t2480`, `t2590`, `t2700`), ADR 0081 (`facade_atlas`, `facade_far`), ADR 0097 (paleta sąsiedztwa i zacieki pod parapetami), ADR 0114 / 0124 (`plot_kit`), ADR 0238 (typologia i bit-identyczność C/Dojlidy), ADR 0295 (domy drewniane Podlasia), ADR 0305 (Dom Klattów), ADR 0316 (płoty `picket_wood`/`picket_paint`/`chainlink_galv`), ADR 0336 (elewacje Tykocina), D68 (lato wszędzie).

## Kontekst
W krytyce buildu #8 (`artifacts/critic-s24-build8/CRITIC.md`, pkt 9; klatki `t2480`, `t2590`, `t2700`) wskazano trzy powtarzające się wady zabudowy wiejskiej wzdłuż DW671 i w Tykocinie:
1. **Okna jako ciemne plamy bez czytelnych ram i parapetów:**
   - kafel wiejski `dw671-tykocin-09` miał puste `overrides: []` (`small_town=False`), więc wszystkie domy wiejskie dostawały głęboki ciemny glif `REVEAL_ETICS = 0,22 m`, brak ram LOD1 (`0 / 288`), brak cokołów kamiennych i spójnej stolarki z ADR 0336;
   - materiał `facade_atlas` miał `"sky_occ": [0.5, 0.9]`, co w `WorldPBR.shader` wygaszało **90 %** odbicia nieba na poziomych promieniach z ulicy i kabiny, a warianty `house` w `sets_buildings.py` miały zbyt ciemną szybę;
   - parapet `window_sill` (`color: [0.45, 0.45, 0.45], metal: 0.6`) renderował się jako ciemnoszara metaliczna listwa zamiast jasnego parapetu zewnętrznego.
2. **Fasady jednobarwne bez akcentów materiałowych:**
   - każdy dom tynkowany otrzymywał jeden płaski materiał `plaster_*` na wszystkich ścianach i szczytach;
   - zacieki pod parapetami (`SILL_CLEAN = 0.40` × pominięcie `28 %` końców w shaderze) były widoczne tylko na części okien, a cokoły wymagały wyraźniejszego odcięcia (0,3–0,6 m).
3. **Powtarzalny żółty płotek (`t2480` po prawej, `t2590` po lewej):**
   - w `plots.py` tabela `PICKET_PAINTS` zawierała nasyconą żółtą ochrę `((0.910, 0.540, 0.108), 0.16)` i bardzo jasny żółtawy krem `((1.330, 1.200, 0.860), 0.12)`, a `plot_kit.py` miał jasnobeżowe `picket_wood` `(132, 86, 54)`;
   - brakowało unikania powtórzeń stylu między sąsiednimi działkami (`plots.plan()`), a wiejskie działki (`old`) nie miały pełnego zestawu 4 rodzin (brakowało nowoczesnych paneli ogrodzeniowych i murków kamiennych z przęsłami).

Referencje (wyłącznie otwarte źródła lokalne, zero pikseli w zasobach, zakaz Google): Wikimedia Commons `Data/raw/refs/tykocin-rynek-commons/` (`cs202183366.jpg`, `cs153250600.jpg`) oraz `Data/raw/refs/posesje/` (`cmFile_Drewniany_dom_przy_ulicy_11_Listopada_27_w_Tykocinie_za_siatk_.jpg.jpg`, `cmFile_Dom_z_mansardowym_dachem_poro_ni_ty_pn_czami_w_Tykocinie.jpg.jpg`).

## Decyzja

### 1. Okna domów jednorodzinnych / wiejskich (generator, 0 nowych draw calli)
- **Wymiary typologiczne (`WORKING_VALUE`, polska zabudowa jednorodzinna/wiejska):**
  - standardowe okno parteru/piętra: `1,20 × 1,40 m` (`facade_atlas.KINDS["house"]`, `buildings_mesh.facade_openings`);
  - okno szczytowe poddasza mieszkalnego: `1,20 × 1,40 m` lub `0,90 × 1,10 m`, strychu nieużytkowego: `0,60 × 0,60 m` (`attic_window`);
  - cofnięta wnęka (glif): `REVEAL_SMALL_TOWN = 0,10 m` (murowane) i `REVEAL_SMALL_TOWN_WOOD = 0,08 m` (drewniane) — w zakresie `8–12 cm` (`WORKING_VALUE`).
- **Rama 3D + podział (słupek / ślemię) + atlas z normalną:**
  - `art-source/world/materials/_src/sets_buildings.py` (`_resid`, `kind == "house"`): 4 warianty stolarki — biała PCV (`0, 2`, liniowe `0.78/0.78/0.75`), brązowa PCV (`1`, `0.25/0.138/0.074`) oraz postarzane drewno ze słojami dla starych domów (`3`, `0.27/0.160/0.090`, `frame_r=0.58`); wyraźny relief wysokości (`glass_h = -0.058 m`) dla mapy normalnych; podział krzyżowy (`muntins=(1, 2)`) oraz klasyczne polskie nadświetle (`transom=0.68`).
  - `buildings_mesh._house_frame_3d`: w trybie `small_town` dodaje w cofniętej wnęce geometrię 3D ramy obwodowej (`fw ≤ 0,068 m`), środkowego słupka (`mw = 0,026 m`) i poziomego ślemienia/szprosu (`th = 0,024 m`) jako czworokąty mapowane na istniejące próbki `facade_atlas` (`sw_pvc_white`, `sw_pvc_brown`, `sw_wood`) — **+0 draw calli, +0 materiałów**.
- **Jasny parapet zewnętrzny:** w trybie `small_town` (`bold_sill=True`) parapet korzysta z jasnego materiału `reveal_plaster` (`[0.60, 0.59, 0.56], rough=0.85, metal=0`, na domach drewnianych `wood_trim_white`), wysunięty `4,2 cm` przed lico muru i `6,5 cm` poza ościeża, z dolną krawędzią kapinosa (`+0 draw calli`); analogicznie w lukarnach (`facade_kit.dormer`).
- **Szyba z odbiciem nieba (nie czarna plama):**
  - `sets_buildings.window(..., sky_refl=True)`: zewnętrzne odbicie gradientu nieba (chłodny błękit na górze przechodzący ku horyzontowi + delikatna modulacja chmur, `rough=0.06`), silniejsze nad ciemnym wnętrzem pokoju i łagodniejsze nad białymi firankami/roślinami;
  - `streetscape/materials.py`: `facade_atlas.sky_occ` zmienione z `[0.5, 0.9]` na `[0.5, 0.35]`, aby szyby o niskiej chropowatości odbijały rzeczywistą sondę nieba Unity z perspektywy ulicy i kabiny (matowe ramy `rough ≥ 0.40` pozostają bez połysku).

### 2. Fasada: ciemniejszy cokół 0,3–0,6 m, zacieki pod parapetami i 2–3 odcienie tynku z ziarna
- **Cokół 0,35–0,58 m (`WORKING_VALUE`):** `SMALL_TOWN_PLINTH_HS = (0.35, 0.42, 0.50, 0.58) m` z ochroną przed spadkiem (`zg85 + 0,35 m`), mieszanka `fieldstone_plinth` i `plinth_dark` (LOD0 + pas `plinth_dark` na LOD1) z per-domowym przyciemnieniem cokołu `0,78–1,02` przez `COLOR_0`.
- **Delikatne zacieki pod parapetami:** w trybie `small_town` próg czystych parapetów obniżony z `0,40` do `SMALL_TOWN_SILL_CLEAN = 0,22` (3-elementowa krotka `sills_`, bez wpływu na Białystok) z delikatną skalą długości `0,46–0,76 m`.
- **2–3 odcienie tynku na dom z ziarna (`_FACADE_TINT`, +0 draw calli, +0 materiałów):**
  - `WorldPBR.shader` i `WorldPbrMaterials.cs`: słowo kluczowe `_FACADE_TINT` aktywowane flagą `facade_tint: true` na `plaster_*` i `plinth_dark`, mnożące albedo przez `lerp(1, COLOR_0.rgb * 2, COLOR_0.a)`. Brak kanału `COLOR_0` na istniejących kaflach (Białystok, Knyszyn) daje `COLOR_0.a == 0` (`WorldMeshBake.cs`) — dokładny no-op.
  - `buildings_mesh._house_shades(key)`: deterministycznie wyznacza 3 harmonijne odcienie tynku per budynek (`col_main` korpus główny, `col_gable` szczyt/poddasze, `col_sec` ściany boczne i opcjonalny górny fryz pod okapem) + `col_plinth` cokołu, przenoszone spójnie na LOD0 i LOD1.
- **Aktywacja dla korytarza wiejskiego DW671:** `Data/Regions/dw671-tykocin-09/overrides.yaml` otrzymuje jawny wpis `dw671-tykocin-09-rural-facades-0348` (`kind: facade_rules`, `small_town: true`). Kafle Białegostoku pozostają bez zmian (bit-identyczne z ADR 0238).

### 3. Płoty: ≥4 warianty deterministyczne z ziarna działki, bez powtarzalnego żółtego płotka (+0 draw calli)
- **Usunięcie żółtego płotka:** w `plots.py` `PICKET_PAINTS` zastąpiono 6 zgaszonymi barwami podlaskimi (leśna zieleń, ciemny orzech, surowe szare drewno, wyblakły błękit łupkowy, tlenkowy brąz/czerwień, zgaszona złamana biel; zero nasyconej żółci/ochry); w `plot_kit.py` `picket_wood` przyciemniono z `(132, 86, 54)` na `(122, 78, 44)`. Układ pasm atlasu `plot_kit` (`2048×2048`) pozostaje bez zmian (zgodność z `test_roof_tiles_0316.py`).
- **≥4 wyraźne rodziny ogrodzeń w jednym atlasie `plot_kit` (+0 draw calli):**
  1. **Sztachety drewniane w kilku kolorach / surowe:** `picket`, `picket_wood`, `picket_paint` (6 barw), nowy `picket_raw` (surowe szarzejące deski z szarymi słupkami `wood_grey`) + deski pełne `boards_*`;
  2. **Siatka na słupkach:** `chainlink` (zielona PVC) i `chainlink_galv` (ocynk) ze słupkami stalowymi 3D na każdym podziale przęsła (`5,12 m`);
  3. **Panel ogrodzeniowy:** `lamella`, `concrete` oraz nowe `panel_graphite` i `panel_green` (sztywny panel na betonowej podmurówce `0,24 m` ze słupkami stalowymi 3D);
  4. **Murek z cegły / kamienia + przęsła:** `brick_picket`, `brick_boards`, `brick_bars` oraz nowe `stone_picket` i `stone_bars` (murek kamienny `0,38 m` + słupki kamienne `0,38×0,38 m` z betonowymi daszkami z tekstury łupanego kamienia/betonu pod ciepłym kamiennym tintem + przęsła sztachetowe/prętowe).
- **Deterministyczne unikanie powtórzeń u sąsiadów (`plots.plan()`):** kara dla identycznego stylu i tej samej rodziny w promieniu `45 m` (2 najbliższe działki), liczona przed nadpisaniami `plot_fence` (pełna zgodność z `test_dom_klattow_0305.py`).

## Wyniki i budżety (zmierzone)
*(Uzupełniane po przebudowie regionów, imporcie Win64 i visual-qa przed | po)*

## Otwarte / UNVERIFIED
- Wymiary okien (`1,20 × 1,40 m`), wnęk (`0,08–0,10 m`), cokołów (`0,35–0,58 m`), zakresy odcieni tynku i udziały wariantów płotów są oznaczone jako `WORKING_VALUE` (typologia zabudowy wiejskiej Podlasia i zdjęcia Commons; brak inwentaryzacji każdego budynku).
- Pomiar czasu klatki w docelowym buildzie Windows (`pc-metrics.ps1`) pozostaje po stronie lidera po scaleniu; zmierzono pamięć importu oraz `drawsEst`/`trisExact` w edytorze (`stats.txt`).
- Wzorzec `facade_rules: small_town: true` jest włączony na prototypowych kaflach `tykocin` i `dw671-tykocin-09`; rozszerzenie na pozostałe kafle wiejskie DW671/DK65 po akceptacji lidera.

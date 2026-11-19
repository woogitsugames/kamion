# ADR 0298 — Mozaika pól per piksel, ciągłość szwów kafli, pierścienie na płytach skrzyżowań, nasadzenia działek (knyszyn-p2-s24)

Status: Proposed, 2026-11-19 (agent knyszyn-p2-s24; zmiana globalna — generator, shader terenu, import fartucha).
Powiązane: ADR 0295 (mozaika pól, swardCalm), 0085 (fartuch / far-field), 0064 (mapa nieba GI), 0110 / 0194 (UV1 płyt
skrzyżowań), 0132 / 0163 (korony z ortofoto → drzewa ogrodowe), 0287 (deski), D68 (lato wszędzie).
Recenzja: `docs/reports/REVIEW-2026-11-18-s24-cabin-lights-knyszyn.md` §3 (N1–N5, FAIL).

## Kontekst — przyczyny (zmierzone / odczytane z danych)

1. **N1 szwy kafli (skok 15–22 poziomów sRGB).** Trzy niezależne przyczyny:
   (a) fartuch poza kaflem (`WorldEdgeBuilder.ApronMask`) to sinusowy szum suchości B 0,35–0,82 i strefy lasu / gruntu
   wpisane dla Białegostoku — nic wspólnego z maską terenu przy krawędzi; (b) mapa widoczności nieba (`KamionWorldGI`)
   kończy się skokiem `inside` 1 → 0 dokładnie na krawędzi kafla (fartuch dostaje pełne niebo naraz); (c) mozaika
   ADR 0295 była zapisana w COLOR_0.b na siatce maski 1 m, ale pas terenu High ma wierzchołki 1 m tylko przy drogach
   (8 m dalej), Low 2 m — miedze 2 m znikały, pasy czytały się jak „blade smugi” (N3), a fartuch nie mógł jej nieść.
2. **N2 koncentryczne pierścienie na asfalcie wlotów.** `roads.meshing._patch_uv1` liczył współrzędną pasa (UV1.x) z
   odległości euklidesowej do najbliższego punktu łańcucha ramienia; za wolnym końcem okna łańcucha (krawędź kafla,
   rozdział jezdni) najbliższy punkt to wierzchołek końcowy, więc „odległość boczna” rosła promieniście, a koleiny
   (`frac(UV1.x)` w `WorldPBR` `_ROADWEAR`) rysowały pierścienie wokół niego (rastrowanie UV1 płyty przy zamknięciu
   DK65 W: `artifacts/knyszyn-p2-s24/u1-before.png`).
3. **N3 pola khaki.** Kolor pól = tekstura trawy × wzmocnienie suchości 0,70 przy niskim B — ciemna oliwka; jedyną osią
   zróżnicowania była suchość.
4. **N4 gołe działki, „brokuły”.** Knyszyn nie miał `plot_canopy.json` (korony z ortofoto, ADR 0132), więc 0 drzew
   ogrodowych z koron; jednocześnie reguła samosiewu sadziła drzewa co ~20 m (siatka 14 m, 45 %) na całym BDOT
   OT_PTTR_A — pola w użyciu — stąd pojedyncze młode drzewa i krzaki na polach.

## Decyzja

### 1. Mozaika pól per piksel (`Environment/Shaders/KamionFieldMosaic.hlsl`, `WorldPBR.shader`) — wszystkie regiony
- Generator (`streetscape/vegetation.ground_masks`) zapisuje w polach BDOT10k OT_PTTR_A tylko **flagę** w COLOR_0.b:
  0,90 „roślinność trawiasta”, 1,00 „uprawa na gruntach ornych”; każdy inny grunt ma B ≤ 0,80 (`GROUND_B_MAX`), więc nigdy
  nie czyta się jak flaga. Poziomy ADR 0295 (`field_mosaic`) zostają jako referencja QA.
- `Kamion/World PBR` (`_GROUNDMASKS`): `farm = smoothstep(0,84; 0,88; B)`; układ pól = ta sama funkcja położenia EPSG:2180
  co `vegetation.field_ids` (bloki 300 m, pasy 22–46 m, te same sole hasza), liczona w pikselu z przestrzeni obiektu
  (= E/N regionu) + `_RegionOriginEN` (materiał regionu, import: `WorldPbrMaterials`). Pas = jedno użycie, miedza ~1,2 m
  filtrowana rozmiarem piksela i wygaszana z odległością, ścieżki technologiczne co 18 m (dwa ślady 1,8 m) na zbożach /
  międzyplonach. Ten sam piksel po obu stronach każdego szwu: sąsiedni kafel, fartuch, pierścień tła.
- **Pora roku: lato jak reszta świata (D68: światło ~15 sierpnia).** Paleta połowy sierpnia na Podlasiu: ścierniska
  (słoma), talerzowane / orane (gleba), kukurydza, ziemniaki / buraki, międzyplony, koniczyna / młody rzepak, trawy w
  uprawie; łąki po drugim pokosie, pastwiska, świeżo skoszone, niekoszone siano. 55 % pasów bloku ma własne użycie
  (podlaska szachownica wąskich działek). Udziały i odcienie `WORKING_VALUE`, dobrane na renderze `rondo_owner_11` do
  zdjęcia właściciela nr 11 (maj: zieleń dominuje); ortofoto 2025 tylko do układu pasów, żaden piksel nie trafia do gry.
- Koszt: ~9 komórek Voronoi × 2 hasze + kilka haszy pasa na piksel terenu z flagą, gałąź dynamiczna (bez flagi: 0);
  zero nowych tekstur, słów kluczowych i draw calli; jeden interpolator (`TEXCOORD8`, tylko `_GROUNDMASKS`).

### 2. Szew kafla i fartuch (`World/Import/WorldEdgeBuilder.cs`, `Rendering/Shaders/KamionWorldGI.hlsl`)
- Pierścień fartucha na krawędzi bierze maski terenu z wierzchołków `terrain_band` wzdłuż krawędzi (interpolacja wzdłuż
  boku) i przechodzi w maskę fartucha do pierścienia 30 m; pole przecinające krawędź zachowuje rodzaj (flaga 0,90 / 1,00)
  dalej w fartuchu. Regiony wiejskie (wszystkie poza C): fartuch = flaga pola uprawnego (mozaika do horyzontu), bez stref
  lasu / gruntu wpisanych dla Białegostoku; C bez zmian.
- Mapa nieba GI: poza prostokątem kafla trzymana wartość brzegu, rozmyta (do mip 6 na 120 m), zamiast skoku do „pełnego
  nieba”; wypieczone cienie słońca wygasają w 24 m (krawędziowy dom / drzewo nie ciągnie smugi).

### 3. Pierścienie na płytach (`roads/meshing._patch_uv1`) — wszystkie regiony
Odległość boczna = prostopadła do linii najbliższego odcinka (nie do punktu obciętego do końca łańcucha); ramię wybiera
nadal najbliższy łańcuch (bez przeskoków); za wolnym końcem okna łańcucha koleiny wygasają w 3 m (`PLATE_END_FADE_M`)
zamiast ekstrapolacji (dwa ekstrapolowane ramiona dawały „romb” kolein u wlotu ronda).

### 4. Działki i drzewa
- `Data/Regions/knyszyn{,-w}/plot_canopy.json` (narzędzie ADR 0132 bez zmian): 18 801 / 5 718 koron z ortofoto →
  drzewa ogrodowe kitu (ADR 0163: jabłonie, klony, lipy, brzozy, jesiony, kasztanowce, tuje / świerki wg G7).
- Samosiew na OT_PTTR_A (ziemia w użyciu rolniczym): 35 % punktów siatki 14 m w pasie 8 m przy granicy wieloboku (miedze,
  rowy), 2 % w środku (pojedyncza grusza / wierzba) zamiast 45 % wszędzie. OT_PTNZ_A bez zmian.

### 5. P2: domy drewniane malowane
`wood_planks_red` (tlenkowa czerwień, liniowo 0,216 / 0,042 / 0,025) i `wood_planks_graphite` (0,076 / 0,088 / 0,102) —
odczytane okiem ze zdjęcia właściciela nr 7; reguła `buildings_mesh.wood_paint`: 32 % czerwone, 24 % grafit, 26 %
bejcowane brązowe, 18 % zielone (`WORKING_VALUE`). Nadpisanie `wall_material` (Dom Klattów) bez zmian.
Ekrany przezroczyste (N7) nie leżą w kaflach Knyszyna — nietknięte.

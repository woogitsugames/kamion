# ADR 0238 — typologia zabudowy Białegostoku: podtypy, proporcje, paleta, dachy, front pawilonu
Status: Proposed (agent world-builder, chmura D runda 2, gałąź `typology-0238`), 2026-11-15. Do scalenia przez lidera.
Powiązane: R4 `research/cloud2/bialystok-building-typology` (PR #64) + recenzja
`docs/reports/REVIEW-2026-11-15-s21-cloudD-64-bialystok-building-typology.md` (gałąź `reviews-0225`, werdykt „SCAL z erratą”),
M53 `research/mistral/p3-buildings-2`, ADR 0081/0091/0094/0097 (fasady, dachy domów), 0126/0129 (frontage), 0184/0185/0190/0196.

## Kontekst
- Generator miał pięć klas (`hall`, `office`, `block`, `house`, `shed`). Każdy „budynek wielorodzinny” był blokiem z
  płaskim dachem, każdy obiekt handlowo-usługowy < 1500 m² biurowcem z siatką okien. Paleta bloków: 7 równych pasteli
  (WORKING_VALUE). Kształt dachu nie mógł przyjść ani z OSM `roof:shape`, ani z override.
- R4: OSM nie nadaje się na źródło typologii (`building=yes` 2224 z 2734; `roof:shape` 2 i 4 budynki), liczby brać z
  BDOT10k + LoD1. Recenzja: R4-075 („280 cm brutto”) ma w Wikipedii „[potrzebny przypis]” — nie SOURCED; brak kolorów
  bloków; propozycja `BASE_M = 2,0`.

## Decyzja
1. **Dwa poziomy** (`tools/worldgen/streetscape/typology.py`): klasa renderu `typ` bez zmian (klucz dla działek,
   życia, far field, kamer QA) + **podtyp** `b["sub"]`: `wielka_plyta`, `kamienica` (klasa block), `biurowiec`,
   `pawilon` (office), `dom`, `dom_drewniany` (house), `hala`, `gospodarczy`, `wiata`. Kolejność źródeł: override
   `typology` (klasa albo podtyp) > tagi OSM dołączone do obrysu (`osm_building`) > funkcja BDOT10k + kondygnacje +
   wysokość LoD1 + zmierzone wzniesienie dachu LoD2. Nieznana nazwa w override = błąd (dotąd: cicho przyjęta).
2. **Dach** (`typology.roof_shape`): override `roof_shape` (flat / gable / hip / mono) > OSM `roof:shape`
   (`roof_shape_osm`) > dla bloków i biur: kod LoD2 1030 / 1040 / 1070 **ze zmierzonym wzniesieniem** kalenica − okap
   ≥ 1,5 m i okapem ≥ 50 % wysokości LoD1. Sam kod nie wystarcza: z 10 budynków wielorodzinnych C + Dojlid o kodzie 1030
   dziewięć ma wzniesienie 0,3–0,8 m (dach niskospadowy za attyką), jeden 1,8 m (pomiar, test). Domy: bez zmian
   (`roofs.plan`), plus `shape` z override / OSM.
3. **Kamienica** = wielorodzinny ≤ 4 kondygnacje, ≤ 900 m², dach spadzisty wg p. 2: dach z `roofs.plan`, bez galerii
   balkonów, maszynowni i kominów regułowych, rzędy okien także na LOD1; kondygnacja 3,2 m, cokół 0,6 m (WORKING_VALUE —
   R4 nie ma kamienic na kaflach C / Dojlidy). W danych: C 1, Dojlidy 0.
4. **Pawilon** = funkcja handlowo-usługowa (BDOT10k / OSM), 1 kondygnacja, LoD1 ≤ 7,5 m (pomiar: n = 71, p10/p50/p90 =
   3,0 / 4,2 / 6,8 m). Ściana najbliższa drogi (≥ 6 m, budynek ≥ 3,2 m) dostaje regułowy front: przeszklenie 0,35–2,75 m
   ze szprosami co 2,4 m i ciemny pas attyki 0,6 m (`streetscape.frontage`, bez napisów i marek), LOD1 = jeden quad szyby
   w materiale `hall_flashing` (`frontage.wall_lod1_flat`, 10 trójkątów). Pozostałe ściany: fasada biurowa. Wymiary frontu
   WORKING_VALUE. Budynek z jakimkolwiek autorskim `set` nie dostaje frontu regułowego. C 43 pawilony / 24 fronty,
   Dojlidy 21 / 15.
5. **Paleta bloków** = obserwacja, nie zgadywanie: 9 bloków M53 ze statusem OK / OK-POŚREDNIE i opisaną elewacją (zdjęcia
   Commons CC0 / CC BY / CC BY-SA, piksele nieużyte): biała 3, szara / jasnoszara 3, beżowa 2, pomarańczowa 1 →
   `plaster_white` ×3, `plaster_grey` ×3, `plaster_cream` ×2, `plaster_peach` ×1 (ESTIMATED, n = 9). Rama SOURCED: MPZP
   części os. Białostoczek, uchwała XXVII/451/26 § 7 ust. 1 pkt 1 lit. a („odcienie bieli, beżu, brązu i szarości”).
   Błękit, żółć, szałwia znikają z reguły (zostają jako `wall_material`). Pawilony: jasne neutralne tynki (barwy firmowe ze
   zdjęć nie są odtwarzane). Hale, biura, domy: bez zmian — zgodne z R4 (hale Dojlid białe / jasnoszare, 1 czerwona z 6).
6. **Proporcje ze statusem** (`typology.PROPORTIONS`): kondygnacja bloku 2,8 m SOURCED (R4-074 / R4-077; R4-075 nieużyte),
   oś okienna 3,0 m WORKING_VALUE (związana z atlasem `facade_far`; siatka OW-T 540 cm = 2 × 2,7 m to ESTIMATED — atlas
   2,7 m jest pracą otwartą), cokoły WORKING_VALUE.
7. **`buildings.py`**: `BASE_M` 1,0 → **1,5** (nie 2,0). Pomiar na 8821 budynkach BDOT10k z LoD1 i liczbą kondygnacji
   (wszystkie regiony w gicie): mediana `h − 3,0·n` = 1,50 m (bloki 1,54, domy 1,77, inne 1,33); MAE 1,29 m przy 1,5
   wobec 1,36 (1,0) i 1,35 (2,0). Do obrysu BDOT10k dołączane są `osm_building` i `roof_shape_osm` budynku OSM
   pokrywającego ≥ 50 % obrysu; `osm_extract` czyta `roof:shape` (nowy klucz cache). Działa przy następnym
   `build_region` (wymaga `Data/raw`); `buildings.geojson` w gicie nie były przepisywane.

## Budżet (kafel C: neutralny lub ujemny)
Narzędzie `tools/worldgen/qa/typology_budget.py`: generator budynków na danych z gita (zastępcze pole wysokości = poziom
bazy LoD1 najbliższego budynku, drogi z grafu), trójkąty per chunk i per kamera regułą `mesh_budget`. Zgodność z
manifestem w gicie: C LOD0 +2,1 %, LOD1 +4,7 %; Dojlidy +7 % / +17 % — to SZACUNEK, wiążący jest pomiar lidera.
- C: LOD0 964 087 → 959 580 (−4 507), LOD1 101 067 → 100 602 (−465). Wszystkie 23 kamery ≤ 0; `stretch_04` High
  2 022 535 → 2 021 842 (−693), Low 974 570 → 974 271 (−299); `route_onramp_andersa_above` High −885, Low −227.
- Dojlidy: LOD0 −4 654, LOD1 −528; 17 kamer ≤ 0.
- Materiały budynków w regionie: C 65 → 62 (LOD0), 66 → 61 (LOD1). Submeshe (suma materiałów per chunk): C LOD0
  1120 → 1126 (**+6**: `showroom_glass` w 9 chunkach), LOD1 758 → 752; Dojlidy LOD0 +7, LOD1 +2. Tier Low rysuje tylko LOD1.
- Kompensacja dachów spadzistych: rynny i rury spustowe bloku / biura z dachem spadzistym tylko na LOD0 (`_L0Only`),
  bez kominów; front pawilonu zastępuje okna z parapetami.

## Czego nie zmienia
Budynki z override, hale, domy, budynki gospodarcze i wiaty mają identyczne trójkąty per (warstwa, materiał) jak przed
zmianą; bloki z płaskim dachem — identyczną liczbę trójkątów (test na C i Dojlidach). ADR 0184 / 0185 / 0190 / 0196 nietknięte.

## Otwarte
1. Ocena wizualna (lider + `visual-critic`): front pawilonu na Low (płaski ciemny prostokąt bez szprosów), nowe barwy
   bloków przy Andersa / Białostoczku, jedyna kamienica w C. W chmurze nie ma renderu.
2. +6 submeshy LOD0 w C od `showroom_glass`; alternatywa (szyba z atlasu fasad) czytała się czarno (ADR 0129).
3. Udział bloków nieocieplonych (`panel_concrete`, 30 %) bez źródła — w próbie M53 0 z 9. Oznaczony jako
   `BLOCK_ETICS_SHARE = 0.7` (WORKING_VALUE) w `buildings_mesh.py`; zmiana wartości wymaga renderu i `visual-critic`.
4. Budynki gospodarcze mają zawsze płaski dach; słownik kodów dachu LoD2 nadal bez cytatu (R4 „Luki”).
5. `far_field.py` ma własny przelicznik kondygnacji (WORKING_VALUE) — nie ruszany.

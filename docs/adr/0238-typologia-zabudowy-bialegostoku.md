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

## Dopisek D32 (16.11, s23 r8): test bit-identyczności czerwony na main — szum zmiennoprzecinkowy w dachach domów
**Objaw.** `test_authored_and_untouched_buildings_are_bit_identical` padał na main `8401944b6` (lokalnie i w CI `gis`,
ubuntu): Dojlidy 18 rozbieżności, C 43 — wszystkie `house`/`dom`, różnice ±1…17 trójkątów w `roof_*`, `soffit_boards`,
ścianach. **Hipotezy odrzucone (liczby):** (a) baseline sprzed c-regen3 / (b) `BASE_M` — wysokości tych 61 domów są z
`gugik_lod1_2024` i ich właściwości w `buildings.geojson` nie zmieniły się w c-regen3 (poza `osm_building` w 3); (c) konflikt
`storey_plan` — rozwiązany zgodnie z recenzją #123 (`storeys_fixed` + bez linii `lo, hi`), test regresji przechodzi; domy
nie przechodzą przez gałąź `office/block`. **Przyczyna (d):** ten sam kod sprzed #123 (`ade885234`) na tych samych danych
daje inne liczby na Linuksie (CI, chmura) niż baseline zacommitowany przez lidera (Windows) i przez FIX #123 — dokładnie dla
tych 61 domów. Generator dachu był chaotyczny: przesunięcie obrysu o 1e-9 m zmieniało trójkąty 51 z 415 budynków Dojlid
i 74 z 644 w C. Źródła: (1) kawałki pokrycia `exp ∩ face` i podbitki z operacji boolowskich zostawiały wierzchołki leżące
NA prostej krawędzi (węzły styku innej połaci) albo kilka µm od innego wierzchołka — które przetrwały, zależało od
ostatnich bitów; (2) `MultiRoof.profile` dzieliła ścianę biegnącą WZDŁUŻ krawędzi domeny / zmiany płaszczyzny w losowych
punktach (znak `fa·fb` przy |fa|,|fb| ~ 1e-12).
**Naprawa u źródła** (`streetscape/roofs.py`, `PLAN_TOL_M = 1 mm`): regiony połaci w `faces`, kawałki pokrycia i podbitki
w `build` przechodzą `_clean` (simplify 1 mm + siatka 1 mm); w `profile` przecięcie liczy się tylko przy |fa − fb| > 1 mm.
Po zmianie przesunięcie 1e-9 m zmienia 3 / 415 (Dojlidy) i 1 / 644 (C) budynków; z 61 rozbieżnych domów niestabilne
zostają 2 (obydwa w C, wyłącznie test w izolacji) — patrz „Otwarte 6”.
**Baseline przeliczony** wg procedury FIX-2026-11-16 (kod `ade885234` = bez #123, z łatką `roofs.py`; dane `origin/main`),
bo zmiana dotyczy generatora „przed” i „po” tak samo. Suma harnessu kodem sprzed #123: Dojlidy LOD0 500 659 → 499 592
(−1 067), LOD1 68 391 → 67 636 (−755); C 963 831 → 962 030 (−1 801), 101 067 → 99 981 (−1 086) — usunięte drzazgi.
Kamery (harness, Δ samej łatki): C wszystkie 23 ≤ 0, `stretch_04` High −1 070 / Low −1 070 (szacunek 1 984 390 ≤ 2 M),
Dojlidy 17 ≤ 0 (max `route_s0761` −717). Test nie był luzowany; nowy test regresji
`test_house_triangles_do_not_depend_on_float_noise` (8 domów, 1e-9 / 1e-7 m) pada na kodzie sprzed łatki.
Zmiana `generated/` (C, Dojlidy i każdy region z domami spadzistymi) dopiero przy przebudowie lidera.

### D32 r2 (CI na #159: C `bdot:2BE4B431-B14F` 510 vs 524)
CI (Linux, CPython 3.12.16 standalone, uv 0.13.8) i chmura (Linux, CPython 3.12.3 systemowy oraz 3.12.13 standalone)
mają te same pakiety z `uv.lock` (numpy 2.5.4, shapely 2.2.0, scipy 1.18.1), a oba Pythony w chmurze dają 524. Różnica
nie wynika więc z wersji, tylko z szumu na poziomie ULP (CPU / libm), który trafiał w progi:
- **B14F:** okap szczytu wychodził jako `zt = 130.65000000000003` albo `130.64999999999998`, a od niego zależy próg okna
  poddasza (`attic_window`): jedno okno więcej lub mniej (−14 trójkątów = 510). Naprawa: profil górnej krawędzi ściany
  (`Roof.profile`, `MultiRoof.profile`) zaokrąglany do 1 µm (`PROFILE_DECIMALS = 6`).
- **B45E:** pas szerokości < 1 mm między płaszczyznami obwiedni, którego nie przejmowała żadna połać, pojawiał się albo
  znikał (±1 trójkąt). Naprawa: pas węższy niż `SLIVER_M = 5 mm` (2 × pole / obwód) przechodzi do połaci o najdłuższej
  wspólnej krawędzi (`MultiRoof.faces`).

Wynik: wszystkie 61 domów rozbieżnych na main jest stabilnych przy przesunięciach od 1e-12 do 1e-6 m. W C żaden budynek
nie zmienia się przy przesunięciach 1e-12, 1e-9, 1e-7 i 1e-6 m. W Dojlidach zostają `…A8BC` (orientacja `_frame`), hala `…BC59` (doki), `rosti-west-wing`
(wywietrzaki). Test regresji obejmuje teraz także B14F i B45E (10 domów; 1e-12 / 1e-9 / 1e-7 m).
Baseline przeliczony tą samą procedurą (kod `ade885234` z łatką `roofs.py`, dane `origin/main`). Suma harnessu względem
kodu sprzed łatki: Dojlidy LOD0 500 659 → 499 578 (−1 081), LOD1 68 391 → 67 636 (−755); C 963 831 → 962 027 (−1 804),
101 067 → 99 980 (−1 087). Wszystkie 23 kamery C i 17 kamer Dojlid mają Δ ≤ 0: `stretch_04` High −1 071 (szacunek
1 984 389), Dojlidy `photo_P11-063` −518.
Sprawdzone i odrzucone: kąt `_angle` hal liczony modulo π naprawia siatkę świetlików (Dojlidy `…BAD2` 600 / 660 przy
przesunięciu 1e-12 m), ale przestawia świetliki w innych halach: 4 kamery dostają +22…+77 High (C `fire_station_abeam`
+46). Zmiana byłaby więc niezerowa dla budżetu i nie weszła do tego PR.

## Otwarte (dopisek D32)
6. Pozostałe progi „na ostrzu” (nie systemowe): orientacja `_frame` przy prawie kwadratowym prostokącie (Dojlidy
   `…A8BC`); hale: siatka świetlików zależna od `_angle` ±π (`…BAD2`, C `…C4AC`, poprawka gotowa, ale +≤77 High na
   4 kamerach — decyzja lidera), doki `…BC59`, wywietrzaki `rosti-west-wing`. Lider: po scaleniu uruchomić
   `test_typology_0238.py` na Windows — oba środowiska muszą dać 24/24.

## Dopisek D39 (16.11, s23 r9): ostatnie progi „na ostrzu” — prostokąt, świetliki, bramy, wywietrzaki
**Pomiar przed zmianą** (skan każdego budynku osobno, obrys przesunięty o (dx, 0,7 dx), dx = 1e-12 / 1e-9 / 1e-7 /
1e-6 m, liczby trójkątów per (warstwa, materiał); obrysy z repo, bez `Data/raw`): Dojlidy 6 / 415 niestabilnych, C 1 / 644.
Przyczyny (każda zmierzona na danym budynku):
- **`…A8BC` (dom):** dwa prostokąty minimalne o polu 67,6097 m² (4,58° i 4,20°) równe z dokładnością do szumu —
  `minimum_rotated_rectangle` wybierał raz jeden, raz drugi (inna oś `_frame`, rynny i rury spustowe).
- **`…BAD2`, `ed098300` (Dojlidy), `…C4AC` (C) — świetliki:** `_angle` dawał kąt dłuższego boku z kierunkiem zależnym
  od narożnika, od którego shapely zaczyna pierścień (±π), a siatka świetlików startuje od narożnika obróconego rdzenia.
- **`…BC59` (hala z dokami):** nie szum — `gate_openings` oznaczał bramę `done` w danych wejściowych, więc drugie
  wywołanie `build` na tym samym budynku (harness, test) rysowało halę bez 2 bram (−32 trójkąty `reveal_hall` itd.);
  przy okazji kontrola „brama nie pasuje do ściany” przechodziła tylko za pierwszym razem.
- **`rosti-west-wing` (wywietrzaki):** prostokąt z remisem krawędzi równoległych — start pierścienia i znak osi `along`
  w `facade_kit.roof_vents` zależały od szumu (168 / 192).
- **`…A92F` (blok, ujawnione po zmianie prostokąta):** pierwszy komin wentylacyjny leży dokładnie 2,0 m od końca
  prostokąta = NA linii `poly.buffer(-2.0)`, gdy ściana szczytowa jest krawędzią otoczki.

**Naprawa:** `streetscape/roofs.py` `stable_rect` — gdy inna krawędź otoczki daje prostokąt o polu w granicy
`RECT_TIE_M2 = 1e-6 m²` (szum pola przy współrzędnych km ~1e-10 m²), wybierany jest prostokąt o najmniejszym kącie
mod π/2, z narożnikami od (min, min) przeciwnie do ruchu wskazówek; bez remisu — prostokąt shapely bez zmian.
Używają go `_frame` (przy bokach równych w granicy `PLAN_TOL_M` dłuższa oś = bliższa W–E), `plan`, `buildings_mesh`
(`_angle`, wiaty, prostokąt pawilonu) i `facade_kit` (`roof_vents`, `machine_rooms`). `_angle` mod π w [0, π)
(krawędź w granicy 1e-6 rad od W–E = W–E). **Świetliki:** budowane są obie siatki (`ang`, `ang − π`), wybierana ta
z mniejszą liczbą świetlików (remis: `ang`) — wybór niezależny od narożnika startowego i nigdy większy niż dawny
(dawny kąt był jednym z tych dwóch). To ta sama poprawka „mod π” przyjęta przez lidera, z wyborem reprezentanta, który
zamienia +22…+363 High na kamerach C (wariant „mod π w [0, π)”, zmierzony) w Δ ≤ 0. Bramy: kopia listy bram na
budynek w `build` (wejście nietknięte). `roof_vents`: linia wewnętrzna `buffer(−2,0 − PLAN_TOL_M)` (komin na linii
zawsze poza).
**Po zmianie:** C 0 / 644 niestabilnych, Dojlidy 1 / 415 — `bdot:daa0c871` (dom) tylko przy 1e-6 m (`soffit_boards`
42 / 41): wierzchołek przechodzi przez linię pół milimetra siatki `PLAN_TOL_M` w układzie świata. Siatka względna
(kotwica w środku ramy dachu) to naprawia, ale przestawia inny dom C (`…B5E4`) już przy 1e-12 m — odrzucona; 1e-6 m to
~10⁷ razy więcej niż różnica między maszynami. Test regresji `test_frames_skylights_docks_and_vents_do_not_depend_on_float_noise`
(7 budynków, 1e-12…1e-6 m + powtórny build) pada na kodzie sprzed zmiany; `test_stable_rect_breaks_ties_the_same_way_under_noise`.

**Baseline przeliczony** procedurą FIX-2026-11-16 (kod `ade885234` + `roofs.py` gałęzi + łatka `buildings_mesh.py` /
`facade_kit.py`, dane `origin/main`); procedura odtwarza obecny baseline bit w bit przed łatką. Harness, kod sprzed
#123: Dojlidy LOD0 499 578 → 499 472 (−106), LOD1 67 636 → 67 615 (−21); C 962 027 → 961 562 (−465), 99 980 → 99 981 (+1).
Δ per kategoria (LOD0 / LOD1): świetliki hal Dojlidy −36 / 0 (3 hale −12; `…BAD2` bez zmian), C −420 / 0 (3 hale);
wywietrzaki `rosti-west-wing` +24 / 0 (remis rozstrzygnięty na stan 192); kominy bloków −12 (Dojlidy), −36 (C, 2 bloki);
domy z remisem prostokąta (rury spustowe na innej parze okapów): Dojlidy 2 domy −82 / −21, C 5 domów −9 / +1.
Kamery (Δ High / Δ Low, szacunek = `frame_estimate` + Δ): C `stretch_04` −123 / +1 (1 985 337 / 937 765),
`route_onramp_andersa_above` −94 (1 962 293), `fire_station_abeam` −94, `biezenstwa_above` −332; C dodatnie tylko
`putry_above` +1 / +1 i Low +1 na 9 kamerach (w tym `putry_above`; dom `…AF10` +1 / +1 i bilans domów z remisem).
Dojlidy dodatnie: `route_s0152` +67, `kuronia2_front` +28, `route_s1675` +12 — wywietrzaki `rosti-west-wing` (+24,
chunk 6_2) i świetliki przesunięte między chunkami (np. 0_2 −76 / 1_2 +80) przy sumie regionu −106;
`photo_P11-063` −20 (1 767 766). Wszystkie szacunki C < 2 M High. Przyjęte świetliki lidera (+22…+77) nie są już
potrzebne: wybór siatki daje Δ ≤ 0 na każdej hali.

## Dopisek props-fix-s24 (26.11, agent `agent-a60f5c7ffe98fe7c7`): budynki gospodarcze wsi (krytyka s24 fala 11, pkt 8)
**Objaw.** `dk65-07/drive-kozince` (x 1400–1610) i `knyszyn-w/dk65-goniadzka` (x 1265–1625): biały pudełkowy budynek bez okien
i detalu. **Ustalenie typu** (dane, nie zgadywanie): dwa obiekty BDOT10k `budynek gospodarczy` (`2C9A9AB4-440C…` 97,8 m²,
LoD1 3,77 m, LoD2 4,52 m, okap 2,64 m, `roof_type_lod2 = 1030`; `…749B…` 109,7 m², 4,63 m) — klasa `shed` generatora:
płaski dach `roof_membrane`, tynk `plaster_grey/light` (w słońcu biały), tylko drzwi garażowe. Model LoD2 podaje dach
dwuspadowy (1030) — typologia gospodarcza ignorowała go (dopisek 4 „Otwarte” wyżej: „budynki gospodarcze mają zawsze
płaski dach”). W danych: **157** takich obiektów w `dk65-07` (76 z dachem spadzistym wg LoD2), **462** w `dw671-tykocin-03`
(184), razem 7 633 (3 603 z dachem spadzistym wg LoD2) w 44 kaflach poza Białymstokiem, lista w `artifacts/props-fix-s24/outbuildings-per-tile.txt`.

**Decyzja (opt-in regionu jak `small_town`, ADR 0336): `facade_rules: rural_outbuildings: true`** (override
`rural-outbuildings-shelters-props-fix-s24` w `dk65-07` i `dw671-tykocin-03`; kafle Białegostoku bez wpisu = bit-identyczne).
Dla klasy `shed` o powierzchni ≥ 18 m² (z wyjątkiem stacji transformatorowych / wiat śmietnikowych — płaskie pudełka):
1. **Dach** z modelu LoD2 przez `roofs.plan` (1030 → dwuspadowy, 1040/1070 → kopertowy, 1010 → pulpitowy, `1000` → zostaje
   płaski); brak LoD2 → dwuspadowy ≥ 36 m², inaczej pulpitowy. Pochylenie i okap z pomiaru LoD2/LoD1 (jak domy).
2. **Pokrycie** (WORKING_VALUE): blacha grafitowa 34 %, dachówka brązowa 33 %, czerwona 33 % - trzy pokrycia `ROOFS_PITCHED`, które mają
   domy tych samych chunków; bez rynien i rur (zagroda).
3. **Ściana** (WORKING_VALUE): tylko tynki `plaster_grey/light/cream/beige` (34 / 22 / 22 / 22 %) **ciemniejsze od domów** przez `COLOR_0`
   (`rural_shed_shades`, luminancja 0,58-0,86 wobec 0,92-1,08 domów, ciepły / chłodny odchył, osobny odcień szczytu i boków; `_FACADE_TINT`,
   0 draw calli); cokół `plinth_dark` 0,3 m. Deski i cegła (pierwsza wersja) wycofane: własne materiały = +20 / +58 draw calli na kamerę.
4. **Okna i drzwi:** okna z kratą jako **płaska komórka atlasu** `base` (0,80 × 0,50 m, parapet 1,50 m; `wall_with_openings` przy
   `depth = 0` rysuje 2 trójkąty zamiast ~18 ościeży i parapetu): 1 / 2 / 3 na ścianę < 5,5 / < 9,5 / dłuższą (prawdopodobieństwo 92 % ściana
   frontowa, 80 % pozostałe); wrota garażowe do 2 na ścianie frontowej (85 %, było 60 %), drzwi personelu. Szczyt bez okna poddasza.
5. Kod: `buildings_mesh.RURAL_SHED_*`, `rural_shed_pick`, `variant["rural"]` w `facade_openings`, gałąź `rural_shed` w
   `build()` (dach, ściana, `wooden`); testy `tests/gis/test_rural_outbuildings_props_fix_s24.py`.
**Wartości `WORKING_VALUE`** (udziały materiałów, wymiary okna) — bez inwentaryzacji zagród; do oceny wzrokowej `visual-critic`.

## Dopisek weathering-s24 (26.11, agent `agent-a05410a22b79fbf0c`): zużycie dachów, ogrodzeń bloczkowych i styku ściana-grunt (krytyka s24 fala 11)
**Objaw** (`artifacts/critic-s24-wave11/CRITIC.md`, ocena „Zużycie” 5/10): (1) dachy czyste jak z katalogu — bez zacieków,
mchu przy okapie, przebarwionych dachówek (pokrycie nie miało kanału koloru wierzchołków); (2) szare ogrodzenia bloczkowe
w jednej fakturze (`tykocin/route-s1441` x ~1100–1650); (3) cokoły bez rozprysków, brak ciemniejszego pasa na styku ściana-grunt.

**Decyzja (+0 draw calli, +0 materiałów, +0 tekstur):**
1. **Dachy — opt-in regionu `facade_rules: roof_weathering: true`** (Białystok bez wpisu = bit-identyczny; test 0238 zielony).
   `roofs.build(weather=…)` zapisuje `COLOR_0` pokrycia (LOD0 i LOD1): r = wiek, g = mech × ekspozycja (stok północny 1,0,
   południowy `WEATHER_MOSS_SOUTH` 0,3), b = metry pod kalenicą / 6, a = 0,5 + 0,5 × ziarno budynku. Wiek: `roof_age_class`
   — reguła działek (`plots.age_class`: powierzchnia + kondygnacje, 1/5 dryfu) i samo pokrycie (stara dachówka, gont,
   cementówka = stary; blacha = młodsza, chyba że na budynku gospodarczym). `ROOF_WEATHER_AGE` stary 0,70–1,0 / PRL 0,38–0,70 /
   nowy 0,06–0,28; mech 1,0 / 0,55 / 0,12 (`WORKING_VALUE`). Shader `Kamion/World PBR` `_ROOF_WEATHER` (manifest `roof_weather`):
   zacieki wzdłuż spadku (szum 2 oktaw rozciągnięty 10–30× w dół, silniejsze ku okapowi), wilgotny pas nad rynną, pojedyncze
   dachówki ciemne / jaśniejsze (wymienione) / poszarzałe na **siatce setu** (S-dachówka 0,20 × 0,35 m, karpiówka 0,183 × 0,15
   z półprzesunięciem, zakładkowa 0,233 × 0,35 z półprzesunięciem — udział 4–20 % wg wieku, wygaszane do średniej z odległością),
   mech w zakładach przy okapie i wzdłuż kalenicy, porosty (Medium+, `_KAMION_WORLD_DETAIL`). Tylko ALU, bez próbkowania.
   Wierzchołki bez `COLOR_0` (inne regiony, daszki nad drzwiami) dostają a = 0 → dokładny no-op.
2. **Ogrodzenia bloczkowe — opt-in `facade_rules: block_fence_variants: true`** (`stage.plan_plots` → `rp["fence_variants"]`):
   działka z ogrodzeniem `concrete` / `wall` losuje deterministycznie wariant `plots.BLOCK_VARIANTS`: bloczek łupany / gładki
   (wiersz `wall` atlasu), bez lub z **daszkiem 3D** (6 cm, nawis 3,5 cm) i **pilastrami** 0,30 m nad stopniami paneli, w jednym
   z 5 kolorów `BLOCK_TINTS` (szary, ciepły szary, piaskowy, grafitowy, brązowawy; tint `COLOR_0`). Wiersz `concrete` atlasu
   `plot_kit` przepisany (globalnie, ten sam układ UV): bloczki BAY_M/6 × 0,167 m w półwiązaniu z własnym tonem (±9 %),
   fakturą łupaną i ciemniejszymi krawędziami, zacieki spod czapy i słupków 0,6–1,3 m, brudna stopka (rozpryski 0,15–0,3 m), mech.
3. **Styk ściana-grunt (materiały, globalnie po przebudowie regionu):** manifest `splash_band` = [wysokość, siła, rozpryski]
   na `plinth_*`, `fieldstone_plinth`, `hall_plinth`, `brick_red`, `panel_concrete`, `plaster_*`, `wood_planks*`, `log_wall_*`
   → w `_SPLASH` ciemniejszy, brązowszy pas 0,25–0,32 m z postrzępioną górą (szum wzdłuż ściany), drobiny gleby gęstsze
   ku ziemi (Medium+) i wilgotna linia w ostatnich 7 cm. Wysokość = UV0.v (na cokołach metry nad terenem przy ścianie).
   `fieldstone_plinth`, drewno i bale dostały też `splash_h` (włącza `_SPLASH`).

Kod: `roofs.weather_col`, `buildings_mesh.roof_age_class / roof_weather`, `plots.block_variant / _block_pilaster`,
`plot_kit._concrete`, `materials.ROOF_WEATHER / SPLASH_BAND`, `WorldPBR.shader` (`_ROOF_WEATHER`, `_SplashBand`),
`WorldPbrMaterials.cs`; test `tests/gis/test_weathering_s24.py`; kamery `tools/worldgen/qa/weathering_cameras.py`.

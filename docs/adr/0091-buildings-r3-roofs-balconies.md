# ADR 0091: Zabudowa r3 — dachy domów nad prawdziwym obrysem, balkony przy trasie, jaśniejszy tynk, spokojniejsza cegła

Status: propozycja (world-builder, gałąź `worktree-buildings-r11`, z main `d205d4a`), 2026-11-11. Kontynuacja ADR 0081;
odpowiedź na `docs/reports/visual/REVIEW-2026-11-11-s9.md` §3 (P1 / P2) i kolizje pkt 3–4.

## Kontekst
Recenzja s9: domy jednorodzinne to płaskodachowe kostki, bloki przy trasie bez balkonów i bez czytelnego otworu okna,
szary tynk jak ciemny beton (94–102 przy niebie 229) z „pieprzem” faktury, cegła przesycona z jasną fugą, cokół jednolity,
kamery `r10_hall_3` (pod terenem) i `r10_hall_1` (zasłonięta naczepą).

Rozpoznanie na stanie main (`artifacts/buildings-r11/base/`):
- 270 domów: 196 miało dach dwuspadowy, ale tylko gdy obrys był prawie prostokątem — i wtedy obrys był **zastępowany
  prostokątem**; 74 były kostkami (38 × typ LoD2 1010, 33 × obrys nieprostokątny, 3 × typ 1000).
- Kalenica była brana z wysokości LoD1. Pomiar na 229 domach regionu z danymi LoD2 2017 (GUGiK, CC BY 4.0): wysokość LoD1
  2024 to nie kalenica, tylko okap + 0,55 × wznios (p10 / p50 / p90 = 0,46–0,49 / 0,54–0,59 / 0,73), a kalenica LoD2 / LoD1
  = 1,20–1,24 (mediana). Domy były więc za niskie. Zmierzone spadki: mediana 36° (typ 1030, n = 15) i 46° (1130, n = 157).
- Typ 1010 (jednospadowy) to w tym regionie połówki bliźniaków: jedna połać 5,0 → 11,0 m na budynek (sprawdzone
  `lod2_extract.py` na dwóch sąsiadach).
- `roof_tiles_*` / `roof_metal_*` nie miały zestawu tekstur (płaski kolor). Balkony istniały, ale tylko na dwóch
  krawędziach najdalszych od jakiejkolwiek drogi. Strefa rozbryzgu tynku była w całości zasłonięta cokołem bez rozbryzgu.
  Zestaw `plaster` (skan 2 m) był próbkowany co 4 m.

## Decyzja
1. **Dachy domów** (`tools/worldgen/streetscape/roofs.py`): dach jest polem wysokości nad rzutem (dwuspadowy,
   czterospadowy, jednospadowy), pokrycie = prawdziwy obrys + okap 0,5 m przycięty wzdłuż załamań pola, ściany rosną do
   pola (szczyty i wyższe ściany wklęsłych narożników wychodzą same). Obrys nie jest już zastępowany prostokątem.
   Kalenica = `height_lod2_2017_m`, okap = `lod2_eave_rel_m`; bez LoD2 oba z wysokości LoD1 i K = 0,55. Typ: 1030 →
   dwuspadowy, 1040 / 1070 → czterospadowy, 1010 → jednospadowy z wysoką stroną przy ścianie wspólnej z sąsiadem (bez
   sąsiada dwuspadowy), 1130 / brak → dwuspadowy, a przy rzucie zbliżonym do kwadratu (bok / bok < 1,25) czterospadowy
   w 60 % / 30 % przypadków (WORKING_VALUE), 1000 → płaski. Wynik: 200 dwuspadowych, 30 czterospadowych, 36
   jednospadowych, 4 płaskie (186 z kalenicą i okapem z LoD2, 15 z samą kalenicą, 41 z LoD1).
   LOD0: podbitka, deska czołowa 0,18 m, rynny na okapach, 2 rury spustowe, 1–2 kominy na połaci 0,45 m nad kalenicą
   z czapą. LOD1 i kolizja: to samo pokrycie i ściany, bez podbitki.
   WORKING_VALUE: okap 0,5 m, spadki domyślne 40° / 30° / 25°, zakresy spadków, udziały czterospadowych.
2. **Okna domów**: rytm 2,7 m (2 okna od 6,4 m ściany, 3 od 9,1 m, 1 na krótkiej), co piąte pole ściany bocznej puste,
   okno poddasza w szczycie, gdy liczba kondygnacji BDOT10k nie mieści się pod okapem (albo małe okienko strychu), okna
   pod niskim okapem (2,5–2,9 m) obniżone zamiast pominięte.
3. **Zestaw `roof_tiles`** (512 px, proceduralny, modulacyjny, `set_tile`): fala 0,20 m, rząd 0,35 m (WORKING_VALUE
   w zakresie wymiarów dachówki i blachodachówki). Jeden zestaw dla dachówki i blachodachówki.
4. **Balkony**: na słonecznej (SSW) długiej stronie bloku + po obu stronach w 25 % bloków, na każdym odcinku ściany
   ≥ 1 przęsło (reguła WORKING_VALUE — brak danych o balkonach per budynek). Poręcz 5 × 4 cm z trzech stron jako
   geometria (12 trójkątów), boki z trzech tonów zamiast zawsze ciemnej stali. LOD1 bez zmian: rzędy `facade_far`
   z tego samego zbioru krawędzi.
5. **Otwór okna**: głębokość ościeża 0,14 → 0,22 m (stolarka w licu starej ściany + ocieplenie), ościeża białe
   (0,40 → 0,60), parapet blaszany na całą głębokość ościeża z kapinosem 5 cm.
6. **Tynk**: `plaster_grey` 0,36 → 0,62, `plaster_white` 0,60 → 0,76 (jasne farby elewacyjne, WORKING_VALUE; zdjęcia CC0
   bloku przy Rondzie Putry pokazują biały / jasnoszary tynk). Zestaw `plaster`: `set_tile` (2 m zamiast 4 m), detal
   drobniejszy niż 3 cm × 0,4 w albedo i wysokości, relief ze skanu × 0,3, AO skanu słabsze.
7. **Cegła**: tint −28 % nasycenia liniowego ([0,26; 0,10; 0,07] → [0,224; 0,109; 0,087]), fuga w zestawie ciemniejsza
   o 35 % (maska z barwy, bo fugi skanu są prawie w licu), dryf tonu makro `macro` = [48 m; 0,18] (domyślnie 64 m; 0,06).
8. **Cokół**: wysokość wg typu (blok = wysoki parter 0,9 m, biuro 0,6, dom 0,45 / 0,60, szopa 0,3), dwa tony na blokach
   i biurach (`plinth_dark`, `plinth_grey`), strefa rozbryzgu na cokole (`splash_h` 0,5 m).
9. **`WorldPbrMaterials.cs`** (+10 linii, poza własnością world-buildera — do przejrzenia): dwa klucze manifestu,
   `splash_h` (włącza `_SPLASH` z własną wysokością) i `macro` ([rozmiar, siła]). Flagi `weather` / `runoff` i warunek
   `_Tile = set_tile || elementScan || atlas` nietknięte. `tint_linear` dalej tylko dla powłoki budynków.
10. **Kamery** (`tools/worldgen/qa/buildings_cameras.py`): oko i punkt patrzenia zapisywane 10 m nad gruntem budynku
    (promień osadzania startuje nad nasypem — `r10_hall_3` stała na rampie 6 m nad gruntem hali), kąty widoku per
    budynek (`ANGLES_FOR`) dla `r10_hall_1`.

## Liczby (edytor; nic z telefonu)
Średnie sRGB z tych samych prostokątów JPG 1280 px (`artifacts/buildings-r11/measure.py`), baza → r3:

| prostokąt | High overcast | Low overcast | High clear |
|---|---|---|---|
| niebo (`r10_block_3`) | 238,2 (bez zmian) | 233,8 | 220,9 |
| szary tynk, szczyt | 92,1 → 127,4 (+35) | 85,6 → 121,9 (+36) | 83,1 → 106,1 (+23) |
| szary tynk, front | 97,9 → 131,1 (+33) | 91,8 → 126,2 (+34) | 86,1 → 108,0 (+22) |
| cegła (`r10_block_4`) R/G/B | 70,5/40,7/34,1 → 64,8/43,6/39,0 | 66,1/37,2/31,0 → 58,0/38,1/33,9 | 67,4/48,6/44,0 → 63,3/50,9/48,4 |
| cegła R/B | 2,07 → 1,66 (−20 %) | 2,14 → 1,71 | 1,53 → 1,31 |
| cokół | 56,5 → 52,5 | 51,1 → 47,1 | 58,5 → 54,9 |

- **„Pieprz” tynku — cel niespełniony na ekranie.** Zestaw: rozrzut albedo p05–p95 0,104 → 0,060 (−43 %), relief
  5,7 mm → 0,7 mm. Na ekranie (odchylenie luminancji po odjęciu rozmycia 3 px, czysty prostokąt szczytu, High overcast)
  2,00 → 1,89 poziomu, czyli −5 % bezwzględnie i −32 % względem jasności ściany (2,17 % → 1,48 %). Połowy nie ma.
  Prostokąt „front” zawiera rurę spustową, jego hf (8,6 → 8,8) nie mierzy tynku.
- Tekstury świata (estymata ASTC z mipami, `materials_spec.json`) H / M / L: 197,5 / 39,6 / 7,3 → 198,1 / 39,7 / 7,3 MB
  (budżet 256 / 96 / 64 MB).
- Geometria regionu (GLB): High 401 → 404 MiB, Low 91 → 92 MiB.
- Budżet Low na kamerach kontrolnych (`stats.txt`, estymata edytora, 58 kamer bez przestawionej `r10_hall_1`):
  trójkąty maks. +2,2 % (`putry-above`) — w limicie +3 %. **Draws: 4 kamery ponad +3 %** — `dk8-dk19-exit` 77 → 81
  (+5,2 %), `r10_fence_1` 306 → 317 (+3,6 %), `putry-above` 291 → 301 (+3,4 %), `r10_block_3` 375 → 387 (+3,2 %);
  pozostałe ≤ +3,0 %. Kamery celu: `r10_block_2` 372 → 383 draws / 361 → 365 tys., `r10_block_5` 375 → 386 / 391 → 394,
  `r10_house_1` 141 → 144 / 170 → 171, `r10_house_2` 142 → 144 / 178 → 179.
- Testy: `pytest tests/gis` 252 passed, 3 failed, 2 xfailed (stan po r3)
  — te same 3 co na main wg `HANDOVER.md` (`test_road_fidelity::test_report_not_stale`,
  `test_route_corridor` × 2 przy s ≈ 1432–1480). EditMode: 191, 188 passed, 3 failed —
  `TruckDoorGlassTests` × 3 tiery („MI_Ext_DoorGlassL … null”), materiał ciężarówki; nie uruchamiałem EditMode na
  main, więc „odziedziczone” jest UNVERIFIED.

Dowody: `artifacts/buildings-r11/{base,r1,r2,r3}/<Tier-light>/` (PNG, `1280/*.jpg`, `stats.txt`),
`artifacts/buildings-r11/adr/` (pary przed / po, arkusze, `runoff_crop_1to1_block_1.png` — crop 1:1 zacieków pod attyką).

## Samokrytyka (docs/06)
- Bez oceny `visual-critic` (zakaz subagentów w zadaniu) i bez telefonu. Rundy poprawek: 3 z 3 wykorzystane.
- Domy: jeden dach nad całym prostokątem ograniczającym — dom w kształcie L nie ma dachu wielopołaciowego z koszami,
  tylko wyższe ściany we wklęsłym narożniku. Brak lukarn, okien połaciowych, ganków. Wszystkie tynkowane domy są
  białe / jasne, tynk na dużej białej ścianie wciąż czytelnie „chmurkowaty”. Drzwi i okna to płaskie komórki atlasu.
- Dach: jedna tekstura fali dla dachówki i blachodachówki; z bliska blacha nie ma arkuszy ani gąsiorów, kalenica jest
  ostrą krawędzią bez gąsiora, kominy bez obróbek.
- Balkony: `r10_block_3` i bliski blok w `r10_block_5` nadal pokazują elewacje bez balkonów — reguła słoneczna
  postawiła je po drugiej stronie; w `r10_block_2`, `r10_block_4`, `r10_fence_3` są widoczne. Reguła jest zgadywaniem
  do czasu zdjęć właściciela lub danych per budynek. Balkony z bliska to ciemne pudełka (spód i boki bez detalu).
- Glif okna jest geometrią ościeża, nie normal mapą komórki atlasu — ramy w komórce dalej płaskie.
- Cokół wysoki na skarpie (`r10_block_5`, ok. 2 m) nadal jednolity: strefa rozbryzgu liczy się od poziomu odniesienia
  budynku, nie od terenu przy ścianie.
- Zacieki pod attyką: w cropie 1:1 słabe szare smugi; siła × 0,6 bez zmian.
- `r10_hall_1` po przestawieniu pokazuje halę z ok. 60 m przez plac — nic jej nie zasłania, ale kadr jest pusty.

## Otwarte / do decyzji lidera
- Draws Low +3,2…+5,2 % na 4 kamerach: najtańsze cofnięcie to jeden ton cokołu (`PLINTHS = ["plinth_dark"]`).
- „Pieprz” na ekranie: źródłem nie jest już zestaw `plaster`; do sprawdzenia w shaderze (`macro.a`, drugi sampel
  `_KAMION_WORLD_DETAIL`) — poza własnością tego zadania.
- Po scaleniu: `build_all.py --only roof_tiles,plaster,brick`, `build_world`, `import-region`.

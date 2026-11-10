# ADR 0073: Zaparkowane auta r9 — sylwetki zamiast „mydelniczek”

- Status: proposed (truck-artist, 2026-11-10); ocena wizualna należy do `visual-critic`
- Kontekst: REVIEW-2026-11-10-r8 („auta-mydelniczki… ciągną obraz w stronę gry mobilnej z 2016 r.”, „matowe jak
  podkład”, „przody to mydło z kreską”). Uzupełnia ADR 0041 (addendum r9) i ADR 0050.

## Ustalenia (stan r8)
- Bryła powstawała z profilu bocznego przeciągniętego w poprzek. Sam mechanizm jest w porządku; mydło dawały
  parametry tego, CO jest przeciągane: rzut z góry jako ćwiartka elipsy 0,80 × 0,27 m (dziób łodzi), maska i szyba o
  zbliżonym pochyleniu (12° / 25°: klin), pas lamp wysokości 5–8 cm na pochylonej ścianie, miękka krawędź maski
  (Bezier 0,16 m), bok bez linii charakteru (rzędy siatki rozłożone równomiernie, nie na liniach bryły), nadkola bez
  wywinięcia.
- Lakier: `WorldPbrMaterials` ignorował `rough` z manifestu, każdy kolor miał gładkość zestawu `car_grime`
  (średnio 0,59) — stąd „podkład”.

## Decyzja
1. **Bryła** (`tools/worldgen/streetscape/life_cars.py`, `_controls` / `_Shell` / `_vehicle2`):
   - profil: maska jako wypukły łuk od podszybia do ciasnej krawędzi, prawie pionowy pas lamp (pochylenie 4–6 cm na
     27–31 cm), lico zderzaka, podbródek; z tyłu półka zderzaka pod klapą; szczyt dachu nad słupkiem B;
   - rzut z góry: narożniki superelipsą (wykładnik 2,3): proste błotniki, potem właściwy narożnik;
   - przekrój: podcięcie progu, pionowa skóra drzwi, faseta barkowa pod linią szyb (łapie niebo), tumblehome;
     rzędy siatki boku leżą NA tych liniach; wywinięcia nadkoli (16–30 mm) + pierścień rantu 10 mm;
   - detale: klosz lampy (jasny odbłyśnik w ciemnej obudowie) zachodzący na błotnik, zespoły lamp tylnych z lampą
     cofania, linie maski / drzwi / zderzaków, czarne słupki B, uszczelka pod szybami, podszybie, wycieraczki,
     klamki we wnęce, lusterka klinowe na stopce, relingi, listwa nad tablicą;
   - koła: bok opony 34–40 % promienia z wybrzuszeniem, felga z beczką 85 mm i ramionami wewnątrz rantu.
2. **Typy** (wymiary klasowe, WORKING_VALUE; żadna marka ani model nie jest odwzorowany, brak znaczków i sygnatur
   grilla / lamp): hatchback kompaktowy 4,26 m, sedan 4,64 m, kombi 4,66 m, SUV kompaktowy 4,42 m, **furgon średni
   4,90 × 1,93 × 1,97 m** (zastępuje kombivana 4,5 m: krótka stroma maska, pionowa szyba, prowadnica drzwi
   przesuwnych, drzwi dwuskrzydłowe, zderzaki niemalowane, felgi stalowe).
3. **Lakier**: `rough` koloru w manifeście = czysty lakier bezbarwny (0,20–0,36); importer skaluje gładkość zestawu
   `car_grime` do tej wartości (`_SmoothnessScale`, tylko `car_paint_*`). Felgi jaśniejsze (0,50), klosze tylne
   ciemniejsze od czerwonego lakieru.
4. **Narzędzia pętli wizualnej**: `tools/worldgen/qa/car_preview.py` (zrzut prototypów z normalnymi jak w GLB) +
   `tools/blender/world/render_cars.py` (stałe kamery: rząd 3/4 przód / tył, z kabiny 2,5 m, zbliżenia, elewacje;
   overcast / lowsun). Referencje proporcji typów: Mapillary (CC BY-SA) z trasy, wyłącznie jako wzór proporcji.

## Zmierzone
- Trójkąty (27 prototypów, `props_meta.json`): LOD0 3195–3497 (r8: 3528–3798; cel ≤ 3500), LOD1 844–882 (limit 900),
  LOD2 54–58 (limit 60).
- Dziury (`car_holes_qa.py`, 8 azymutów × 3 elewacje, 25 mm): 0 z 81 siatek (`artifacts/cars-r9/holes-final.log`).
- Budżet klatki (szacunek `streetscape_qa.json`): High maks. 1 997 661 (`stretch_04`, limit 2,0 M; r8 1 997 615),
  `stretch_01` 1 661 414 → 1 636 945, `stretch_05_docks` 1 742 105 → 1 724 078; Low maks. 962 150 → 961 666, DK8 Low 357 442.
- Koszt Low w edytorze (`stats.txt`, overcast, rysowania instancjonowane / trójkąty; pierwszy przebieg r9): `cab-dash`
  553 → 542 / 76k → 73k, `stretch-01` 624 → 624 / 95k → 91k, `car_lod_08` 597 → 593 / 99k → 97k. Telefon: UNVERIFIED.
- Testy: pytest `tests/gis` 170 zielonych (w tym nowy `test_cars_r9.py`), EditMode 176 / 176.
- Rendery: Blender `artifacts/cars-r9/it0` (r8) … `it8`, montaż z referencją `compare/it5_cab_vs_refs.jpg`; silnik
  `artifacts/cars-r9/after/{Low,High}-{overcast,lowsun}/`, montaże r8 / r9 `compare/<tier>-<light>_<kamera>.jpg`.

## Konsekwencje / otwarte
- Bryły są wiarygodne klasowo, ale nadal proceduralne: lampy i grill to płaskie nakładki bez głębi, lusterka i klamki
  uproszczone; z 3–5 m widać to. Auto „starsze ~2005” jako osobny typ nie powstało (27 prototypów bez zmian: każdy
  nowy prototyp to dodatkowe rysowania na Low, a `stretch_04` High ma 2,3 tys. trójkątów zapasu).
- Lakier metaliczny: `car_grime` nie ma kanału metalu, więc srebrny i szary są dielektrykiem z jasnym albedo; odbicie
  nieba rośnie tylko przez Fresnela. Prawdziwy płatek wymaga kanału w zestawie albo osobnego shadera (rendering-perf).
- LOD2 (Low od 42,5 m) pozostał pierwszą, pudełkową bryłą (≤ 60 trójkątów) w nowych wymiarach.
- Film drogowy i kurz na szybach są na prototyp, nie na instancję (bez zmian).
- Koszt na A16 / S24+ niezmierzony (UNVERIFIED); trójkątów LOD0 jest mniej niż w r8, rysowań tyle samo lub mniej.
- Atrybucja Mapillary dla zdjęć użytych jako wzór proporcji (1523897771888181, 513486983365569, 364149059846390):
  `uv run --project tools/refs python tools/refs/mapillary_fetch.py --region bialystok-industrial-c --use <id>… --attribution`
  (wymaga `Data/raw/mapillary` z main) — do wykonania przez lidera.

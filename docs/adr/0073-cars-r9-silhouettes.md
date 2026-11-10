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
WYNIKI_PLACEHOLDER

## Konsekwencje / otwarte
OTWARTE_PLACEHOLDER

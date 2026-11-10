# ADR 0078: Zaparkowane auta r10 — lampy pod kloszem, lakier dwuwarstwowy, sylwetka LOD2, brud

- Status: proposed (truck-artist, 2026-11-10); ocena wizualna należy do `visual-critic`
- Kontekst: po r9 (ADR 0073) auta miały sylwetkę, ale z 4–8 m nadal czytały się jak gra mobilna: lampy i grill jako
  płaskie naklejki 6–10 mm nad blachą, opony bez bieżnika, lakier jednowarstwowy (brak głębi clear coatu i płatka),
  LOD2 jako pudełko ≤ 60 trójkątów, film drogowy na tyle jako prostokąty o twardych krawędziach.
  Uzupełnia ADR 0041 (życie świata) i ADR 0073.

## Decyzja
1. **Geometria LOD0** (`tools/worldgen/streetscape/life_cars.py`, `_vehicle2`):
   - otwory wycięte w skorupie (`holes`, punkty `bp` / `hp` na cięciwach kolumn skorupy, żeby cięte ściany dzieliły
     krawędzie z sąsiadami): kubły reflektorów 45 mm (odbłyśnik, ciemne ścianki, soczewka projektora, przegroda),
     grill 38 mm i dolny wlot 35 mm z lamelami, lampy tylne 22 mm (czerwona taca, listwa światłowodu, lampa cofania);
   - przezroczysty klosz nad każdym otworem = materiał szyb `car_glass_tint` z kodem w UV0 (`LENS_U` = 8), dekodowany
     w `WorldCarGlass.shader` (`_LensOpacity`); ten sam materiał i draw call co szyby;
   - tablice na ramce 20 mm nad zderzakiem, wycieraczki (ramię + pióro), klamki-uchwyty, uszczelki szyb;
   - opony: tekstura bieżnika / boku (`tyre_texture`, 8 powtórzeń na obwód), pierścień barku; felgi: żebrowane
     ramiona, kołpak na feldze stalowej, alufelga dwuramienna;
   - film drogowy: rant nadkola za kołem; **film na tyle i przodzie leży na kolumnach skorupy** (czworokąt od g = 0,7
     do 2,0 był cięciwą przez łuk barku: połowa tonęła w blasze, reszta odstawała jako prostokąt); film nie wchodzi
     na przednią tablicę;
   - **nakładki na boku kładzione NA siatce** (`drape`, `drape_line`): zachodzące na błotnik części lamp i szwy
     zderzak / błotnik są cięte trójkątami poszycia (każda strona ma własne przekątne, patrz `_oq`) i leżą w ich
     płaszczyznach. Wcześniej płaskie trójkąty na analitycznym `sh.X` tonęły w załamaniu pod pasem barkowym albo
     odstawały od błotnika jako „drzazgi”;
   - poprawka błędu r9: krawędź przednich drzwi była 10 cm PRZED przednim nadkolem (`y1d = yfa + ra + 0,10`), a linia
     dołu drzwi przecinała wnękę koła; teraz `yfa − ra − 0,14`.
2. **LOD1** bez otworów (nakładki jak w r9) + listwy; **LOD2** = sylwetka (`_vehicle_far`): profil boczny z szybami,
   pas lamp, koła jako płaskie tarcze — zamiast pudełka.
3. **Lakier** (`_CARPAINT` w `Kamion/World PBR`, wypełniany przez `WorldPbrMaterials` z pola `paint` manifestu
   = [metal bazy, pochylenie płatka, perła, szorstkość bazy], opcjonalnie `pearl_tint`):
   baza (płatek aluminium / mika; kolory lite mają metal 0) + clear coat F0 0,04 z ostrym odbiciem otoczenia przy
   gładkości zestawu (film drogowy i kurz nadal go matowią). Medium+ (`_KAMION_WORLD_DETAIL`): iskrzenie płatka —
   pochylenie normalnej bazy per komórka w przestrzeni obiektu (400 komórek / m = 2,5 mm), wygaszane, gdy piksel
   pokrywa komórkę (pełne przy śladzie ≤ pół komórki, zero przy ≥ komórce). Pierwsza wersja (900 komórek / m, hash
   na `sin`, wygaszanie dopiero przy 8 mm) dawała na High widoczną „tkaninę” (mora) na całym srebrnym aucie z 4 m —
   patrz `artifacts/cars-r10/after1`; hash zastąpiony wersją bez `sin`. Low: bez płatka, 0 dodatkowych próbek tekstur; koszt = jeden płat GGX i jedna próbka
   otoczenia. Typy (WORKING_VALUE, brak polskiego rejestru rodzajów lakieru): srebrny, szary, niebieski — metalik;
   czarny — perła; biały, biały flotowy, czerwony — lite.
   **Zmiany w `WorldPBR.shader` są wydzielone**: 1 akapit komentarza w nagłówku, 3 właściwości, 1 linia CBUFFER,
   1 `shader_feature_local _CARPAINT` i trzy bloki `#if defined(_CARPAINT)` (metal bazy, płat bazy + coat w świetle
   kierunkowym, odbicie otoczenia). Poza tymi blokami kod jest nietknięty — do scalenia z ADR 0080 (oświetlenie).

## Budżety (zmierzone, `car_preview.py` / testy)
- LOD0: 3936–4158 trójkątów (r9: 3195–3497). Limit testu 3500 → **4200** (WORKING_VALUE). Z tego ok. 150 trójkątów
  to koszt kładzenia nakładek na siatce (cięcie trójkątami poszycia w narożnikach).
- LOD1: 864–890 (limit 900), LOD2: 86–90 (limit 96; r9 ≤ 60).
- Klatka (estymata `mesh_budget`, kamery kontrolne): najwięcej aut LOD0 w kadrze na High = 63 (stretch_01),
  Low = 5; `test_frame_budget_with_forest_hlod` i `test_hero_bridge` (stretch_04 ≤ 2,0 M) przechodzą.
- `car_holes_qa.py`: 0 z 81 siatek z dziurami (27 prototypów × 3 LOD).
- Koszt na telefonie: **UNVERIFIED** (bez pomiaru na urządzeniu w tym zadaniu).

## Odrzucone
- Podniesienie nakładek (większy `lift`) zamiast kładzenia na siatce: przy 12 mm nadal tonęły w załamaniu, przy
  30 mm rzucałyby widoczny cień i odstawały z profilu.
- Usunięcie zachodzących lamp i szwów: bez nich bok auta nie ma lampy ani podziału zderzak / błotnik.
- Osobny materiał kloszy: +1 draw call na prototyp; kod w UV0 nic nie kosztuje.

## Otwarte
- Bryła nadal jest fasetowana (rzędy na liniach charakteru, brak wygładzonych normalnych na łukach) — z 3–4 m widać
  wielokąty maski i błotników.
- Pomiar kosztu `_CARPAINT` i LOD0 4200 na telefonie (Low / Medium).
- Wnętrze: bryły foteli bez detalu.

## Wynik r10b (2026-11-10, po scaleniu `main` z ADR 0080; trzeci agent)
Dowody: `artifacts/cars-r10/{m1,m2,m3}/<Tier>-<światło>/` (m1 = przed zmianami lakieru, m3 = stan końcowy), kamery
`r10b_<black|grey|blue|silver>_<05|20|45>` z `artifacts/cars-r10/add_dark_cams.py` (przód 3/4 z 5, 20 i 45 m, oko 1,7 m).
Referencje (Mapillary, otwarte): `artifacts/cars-r9/refs/mapillary_*_crop.jpg` (czarny van w słońcu, szary hatchback
i biały SUV pod chmurami).

- **Mora płatka: usunięta.** High overcast i clear, srebrny SUV z 1,5–5 m i z 20–45 m: brak „tkaniny”. W m1 została
  ziarnistość „sól z pieprzem” na srebrnym z 1,5 m (pochylenie płatka działało też na odbicie nieba w bazie);
  w m3 pochylenie płatka w pełni tylko w płacie słońca, w odbiciu otoczenia × 0,3.
- **Ciemne auta „w czerni” (recenzja 0080 P1 #2): przyczyna po stronie lakieru potwierdzona i poprawiona częściowo.**
  (a) `diffColor = albedo · (1 − metal)` zostawiało ciemnym metalikom 25–45 % albedo → teraz `1 − 0,5 · metal`;
  (b) albedo: czarny 0,018 → 0,035, granat 0,03/0,05/0,12 → 0,045/0,085/0,21, szary 0,13 → 0,16;
  (c) płatek odbija jaśniej niż pigment: `specColor = lerp(0,04, albedo + _CarFlake.z, metal)`, `_CarFlake.z` = 0,08.
  Wszystko WORKING_VALUE (brak pomiaru lakieru). Zmierzone sRGB 8-bit, średnia z wycinka kadru zmniejszonego do
  1100 px (ten sam wycinek we wszystkich przebiegach):

  | kadr | przed | po (m3) | tło w kadrze |
  |---|---|---|---|
  | granatowy SUV, drzwi, High overcast (`r10_front_04`) | 18/19/21 (m1) | 19/22/33 (m2) | opona 39/35/31 |
  | czarny hatchback, drzwi, High overcast (`r10b_black_05`) | 15/15/15 (m2) | 20/21/20 | asfalt 70/68/65, niebo 184 |
  | czarny hatchback, maska / dach, High overcast | 60/61/64 · 74/75/77 (m2) | 67/68/78 · 82/83/92 | opona 57/55/51 |
  | czarny hatchback, drzwi, High clear | 41/42/40 (m2) | 49/50/49 | opona 96/94/88 |
  | czarny hatchback, drzwi, Low overcast | 13/13/12 (m2) | 17/18/17 | opona 62/59/56 |

  Maska i dach odbijają niebo i czytają bryłę; granat jest granatowy, szary — szary; z 20–45 m auta nie zlewają się
  w plamę. **Bok czarnego auta w overcast nadal jest ciemniejszy od opony** (20 wobec 57): pionowa, płaska blacha
  widziana z 1,7 m odbija w clear coacie grunt (R.y < 0), a nie niebo, i dostaje połowę światła otoczenia; resztę
  robi krzywa tonalna ADR 0080. Tego nie da się uczciwie podnieść lakierem bez zawyżania albedo — zostaje dla światła
  (r11) albo dla geometrii (wypukły bok z pochyleniem ku górze).
- **Lampy:** reflektory z 4–5 m czytają się jako kubeł z jasnym odbłyśnikiem pod kloszem; z 20 m jako jasny klin —
  akceptowalne. **Lampy tylne nadal płaskie**: jednolita czerwona taca z jasnym prostokątem lampy cofania, klosz
  daje tylko mleczny nalot w clear; z 4 m to wciąż „naklejka pod szkłem”. Nie poprawiane w tej rundzie.
- **Szwy / drzwi a nadkole:** w m3 krawędź drzwi leży za nadkolem, szwy zderzaka nie odstają (`r10_wheel_02`,
  `r10_front_04`). Rant brudu na dole drzwi ma twardą, schodkową krawędź.
- **Budżet:** geometria bez zmian w tej rundzie (LOD0 3936–4158, limit 4200 zostaje). Estymata klatki Low
  (`streetscape_qa.json`, 19 kamer kontrolnych) względem `main`: suma +0,69 % (10 815 289 → 10 890 317), High
  +0,47 %; największa pojedyncza kamera Low +1,80 % (`route_onramp_andersa_above`, +14 804), kolejne +1,52 %
  (`kwadrat_park_gate`), +1,28 % (`stretch_05_docks`), +1,02 % (`stretch_02`). Przyrost pochodzi z kategorii `props`,
  głównie z LOD1 / LOD2 (LOD2 60 → 86–90), nie z limitu LOD0 — obniżenie limitu LOD0 do 3500 nie zmieniłoby tych
  czterech kamer istotnie (rozbicia na LOD nie mierzono: UNVERIFIED).
- **Testy:** EditMode 188/188. `pytest tests/gis`: 225 passed, 3 failed, 2 xfailed — te same 3 padają na `main`
  (`test_road_fidelity::test_report_not_stale`, `test_route_corridor::test_route_corridor_is_clear`,
  `::test_route_profile_has_no_steps`); nie dotyczą aut.
- **Scalenie z `main`:** `WorldPBR.shader` scalony automatycznie (bloki `_CARPAINT` i ADR 0080 obok siebie),
  pliki generowane `--ours` + regeneracja (`build_world_4.log`).
- Koszt shadera na telefonie: nadal **UNVERIFIED**. Recenzja `visual-critic` r10b: do zlecenia przez lidera.


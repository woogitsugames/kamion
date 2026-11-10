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
   pas lamp, koła jako ciemne pasy — zamiast pudełka.
3. **Lakier** (`_CARPAINT` w `Kamion/World PBR`, wypełniany przez `WorldPbrMaterials` z pola `paint` manifestu
   = [metal bazy, pochylenie płatka, perła, szorstkość bazy], opcjonalnie `pearl_tint`):
   baza (płatek aluminium / mika; kolory lite mają metal 0) + clear coat F0 0,04 z ostrym odbiciem otoczenia przy
   gładkości zestawu (film drogowy i kurz nadal go matowią). Medium+ (`_KAMION_WORLD_DETAIL`): iskrzenie płatka —
   pochylenie normalnej bazy per komórka w przestrzeni obiektu (900 komórek / m), wygaszane po śladzie piksela
   (bez migotania z daleka). Low: bez płatka, 0 dodatkowych próbek tekstur; koszt = jeden płat GGX i jedna próbka
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

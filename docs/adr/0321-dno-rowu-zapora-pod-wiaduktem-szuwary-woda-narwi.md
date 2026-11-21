# ADR 0321 — Teren pod rowem, zapora krawędzi pod wiaduktem, szuwary poza chodnikami, barwa Narwi

Status: Proposed (agent world-fix2-s24, gałąź `world-fix2-s24`), 2026-11-21. Do scalenia przez lidera.
Powiązane: ADR 0110 (węzły „soft” pod trawą), ADR 0311 (obrys skarpy — inny przypadek), ADR 0169/0295 (zamknięcia
krawędzi kafla), ADR 0213/0318 (pas szuwarów, woda), przegląd vqa-wave5 i water-tykocin-s24.

## 1. Ząbki na skarpach rowów (P2, DK65 knyszyn-w / knyszyn / dk65-07)
Przyczyna (sonda przekroju GLB knyszyn-w E 122 N 787): teren w węzłach pokrytych tylko trawą rowu stał
`SOFT_UNDER` = 0,04 m pod powierzchnią w samym węźle. Rów wiejski ma skarpy 1 : 1,5 i dno 0,4 m — profil wypukły
(wklęsłe załamania). Trójkąt siatki terenu 1 m (przekątna 1,41 m) przechodzący przez załamanie leży do ~0,24 m nad
dnem, więc trawa terenu przebijała skarpę tylną rowu w regularne zęby (inny materiał: `terrain_grass` vs
`verge_grass`). To nie jest przypadek ADR 0311 (tam schodki rastra w obrysie nasypu poza drogą).

Decyzja: `conform.rasterise_floor` — najniższa wysokość powierzchni trawy pobocza (wierzchołki + siatka
barycentryczna co 0,2 m) w czterech komórkach wokół każdego węzła; `conform(..., soft_floor=)` obniża KAŻDY węzeł do
`floor - SOFT_UNDER`. Trójkąt terenu leży w komórkach wokół każdego swojego wierzchołka, więc z definicji nie może
wystać nad trawę. Poza obrysem działa najwyżej jedną komórkę za skarpą tylną, gdzie dolny fartuch pasa (0,5 m,
1 : 1,5) zakrywa obniżenie. Płaskie pobocza miejskie bez zmian pod pasem (test). Geometria drogi bez zmian.
Parametry WORKING_VALUE. Test: `tests/gis/test_ditch_floor_0321.py` (stara reguła przebija > 5 cm, nowa ≤ 0).

## 2. Zapora B-1 wzdłuż pasa DK8 przy wiadukcie (P2, dk8-wasilkow-01)
Przyczyna: droga w1220009817 (tertiary) wychodzi zachodnią krawędzią kafla i przechodzi pod wiaduktem DK8
(w145631572, bridge, 9,5 m). Domyślne odsunięcie 60 m wypadało pod pomostem; `RoadY` bierze najwyższą jezdnię, więc
rząd zapór stał na pomoście DK8, prostopadle do drogi dolnej = wzdłuż pasa DK8.
Decyzja: `WorldEdgeBuilder.ReadExits` (jedyne źródło zamknięć, czyste, bez sceny) przesuwa zamknięcie w krokach
2 m najpierw ku krawędzi, potem w głąb, aż cały rząd (połowa pomostu + połowa rzędu + 2 m) omija pomost innej drogi
(`bridge` ≠ no albo `layer` ≥ 1, poza własnym łańcuchem drogi, tylko odcinki pomostu pod kątem > 30° do drogi —
most bliźniaczej jezdni obok nie jest pomostem nad drogą: bialystok-industrial-c, Maczka, w262140922). Test EditMode `WorldEdgeClosureDeckTests`.

## 3. Szuwary: „jodełki” i trzcina na promenadzie (P2, tykocin)
- `water_banks.walk_polys`: chodniki/ścieżki/deptaki z `generated/osm_context.json` (pół szerokości wg typu +
  0,75 m) wyłączone z pasa (jak drogi) i dodane do `keep_out` kart w etapie wody. Promenada S brzegu Narwi:
  OSM 1132985888 / 1132988375. `water_banks.json` VERSION 2.
- `reeds.build` High: kępy nieregularne — gęstość kępy 0,55–1,0 próbek, para kart przesunięta ±0,9 m wzdłuż /
  ±0,5 m w poprzek, szerokość 0,6–1,15 × 2,6 m, pierwsza karta dowolny kąt, druga 70–110° do niej (zamiast ±40° do
  brzegu co 2 m = regularna jodełka z góry). Low: losowa amplituda zygzaka 0,35–1,0 × 0,9 m. Liczba trójkątów
  High maleje (pomijane próbki). Wszystko WORKING_VALUE, deterministyczne (sha1 pozycji).

## 4. Tafla Narwi z bliska ciemnoszara (P3, tykocin)
Pomiar: Commons `Tykocin_Most_drogowy_03.jpg` — tafla sRGB ~98/115/121 (niebieskoszara, odbicie nieba, mały kąt);
render tyk_narew_side (vqa r3) ~62/65/66, neutralna szarość. Domyślne ciało wody (ADR 0213) strojone na humusowej
Supraśli. Decyzja: nadpisanie per region `Region.water_material` → `build_region` zapisuje `water.material` w
region.yaml (przeżywa regenerację) → `build_world.region_water_materials` (manifest + GLB). Tykocin: ciało
0,095/0,118/0,128, płycizna 0,120/0,135/0,115 (liniowo, WORKING_VALUE). Shader bez zmian.

## Wyniki (zmierzone, render High 1920×1080 clear, edytor; przed = vqa-wave5 / water-tykocin-s24 r3)
- knyszyn-w: węzły soft 8 596, obniżone przez floor 7 560; sonda E 122 N 787: teren 0,6 m pod skarpą tylną (było
  0,04 m), za koroną −0,14 m, fartuch zakopany. `terrain_walls` steep_grass 18 → 5, max 0,505 → 0,441 m.
  dk8-wasilkow-01: soft 5 949 / obniżone 5 430, steep_grass 30 → 7. Rendery dk65-fields-nw, dk65-goniadzka,
  drive-wood (dk65-07): zęby zniknęły, rów ciągły.
- dk8-wasilkow-01: zamknięcie drogi w1220009817 na E −974,2 N 404,8, wysokość 124,83 m (jezdnia dolna; pomost
  ~141 m), rząd w poprzek drogi na zachód od wiaduktu; w01_br1_on_deck / eye_ab bez zapory na DK8.
- tykocin (po scaleniu ADR 0320): trzcina High 139 168 → 116 752 tris (−16 %), wstęgi 4 193 → 4 050; pas 9 132 m;
  koniec pasa w buforze chodnika p50/p90 0,23/0,47 m (było 1,05/1,64, max 1,99 = na ścieżce); szuwar między
  promenadą a wodą zostaje (zgodnie z Commons 03/05). Z góry kępy losowe zamiast jodełki. Tafla w widoku skośnym
  niebieskoszara z odbiciem nieba (water-oblique-bridge), z boku 20 m nad wodą 58/65/68 sRGB (było 62/65/66).
- EditMode 1525: 1410 pass, 0 fail (w tym WorldEdgeClosureDeckTests, WorldEdgeClosureDuplicateTests).
  pytest: test_ditch_floor_0321, test_water_0213, test_embankment_pylons_s24 zielone.

## Otwarte
- Granica `verge_grass` (ciemniejsze albedo) / teren to teraz prosta krawędź korony rowu — miękkie przejście
  materiału (mieszanie) nie zrobione; P3.
- Z góry karty trzciny nadal czytelne jako pojedyncze „krzyżyki” (już bez regularnego wzoru); gęstsza tekstura / kępy
  wielokartowe — osobne zadanie.
- Kafle sąsiednie z wodą Narwi/Nereśli (dw671-tykocin-08/-09) mają domyślne ciało — przy ich regeneracji rozważyć
  to samo nadpisanie (inaczej skok barwy na szwie, jeśli tafla przechodzi przez szew).
- Kafle z rowami poza przebudowanymi (np. knyszyn — kamera dk65-inlet-south) dostaną poprawkę 1 przy regeneracji.
- `visual-critic` do zlecenia przez lidera.

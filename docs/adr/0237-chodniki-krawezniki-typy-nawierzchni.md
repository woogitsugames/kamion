# ADR 0237 — chodniki i krawężniki Białegostoku: typy nawierzchni, obniżenia na przejściach, czerwona kostka, skala behatonu
Status: przyjęty (scalony do main 2026-11-16, `e4fad6868`; status zaktualizowany 2026-11-16); pierwotnie: Proposed (agent world-builder, chmura D runda 2, s21, gałąź `kerbs-0237`), 2026-11-15. Do scalenia przez lidera.
Powiązane: research R6 (PR #65, `origin/research/cloud2-pavements-kerbs`), recenzja
`docs/reports/REVIEW-2026-11-15-s21-cloudD-65-pavements-kerbs.md` (`origin/reviews-0225`), ADR 0063 (skany CC0), 0114
(obniżenia przy zjazdach), 0123 (`bridge_kerb` jako zmiana nazwy przy eksporcie), 0188 (DDR), 0221 (budżet dróg C).

## Kontekst
- Każdy chodnik przy jezdni był jedną nawierzchnią (`sidewalk_paving`, szara kostka 20 × 10), krawężnik miał stałą
  wysokość także na przejściach dla pieszych, a `cycle_red` wskazywał nieistniejący zestaw tekstur `paving_red`
  (płaski kolor 0,20/0,06/0,05; 175 m² w C, 252 m² w Dojlidach).
- Krawężniki i pas chodnika są siatkowane w `tools/worldgen/roads/meshing.py`, a eksport w `roads/build_world.py`.
  Ten plik zmienia gałąź `budget-fix-s21` (ADR 0221), więc zadanie nie mogło go ruszać.
- Kamery regionu C są na granicy 2 mln trójkątów High (`stretch_04` 2 022 535).

## Decyzja
1. **Typy nawierzchni chodnika** (`tools/worldgen/streetscape/pavements.py`): `paving_grey` → `sidewalk_paving`,
   `paving_red` → `sidewalk_paving_red`, `slabs` → `sidewalk_slabs` (płyty 35 × 35), `asphalt` → `path_asphalt`.
   Reguła, pierwsze trafienie wygrywa: (1) override `kind: sidewalk_surface` (`polygon_en` albo `target.osm_way`
   jezdni), (2) OSM `surface` chodnika w 3 m, (3) BDOT10k `OT_SKRP_L.materialnawierzchni` linii „aleja lub pasaż” w
   3 m (kostka prefabrykowana / masa bitumiczna / płyty betonowe), (4) klasa ulicy + typ zabudowy: ulica lokalna przy
   blokach ≥ 10 m → płyty, (5) szara kostka. Włączane per region wpisem `kind: pavement_rules`; region bez wpisu
   buduje się jak dotąd. Reguła (2) jest gotowa, ale `osm_context.json` nie przenosi dziś tagu `surface` (0 linii).
   Reguła (4) jest w obu regionach wyłączona (`estate_slabs: false`): R6 nie ma kadru z płytami przy blokach.
2. **Zmiana materiału tylko przy eksporcie.** `retype_sidewalks` dzieli części `sidewalk_paving` na podczęści z
   atrybutem `export_mat`; `mat` zostaje, więc reguły QA, fidelity i cull widzą chodnik jak dotąd. Liczba trójkątów
   jest zachowana (`tris_in == tris_out`, inaczej wyjątek).
3. **Obniżenia krawężników na przejściach**: `crossing_drops` tworzy wpisy dla `plots.apply_drops` (ten sam mechanizm
   co zjazdy 0114) z własną wysokością 0,02 m i rampą 1,0 m, na obu krawężnikach łańcucha, na którym leży węzeł OSM
   `highway=crossing` (bez `unmarked/no/informal`, czyli tam, gdzie generator maluje zebrę). Wpisy dokłada
   `stage.plan_plots`, więc trafiają do przebiegu 2 bez zmian w `build_world.py`. Bez obniżenia: przejście w płycie
   skrzyżowania lub bliżej przycięcia niż rampa + 0,5 m, na obiekcie mostowym, profil z rowem, krawędź bez krawężnika.
4. **Materiały**: `sidewalk_slabs` (zestaw `sidewalk_slab_35`, dotąd nieprzypisany), `sidewalk_paving_red` i
   `cycle_red` na nowym zestawie `paving_20x10_tint` (skan szarej kostki jako mapa modulacji, kolor z manifestu).
   Importer: `WorldPbrMaterials.BlockPavingElementSize` daje nowym zestawom jitter elementów, brud spoin i zabrudzenie
   jak szarej kostce.
5. **DDR**: kolor per odcinek zostaje w `kind: cycleway` (ADR 0188; C: 11 czerwonych way, Dojlidy: 0). Nowe:
   `foot_surface` w tym override (nawierzchnia połowy pieszej) oraz materiał ścieżki rowerowej z BDOT bez way OSM:
   kostka → `cycle_paver_material` regionu (C `cycle_red`, Dojlidy `sidewalk_paving`), bitumiczna → `cycle_asphalt`.
6. **Behaton**: skala per oś zamiast „jak w skanie”. **Wniosek recenzji „×1,16” jest błędny co do kierunku.**
7. **Wpust**: `GULLY_SIZE` 0,50 × 0,60 → 0,42 × 0,62 m w `roads/decals.py` i `streetscape/life.py` (sam parametr).
8. **Wysokość krawężnika** `roads.standards.KERB_HEIGHT = 0,13` zostaje (WORKING_VALUE). Zmiana przesuwa każdy
   krawężnik każdego regionu i wymaga oceny wizualnej; źródła są w `pavements.KERB_SOURCES`.

## Liczby i źródła
| Wielkość | Wartość | Status | Źródło |
|---|---|---|---|
| światło krawężnika, domyślne | 10–12 cm | SOURCED | OST D-08.01.01b pkt 5.5.1 (R6-001) |
| światło krawężnika, wyjątki | 6–16 cm | SOURCED | OST jw. (R6-002); Dz.U. 2016 poz. 124 § 43 ust. 5, akt uchylony (R6-003) |
| Dz.U. 2022 poz. 1518, wysokość krawężnika jezdni | brak liczby | SOURCED (wynik negatywny) | § 36 ust. 3: „uskok … o wysokości dostosowanej…” (R6-005) |
| krawężnik generatora | 0,13 m | WORKING_VALUE | 1 cm ponad zakres domyślny OST, w zakresie 6–16 |
| krawężnik na przejściu dla pieszych | 0,02 m | SOURCED dla wysp i pasów dzielących; WORKING_VALUE dla krawężników zewnętrznych | Dz.U. 2016 poz. 124 § 127 ust. 10 (R6-004, akt uchylony) |
| uskok na przejeździe rowerowym | ≤ 0,01 m | SOURCED | Dz.U. 2022 poz. 1518 § 45 ust. 4 (R6-006); generator: `cycleways.crossing_drops`, bez zmian |
| krawężnik na zjeździe | 0,03 m | WORKING_VALUE | `plots.DROP_H_M`; ZDM Białystok rys. 9: k1 25×12×100, rzędne 0 → +3, jednostka ESTIMATED (R6-015) |
| długość rampy obniżenia | 1,0 m | WORKING_VALUE | jeden prefabrykat 100 cm (OST zał. 3, R6-009); żadne źródło nie podaje długości |
| WR-D (piesi, rowery) | nieużyte | — | hosty niedostępne w R6; tylko WR-D-42-2 pośrednio (R6-048) |
| wpust D400 | 620 × 420 mm | SOURCED | karta producenta (R6-034) |
| behaton, podziałka w skanie | 274,7 mm wzdłuż, 319,7 mm na dwa rzędy | zmierzone | autokorelacja `concrete_pavers` 2k (1,92 m), `materials_spec.json` → `measured_period_m` |
| behaton, podziałka docelowa | 201 mm i 289 mm na dwa rzędy | SOURCED 198 × 163 (R6-023), spoina 3 mm (R6-020: 3–5); talia 120 mm WORKING_VALUE | skala x 0,7317, y 0,904; kafel 1,405 × 1,736 m |
| czerwona kostka, kolor liniowy | 0,26 / 0,125 / 0,11 | WORKING_VALUE | kadr F38 (P11-063): pas 97/76/75 sRGB, obrzeże obok 84/82/82; jeden kadr, JPEG |

Behaton: recenzja przyjęła, że skan ma rzędy 140 mm (tekst ADR 0063) i porównała je z szerokością obrysu 163 mm.
Pomiar pokazuje, że kostka w skanie jest dłuższym wyrobem (obrys ok. 269 × 183 mm), więc przy kaflu 1,92 m była o
37 % za długa. Kostki trzeba zmniejszyć, nie powiększyć. Podziałka rzędów zależy od talii, której R6 nie podaje.

## Dane regionów
- `bialystok-industrial-c`: `pavement_rules` (BDOT, obniżenia, `cycle_red`). Bez `sidewalk_surface`: kadr F16
  (przystanek na Andersa, „płyty”) nie rozstrzyga nawierzchni przy 1600 px (obejrzany).
- `bialystok-dojlidy`: `pavement_rules` (`cycle_paver_material: sidewalk_paving`) i jeden `sidewalk_surface`
  `mickiewicza-kuronia-red-block-strip` (pas czerwonobrązowej kostki z kadru F38 / P11-063). Położenie z geometrii
  zdjęcia, bez ortofoto: `confidence: low`.
- Szacunek zasięgu reguły BDOT (ESTIMATED, próbkowanie krawędzi grafu co 5 m, nie siatek): C ok. 380 m chodnika
  asfaltowego i 3,0 km z kostki; Dojlidy ok. 2,1 km asfaltowego i 1,4 km z kostki; reszta bez linii BDOT (domyślna
  szara kostka). Oznakowane przejścia w `osm_context.json`: C 90 (83 w 6 m od osi), Dojlidy 85 (77).

## Budżet
- Trójkąty: **0 netto na każdej kamerze** z konstrukcji. Obniżenia zmieniają wysokości istniejących stacji (test
  `test_lowered_kerb_adds_no_triangles`), retype dzieli części, wpust pozostaje jednym quadem. `frame_estimate` C
  (23 kamery, maks. `stretch_04` 2 022 535) i Dojlid (17 kamer, maks. 1 790 621) nie zmienia się w kolumnach tris.
- Materiały: do +2 identyfikatorów (`sidewalk_slabs`, `sidewalk_paving_red`) oraz `path_asphalt` w warstwie dróg, czyli
  dodatkowe prymitywy w kaflach, gdzie wystąpią (ESTIMATED, do zmierzenia po przebudowie: `materials_high`).
- Tekstury: `paving_20x10_tint` 2,49 MB ASTC High (nowy); `behaton_i_grey` High 1024 × 1264 px (było 1024 × 1024,
  +0,58 MB wg szacunku, o ile importer nie sprowadzi NPOT do potęgi dwójki). Do pomiaru na A16.

## Konflikt z `budget-fix-s21` i co NIE jest podłączone
`retype_sidewalks` wymaga trzech małych zmian w `roads/build_world.py` (`assemble` czyta `export_mat`, `WELD`, jedno
wywołanie `PVM.run` przed eksportem). Są w `docs/adr/0237-build-world-hook.patch`; `git apply --check` przechodzi na
`origin/main` i na `origin/budget-fix-s21`, a `git merge-tree` tej gałęzi z `budget-fix-s21` jest czysty. **Dopóki
lider nie nałoży łatki, chodniki przy jezdniach pozostają szarą kostką**, a override czerwonego pasa nie działa.
Bez łatki działają: obniżenia na przejściach, materiały, ścieżki z BDOT, `foot_surface`, behaton, wpust.

## Weryfikacja
- `tests/gis/test_pavements_0237.py`: 21 testów (syntetyczne + dane C i Dojlid z gita).
- Tekstury zbudowane w chmurze ze skanów zgodnych z sha256 manifestu; obejrzany arkusz: behaton przed/po z miarą
  198 × 163 mm, czerwona kostka, płyty. Pierwsza próba koloru (0,33/0,20/0,20) była różowa, poprawiona.
- **Nie zrobione w chmurze:** `build_world` (brak `Data/raw`), import do Unity, kamery kontrolne, porównanie ze
  zdjęciem, `visual-critic`, kompilacja C#, EditMode. Pętla wizualna jest po stronie lidera.

## Otwarte
- Obniżenia w płytach skrzyżowań (narożniki) i wysp; krawężnik 0,12 m; wieniec z kostki wokół włazów (R6-027);
  kolor kapy na estakadzie; `surface` chodników w `osm_extract.py`; płyty przy przystanku Andersa (brak dowodu).
- Kratka wpustu ma teksturę rysowaną dla proporcji 0,50 × 0,60, do oceny na renderze.

## Dopisek D38 (s23, 2026-11-16) — chodniki domniemane w zabudowie (Knyszyn) i skrzyżowanie Południowa × Szkolna
Gałąź `knyszyn-sidewalks-s23` (chmura D, runda 9). Fakty właściciela: `docs/owner/KNYSZYN-OWNER-FEEDBACK-S21.md`
„ul. Szkolna i skrzyżowanie Południowa × Szkolna” (chodniki wszędzie, obustronne, kostka; przejścia z pasami przy
skrzyżowaniu). Zrzutów Street View właściciela NIE użyto (zasada 8). Dane: `docs/reports/knyszyn-szkolna/`.

**(a) Reguła chodników domniemanych** (`streetscape/pavements.py`: `implied_rules`, `osm_sidewalk`, `eligible`,
`built_up_area`, `implied_plan`, `implied_mask`; wywołanie w `roads/network.assign_sides`). Włączana per region:
`pavement_rules: implied_sidewalks: true` (mapowanie nadpisuje listy). Na każdej stacji i stronie jezdni:
1. tagi OSM drogi wygrywają: `sidewalk:left|right` > `sidewalk:both` > `sidewalk`; `no|none|separate` = bez chodnika
   domniemanego (separate: chodnikiem jest zmapowany footway), `yes|both|left|right` = chodnik;
2. bez tagu: chodnik 2,00 m (`SIDEWALK_W`, WORKING_VALUE) za krawężnikiem, jeśli `highway` ∈ residential / tertiary /
   secondary / unclassified, nawierzchnia utwardzona (nie unpaved / ground / gravel / dirt / compacted / fine_gravel /
   sand / grass / mud), stacja w obszarze zabudowanym, krawędź nie jest „otwartą drogą” (ADR 0272) ani pasem
   dzielącym i w 6 m od krawężnika nie ma zmapowanej ścieżki (OSM footway/cycleway, BDOT10k OT_SKRP_L utwardzona) —
   okno większościowe 40 m jak przy regule footway. `living_street` wyłączone (strefa zamieszkania = wspólna
   nawierzchnia, WORKING_VALUE); `service`, `track`, `path` nigdy.
3. Obszar zabudowany: **cienki adapter** `built_up_area` — BDOT10k OT_PTZB_A o rodzaju jednorodzinna / wielorodzinna /
   zagrodowa + 60 m (te same wartości co ADR 0279). `streetscape/built_up.py` (#158) jest tylko na gałęzi
   `signs-a7-s23`; nie skopiowano z niej kodu. TODO(#158): po scaleniu podmienić adapter na strefę z `built_up.py`.
4. `roads.graph.json` nie niesie dziś tagów `sidewalk*` (stała lista tagów w `roadgraph.py`, poza zakresem rundy):
   `EdgeSection.osm_sidewalk` jest gotowe, ale puste do czasu dodania kluczy `sidewalk`, `sidewalk:left`,
   `sidewalk:right`, `sidewalk:both` w roadgraph i przebudowy grafów (lider). Knyszyn: w bbox skrzyżowania żadna droga
   nie ma `sidewalk=*` (OSM API 0.6, 16.11), więc brak tagów nic tu nie zmienia.
Knyszyn: wpis `knyszyn-pavement-rules-d38` (`implied_sidewalks: true`, `sidewalk_bdot: false` — właściciel mówi
„kostka”, `crossing_kerb_drops: true`). Wynik (płaski teren, sama geometria): +21,8 km chodnika (residential 14,4;
tertiary 3,5; secondary 3,5; unclassified 0,4), drogi regionu 225 427 → 264 161 trójkątów (+17 %).
**Szew z `knyszyn-w`:** 6 ulic przechodzi przez zachodnią krawędź kafla; z tym samym wpisem w `knyszyn-w` wszystkie 6
mają chodniki po obu stronach szwu (sprawdzone wstrzyknięciem reguły), bez wpisu — urwą się na szwie. Wpis do
`Data/Regions/knyszyn-w/overrides.yaml` dodaje lider (plik poza zakresem D38). `knyszyn-s`: reguła nic nie dodaje.
C i Dojlidy nie mają `implied_sidewalks` — test potwierdza identyczne tablice `walk` z regułą i bez.

**(b) Południowa × Szkolna (OSM 1134846746).** Przyczyna z grafu: 23,1 m dalej na Południowej jest węzeł 7015352011,
z którego wychodzi nieotagowana `highway=service` 750267067 (alejka parkingu szkoły). Klastrowanie złączyło oba węzły
w jedno skrzyżowanie 5 ramion; pierwszy odcinek alejki (13 m na ESE) biegnie prawie równolegle do ramienia Szkolnej E,
więc narożnik między nimi stał się „nosem” pasa dzielącego (półkole R 21,8 m przez wylot alejki), a ramię alejki
przycięto 28,3 m — za jej zakrętem: łezka asfaltu donikąd. Odcinek 23 m został „wchłonięty”, więc przejście
11514832009 nie miało jezdni do przyczepienia P-10, a 11514832007 wypadło z płata (skipped): 2 z 4 zebr.
Ortofoto GUGiK: zwykłe skrzyżowanie 4-wlotowe, zebra na każdym wlocie 0,4–1,6 m od węzłów OSM
(`crossing:markings=zebra`), wjazd na parking ~20 m na N. Poprawka: `roads/junctions.py` — override węzła
`cluster: separate` (wpis `knyszyn-szkolna-parking-tee-d38`): węzeł, w którym z drogi publicznej odchodzą tylko drogi
podrzędne (`service/track/path/footway/cycleway`), nie jest scalany z sąsiednim skrzyżowaniem, jeśli odcinek między
nimi ma ≥ 15 m (WORKING_VALUE); odcinek dzielą `max_trims`. Użyty na innym węźle — ignorowany z notatką. Po zmianie:
4 łuki (R 8/8/8/3,9 m), osobne T parkingu, 4 × P-10 (0,15–0,6 m od węzłów OSM). **`markings.py` bez zmian** (brak
P-10 wynikał z wchłoniętego odcinka). Jako reguła globalna ten sam test rozdzieliłby 12 klastrów w C, 1 w Dojlidach
i ~45 w innych regionach — nieobejrzane, więc tylko opt-in per węzeł.

**Budżet (ESTIMATED, `tools/worldgen/qa/knyszyn_szkolna_d38.py budget`, centroidy trójkątów, reguła widoczności
frame_estimate):** najwyższe High: `route_s0725` 1 893 995 → ~1 930 014 (+36 019), `tykocka_into_town` → ~1 833 719
(+38 055); Low `route_s0725` 603 399 → ~639 418 (Low było już ponad hipotezą 600 k). C/Dojlidy: 0.
Kamery kontrolne (authored): `knyszyn_szkolna_junction` (oko kierowcy na Południowej 40 m przed skrzyżowaniem),
`knyszyn_szkolna_top` (widok z góry, para do ortofoto).
**Otwarte D38:** szerokości chodników niezmierzone (2,0 m WORKING_VALUE); alejka parkingu w OSM ~12 m na E od
rzeczywistej (`ortho_readings.json`, niepoprawiona); żółte barierki na narożnikach SW i NE widoczne z góry —
UNVERIFIED, niemodelowane; sklep / zakład pogrzebowy / blok z muralem (bez marek, nazw i herbu) — poza zakresem;
`roadgraph.py` bez tagów `sidewalk*`; wpis w `knyszyn-w`; pętla wizualna (render, `visual-critic`) po stronie lidera.

## Dopisek s24 — nawierzchnie i krawężniki małych miast

`pavement_rules.mixed_sidewalks` włącza wspólny materiał chodnika. Kolejność wyboru to
override, OSM, BDOT10k, typologia i domyślna szara kostka. Gdy brakuje danych, klasy lokalne
dostają wariant według stabilnego skrótu identyfikatora OSM way. Obie strony i wszystkie chunki
odcinka dostają to samo rozstrzygnięcie. `older_sidewalks` dopuszcza płyty 35 × 35 cm i asfalt
na ulicach lokalnych oraz klasach `secondary` i `tertiary`. Udziały fallbacku oraz pigment czerwieni są
`WORKING_VALUE`. W Knyszynie fallback zachowuje kostkę zgodnie z uwagą właściciela.
Wpisy `sidewalk_surface` pozostają sposobem na wprowadzenie potwierdzonych miejscowych różnic.

Eksport zachowuje identyfikator `sidewalk_paving` i koduje wybór w COLOR_0. Na granicy typów
wierzchołki zachowują osobne wartości koloru i wspólną normalną geometryczną. World PBR
barwi szary skan kostki na czerwono albo pobiera istniejący skan płyt lub asfaltu.
Płytę i kostkę różnicują też dotychczasowe maski wymian nawierzchni z ADR 0349. Asfalt
ma własną maskę ciemniejszego uzupełnienia. Każdy wariant korzysta z tego samego prymitywu
w obrębie warstwy i chunka.

Krawężnik używa UV1 wzdłuż prefabrykatów i ziarna z identyfikatora pasa. Ton betonu zmienia się
między prefabrykatami, a miejscowe ubytki na górnej krawędzi od strony jezdni są symulowane
kolorem, chropowatością i normalną. Rozmiar i częstość ubytków są `WORKING_VALUE`. Obniżenia oznakowanych
przejść używają istniejącej reguły tego ADR (2 cm, rampy 1 m, poza płytami skrzyżowań i mostami).

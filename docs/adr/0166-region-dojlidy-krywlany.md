# ADR 0166 — drugi region: Dojlidy/Krywlany (`bialystok-dojlidy`) i potok świata dla regionu innego niż C
Status: Proposed (agent geo-worldgen, s17, gałąź `region-0166`), 2026-11-13. Do scalenia przez lidera. Bez importu do Unity
w main (decyzja lidera; import i kamery wizualne = osobny krok).

## Kontekst
Właściciel (D60) wybrał obszar Dojlidy/Krywlany jako następny region. Research P6 (`research/gptpro/p6-next-regions-2`,
przyjęty w `docs/reports/REVIEW-2026-11-13-s16-research-pack-02.md` §5) wskazuje tam najgęstszy klaster celów ciężarówek
(SSSE: Rosti, KAN, Odlewnia, Bravilor, PSS Społem DC; UNVERIFIED: BISON, Masterpress) i korytarz ciężki G10
Ciołkowskiego – Dywizjonu 303 – Kuronia. Potok `tools/worldgen` był dotąd uruchamiany tylko dla regionu C i miał trzy
założenia prawdziwe wyłącznie dla C, które wyszły przy pierwszym przebiegu nowego regionu.

## Decyzja
1. **Kafel** `bialystok-dojlidy`: EPSG:2180 [779019, 589055, 781067, 591103] (siatka 2048 m regionu C, i=+1, j=−3),
   origin (780043, 590079), z = NMT (EVRF2007). Pokrywa ~96 % kafla P6-K04 (779019,589199→781019,591199; P6 używa kafli
   2000 m — przesunięcie siatki 48/144 m zapisane, nie poprawiane). Trasa kontrolna (authored_override, nie trasa gry):
   Dywizjonu 303 na wschód od zachodniej krawędzi → Kuronia do wschodniej krawędzi (`route_endpoints.json`).
2. **Kamery kontrolne zależne od regionu.** `build_world.cameras()` = dispatcher: region C → `cameras_industrial_c`
   (dotychczasowy kod bez zmian; Andersa, Putry, Kwadrat Park, JRG2…), inny region → `cameras_generic`: oko kierowcy 2,5 m
   na prawym pasie w 3–8 stacjach trasy (co ~300 m), każde rondo z ~40 m, jedna orto kafla. Przyczyna błędu:
   `IndexError` przy szukaniu ulicy Andersa na trasie dojlidy.
3. **Wspólna biblioteka `art-source/world/{props,signs,textures}` należy do regionu C** (`SHARED_LIBRARY_REGION`).
   Region inny niż C zapisuje własną bibliotekę obok wyjścia świata: `Data/raw/derived/<id>/{props,signs,textures}`
   (poza gitem). Wcześniej build_world dojlidy przepisał `street_props.glb`, `props_meta.json` (−518 linii: inne znaki
   i tablice) i 7 tekstur mebli/`plot_kit` (w worktree bez Megascans/cc0 `_raw` → tekstury zastępcze). Pliki przywrócone
   do main. Następstwo dla importu (poza tym ADR): `InstanceImporter` czyta jedną bibliotekę z `art-source`; import regionu
   ≠ C musi czytać bibliotekę regionu albo bibliotekę-sumę — decyzja przy imporcie.
4. **Wspólne manifesty źródeł (per powiat, np. `gugik-bdot10k-2061`) nie są przepisywane przez nowy region**, gdy ich
   treść poza `used_by` jest identyczna: `region.yaml` regionu C przypina ich sha256, więc samo dopisanie `used_by`
   unieważniało C. Nowy region zapisuje manifest i jego sha256 we własnym `region.yaml`.
5. **Landmarki D51** jako dane: `Data/Regions/bialystok-dojlidy/landmarks_d51.authored.json` (wybór z P6 + Mistral P11/P12
   zweryfikowane w `docs/reports/REVIEW-2026-11-13-s17-mistral-r8-p11-p12.md` §4) → `tools/worldgen/qa/region_landmarks.py` → `generated/landmarks_d51.json`
   (geometria OSM w EPSG:2180, sha256 wycinka, nasze budynki w obrysie, brama na grafie lub nie) + mapa
   `docs/reports/map/bialystok-dojlidy_landmarks.png`. Wyniki, nie zgadywanie:
   - OK: Odlewnia (13,1 m LoD1), PSS DC, BISON, lotnisko Krywlany (61 % w kaflu), pas 09R/27L.
   - Rosti: w naszych danych brak osobnego obrysu — obrys BDOT10k (27 205 m², LoD1 18,92 m) jest 2× większy od budynku
     OSM Rosti (13 578 m²) i ma środek poza nim (łączy halę z sąsiednią); do `authored_overrides` przy modelowaniu.
   - Bramy Rosti, KAN, Bravilor, Masterpress (OSM node z P6) nie są węzłami grafu: drogi dojazdowe kończą się przed bramą
     albo brama stoi poza zmapowaną drogą — wjazdy do zleceń wymagają dociągnięcia `service` (szerokości i łuki
     UNVERIFIED, pomiar na `P6-G*.jpg`).
   - Sąd Rejonowy Mickiewicza 103 (way 484566822, LoD1 24,44 m) — najwyższy budynek kafla, dodany jako punkt orientacyjny.
   - Hangar Aeroklubu (way 304300294) ~360 m na zachód od kafla → usunięty z listy, zapisany jako tło (`out_of_tile_background`).
   - Kadry kontrolne (CC0, przegląd s17 §4): P11-001 (Kuronia, wzorcowy), P11-063, P11-094, P11-056, P11-129; ortofoto
     P12-A01; odrzucone P11-084/091/092/064. Zapisane w `control_photos`; ustawienie kamer pod te kadry = krok importu.

## Dane i QA (z naszych danych; liczby z `generated/*.json` i `docs/reports/map/bialystok-dojlidy_qa.json`)
- Graf: 355 węzłów, 421 krawędzi, 31,3 km (trunk 4,5 km, tertiary 5,4 km, service 13,9 km); 32 węzły brzegowe.
- Spójność: 5 słabych składowych (główna 346 węzłów; 4 małe = obcięte narożnikiem kafla odcinki Ciołkowskiego, Króliczej
  i jednej strefy zamieszkania). 22 silne składowe — pozostałe 18 węzłów „off-reach” to jednokierunkowe jezdnie trunk
  wjeżdżające do kafla z krawędzi (Dywizjonu 303, Kuronia, Ciołkowskiego, Mickiewicza): artefakt granicy kafla, znika po
  dołączeniu sąsiednich kafli; nie błąd OSM.
- Wolne końce (stopień 1, nie na krawędzi): 67 = 58 `service` + 9 `living_street`; zero na drogach ≥ unclassified.
- Pomosty/wiadukty: 0 w grafie (brak `bridge=*`), `hero bridges` puste. Jeden `prop_through_deck` (słupek znaku
  osm:node/5499949617, dz 0,52 m) mimo braku pomostu — przyczyna niezbadana (UNVERIFIED), do sprawdzenia przy imporcie.
- Spójność nawierzchni (`road_consistency_qa.json`): 27 przypadków (21 `lane_blind_end`, 5 `arrow_no_exit`,
  1 `prop_through_deck`), 0 na trasie kontrolnej.
- Wyrównanie osi OSM do ortofoto GUGiK 2024: 7 odcinków, |przesunięcie| mediana 0,25 m; odstający 9,25 m (Mickiewicza
  przy skrzyżowaniu: kolejka aut i szeroki wlot zaburzają klasyfikację jezdni — na renderze oś leży na jezdni);
  odległość do osi BDOT10k mediana 0,34 m, max 1,03 m.
- Budynki: 406 (BDOT10k 351, OSM 55); wysokość LoD1 2024 329, LoD2 2017 4, BDOT kondygnacje 8, OSM 1, domyślna 64.
- Teren: NMT 137,7–160,9 m EVRF2007, brak dziur; ściany terenu > 0,15 m: 9 (max 0,33 m).

## Testy (worktree, 2026-11-13)
- `tests/gis` pełny przebieg: 999 passed, 5 failed, 3 xfailed (worktree bez Megascans/cc0 `_raw`). Po skopiowaniu ich z
  main: `test_world_roads::test_export_is_deterministic` zielony (region C bajt w bajt jak w main), nowe
  `test_region_generic_0166.py` 3/3. Pozostałe 4 czerwone to środowisko/aktualizacja raportu, nie zmiana wyniku C:
  `test_road_fidelity::test_report_not_stale` (sha256 `build_world.py` — lider: rerun `fidelity/run.py` po scaleniu);
  `test_hero_bridge::test_instances_emitted`, `test_streetscape::test_instances_reference_existing_prototypes`,
  `test_far_field::test_generated_far_field_qa_and_manifests` czytają współdzielony (junction) `Data/raw/derived/
  bialystok-industrial-c/world` z innego przebiegu (instancje z 2026-11-12 13:37) — do potwierdzenia w main.
- Testy C przepisują pliki C w drzewie roboczym (in-process build) — przywrócone `git checkout`; `git diff origin/main`
  dla `Data/Regions/bialystok-industrial-c`, `art-source` i manifestów GUGiK 2061 pusty.

## Konsekwencje
- Region C: wynik bez zmian (te same funkcje kamer i ścieżka biblioteki; `git diff origin/main` dla
  `Data/Regions/bialystok-industrial-c`, wspólnych manifestów i `art-source` pusty).
- `fidelity_qa.json` regionu C liczy sha256 `build_world.py` → po scaleniu lider uruchamia
  `uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region bialystok-industrial-c`.
- Plik GPS `game/Assets/_Project/UI/Resources/CabDisplay/Nav/bialystok-dojlidy_route.bytes` (35,5 KB) jest generowany,
  ale NIE commitowany (trafiłby do APK bez importu regionu).
- Worktree agenta musi mieć skopiowane `art-source/world/megascans/_generated` i `art-source/world/cc0/_raw` z main przed
  build_world, inaczej tekstury mebli idą w fallback.

## Odtworzenie
```
uv run --project tools/worldgen tools/worldgen/ingest.py --region bialystok-dojlidy
uv run --project tools/worldgen tools/worldgen/build_region.py --region bialystok-dojlidy
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-dojlidy --context
uv run --project tools/worldgen tools/worldgen/qa_report.py --region bialystok-dojlidy
uv run --project tools/worldgen python tools/worldgen/qa/region_landmarks.py --region bialystok-dojlidy
uv run --project tools/worldgen python -m pytest tests/gis/test_region_generic_0166.py
```

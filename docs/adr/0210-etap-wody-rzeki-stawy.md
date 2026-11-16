# ADR 0210 — etap wody w generatorze świata (rzeki, strumienie, stawy) + Supraśl pod mostem DK65
Status: przyjęty (scalony do main 2026-11-15, `e243e3e86`; status zaktualizowany 2026-11-16); pierwotnie: Proposed (agent world-builder, s20, gałąź `water-0210`), 2026-11-15. Do scalenia przez lidera.
Powiązane: ADR 0207 (otwarte p. 1: brak rzeki pod mostem km 10,85), ADR 0173 / 0096 (determinizm), ADR 0064 (bake
widoczności nieba), docs/06 §6 (budżety).

## Kontekst
Generator (`tools/worldgen/roads/build_world.py`) nie miał etapu wody: dolina Supraśli pod mostem DK65 w `dk65-02`
była samym terenem NMT (ADR 0207). Zadanie wskazywało `dk65-04/05`, ale **most (way 41533342) i ujście Białej do
Supraśli leżą w `dk65-02`** (rzeka biegnie dalej przez `dk65-03`); `dk65-04/05` mają tylko stawy (Glinianki,
zbiorniki przeciwpożarowe) i rowy. Pierwszy cel = `dk65-02`.

Sondowanie danych (OSM `podlaskie-261108.osm.pbf`, BDOT10k) pokazało, że **oba istniejące regiony mają wodę w bbox**:
- `bialystok-industrial-c`: rzeka Biała (way 211185486, 937 m w kaflu), strumienie (~1,5 km, część w przepustach),
  zbiorniki `access=no` (oczyszczalnia) i ppoż.;
- `bialystok-dojlidy`: strumienie (way 301894169, 307734806 …, odcinki 18–356 m + przepusty), rowy, jeden zbiornik
  retencyjny `intermittent=yes`. **Stawów Dojlidzkich w kaflu nie ma** (leżą poza bbox 779019–781067 × 589055–591103).
Dlatego etap „automatycznie, gdy są dane” zmieniłby C i Dojlidy — odrzucone.

## Decyzja
1. **Opt-in per region**: `Region.water: bool = False` w `regions.py`; `build_region.py` dopisuje do `region.yaml`
   klucz `water: {enabled: true, sources: …}` i zapisuje `generated/water_sources.json` **tylko** gdy flaga jest
   ustawiona. `build_world` uruchamia etap tylko przy `water.enabled`. Bez flagi: żadna tablica nie jest dotykana,
   materiał `water`, węzeł GLB `water`, klucz manifestu `water` i źródło `generated/water_sources.json` nie powstają.
   Włączone: `dk65-02`. C i Dojlidy zostają wyłączone (decyzja o Białej w C po obejrzeniu — otwarte).
2. **Źródła** (`streetscape/water.py`, plik `generated/water_sources.json`, mały, w gicie; kafel + 60 m):
   - BDOT10k `OT_PTWP_A` (woda płynąca / stojąca) — **zarys rzeki** (obrysowany na ortofoto; na `dk65-02` lepiej
     trzyma ciemną wodę niż OSM — riverbank OSM wychodzi 3–5 m na łąkę SE od mostu; nakładka obejrzana);
   - BDOT10k `OT_SWRS_L` (osie rzek, `SZEROKOSC`: Supraśl 11 / 24 m, Biała 10 m) + OSM `waterway=river|stream|canal`
     (bez `tunnel=culvert`) — osie do poziomów i kierunku płynięcia; kanały OSM poza zarysami → bufor szerokości
     (`width` albo WORKING_VALUE 8 / 2 / 4 m);
   - OSM `natural=water` / `waterway=riverbank` / `landuse=reservoir` — stawy; zarys rzeki OSM pomijany, gdy
     nakłada się na BDOT; **`intermittent=yes` pomijane** (6 suchych zbiorników przy budowie S19 na `dk65-02`).
   - Rowy i dreny (`ditch`/`drain`, setki odcinków, na ortofoto suche/zarośnięte) — nie są ciałami wody (otwarte).
3. **Poziom wody z NMT** (GUGiK NMT nad wodą = powierzchnia wody w dniu nalotu): rzeka — stacje co 5 m na osi,
   30. percentyl NMT w zarysie w promieniu 8 m, mediana z 7 stacji, monotonicznie nierosnący w dół rzeki (oś BDOT
   odwracana, gdy poziom rośnie). Stawy — 30. percentyl NMT w zarysie. Pole poziomu na węzłach wody = IDW 6
   najbliższych stacji. `dk65-02`: Supraśl 110,64 → 110,24 m na 2,6 km, Biała 111,31 → 110,18 m na 2,1 km,
   w ujściu 110,13–110,21 m (spójne).
4. **Koryto i brzegi** (na `zc` po wpasowaniu dróg, w `streetscape.stage.run`, więc drzewa/słupy/kolizja widzą ten
   sam teren): dno = poziom − min(głęb., 0,12 + 0,35·d) (rzeka 1,2 m, strumień 0,45 m, staw 1,0 m — WORKING_VALUE);
   brzeg w pasie 10 m ≤ poziom + 0,18 + d/3 (płytki spadek 1:3); próg 2 m (`LIP_M`) ≥ poziom + 0,04, pod który
   wchodzi tafla (zakład 1 m) — brak szczeliny na linii brzegu. Węzły dróg/placów (+2 m) nietknięte; pomost mostu
   nie jest w tej masce, więc koryto biegnie pod mostem. Grubsze LOD terenu: rdzeń wody (zarys − 2 m) dołączony do
   maski min-filtra (`lod_grid`), jak przy drogach — dno nie wystaje nad taflę na LOD2/3. Drzewa: woda + 1 m
   zablokowana. Kolory gruntu: wysoka trawa (kanał B) 6 m od wody, cienka mokra linia (A 0,15).
5. **Tafla** (warstwa/węzeł `water`): zarys + 1 m − jezdnie naziemne, cięta na chunki 256 m i siatkę 4 m
   (`paved.triangulate`), wierzchołki na poziomie wody; UV0 = metry lokalne, COLOR_0 = (odl. od brzegu/8 m,
   głęb./1,5 m, kierunek płynięcia E/N; wygładzony σ 6 m, żeby w ujściu nie było szwu).
6. **Shader `Kamion/World Water`** (`Environment/Shaders/WorldWater.shader`): nieprzezroczysty (bez depth/opaque
   texture, bez SSR, bez odbić planarnych), Fresnel F0 0,02, mętna woda (oliwkowo-brązowa, linear 0,024/0,029/0,018,
   przy brzegu 0,052/0,052/0,030), widoczność nieba z bake ADR 0064 (ciemniej pod pomostem), cień słońca.
   **Low**: płaska normalna, jedno rozmyte pobranie sondy × 0,55 (przyciemniony połysk), szeroki słaby odblask.
   **High** (`_KAMION_WORLD_DETAIL`): dwie oktawy zmarszczek przesuwane wzdłuż nurtu schematem dwufazowym (offset
   ograniczony, bez ścinania przy zmianie kierunku), zanik z odległością 25–140 m, ostra sonda, glint słońca.
   Import: `RegionImporter.WaterMaterial`, `water` w `k_LowLayers`/`k_HighLayers`, w `WorldSceneBuilder` na
   wszystkich 4 LOD (bez rzucania cieni).

## Budżet (visual-qa 1920×1080, edytor, szacunek przed SRP batching)
`WORLD_MEMORY` (import r1): water 0,4 MB Low i High; razem Low 60,2 MB (0207: 59,9), High 139,3 MB (0207: 139,0).
Tafla `dk65-02`: 88 700 m², 16 704 trójkąty (cały kafel). A/B na kamerach wspólnych z ADR 0207 r2 (Low):
| kamera (Low) | draws A → B | trójkąty A → B |
|---|---|---|
| `top-bridge` | 19 → 21 | 49,3 → 51,3 tys. |
| `drive-bridge-approach` | 31 → 32 | 73,5 → 74,6 tys. |
| `rev-elcka` | 41 → 45 | 82,9 → 86,4 tys. |
| `route-s0450` (max trasy) | 196 → 201 | 220,1 → 224,7 tys. |
| `drive-s19-approach` | 119 → 123 | 153,7 → 157,3 tys. |
| pozostałe 15 kamer (route-s1651+, edge-*, top-*) | bez zmian | bez zmian |

A = `artifacts/dk65-tiles-0207/dk65-02/r2/Low-clear/stats.txt` (kod main przed scaleniem 0206, ta sama scena bez
wody), B = `artifacts/water-0210/dk65-02/r2/Low-clear/stats.txt`. Koszt wody: ≤ +5 draws (jeden materiał, jeden
draw na chunk z wodą) i ≤ +4,6 tys. trójkątów na klatkę. Kamery wodne (nowe, bez A), Low / High: `water-bank-west`
149 / 435 draws, 159 / 531 tys. tris (las przy brzegu); `water-deck-east` 87 / 322, 138 / 452 tys.;
`water-oblique-bridge` 31 / 54, 72 / 122 tys. Odniesienie docs/06 §6 (hipotezy): Samsung A ≤ 300–400 draws,
≤ 400–600 tys. tris — Low mieści się. Telefon: nie mierzono (zadanie bez telefonu).

## Walidacja
- Determinizm (stage off): `build_world` na tej gałęzi dla `bialystok-industrial-c` i `bialystok-dojlidy` —
  `world_manifest.json` (sha256 wszystkich GLB High/Low i plików instancji), `far_field_qa.json`,
  `Data/SourceManifests/<id>-far-field.manifest.json` identyczne z zacommitowanymi (po normalizacji LF;
  `artifacts/water-0210/determinism.txt`).
- `tests/gis/test_water_0210.py` 8/8 (opt-in, strażnicy w stage/build_world, poziomy w dół rzeki, staw, pominięcie
  `intermittent`, dno/brzeg/próg, drogi nietknięte, tafla bez jezdni i w granicach chunków, kolory brzegu,
  dane Supraśli/Białej na `dk65-02`).
- `build_world dk65-02` r3: 19 ciał wody (6 OSM `intermittent` i 6 zarysów OSM pokrytych przez BDOT pominiętych),
  78 239 węzłów wody, dno do 3,23 m pod NMT (krawędzie zarysu na skarpie), 39 240 węzłów brzegu obniżonych,
  354 podniesionych (próg), 75 węzłów wody przy drogach nietkniętych; tafla 82 341 m², 15 631 trójkątów.
  Ściany terenu (22, max 0,665 m) i spójność dróg (4 × `lane_blind_end`, 0 na trasie) — jak w ADR 0207 (bez zmian).
- Import: bez błędów shadera / C#; `WORLD_MEMORY` water 0,3 MB (Low i High).
- Pętla wizualna (3 rundy): `artifacts/water-0210/dk65-02/r{1,2,3}/view/` — pary `pair-{low,high}-top-bridge.jpg`
  (render | ortofoto 2024-05-27), `{low,high}-water-bank-west / -deck-east / -oblique-bridge.jpg`,
  `*-drive-bridge-approach.jpg`. r1: Low wyglądał jak asfalt (SH zamiast sondy), na High szwy zmarszczek w ujściu
  (adwekcja bez ograniczenia) → r2: dwufazowa mapa przepływu, wygładzone pole kierunku, Low = rozmyta sonda; r3:
  jaśniejsza, oliwkowa toń. Przebieg, szerokość i ujście Białej zgodne z ortofoto (para top-bridge).
- Pełny `pytest tests/gis`: 1209 passed, 3 xfailed; pominięte 2: `test_determinism::test_road_stage_independent_of_hash_seed`
  (3 × pełny build C, ~25 min) i `test_road_fidelity::test_report_not_stale` — **pada też na czystym main**
  (`fidelity_qa.json` C nieaktualny dla `build_world.py`, `markings.py`, `network.py`, `standards.py`); nie
  odświeżany tutaj (wynik C się nie zmienia — patrz determinizm), do zrobienia przez lidera po scaleniu.
- EditMode: 587 testów, 586 zaliczonych, 0 błędów, 1 pominięty (`artifacts/tests/editmode-20261115-070515.xml`). Krytyk `visual-critic`: nie uruchamiany (agent nie tworzy subagentów) — do zlecenia przez lidera.

## Otwarte
1. **Kolor toni** z góry nadal ciemniejszy i bardziej neutralny niż na ortofoto (render ~30/30/28 sRGB vs ~40/50/40);
   z bliska na Low tafla pod stromym kątem prawie czarna. Strojenie po zdjęciu właściciela z brzegu (WORKING_VALUE).
2. **Brzegi zbyt czyste**: równa linia trawy przy wodzie; na ortofoto szuwary, krzewy i olchy wzdłuż Białej —
   potrzebny pas roślinności nadbrzeżnej (trzciny jako karty / instancje) — osobne zadanie.
3. Podpory mostu kończą się na pierwotnym NMT (≈ poziom wody), dno jest niżej — pod nieprzezroczystą taflą
   niewidoczne; przy przezroczystej wodzie trzeba by przedłużyć filary.
4. Rzeka biegnie dalej przez `dk65-03` (Supraśl ~2,3 km) — włączyć `water=True` i sprawdzić ciągłość poziomu na
   szwie (koniec `dk65-02` ~110,24 m na W krawędzi). `dk65-04/05`: tylko stawy (Glinianki, ppoż.) — opcjonalnie.
5. **C (Biała 937 m) i Dojlidy (strumienie)** — świadomie wyłączone; włączenie zmieni ich wynik (nowa linia
   bazowa determinizmu, fidelity C) — decyzja lidera/właściciela.
6. Rowy/dreny (`ditch`/`drain`) bez wody i bez wcięcia; przepusty pod drogami nieodtworzone.
7. `Gate3Audit` (Editor/VisualQA, poza obszarem) nie zna węzła `water` — dopisać do listy powierzchni.
8. Telefon: brak pomiaru (koszt shadera High: 4 × NoiseGrad + sonda na piksel wody — UNVERIFIED na Mali).

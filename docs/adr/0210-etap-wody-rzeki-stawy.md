# ADR 0210 — etap wody w generatorze świata (rzeki, strumienie, stawy) + Supraśl pod mostem DK65
Status: Proposed (agent world-builder, s20, gałąź `water-0210`), 2026-11-15. Do scalenia przez lidera.
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
TODO_AB

## Walidacja
- Determinizm (stage off): `build_world` na tej gałęzi dla `bialystok-industrial-c` i `bialystok-dojlidy` —
  `world_manifest.json` (sha256 wszystkich GLB High/Low i plików instancji), `far_field_qa.json`,
  `Data/SourceManifests/<id>-far-field.manifest.json` identyczne z zacommitowanymi (po normalizacji LF;
  `artifacts/water-0210/determinism.txt`).
- `tests/gis/test_water_0210.py` 9/9 (opt-in, strażnicy w stage/build_world, poziomy w dół rzeki, staw, pominięcie
  `intermittent`, dno/brzeg/próg, drogi nietknięte, tafla bez jezdni i w granicach chunków, kolory brzegu,
  dane Supraśli/Białej na `dk65-02`).
TODO_VAL

## Otwarte
TODO_OPEN

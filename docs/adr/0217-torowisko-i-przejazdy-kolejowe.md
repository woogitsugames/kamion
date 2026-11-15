# ADR 0217 — torowisko i przejazdy kolejowe w generatorze świata (opt-in `Region.rail`)
Status: Proposed (chmura C, s20/s21, gałąź `rail-0217`), 2026-11-15; poprawki po weryfikacji
(`docs/reports/VERIFY-2026-11-15-rail-0217.md`, FIX 1-5) na gałęzi `rail-fix-s21` - sekcja „Poprawki rail-fix-s21”
na końcu, punkty niżej zaktualizowane. Do scalenia przez lidera.
Powiązane: ADR 0210 (wzorzec etapu opt-in: woda), ADR 0212 „Otwarte 4” (brak przejazdu na DW671), ADR 0205 p. 1
(generator bez torów), K1 `research/dk65-knyszyn-refs/README.md` §(g) (linia nr 38 wzdłuż DK65), docs/06 §6 (budżety).

## Kontekst
Generator (`tools/worldgen/roads/build_world.py`) nie ma torów. Agent 0212 zgłosił, że linia kolejowa przecina DW671
ok. (758830, 610030) — droga jest przejezdna, przejazdu nie ma. K1 podaje linię nr 38 (zelektryfikowana 3 kV) 111–330 m
na L od DK65 w `dk65-01`/`dk65-02`. Etap „automatycznie, gdy są dane” zmieniłby istniejące kafle (jak przy wodzie,
ADR 0210) — odrzucone.

## Decyzja
1. **Opt-in per region**: `Region.rail: bool = False` (`regions.py`). `build_region.py` dopisuje do `region.yaml`
   klucz `rail: {enabled: true, sources: …}` i zapisuje `generated/rail_sources.json` **tylko** przy fladze.
   `build_world` uruchamia etap tylko przy `rail.enabled`. Bez flagi: żadna warstwa nie dostaje części, materiały
   `rail_*`, węzły GLB `rail_*`, klucz manifestu `rail`, pliki `rail_sources.json`/`rail.json` nie powstają.
   **Ta zmiana nie włącza żadnego regionu** (lista włączeń = pusta; test). Kafle zakazane (knyszyn*,
   bialystok-knyszynska, dk65-06…11) — nietknięte.
2. **Źródła** (`streetscape/rail.py`, `extract_osm`, OSM ODbL, kafel + 100 m, mały plik w gicie):
   - drogi `railway=rail` z tagami `gauge` (domyślnie **1435 mm**, `gauge_src: default`; wartość „1435;1520” → pierwsza),
     `tracks` (domyślnie 1, max 6), `service` (siding/yard/spur/crossover — budowane jak tor pojedynczy, zapisane),
     `usage` (main/branch/industrial… — tylko zapisane), `bridge` (profil liniowy między końcami, bez podpór),
     `electrified`, `ref`, `name`;
   - **pomijane z powodem w `skipped`**: `railway=disused|abandoned|construction|proposed|razed|narrow_gauge|
     light_rail|tram|…`, `railway=rail` z `disused=yes`/`abandoned=yes`, `tunnel=yes|building_passage`;
   - węzły `railway=level_crossing` z `crossing:barrier` (no/half/double_half/full/gate/…), `crossing:light`,
     `crossing:bell`, `crossing:saltire`, `supervision`; **`railway=crossing`** (przejście dla pieszych/rowerów)
     zapisane w `skipped` — generator nie ma siatki chodników przez tor.
3. **Profil toru** (zmienione w rail-fix-s21, FIX 5): NMT pod istniejącym torem JEST powierzchnią podsypki, więc tor
   nie stoi już 0,45 m nad terenem. Główka szyny = wygładzony teren (gauss σ 15 m, WORKING_VALUE) + `TRACK_H` =
   `BED_LIFT` 0,12 + wystawanie podkładu 0,05 + szyna 0,172 = **0,342 m**; na przejeździe główka = jezdnia + 0,015 m
   (płyty), przejście liniowe na 25 m (WORKING_VALUE). W strefie płyt główki szyn biorą wysokość jezdni w swoim
   punkcie (spadek poprzeczny / daszek). **Teren jest wyrównywany pod torem** (`Plan.conform`, tylko przy fladze, wzorem
   `water.carve`): węzły siatki 1 m w pasie korona + 0,75 m dostają poziom ławy (góra podsypki − 0,12 m), dalej
   przejście do terenu na 3 m (smoothstep); węzły dróg, placów i budynków nietknięte; zgrubne LoD terenu biorą minimum
   w pasie toru (jak przy jezdni). Skarpa podsypki 1:1,5 schodzi 0,30 m poniżej góry podsypki (`SKIRT_M`), czyli
   0,18 m w grunt. Kontrola na całej długości: `rail.json` → `bed_qa` (góra podsypki − teren na krawędziach korony,
   zagłębienie stopy skarpy; `buried_crown_stations` i `open_toe_stations` muszą być 0).
4. **Przekrój** (lokalnie, pas boczny w lewo = +):
   | element | wartość | źródło |
   |---|---|---|
   | prześwit toru | 1435 mm (lub `gauge` z OSM) | OSM Key:gauge; tor normalny |
   | szyna 60E1: wysokość / główka | 172 mm / 72 mm (prostopadłościan) | katalog 60E1 (EN 13674-1): 172 mm SOURCED; 72 mm jako szerokość główki **UNVERIFIED** |
   | podkład PS-94: długość | 2,60 m | Plastwil / katalog PS94/SB/60E1 |
   | podkład: szerokość / wysokość widoczna / wystaje nad podsypkę | 0,30 / 0,20 / 0,05 m | WORKING_VALUE |
   | rozstaw podkładów | 0,60 m | WORKING_VALUE (artykuł Baztech: przytwierdzenia PS-94 co 0,6 m; Id-1 nie sprawdzona) |
   | ława podsypki za czołem podkładu / skarpa | 0,45 m / 1:1,5 | ława **ESTIMATED** z ortofoto GUGiK 2025 0,1 m (10 przekrojów 40–120 m od przejazdu: pas bez roślinności 3,5–4,5 m, średnio 3,9 m; model: korona 3,50 m + 2 × 0,12 × 1,5 = **3,86 m** widocznego pasa); skarpa WORKING_VALUE |
   | podsypka pod podkładem | 0,30 m | WORKING_VALUE, nie jest geometrią (pod torem leży NMT) |
   | rozstaw osi torów (tracks ≥ 2) | 4,00 m | WORKING_VALUE (typowe minimum na szlaku, paragraf **UNVERIFIED**) |
5. **LoD** (warstwy/węzły GLB): `rail_lod0` — podsypka (korona: jeden pas na tor + 2 skarpy) + podkłady (góra + 2 boki)
   + szyny (góra + 2 boki), stacje co 5 m; `rail_lod1` — podsypka + szyny co 10 m; `rail_lod2` — płaski pas (jeden na
   tor) co 20 m, szerokości widocznego pasa. GLB High: LoD0–2; GLB Low: LoD1–2 (`LOW_EXCLUDE`). Pod płytami przejazdu
   podsypki i podkładów nie ma.
   **Jeden materiał `rail_bed` z kaflem `rail_bed.png`** (rail-fix-s21, FIX 3; `streetscape/rail_textures.py`,
   proceduralny, 512 × 256 px = 5,12 m w poprzek × 2,40 m wzdłuż = 4 podkłady): tłuczeń (komórki Voronoi ~4,5 cm,
   brunatny przy szynach, szarzejący na ławach), podkłady betonowe 2,60 × 0,30 m z przytwierdzeniami, stopka i
   wypolerowana główka szyny. UV0 = (0,5 + odległość od osi SWOJEGO toru / 5,12 m, odległość wzdłuż / 2,40 m) dla
   podsypki wszystkich LoD, podkładów LoD0 (leżą dokładnie na malowanych) i szyn (próbkują malowaną szynę: główka
   na górze, rdza na bokach). Dzięki temu na Low (LoD1: wstęga + szyny, LoD2: wstęga) tor ma czytelne podkłady i
   szyny, przełączenie LoD0 → LoD1 nie zmienia obrazu, a cały tor to 1 materiał (1 draw na chunk i LoD). Kafel
   zapisuje tylko etap rail (`Plan.export_textures`, obok `water_reeds.png`); kolory w PNG (sRGB), `color` = 1.
6. **Przejazd w poziomie jezdni**: z węzłów `railway=level_crossing` (≤ 8 m od osi toru) + przecięcia osi toru z osiami
   jezdni naziemnych (bez odcinków mostowych; duplikat ≤ 10 m od węzła OSM odrzucany; bez węzła OSM → ostrzeżenie,
   rogatki nieznane, oznakowanie jak kat. D). Strefa płyt = oś toru ∩ (obrys jezdni + 0,5 m). **Płyty** (materiał
   `rail_crossing_panel`, betonowo-gumowe, bez marki): na szerokość podkładu (±1,30 m od osi skrajnego toru),
   siatka co 0,5 m wzdłuż toru (s22; przy 2 m korona jezdni przebijała przez płyty), przerwa 0,07 m + główka przy
   każdej szynie (żłobek), wysokość = najwyższa z 5 próbek jezdni w promieniu 0,25 m + 0,015 m (`_deck_z`,
   `PANEL_LIFT` WORKING_VALUE: próbnik to siatka `road_z` 1 m, która ścina grzbiet korony o ok. 0,01 m).
   Wysunięcie płyt poza obrys jezdni można podać w nadpisaniu przejazdu (`panel_margin_m`).
   **Nadpisanie przejazdu** (rail-fix-s21, FIX 4): `overrides.yaml`, `kind: rail_crossing`, `target: {osm_node: id}`
   albo `{near_epsg2180: [x, y], radius_m}`, `set: {barrier, light, light_left, bell, saltire, panel_margin_m}` —
   fakty odczytane z ortofoto / zdjęć wygrywają z OSM, przeżywają każdą regenerację i są nazwane w `rail.json`
   (`crossings[].override`); nieznany klucz = błąd, nadpisanie bez przejazdu = ostrzeżenie.
7. **Markery** (`generated/rail.json` → `markers`; pozycja E/N/Z lokalnie, `heading_deg` = azymut, w który patrzy
   lico/ramię, zgodnie z ruchem wskazówek od N = obrót Y w Unity), po jednym na wlot:
   - `sign` **G-3** (1 tor) / **G-4** (≥ 2 tory, suma `tracks` wszystkich dróg kolejowych przy przejeździe) — tylko
     gdy brak rogatek (`crossing:barrier` brak/`no`), zgodnie z § 80 ust. 1 Dz.U. 2025 poz. 1105 (G-3/G-4 przed przejazdami
     kat. A bez rogatek, C i D; źródło: `https://api.sejm.gov.pl/eli/acts/DU/2025/1105/text.pdf`, pobrane 2026-11-15,
     SHA256 `c3caeb070b48af809707db4d3c77cb2b3aa00bebd27d55d3fbfc8cb6857dd924`; Dz.U. 2015 poz. 1744 ma w ELI status
     „uznany za uchylony” z dniem 2025-08-27 przez DU/2025/1105); jawny `crossing:saltire` ma pierwszeństwo. Słupek po prawej stronie wlotu,
     3,0 m przed krawędzią płyt, 1,0 m za krawędzią jezdni (WORKING_VALUE). Ramię 1,20 × 0,20 m, kąt 50°, dolna
     krawędź 1,50 m — **WORKING_VALUE** (rysunku G-3 z rozporządzenia o znakach nie sprawdzono);
   - `barrier`: `half` → 1 ramię na wlot (wjazd, prawy pas, długość ½ jezdni + 0,5 m), `double_half` → 4 (wjazd +
     druga półrogatka po tej samej stronie toru na lewym poboczu, ramiona naprzeciw siebie — s22: wcześniej leżała
     na rogatce wjazdowej drugiego wlotu, 4 markery dawały 2 widoczne ramiona), `full`/`gate` → 1 na wlot przez całą jezdnię; słupek 2,0 m przed płytami (WORKING_VALUE);
   - `light` (`crossing:light=yes`) na słupku znaku każdego wlotu (+ powtarzacz po lewej, gdy nadpisanie podaje
     `light_left`); `bell` — jeden przy przejeździe.
   **Obiekty w scenie** (rail-fix-s21, FIX 4; `streetscape/rail_props.py`): markery stają się zwykłymi instancjami
   biblioteki `street_props.glb` regionu (ten sam import, LOD i kolizja co znaki i sygnalizatory — bez zmian w C#):
   `signal_rail_saltire_g3` / `signal_rail_saltire_g4` (białe ramiona z czerwoną obwódką na słupku Ø60; G-4 = krzyż + półkrzyż
   niżej), `signal_rail_barrier_<dm>` (pomarańczowa szafa napędu + ramię w biało-czerwone pasy 0,5 m, podniesione 86° —
   przejazd otwarty, ruchu pociągów nie symulujemy; kolizja tylko szafy), `signal_rail_lamps` / `signal_rail_lamps_bell` (maszt
   3,0 m, dwie czerwone komory obok siebie na okrągłych czarnych tarczach, zgaszone). Prototypy rejestruje tylko etap
   rail (`rail_props.PROTOS`, wzorem `gate3_landmarks.PROTOS`); używają wyłącznie istniejących materiałów. Wymiary
   WORKING_VALUE ze zdjęć Mapillary; rysunki G-3 / G-4 z rozporządzenia nie sprawdzone (UNVERIFIED).
8. **Skrajnia**: uproszczony przekrój (szer. 4,40 m od 0,4 do 4,0 m nad główką, zwężenie do ±1,60 m na 6,0 m) —
   **UNVERIFIED** (do zastąpienia obrysem z PN-K-02057 / Id-1). Zapisana w `rail.json` (`clearance`), używana do QA
   (`min_marker_distance_m` > 2,20 m — test) oraz jako obrys: `Plan.footprint()` = oś ± max(korona + 1 m, skrajnia)
   blokuje drzewa (hook w `streetscape/stage.py`).

## Budżet trójkątów
Wzór (tor bez przejazdów, n torów pod jedną podsypką, Δs = krok stacji LoD, a = 0,60 m rozstaw podkładów):
- LoD0 = (1000/5)·(4 + 2n + 6·2n) + (1000/a)·6n → **13 600 / km** (n = 1), 26 400 / km (n = 2)
- LoD1 = (1000/10)·(4 + 2n + 6·2n) → **1 800 / km** (n = 1), 3 200 / km (n = 2)
- LoD2 = (1000/20)·2n → **100 / km** (n = 1), 200 / km (n = 2)
  (rail-fix-s21: korona ma jeden pas na tor, żeby każdy tor miał swoje malowane podkłady; dla n = 1 bez zmian)
- przejazd: ⌈(B/sinθ + 2·m)/0,5⌉·(2n + 1)·2, B = szer. jezdni, m = margines płyt (0,5 m) → 7 m, 90°, 1 tor: **96**;
  2 tory: 160; DW671 × linia 38 (7,4 m, m = 1,5 m, strefa 10,66 m): **132** (`rail.json`).
  Szyny w strefie płyt dochodzą (≈ 6 stacji × 6 tris × 2n).
Zmierzone na syntetycznym kaflu (test): 1 km, 1 tor bez przejazdu — LoD0 13 602 (200·18 + 1667·6), LoD1 1 800,
LoD2 100 = wzór (LoD0 ±6 przez liczbę podkładów).

Porównanie z docs/06 §6 (hipoteza Samsung A: ≤ 400–600 tys. tris, ≤ 300–400 draws w kadrze): przy przełączaniu
LoD per chunk 256 m (jak teren) najgorszy kadr wzdłuż toru = 2 chunki LoD0 (512 m) + 2 chunki LoD1 + reszta LoD2:
1 tor ≈ 0,512·13 600 + 0,512·1 800 + 1,5·100 ≈ **8,0 tys.** tris (≤ 2 % dolnej granicy budżetu), 2 tory ≈ 15 tys.
W GLB Low LoD0 nie ma (sam LoD1: 0,512·1 800 ≈ 0,9 tys. na chunk). Draws (rail-fix-s21: jeden materiał `rail_bed`):
≤ 2 na chunk z torem i przejazdem w każdym LoD (tor, płyty). Telefon: nie mierzono.

## Walidacja
- `tests/gis/test_rail_0217.py` (syntetyczne OSM, bez Data/raw): opt-in (żaden region nie włączony, brak kluczy/plików
  w `region.yaml` i `world_manifest.json` wszystkich regionów), strażnicy w build_world/stage/build_region, puste
  warstwy nie zmieniają `assemble`, klasyfikacja tagów (gauge/tracks/service/disused/tunnel, level_crossing vs
  crossing), trójkąty per LoD = wzór (1 i 2 tory), prześwit 1435 mm, trapez 1:1,5, orientacja ścian, płyty na
  wysokości jezdni (ze spadkiem 2 %), szyny zlicowane, brak podsypki pod płytami, G-3 vs G-4 (tracks=2 oraz dwie
  drogi kolejowe), rogatki no/brak/half/double_half/full (0/0/2/4/2 ramion, długości), światła/dzwon, pominięcie
  `railway=abandoned`, footprint blokuje roślinność, próbnik `road_z` poza jezdnią.
- Determinizm: kod etapu jest wyłącznie za `RL.enabled(...)` / `w.rail is not None`; nowe pozycje w `LAYERS`/`NODES`
  dla regionów bez toru są puste, więc GLB i manifest bez zmian. Sprawdzone pełnym `build_world` tykocina z flagą
  wyłączoną (s21): `derived/` 240/240 plików o identycznym SHA256 względem kodu main
  (`artifacts/rail-fix-s21/flagoff/`).
- `test_road_fidelity::test_report_not_stale` pada, bo `fidelity_qa.json` C hashuje `build_world.py` (zmieniony
  tutaj); wynik C się nie zmienia, ale raport trzeba odświeżyć z Data/raw:
  `uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region bialystok-industrial-c`.
- Ocena wizualna: nie wykonana (brak Unity/GPU) — do lidera.

## Integracja z Unity (lider)
Eksport idzie przez istniejące GLB chunków (glTFast), więc w `game/` potrzeba:
1. `RegionImporter.k_HighLayers` += `rail_lod0`, `rail_lod1`, `rail_lod2`, `rail_crossing`; `k_LowLayers` += `rail_lod1`,
   `rail_lod2`, `rail_crossing` (materiały `rail_*` z manifestu idą zwykłą ścieżką: `rail_bed` z kluczem `texture` =
   URP Lit z kaflem z `textures/rail_bed.png` regionu — bez osobnego shadera). **Zrobione** (`fix-pr95-96-s21`, scalone
   do `rail-fix-s21`).
2. `WorldSceneBuilder` listy LOD (l. 284–294): LOD0 High `rail_lod0` / Low `rail_lod1` + `rail_crossing`; LOD1 `rail_lod1`
   + `rail_crossing`; LOD2 `rail_lod2` + `rail_crossing`; LOD3 `rail_lod2`. Bez rzucania cieni dla LoD2.
3. Markery `generated/rail.json` → obiekty: **zrobione w generatorze** (`rail_props.py`, instancje biblioteki
   rekwizytów, patrz p. 7). `rail.json` zostaje dla przyszłej logiki (opuszczanie ramion, światła, dzwonek).
4. `Gate3Audit` / `mesh_budget` (streetscape_qa) nie liczą `rail_*` — dopisać.

## Odtworzenie (lider, po włączeniu `rail=True` w wybranym regionie)
```
uv run --project tools/worldgen tools/worldgen/build_region.py --region dw671-tykocin-01
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region dw671-tykocin-01
uv run --project tools/worldgen python scripts/export-route.py --region dw671-tykocin-01
pwsh scripts/import-region.ps1 -Region dw671-tykocin-01 -Build
pwsh scripts/visual-qa.ps1 -Scene World_dw671-tykocin-01 -Tier Low -Lighting clear -OutputDir artifacts/rail-0217/vqa/dw671-tykocin-01/Low
pwsh scripts/visual-qa.ps1 -Scene World_dw671-tykocin-01 -Tier High -Lighting clear -OutputDir artifacts/rail-0217/vqa/dw671-tykocin-01/High
# scena = World_<region> (WorldC to wyłącznie bialystok-industrial-c); kamery przejazdu: -Cameras rail_xing_top,rail_xing_above,...
uv run --project tools/worldgen python -m pytest -q tests/gis/test_rail_0217.py   # po włączeniu: zaktualizować listę `on`
```
Determinizm C/Dojlidy (bez flagi): `build_world` dla `bialystok-industrial-c` i `bialystok-dojlidy` →
`git diff --stat origin/main -- Data/Regions/*/generated` = tylko `dw671-tykocin-01` (region z włączonym torem).

## Wyniki s22 (dw671-tykocin-01, `rail.enabled`, po scaleniu main @b4e42ef34, regeneracja r6)
- **Generator** (`generated/rail.json`): 1 tor, `bed_qa` 543 stacje co 2 m — `buried_crown_stations` 0,
  `open_toe_stations` 0, krawędź korony 0,114–0,121 m nad terenem, stopa skarpy 0,171–0,200 m w terenie; pas widoczny
  3,86 m (orto 3,5–4,5 m, ESTIMATED); 4 rogatki w 4 różnych miejscach + 4 sygnalizatory, `warnings` puste, najmniejsza
  odległość urządzenia od skrajni 2,16 m. Trójkąty: LoD0 15 084, LoD1 2 256, LoD2 112, płyty 132.
- **Budżet A/B** (`streetscape_qa.json` → `mesh_budget.frame_estimate`; „przed” = `build_world` z flagą wyłączoną,
  `artifacts/rail-fix-s21/flagoff/after-fix/generated/`, „po” = r6): najcięższy kadr High 1 053 777 → 1 053 777
  (`route_s0489`), Low 308 051 → 308 051 (`dw671_seam_north_out`) — kamery trasy bez zmian co do trójkąta;
  `rail_xing_above` 993 279 → 994 608 (+1 329 `props` = urządzenia przejazdu). Estymata kadru **nie liczy siatek
  toru** (brak kategorii) — dochodzi najwyżej cały tor regionu: +15 216 High (LoD0 + płyty), +2 388 Low (LoD1 +
  płyty). Kamery `rail_*`: High ≤ 994 608, Low ≤ 305 221 (bez siatek toru). Zacommitowany na main
  `streetscape_qa.json` tykocina jest nieświeży względem kodu (1 068 212 High) — różnica main → gałąź to drzewa
  (`trees_lod0/1`) i nie pochodzi od toru. Draws: nie mierzono. Telefon: nie mierzono.
- **Pętla wizualna** (scena `World_dw671-tykocin-01`, Low + High, clear, 14 kamer; `artifacts/rail-fix-s21/vqa/r1…r6`,
  referencje `artifacts/rail-fix-s21/ref/ortho_0p10_crossing_60m.jpg` i `ref/mapillary/crop_*.jpg`):
  - r1: rogatki `double_half` — 4 markery w 2 miejscach (wyjazdowa leżała na wjazdowej drugiego wlotu) → poprawione,
    r2 pokazuje 4 ramiona w 4 ćwiartkach jak na orto i Mapillary 1832769196903759;
  - r1: pasmo toru / asfalt (luminancja liniowa, `rail_xing_top`, `artifacts/rail-fix-s21/measure_render.py`)
    0,94 High / 0,98 Low; orto 0,44 (`measure_ortho_rel.py`). r2–r6: **0,81 / 0,83**, tor / trawa 0,52 / 0,55
    (orto 0,66), R : G : B 1,06 : 1 : 0,91 (orto 1,09 : 1 : 0,87). Kotwice są sprzeczne: asfalt gry / trawa = 0,65,
    na orto 1,48 (stara, jasna nawierzchnia DW671), więc 0,44 dałoby prawie czarny tłuczeń. Zostawione jako
    WORKING_VALUE do zdjęcia właściciela;
  - r1: boki szyn srebrne (bok pudełka próbkował główkę) → rdza na bokach, główka tylko na górze;
  - r2–r4: korona jezdni przebijała przez płyty (siatka 2 m, potem próbnik 1 m ścinający grzbiet) → siatka 0,5 m,
    `_deck_z`, `PANEL_LIFT` 0,015 m; r5 i r6: płyty ciągłe na całej szerokości jezdni w Low i High.
  - teren pod torem bez szczelin i bez „wiszącej” podsypki (`rail_bed_close`, `rail_track_along`).
  Ocena `visual-critic`: **nie wykonana** (agent nie tworzy subagentów) — dla lidera.
- **Albedo**: `docs/06` nie podaje progu liczbowego (tylko „tabela referencyjna” i „histogram albedo w walidatorze”);
  kafel `rail_bed.png` ma średnią sRGB (61, 57, 50), najciemniejsze są spoiny między kamieniami — WORKING_VALUE.
- **`region.yaml`**: względem main zmienia się tylko blok `rail`. Dwa `manifest_sha256` (NMT, orto) zmienione przez
  wcześniejszy `build_region` były artefaktem checkoutu CRLF manifestów w worktree (hash treści LF = wartość z main) —
  przywrócone; `build_manifest.json` przeliczony.

## Otwarte
1. **Włączenie**: proponowane `dw671-tykocin-01` (przejazd DW671 z 0212; kafel spoza listy zakazanej), potem `dk65-01`
   i `dk65-02` (linia 38, K1; w `dk65-02` most kolejowy nad Supraślą = `bridge=yes` bez podpór). Zmienia wynik tych
   kafli (nowa linia bazowa) — decyzja lidera.
2. Wymiary G-3/G-4 i odległości ustawienia, skrajnia, podsypka/rozstaw wg Id-1 — do sprawdzenia w tekstach źródłowych
   (WORKING_VALUE/UNVERIFIED wyżej).
3. Teren pod torem nie jest profilowany (nasyp/przekop); na stromym terenie podsypka może wisieć > 0,3 m — QA po
   pierwszym kaflu (`rail.json` + render).
4. Brak: słupków G-1a…f przed przejazdem, znaków A-9/A-10, linii P-12 przed rogatkami, sieci trakcyjnej (3 kV),
   rozjazdów, peronów, mostów kolejowych z podporami, przejść dla pieszych `railway=crossing`.
5. Bardzo skośne przejazdy: sinθ obcięty do 0,2 (≈ 11,5°) przy liczeniu szerokości jezdni.
6. Przejazd DW671 × linia 38 wobec orto GUGiK 2025 — brak w grze: linii P-12 i linii ciągłej P-4 przed przejazdem,
   czerwonych pasów akustycznych, barier energochłonnych przy torze, słupów sieci trakcyjnej, biało-czerwonych
   słupków sygnalizatorów (są szare); jezdnia ma krawężniki, na orto pobocze gruntowe (poza zakresem toru).
7. Barwa podsypki: tor / asfalt 0,81–0,83 zamiast 0,44 z orto (patrz „Wyniki s22”) — zdjęcie właściciela rozstrzygnie.
8. `PANEL_LIFT` 0,015 m to obejście siatki `road_z` 1 m; docelowo próbnik z siatki jezdni (trójkąty), wtedy 0,005 m.

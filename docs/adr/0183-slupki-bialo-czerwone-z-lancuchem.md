# 0183 — Słupki biało-czerwone z łańcuchem (prototyp mebla ulicznego + override `chain_bollards`)

Status: kandydat (gałąź `bollards-0183`), nie scalone. Data: 2026-11-13.

## Problem
Agent 0179 (Dojlidy) znalazł na zdjęciu P11-063 (Wikimedia Commons, CC0, Rakoon; w rejestrze `refs-commons` w `docs/LICENSES.md`) (ul. Mickiewicza przy Kuronia) rząd biało-czerwonych
słupków blokujących połączonych dwoma łańcuchami. Biblioteka mebli (`street_props.glb`) ma tylko szary `bollard`
Ø0,12 m i żółte U-12a / U-5a; OSM i BDOT10k nie opisują takich rzędów (`barrier=bollard` najbliżej 87 m — audyt
Mistral p9, M50-056), więc reguła generatora nie ma z czego ich postawić.

## Decyzja
1. **Nowy moduł** `tools/worldgen/streetscape/chain_bollards.py` (bez zmian w `plot_kit.py` i `furniture.py`).
   Wpięcia jednowierszowe: `props.build_all` (prototypy), `export.textures` (atlas), `stage.py` (po `lamp_rows`,
   czyli po przejściach czyszczących jezdnię — rząd jest autorski), `materials.py` (blok addytywny na końcu).
2. **Dwa prototypy, jeden materiał** `chain_bollard` (jeden atlas alfa 256 × 512 px, kolory w teksturze):
   - `bollard_rw_chain` — słupek w początku układu + oba łańcuchy jednego przęsła wzdłuż lokalnego +x (słupek
     końcowy przęsła to następna instancja);
   - `bollard_rw` — sam słupek (zamyka rząd; rzędy `chain: false`).
   LOD0: słupek 10-kątny z kopułką, 4 ucha, każdy łańcuch jako dwie skrzyżowane karty alfa z teksturą ogniw
   (ogniwa na płask / bokiem na przemian, druga karta przesunięta o jedno ogniwo). LOD1: słupek 5-kątny, każdy
   łańcuch = jedna nieprzezroczysta taśma 12 mm (bez alfa-testu ogniw, żeby łańcuch nie znikał w mipmapach).
   Kolizja: jedno niskie pudło na przęsło.
   **Rdzeń łańcucha (r3b).** W LOD0 pod każdą kartą ogniw jest nieprzezroczysta wstęga o szerokości drutu (8 mm), 2 mm
   obok płaszczyzny karty (bez z-fightingu), UV = lita łata taśm LOD1. Sama karta pokrywa ~46 % szerokości (ogniwa
   puste w środku) i w kadrze dopasowanym do P11-063 (13 m) dolny łańcuch znikał na jasnym bruku. +2 tris na segment.
   **Układ atlasu (r2).** Render r1 pokazał czerwone ogniwa blado-różowe w Unity (w Blenderze czerwone). Przyczyna:
   import świata to ASTC 6×6 + trilinear (`InstanceImporter.ImportTexture`), a granica czerwone|białe ogniwa leżała na
   u = 160 px — w środku bloku 6×6 (160/6 niecałkowite) i tuż przy krawędzi karty, więc koder bloków i próbki
   bilinearne mipów ≥ 2 mieszały biel z czerwienią. r2: każda granica kolorów na wielokrotności 24 px (całe bloki
   4/6/8/12), kolumna ogniw 32 px ma po bokach 8 px przezroczystego marginesu w kolorze własnej farby (1 teksel mipa 3),
   czerwony i biały slot stykają się na u = 192 px (krawędź teksela każdego mipa do 64 px), a taśmy LOD1 mają stały
   UV w litej łacie 24 × 48 px (zero śladu filtra przez granicę). Układ (px): słupek 0–120, stal 120–144 (wiersze 0–48
   łata czerwona, 48–96 biała), ogniwa czerwone 144–192, białe 192–240, 240–256 rezerwa (biel, α 0). Zużycie farby
   na koronach ogniw 0,6 → 0,4 (na zdjęciu łańcuch czyta się jako ciemnoczerwony). Test
   `test_atlas_r2_no_red_white_bleed` pilnuje wyrównania i koloru kolumny czerwonej w mipach 0–4. Polityka LOD/cull = domyślna małych mebli (`InstanceImporter.Policy`:
   30 / 120 m × lodBias) — bez zmian w C#.
3. **Wymiary** (stałe w module, każda z opisem źródła):
   | wielkość | wartość | źródło |
   |---|---|---|
   | wysokość słupka | 0,80 m | U-12c 0,6–0,8 m, biało-czerwone: `research/mistral/p9-furniture-3/manifest.csv` wiersz M50-043 (cytuje Dz.U. 2019 poz. 2311, zał. 4, s. 847; aktu nie czytałem ponownie). P11-063 pasuje do górnej granicy (słupek 75 px przy f ≈ 1230 px → 13,1 m; krawężnik na ortofoto 13,5–15 m od pozycji zdjęcia). 0,90 m pasuje równie dobrze — WORKING_VALUE |
   | średnica | Ø60,3 mm | WORKING_VALUE: rura słupków U-12a ze standardu ZDM (G5-010); na zdjęciu 5–7 % wysokości |
   | przęsło | 1,60 m | WORKING_VALUE = 2,0 × wysokość; P11-063: 3 przęsła = 5,9 wysokości słupka (niezależnie od ogniskowej ±10 %) |
   | pasy od ziemi | biały 22 %, czerwony 21 %, biały 25 %, czerwony 21 %, biały 11 % | P11-063 (kadr 4×: 60/60/70/60/30 px z 280) |
   | ucha łańcuchów | 0,94 i 0,46 wysokości | P11-063, WORKING_VALUE |
   | zwis łańcucha | 0,18 i 0,16 wysokości (krzywa łańcuchowa) | P11-063 (50 i 45 px z 280), WORKING_VALUE |
   | łańcuch (r3) | tworzywo, drut 8 mm, podziałka 42 mm, szer. 30 mm; taśma LOD1 22 mm | szerokość pozorna z P11-063: 2–3 px przy ~13 m, f ≈ 1230 px (ASSUMED) → 0,021–0,032 m; materiał i ogniwa UNVERIFIED (r1/r2: stal 6 mm, 24 mm — w r2 łańcuchy znikały od ~10 m, na zdjęciu czytają się jak liny) |
   | malowanie łańcucha | odcinki czerwone i białe ~pół przęsła, niezgrane ze słupkami | P11-063, jeden stały wzór na przęsło — WORKING_VALUE |
4. **Override** `kind: chain_bollards` w `Data/Regions/<id>/overrides.yaml` (przeżywa każdą regenerację):
   `line_epsg2180: [[x, y], ...]` albo `lines: [{line_epsg2180: [...]}, ...]`, opcjonalnie `chain: false`.
   Rząd idzie od pierwszego punktu, słupki dokładnie co 1,60 m (cięciwa) na zadanej linii, także po łuku; ostatni
   słupek może wyjść poza koniec linii o < 0,80 m (siatka przęsła ma jedną długość, instancje skalują tylko oś
   pionową). Przerwa (przejście) = dwa rzędy. Błędny wpis trafia do `stale` w raporcie, nie znika po cichu.
   Raport `streetscape_qa.json → furniture.chain_bollards`: słupki, przęsła, długość, `end_shift_m`, `max_step_m`.
5. **Osadzanie**: prefiks `bollard` → `Placer.seat` jak każdy słupek. Przęsło jest poziome (instancja ma tylko
   obrót wokół pionu), więc na spadku łańcuch trafia w następny słupek o `max_step_m` wyżej/niżej niż ucho —
   raportowane; rzędy stoją na chodnikach (spadki ≤ kilka %), przy > 0,10 m rząd trzeba podzielić.

## Odrzucone
- Jeden prototyp „przęsło z dwoma słupkami” lub odwrócone przęsło jako zakończenie (0 dodatkowych draw): daje
  pokrywającą się geometrię alfa (migotanie) i zdublowane słupki o różnych wysokościach na spadku.
- Łańcuch wypalony w siatce chunku (`Lin`, jak ogrodzenia): brak LOD i instancjonowania, nowy materiał w każdym
  chunku z rzędem.
- Ogniwa jako geometria: ~70 ogniw × 2 łańcuchy na przęsło — poza budżetem dla mebla widzianego z kabiny.

## Integracja (blok dla Dojlid — wkleja lider; plików regionu ta gałąź NIE zmienia)
Na `main` istnieje już `Data/Regions/bialystok-dojlidy/overrides.yaml` (ADR 0179), na tej gałęzi go nie ma — commit
całego pliku dałby konflikt, a `generated/*` Dojlid są poza zakresem. Lider dopisuje poniższy wpis na koniec listy
`overrides:` w pliku z `main` (wcięcie 2 spacje), potem regeneracja Dojlid (`build_world.py --region bialystok-dojlidy`
→ `import-region.ps1`). Ten sam wpis: `artifacts/bollards-0183/overrides.dojlidy.chain_bollards.yaml`.
```yaml
  - id: mickiewicza-kuronia-chain-posts-p11-063
    kind: chain_bollards
    line_epsg2180: [[780014.43, 590462.87], [780019.44, 590452.85]]
    chain: true
    sources: ["research/_incoming/mistral-p11-dojlidy-photos-v2/files/P11-063.jpg", "GUGiK orthophoto 2024 0.25 m"]
    reason: >-
      Photo P11-063 (Wikimedia Commons, CC0, Rakoon, 2024-06-23, File:20240623_124644_June_2024_in_Białystok.jpg; from the bus-stop island of ul. Mickiewicza, looking east): 8 red-white posts with two
      chains on the paving behind the east kerb of the NW-bound carriageway (osm way 691820489 / 258564444), up to
      the crossing at the Kuronia corner; 8 posts = 7 bays x 1.60 m. On the orthophoto the row stands on paving at
      [780011.30, 590461.30] -> [780016.31, 590451.28]; the generated world has a grass verge there, so the line is
      moved 3.5 m away from the carriageway onto the generated sidewalk_paving (ADR 0183 r2). Move it back when the
      Dojlidy paving matches the photo.
    confidence: low
    verify: start / end post on site (+-2 m along the kerb); the further row visible behind (smaller posts) is not placed
```
Podstawa położenia: zdjęcie z wysepki przystankowej ul. Mickiewicza w stronę wschodnią; linia krawężnika z ortofoto
GUGiK 2024 (0,25 m): lokalnie E = −33,5 − 0,5 (N − 385). Początek: 21° w lewo od białej szafki przy (−15,5; 371,0)
widzianej z (−46,5; 381,8) — szafka stoi na zdjęciu za słupkami 5–6. Pozycja kamery `photo_P11-063` (ADR 0174) ma błąd
kilku metrów (szafka wypada 13° zamiast 27° od osi kadru), stąd `confidence: low`.
**Przesunięcie r2 (+3,5 m, normalna (0,894; 0,447)):** na zdjęciu słupki stoją na płytach chodnikowych (pas kostki
granitowej przy krawężniku), na ortofoto pierwotna linia też leży na nawierzchni utwardzonej, ale w wygenerowanym
świecie jest tam trawnik (krawężnik → ~4 m trawy → `sidewalk_paving`; sonda trójkątów chunku 3_2). Na trawie (r1)
trawa Fab High zakrywała stopy słupków i dolny łańcuch. Linia przesunięta stoi ~1 m w głąb wygenerowanego chodnika i
nadal na nawierzchni utwardzonej według ortofoto. Rozbieżność chodnik/trawnik — do 0179.

## Budżet
Prototypy (z kodu, `CB.prototypes()`): `bollard_rw_chain` LOD0 174 tris (r1/r2: 142; +32 = rdzeń r3b), LOD1 31;
`bollard_rw` 78 / 15. Jeden materiał `chain_bollard`, atlas 256 × 512 RGBA (ASTC 6×6 na Androidzie ≈ 79 KB z mipami).
Rząd Dojlid: 8 instancji (7 × bay + 1 × post) → 1 draw instancjonowany na prototyp i LOD.
A/B zmierzone w Unity (statystyki visual-qa, `renders/ab-off-*/stats.txt` vs `renders/r2-*/stats.txt`; ab-off i r2
z tego samego kodu poza rzędem; r3/r3b zmieniają tylko trójkąty łańcucha):

| kamera | tier | draws inst. bez → z | instancje | tris inst. bez → z |
|---|---|---|---|---|
| bollards-close-5m | Low | 141 → 143 | 372 → 380 | 33 634 → 34 706 |
| bollards-cab-20m | Low | 116 → 118 | 338 → 346 | 20 986 → 21 218 |
| bollards-along-8m | Low | 147 → 150 | 126 → 134 | 41 277 → 42 064 |
| photo-P11-063 | Low | 115 → 117 | 343 → 351 | 21 471 → 21 703 |
| bollards-close-5m | High | 241 → 243 | 820 → 828 | 165 579 → 166 651 |
| bollards-cab-20m | High | 200 → 202 | 823 → 831 | 138 253 → 139 325 |
| bollards-along-8m | High | 286 → 288 | 430 → 436 | 115 376 → 116 424 |
| photo-P11-063 | High | 195 → 197 | 826 → 834 | 138 212 → 139 284 |

Nieinstancjonowane `drawsEst` / `trisExact` chunków identyczne w A i B (siatki chunków bez zmian). Koszt rzędu:
+2–3 draw, +8 instancji, +0,2–1,1 k tris; r3b dodaje ≤ 7 × 32 = 224 tris na rząd w LOD0. Telefon: nie mierzone
(bez adb w tym zadaniu) — budżet `docs/06` §6 do potwierdzenia na A16 przy bramce.

## Dowody
Dowody (kopia w main `artifacts/bollards-0183/`): rendery `renders/{r1,r2,r3,r3photo,r3b,ab-off}-{low,high}/`
(Unity, overcast, 1920 × 1080; `stats.txt` na kamerę), zestawienia `compare/`:
- `r1-vs-r2-*.jpg` — r1 (trawnik, różowe ogniwa) vs r2 (bruk, atlas r2): czerwień ogniw czerwono-brązowa zamiast
  blado-różowej (ocena wzrokowa, detal 2 m Low/High).
- `r2-photo-P11-063-side-by-side.jpg`, `r2-photo-P11-063-row-crops.jpg` — kamera ADR 0174 `photo_P11-063` stoi ~2–2,5×
  za daleko (słupki ~30 px zamiast 60–75 px w 1600 px), łańcuchów nie da się tam ocenić → dodana kamera
  `bollards-photo-13m` (`tools/photo_cam.py`: słupek 1 w 13,05 m, słupek 8 w 19,05 m, oko 1,5 m, hfov 66°).
- `r3b-photo-13m-vs-P11-063.jpg` — zdjęcie / r3 Low / r3 High / r3b Low / r3b High w tym samym kadrze. r3b: górny
  łańcuch czyta się jako ciągła lina jak na zdjęciu; dolny czerwony na jasnym bruku nadal słabszy niż na zdjęciu
  (na zdjęciu łańcuchy są ciemne w cieniu; tu pochmurne, płaskie światło) — otwarte.
- Rozstaw: `streetscape_qa.json → furniture.chain_bollards`: 8 słupków, 7 przęseł, 11,20 m, `end_shift_m` 0,
  `max_step_m` 0,025.
Testy: `tests/gis/test_chain_bollards_0183.py` 19/19 (w tym `test_atlas_r2_no_red_white_bleed`, budżet trójkątów
≤ 180 / ≤ 40). Pełne `pytest tests/gis` (kod r2/r3, 2026-11-13): 1084 pass, 2 xfail, 3 fail — wszystkie w
bialystok-industrial-c (`test_road_fidelity::test_report_not_stale` — fidelity_qa.json starszy niż overrides.yaml /
build_world.py, których ta gałąź nie zmienia; `test_world_roads::test_export_is_deterministic`,
`test_world_v31::test_forest_trees_reference_their_cell` — dane industrial-c na wspólnym junction `Data/raw`, w tym
czasie trzy inne worktree przebudowywały industrial-c). Diff gałęzi dotyka tylko `streetscape/{chain_bollards,props,
stage,materials,export}.py` i testu 0183. EditMode (Unity 6000.3.28f1, 2× w s20): 535, 511 pass, 13 skip, 6 fail —
`TruckDoorCrownTests` ×3 („Build canonical truck before fixture tests”), `MirrorPresentationTests` ×2 („build TRAKT
before testing”), `LightPostPolicyTests.ImportedGlassSemanticIsRestrictedAndStillReceivesShadows` (importer szkła
ciężarówki) — fixture ciężarówki niezbudowanej w tym worktree, niezwiązane z 0183.
Po `git merge origin/main` (8b2f3a3ac, bez konfliktów): test 0183 + meble/streetscape/materiały + `test_dojlidy_0179`
+ trzy wcześniej czerwone testy industrial-c: 153 pass, 1 fail (`test_forest_trees_reference_their_cell`, komórka
lasu `25_16` w instancjach industrial-c na wspólnym `Data/raw` — dane innego worktree, nie kod tej gałęzi).

## r4 (po recenzji visual-critic `docs/reports/REVIEW-2026-11-14-s20-0183.md`, werdykt SCAL WARUNKOWO)
- **P1-1 różowa czerwień — przyczyna znaleziona:** karty łańcucha miały normalną lokalnie +y (strona od jezdni
  wstecz), a wszystkie kamery dowodowe patrzą od jezdni, czyli na tył. Materiał jest dwustronny (alfa-clip, `_Cull 0`),
  ale URP Lit nie odwraca normalnej tylnej ściany: N·V < 0 → pełny Fresnel zachmurzonego nieba (smoothness 0,5)
  dodawał ~60–100 szarości. Poprawka: każdy quad łańcucha ma dwie kopie (±1 mm wzdłuż własnej normalnej, rdzeń
  ±2,5 mm; bliższa wygrywa test głębi i patrzy w kamerę) + osobna farba łańcucha: bordo `CHAIN_RED_SRGB` (120,20,22),
  biel `CHAIN_WHITE_SRGB` (238,237,231), WORKING_VALUE wg P11-063. Pomiar `tools/measure_gr.py` (detail-2m, regiony
  z recenzji, piksele R > 1,25 G): łańcuch G/R **High 0,70 → 0,34** (77,26,26), **Low 0,76 → 0,56** (95,53,52); słupek
  0,16 / 0,32 bez zmian. Cel ≤ 0,3: High prawie, Low nie (Low ma bledszą czerwień także na słupku — 0,32; renderScale
  0,75 i MSAA 2 mieszają cienkie ogniwa z brukiem).
- **P1-3 kontrast dolnego łańcucha:** w kadrze 13 m (`compare/r4-photo-13m-vs-P11-063.jpg`) oba łańcuchy czytają się
  jak na zdjęciu — dolny bordowy, wyraźny na bruku; biel widoczna na bruku także z 2 m (P1-2 w dużej mierze usunięte).
- **P1-5 Low wzdłuż rzędu:** taśma LOD1 = pasek pionowy + poziomy (dwustronne). Z 8 m na Low łańcuchy są, ale słabe
  (`compare/r3b-low_r4-low_r4-high-along-8m-zoom.png`; bliskie przęsła to LOD0 widziane prawie wzdłuż) — częściowo.
- **P2-6:** P11-063 = Wikimedia Commons, CC0, Rakoon, 2024-06-23 (`File:20240623_124644_June_2024_in_Białystok.jpg`,
  manifest `research/mistral/p11-dojlidy-photos/manifest.csv`); poprawione w bloku override, ADR i docstringu modułu.
- **P2-4:** kamera `bollards-photo-13m` 0,6 m dalej; słup znaku zasłania teraz inne przęsło (świat, nie 0183).
- Budżet r4: `bollard_rw_chain` LOD0 **270** tris (r3b 174), LOD1 **79** (31); `bollard_rw` 78 / 15 bez zmian. Rząd
  Dojlid = 7 × bay: +672 tris LOD0 względem r3b; draws i instancje bez zmian (+2–3 / +8 jak w A/B).
- Świat r4 zbudowany z `overrides.yaml` z main (0179) + blokiem 0183 dopisanym lokalnie (kopia:
  `artifacts/bollards-0183/local-overrides.dojlidy.r4.yaml`), po `git merge origin/main`. Rendery `renders/r4-{low,high}/`.
- Testy: `test_chain_bollards_0183.py` 20/20 (nowy `test_chain_quads_are_two_faced`, budżet ≤ 280 / ≤ 80).

## Otwarte
- Wysokość 0,80 vs 0,90 m i długość przęsła — do pomiaru na miejscu (właściciel) albo z drugiego zdjęcia z obiektem
  o znanym wymiarze.
- Łańcuch: typ i wymiary ogniw UNVERIFIED (r3: klasa tworzywowa 8 mm z szerokości pozornej na P11-063).
- Low: czerwień łańcucha G/R 0,56 (cel 0,3) i słaby łańcuch wzdłuż rzędu z 8 m; migotanie kart w ruchu (P1-4) —
  ocena na A16 przy bramce. P2-1/P2-2/P2-3 (brud przy ziemi, AO stopy, nasycenie) — backlog.
- r1–r3b budowane bez overrides 0179; r4 już z nimi (lokalnie). Po wklejeniu bloku na main: regeneracja Dojlid.
- Przesunięcie r2 (+3,5 m na wygenerowany chodnik) cofnąć, gdy 0179 poprawi nawierzchnię (trawnik → bruk).
- visual-critic: r3b oceniony (SCAL WARUNKOWO); r4 do ponownej oceny przez lidera/krytyka.
- Telefon: koszt nie mierzony na A16 (bez adb w zadaniu).
- Kolizja przęsła jest sztywna (ciężarówka nie zerwie łańcucha) — jak wszystkie meble; fizyka zrywania poza zakresem.
- Rozstawienie w Dojlidach i korekta pozy `photo_P11-063` — 0179 / lider.

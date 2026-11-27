# ADR 0352 — Drzewa: blaszki per gatunek także w zestawie działek, wariacja per drzewo, miękkie cieniowanie koron, dąb (tree-species-s24)

Status: Proposed, 2026-11-27 (agent tree-species-s24; numer zarezerwowany przez lidera).
Powiązane: ADR 0308 (korony z płatów, atlasy gałązek), 0163 / 0170 (drzewa ogrodowe zestawu działek), 0088 (`_CrownShade`),
0023 (impostory), 0339 (`foliage_tint`), 0347 (skrajnia z zmierzonej siatki), krytyk s24 fala 11
(`artifacts/critic-s24-wave11/CRITIC.md` pkt 10 i „lizakowe drzewka w dali”, P0 #3).

## Kontekst
Krytyk: „ten sam atlas liści na wszystkich drzewach, efekt papierowych kart; sztywny gradient jasne/ciemne na koronie;
lizakowe drzewka w dali, identyczne”. Render „przed” (`artifacts/tree-species-s24/before/knyszyn-w/`, High PC, pogodnie i
pochmurno) i dane kafla pokazały cztery niezależne przyczyny:

1. **Biblioteka drzew ma już atlasy per gatunek** (ADR 0308: lipa, klon, brzoza, olsza, topola, sosna, świerk). Jeden
   stempel liścia mają **drzewa ogrodowe zestawu działek** (`plot_kit._crown_card`: `crown_ovoid/round/birch` rysowane
   jedną soczewkową blaszką `_leaf_stamps`). To one stoją przy ulicy wsi: na `knyszyn-w` 213 drzew liściastych o
   promieniu korony < 1,6 m i 156 owocowych zostaje kartami zestawu także na High (większe są instancjami biblioteki).
2. Karta korony miała pod liśćmi **płaski wielokąt cienia** (22, 34, 20), a pełny wariant drzewa **wachlarz 4 trójkątów**
   z ciemnym wierzchołkiem na osi (`occ_mid`) — w koronie ciemny klin o prostych krawędziach.
3. `Kamion/Vegetation`: okluzja kart = `smoothstep(-0.6, 0.75, normal.y)` — jedna pozioma rampa na każdej koronie;
   brak jakiejkolwiek różnicy koloru między dwoma drzewami tego samego gatunku.
4. Ten sam prototyp przy tej samej wysokości = ta sama sylweta; żaden gatunek biblioteki nie miał klapowanej blaszki
   ani szerokiej korony na ciężkich konarach.

## Decyzja

### 1. Blaszki per gatunek w kartach koron zestawu działek (`plot_kit._blade_stamps`, `_CROWN_BLADE`)
`crown_ovoid` = lipa (sercowata), `crown_round` = klon (pięcioklapowa, × 1,35), `crown_birch` = brzoza (rombowa, × 0,85);
obrysy z `leaf_sprays.blade` — jedno źródło z biblioteką. Płaski wielokąt cienia przykrywają ciemne liście dalszej strony
korony wychodzące poza jego obrys. Atlas `plot_kit` bez zmiany rozmiaru i układu (wiersz `tall`, te same UV).

### 2. Pełny wariant drzewa ogrodowego bez klina (`plantings._crown_quad`)
Karta korony to jeden czworokąt (2 trójkąty zamiast 4) z okluzją na narożnikach: ciemniej u dołu, nierówno lewa/prawa,
poziom jasności per drzewo 0,86–1,0. Każda z trzech kart ma własną szerokość (0,82–1,12), wysokość, lustro, pochylenie
wierzchołka i odchyłkę kąta; drzewo < 6,5 m ma „spódnicę” gałązek 12–24 % wysokości korony poniżej nominalnej podstawy.
Trójkąty pełnego drzewa: 34 → 28. Wariant lite (Low / Medium, drzewa dalej od ulicy) bez zmian — budżety A16.

### 3. Wariacja per drzewo i kępy światła w shaderze (`Vegetation.shader` `_TreeVar`, `VegetationCanopyPolicy.TreeVariation`)
- Ziarno drzewa = hasz macierzy instancji (obrót + skala): nie zależy od floating origin, ten sam na LOD0 / LOD1 / impostorze.
- Albedo × jasność ±x i odcień ±y (cieplej / chłodniej). Liściaste (0,11; 0,05), iglaste (0,07; 0,02).
- Karty: gładki pseudo-szum (dwa zagięte sinusy, etap wierzchołków, bez tekstury) w metrach modelu daje kępy ±z/2 albedo
  i przesuwa rampę `_CrownShade` o ±0,45 — granica światła idzie po kępach, nie po poziomicy. z = 0,30 / 0,18, w = 1,5 rad/m.
- Domyślnie 0 (żywopłoty, rośliny Fab, ściany HLOD lasu bez zmian). Zero nowych tekstur, draw calli i trójkątów;
  jeden interpolator więcej (`TEXCOORD9`).

### 4. Szerokość korony per instancja (`InstanceImporter.TreeCrownWidth`)
Skala XZ 0,84–1,0 z hasza pozycji (cm), na macierzy instancji — wspólna dla kart, impostora i kolidera pnia. Nigdy szerzej
niż model: skrajnia ADR 0347 liczona jest na nieskalowanej siatce. Rekordy z `garden_canopy_width` (ADR 0154) bez zmian.

### 5. Dąb szypułkowy w bibliotece (`leaf_sprays` `oak`, `make_trees.CROWN["oak"]`, `vegetation.oak_share`)
- `leaves_oak.png`: atlas 2 × 2 gałązek, blaszka odwrotnie jajowata z 3–4 zaokrąglonymi klapami na stronę, najciemniejsza
  zieleń zestawu. Rysunek proceduralny (numpy + PIL), bez zdjęć i cudzych pikseli.
- `tree_oak_{0,1}`: krótki gruby pień (0,16 H), korona 2r/H ≈ 0,94 najszersza poniżej połowy, 7 konarów prawie poziomych,
  płaska kopuła; 3270 / 3332 trójkąty LOD0, 766 / 748 LOD1, impostor 6 widoków. Kora `bark_alder` (bez nowej tekstury).
- Rozmieszczenie: `oak_share` zamienia dojrzałe (≥ 9 m) lipy i klony POZA drzewostanami w dęby wewnątrz płatów gładkiego
  szumu pozycji (okres 150 m, próg 0,60, udział 0,85) — grupami, jak szpaler albo kępa przy zagrodzie. Bez zmian: drzewa
  leśne (`fk` / `fc`: wypieki HLOD, linia koron, reguły CHM), drzewa ogrodowe `tier: high`, nadpisania, drzewa OSM i działek.
  Tylko hasz pozycji — strumień losowy pozostałych drzew nietknięty. OSM: `species/genus` Quercus / dąb → `oak`.
- Wszystkie proporcje i udziały to `WORKING_VALUE` (brak inwentaryzacji gatunkowej kafli).

## Odrzucone
- **Wspólny atlas liści wszystkich gatunków**: instancje rysowane są per (komórka, prototyp, LOD), wspólna tekstura nie
  zmniejsza liczby draw calli, a pogarsza mipy (sąsiedztwo gatunków).
- **Instancje biblioteki także dla koron < 1,6 m**: +750…3100 trójkątów na drzewo zamiast 28 (warunek „trójkąty bez wzrostu”).
- **Dąb w mieszankach BDOT (`SPECIES` / `MIX`)**: wagi pozycyjne i wspólny strumień losowy — zmieniłby każde drzewo leśne
  wszystkich kafli oraz wypieki HLOD.
- **Wierzba w bibliotece**: generator 0227 istnieje (`--include-willow`), ale to studium płaczącej formy parkowej; wierzba
  nadbrzeżna wymaga własnej formy i reguły w `water_banks` — otwarte.

## Skutki
- Zmiana wyglądu wszystkich drzew biblioteki we wszystkich kaflach bez przebudowy (shader + import): tint, kępy, szerokość.
- Dąb i nowe karty zestawu działek wymagają `build_world.py` kafla; lista i liczby w `docs/status/tree-species-s24-STATUS.md`.
- Tekstury: +1 atlas 1024² i 2 × (1536 × 384 albedo + normal). Pomiar pamięci i draw calli — STATUS.

## Weryfikacja
`tests/gis/test_trees_0352.py` (6), `test_trees_0308.py`, `test_trees_0347.py`; EditMode `VegetationCanopyPolicyTests`,
`TreeCrownWidthTests`. Rendery przed / po: `artifacts/tree-species-s24/`.

## Wynik (High PC, 1920 × 1080; `artifacts/tree-species-s24/compare/`)
- `knyszyn-w`, czyste A/B drzew (przed = derived fali 11 z 26.11 13:51, po = ta gałąź), pogodnie i pochmurno, 10 kamer:
  draw calle instancji (rekwizyty + drzewa) −7…+2 na kamerę (dąb: +1…+2 tam, gdzie stoi); trójkąty instancji −2964…+84;
  trójkąty sceny −346…−5753. `drawsEst` obiektów kafla +0…+8 na 5 kamerach — to różnica kodu bazowego między falą 11
  a tą gałęzią (inne scalone zmiany), nie drzew: do potwierdzenia czystym A/B po fali 12.
- Dęby: `knyszyn-w` 78, `dw671-tykocin-03` 112; skrajnia `violations_after: 0` w obu kaflach.
- Tekstury dębu: 1 × 1024² + 4 × 1536 × 384, Standalone kompresja automatyczna ≈ 4,5 MB z mipami (WYLICZONE z rozmiarów
  i 8 bpp, nie zmierzone profilerem — `UNVERIFIED`).
- **Nie rozwiązane:** małe drzewa ogrodowe zestawu działek (korona < 1,6 m) nadal czytają się jak „lizaki”, a w świetle
  słonecznym w ich koronach zostaje ciemny klin — to karta skrzyżowana stojąca bokiem do słońca (normalna promieniowa),
  nie wachlarz `occ_mid` ani wewnętrzne karty (oba usunięte w pełnym wariancie; pochmurno klin znika). Potrzebna inna
  bryła małego drzewa (np. młode prototypy biblioteki albo karty koron z normalną „w górę”) — poza budżetem tej rundy.

## Dopisek crown-lod-s24 (2026-11-27)
`Vegetation.shader` po ręcznym scaleniu 0352 + 0354 kompiluje się (d3d11) bez błędów; dwa ostrzeżenia fxc obecne już
w buildzie #10 (`VegAlpha`, `VegShadow`) usunięte. `_TreeVar` bez zmian; nowe: cross-fade LOD1 → impostor i fill
zminiaturyzowanych liści (ADR 0308, dopisek crown-lod-s24) — ten sam hasz instancji, tint identyczny na obu LOD w paśmie.
## Dopisek 2026-11-27 (garden-trees-s24): małe drzewa ogrodowe i owocowe — płaty i kępy na konarach
Zamyka punkt „Nie rozwiązane” (krytyk build #10: „lizaki”, ciemny klin w słońcu, ciemny `_core` drzew owocowych).

### Diagnoza
- Trzy karty całej korony skrzyżowane na osi = kula na patyku z każdej strony; każda karta cieniuje się WŁASNĄ normalną
  promieniową, więc sektor między kartami odwróconymi od słońca stoi w koronie jako ciemny klin o prostych krawędziach
  (a karta rzuca cień na sąsiednią wzdłuż linii przecięcia). Pochmurno klin znika — zgodnie z renderami ADR 0352.
- Karty koron atlasu kończyły się u dołu prostym cięciem na 30–34 % szerokości — płaski spód „lizaka”.
- `PLT.fruit_tree`: ciemny 4-ścienny `_core` (okluzja 0,22–0,26) pod dwoma symetrycznymi piętrami kart.

### Decyzja (`tools/worldgen/streetscape/small_trees.py`)
- **`young_tree`** — pełny (High) wariant drzewa liściastego zestawu działek o promieniu korony < 1,6 m
  (`garden_trees` → `garden_tree(young=True)`; poza `garden_trees`: H < 6,5 m): pień 3-ścienny wchodzący w koronę,
  3 dolne płaty korony odsunięte od pnia i pochylone NA ZEWNĄTRZ, 3 górne między nimi pochylone DO ŚRODKA, 2–3 konary
  (po 1 trójkącie) od pnia do dolnych płatów. Płat = pomniejszona karta korony gatunku z ADR 0352 (lipa / klon / brzoza;
  namalowany w niej konar jest gałęzią płata) — ten sam atlas i materiał. **20–21 trójkątów (było 14).**
- **`orchard_tree`** (`PLT.fruit_tree`) — jabłoń / śliwa / grusza: krótki gruby pień, rozwidlenie na 0,22–0,35 H,
  3–4 konary (skrzyżowane zwężające się pasy), na każdym gałązka z wachlarzem pędów (`apple_*`), gęsta kępa na końcu
  i mniejsza w poprzek po stronie wewnętrznej (`shrub_a`), dwie karty wierzchołka. **Bez `_core`. 40 / 50 trójkątów
  (było 46).**
- **Brak klina:** normalna wierzchołka = kierunek od środka korony do wierzchołka (spłaszczony, z dodatkiem „w górę”),
  nigdy płaszczyzna karty — cała korona cieniuje się jak jedna bryła; okluzja (długość normalnej) 0,7–0,9 u stopy płata,
  ≈ 1 na czubku; żadnej ciemnej geometrii. Żadna karta nie stoi na osi korony i żadne dwie nie mają wspólnej linii.
- **Karta skręcona:** krawędź czubka obrócona wokół osi płata o 0,2–0,5 rad względem krawędzi stopy — dwa trójkąty
  czworokąta leżą w różnych płaszczyznach (0 dodatkowych trójkątów), więc płata nie widać w całości „na ostrzu”.
- **Warianty z ziarna:** 3 formy drzewa młodego (`vase`, `lean`, `broad`) i 3 owocowego (`open` — jabłoń o otwartym
  środku, `flat` — stara śliwa, `upright` — grusza); kąty, wysokości, szerokości i odsunięcia płatów per drzewo.
- **Atlas** (`plot_kit._crown_hw`, `_UNDER` 0,07): spód kart `crown_ovoid` / `crown_round` zaokrąglony, pień wchodzi w
  jednym punkcie. Układ i rozmiar atlasu bez zmian (te same UV); dotyczy też wariantów lite i dużych drzew zestawu.
- Warianty lite (Low / Medium, drzewa dalej niż 12 m od frontu działki) bez zmian — budżety A16.
- Wszystkie proporcje `WORKING_VALUE` (brak inwentaryzacji drzew ogrodowych; referencje: zdjęcia właściciela, docs/05).

### Wynik (`knyszyn-w`, High PC 1920 × 1080; `artifacts/garden-trees-s24/`)
- 164 małe drzewa liściaste w pełnym wariancie: 3384 trójkąty, śr. 20,6 / drzewo (było 14: **+47 %**); 121 owocowych:
  5600, śr. 46,3 (było 46: **+0,6 %**). Kafel High: **+1122 trójkąty** (z licznika `garden_trees.small_full` w
  `streetscape_qa.json`); Low / Medium: `tris_low` 15 428 bez zmiany.
- Draw calle: drzewa zostają w tych samych grupach chunków zestawu działek, ten sam materiał i atlas — **+0 z konstrukcji**;
  draw calle instancji 76–160 / kamerę bez zmiany na 10 z 11 kamer. `drawsEst` obiektów kafla −8…+1 i trójkąty sceny
  +0…+5184 / kamerę NIE są czystym A/B drzew: „przed” = derived zbudowany na gałęzi tree-species (27.11 rano), „po” = main
  9ec10a5a2 + ta zmiana (inne scalone gałęzie).
- Pary przed | po: `compare/knyszyn-w/*-{clear,overcast}.jpg` (5 kamer kontrolnych + 6 ogrodowych `garden_cams.json`).

### Otwarte
- Płat to jeden czworokąt: z ukosa i z góry (kamera `garden_small_2`) pojedyncze płaty nadal czytają się jak płaskie
  „wiosła”; kępa z 2 skrzyżowanych kart = +12 trójkątów na drzewo (ponad budżet +50 %).
- Liście w płatach są pomniejszone ok. 0,4× (cała karta korony w roli gałęzi); osobne sprite'y kęp gatunków wymagają
  miejsca w atlasie (wiersze `sprites` / `tall` są pełne).
- Młoda brzoza (wąska karta 0,44) bywa pierzasta i zbyt rzadka. Drzewa lite na High (dalej od ulicy) i > 6,5 m poza
  `garden_trees` (`garden_trial`) zostają przy kartach skrzyżowanych.
- Ocena `visual-critic` — do zlecenia przez lidera (subagent nie tworzy subagentów).
## Dopisek neon-avenue-s24 (2026-11-27): szpalery drzew przy drodze — koniec „klonów bliźniaków”

Powiązane: krytyk build #10 (`artifacts/critic-s24-build10/CRITIC.md`, TOP #10, zrzuty `artifacts/full-build-10-s24/evidence/run-stream-on/shot_t0180.png` i `run-stream-off/shot_t0180.png`), ADR 0222 (szpalery DK65), ADR 0308 (korony z płatów), ADR 0347 (skrajnia z zmierzonej siatki).

### Przyczyna
1. Domyślna ścieżka BDOT10k `OT_OIPR_L` („rząd drzew”, używana w kaflach bez `tree_rows.yaml`, np. korytarz `dw671-tykocin-*` i `dk65-monki-*` oraz linie poza korytarzem) stawiała co równe 8 m jeden gatunek (`linden` albo `maple`) z rozrzutem poprzecznym ±0,3 m, bez luk i bez młodych nasadzeń.
2. Ścieżka `streetscape/tree_rows.py` (kafle `knyszyn-w`, `dk65-01…11`) miała zmienny krok i przerwy, ale wąski rozrzut poprzeczny, brak młodych dosadzeń/samosiejek w lukach, brak domieszki dębu i losowanie wariantu/obrotu/wysokości niezależne od sąsiada — sąsiednie drzewa trafiały w ten sam wariant (`v0/v1`) i podobną skalę/obrót („klony bliźniaki”).

### Decyzja (`tools/worldgen/streetscape/tree_rows.py`, `tools/worldgen/streetscape/vegetation.py`)
Wszystkie wartości poniżej są `WORKING_VALUE` (brak inwentaryzacji dendrometrycznej szpalerów):
- **Wspólna emisja alejowa (`vegetation.emit_avenue`, `_avenue_emit_attrs`)** dla `tree_rows.py` oraz domyślnych rzędów BDOT (`avenue_row_candidates`). Deterministyczna z ziarna linii; losowania wykonywane dla każdego stanowiska przed filtrowaniem luk i skrajni (ADR 0173).
- **Wiek / skala (`0,70–1,15 × href_m`)**: dla dojrzałych drzew `AVENUE_ROW_AGE_SCALE = (0.70, 1.15)` (w granicach `height_m` wiersza, gdy podane); sąsiednie drzewa tego samego gatunku rozsuwane wysokościowo (`|Δh| ≥ 1,4 m`).
- **Wariant i obrót**: dla gatunków z `NVAR > 1` sąsiednie drzewo tego samego gatunku nie powtarza wariantu `v`; separacja obrotu między kolejnymi drzewami `yaw ≥ 1,05 rad` (~60°); pochylenie pnia `0,005–0,065 rad`.
- **Rytm i przesunięcia**: odstęp wzdłuż `10–16 m` (BDOT) / `12–18 m` (`tree_rows`), przesunięcie poprzeczne `σ = 1,0–1,05 m` z ograniczeniem `±2,5 m`. Odsunięcie prawne pnia `≥ 3,0 m` (`_push_out`) i skrajnia korony z zmierzonej siatki ADR 0347 (`4,7 m / 1,5 m`) egzekwowane po rozrzucie.
- **Przerwy i młode nasadzenia / samosiejki**: `missing_share` 0,16 (BDOT) / 0,18 (`tree_rows`); w `replant_share = 0,35` luk wstawiane jest pojedyncze młode drzewo lub krzew (`birchyoung` 0,35 / `linden` 0,25 / `maple` 0,25 / `shrub` 0,15; młode `linden`/`maple` `4,0–8,2 m`, `birchyoung`/`shrub` wg `HEIGHT`), pozostałe ~10–12 % pozycji zostaje otwartą luką.
- **Domieszka gatunków**: `linden` / `maple` / `oak` / `birch` / `alder` z dominacją jednego gatunku w rzędzie (`dominant_share` 0,60–0,62; jesion → model lipy wg ADR 0308). **Zero nowych prototypów i tekstur** — używana jest wyłącznie istniejąca biblioteka drzew.

### Wynik (prototyp `knyszyn-w` i `dk65-07` w prywatnej kopii `Data/raw/derived`, High PC 1920 × 1080, `clear` + `overcast`; dowody `artifacts/neon-avenue-s24/`)
- **`knyszyn-w`**: szpalery (`treerow:*`) `85 → 88` drzew (109 planowanych, 16 luk, 4 młode dosadzenia `replants`, 13 `blocked`), gatunki: `alder 5→6, birch 10→11, birchyoung 0→2, linden 32→22, maple 38→21, oak 0→26`; rozpiętość wysokości `11,2–18,9 m → 2,4–19,5 m`; różne `(gatunek, wariant)` `11 → 14`. Cały kafel: `11 360 → 11 327` drzew (`−33`), `violations_after: 0` (ADR 0347).
  - Visual-QA (10 kamer, `clear` i `overcast`): `scene_draws` `−1..+0` (suma `−1`), `scene_tris` `−25 954..−5 216` (suma `−154 163`); `instanced draws` `−1..+7` (suma `+19`, max `route-s1562`: `50 → 57`), `inst_tris` `−104..+2 986` (suma `+7 650`).
- **`dk65-07`**: szpalery (`treerow:*`) `18 → 17` drzew (19 planowanych, 4 luki, 2 `replants`, 3 `cut_sight`, 1 `blocked`), gatunki: `birch 6→3, birchyoung 0→1, linden 4→0, maple 8→2, oak 0→11`; wysokość `11,2–18,8 m → 3,7–17,8 m`. Cały kafel: `166 578 → 166 534` drzew (`−44`), `violations_after: 0` (ADR 0347).
  - Visual-QA (6 kamer, `clear` i `overcast`): `scene_draws` `−1..+0` (suma `−5`), `scene_tris` `−13 876..−10 860` (suma `−68 896`); `instanced draws` `+0..+2` (suma `+4`), `inst_cnt` `−7..−2`, `inst_tris` `−84..+728` (suma `+594`).
- *Uwaga o bazie A/B*: kopia bazowa `Data/raw/derived/{knyszyn-w,dk65-07}` z `main` pochodziła z 17.11/19.11 (przed przebudową kafli z dębem ADR 0352 i 28-trójkątnymi kartami ogrodowymi), stąd w `after` pojawiły się `tree_oak_0/1` (`all_oaks: 0 → 78` w `knyszyn-w`, `0 → 72` w `dk65-07`; lokalny wzrost `instanced draws` +1…+7 w komórkach z dębem, przy łącznym spadku trójkątów sceny). Liczba prototypów biblioteki bez zmian.
- **Ocena wizualna (SBS `artifacts/neon-avenue-s24/sbs/`)**: w `knyszyn-w` (`route-s1562`, `route-s0710`, `dk65-goniadzka`, `dk65-north-edge-in`, `route-s1278`) i `dk65-07` (`drive-wood`, `route-s0144`, `route-s0721`) zniknął „wzór stempla”: wyraźne różnice wysokości i pokroju koron (dąb, brzoza, lipa/klon), otwarte luki, przesunięcia poprzeczne i zróżnicowanie wariantów przy zachowanej czystej skrajni drogi. W `tykocka-dw671-out` widoczne blisko ulicy niskie drzewa to karty działkowe `plot_kit` (poza zakresem szpalerów — otwarty punkt ADR 0352 wyżej).
- **Testy**: `test_trees_0352.py` (+ nowy test `test_avenue_rows_break_twin_clones_and_stay_within_library_and_clearance`), `test_treerows_0222.py`, `test_trees_0308.py`, `test_trees_0347.py` (wszystkie 28 kafli korytarza zielone; jedyna usterka w `test_profile_table_matches_the_glb` to pre-existing różnica CRLF vs LF w hashu `trees_meta.json`, przy 29/29 identycznych prototypach), `test_budget_0221.py`, `test_typology_0238.py`, `test_world_v31.py`, `test_hero_bridge.py` (62/62 zielone).
- **Po scaleniu (lider)**: przebudować (`build_world.py` + `import-region.ps1`) kafle z szpalerami przydrożnymi (korytarz DK65 `dk65-01…11`, `knyszyn*`, `dw671-tykocin-*`, `dk65-monki-*`) — wtedy zmiana obejmie także odcinek ze zrzutu `shot_t0180.png` (build #10).
## Dopisek agy-garden-var-s24 (2026-11-27): małe drzewa ogrodowe — usunięcie „lizaka” i wariacja per egzemplarz (+0 DC)
Zamyka uwagę krytyka `artifacts/critic-s24-day27/CRITIC.md` pkt 2 („jedno »lizak« zostało; powtarzalność”).

### Diagnoza
- W `small_trees.young_tree` formy `vase` i `lean` z małymi przechyłami dolnych płatów (0,04–0,30 rad) i całokoronowymi kartami `crown_ovoid` / `crown_round` (`v_lo = 0`) składały się w zwartą, symetryczną bryłę na prostym pniu bez widocznych konarów (`_bough` był pojedynczym płaskim trójkątem schowanym w koronie); młoda brzoza (`slim = 0,72`) dawała dwa wąskie „kolce”.
- Wszystkie małe drzewa tej samej średnicy koronowej z ortofoto miały prawie identyczną wysokość (klamp 3,5 m u owocowych, 4,3–5,5 m u liściastych), jednakowy pion i brak różnic odcienia/jasności (`WorldPlotKit.shader` czytał z `COLOR_0` wyłącznie skalar `occ`, bez tintu per drzewo jak `Vegetation.shader` `_TreeVar`).

### Decyzja (`tools/worldgen/streetscape/small_trees.py`, `plantings.py`, `plots.py`, `WorldPlotKit.shader`)
1. **Konary 3D pod koroną i brak „lizaka” (`young_tree`, `orchard_tree`)**:
   - Pień `young_tree` kończy się na rozwidleniu **poniżej korony** (`fork_k` zależne od gatunku: `birch` 0,92 z wygiętym przewodnikiem i `concrete`/`trunk`, `ash` 0,88, `linden` 0,84, `maple` 0,78, `chestnut` 0,76) i dzieli na 3 konary z dwóch skrzyżowanych pasów (`_strip`, widoczne z każdej strony).
   - 6 asymetrycznych płatów liści (3 osadzone od połowy długości konarów + 3 przesunięte górne z domieszką `shrub_a`/`apple_b`, przycięte u spodu `v_lo`, `twist` 0,65–0,95 rad, bez pojedynczych cienkich kart na osi); 4 formy: `YOUNG_FORMS = ("forked", "lean", "broad", "tiered")` oraz `ORCHARD_FORMS = ("open", "flat", "upright", "leaning")`.
   - Brzoza: pełniejsza szerokość płata (bez `slim = 0,72`), piętrowe gałęzie wzdłuż przewodnika.
   - `tree_dims`: wyższe minimum podstawy korony w działkach dla brzozy (1,50 m), jesionu (1,42 m), lipy (1,35 m) względem klonu/kasztanowca (1,30 m) oraz `cb_k` 0,15–0,19.
2. **Zmienność per egzemplarz bez nowych draw calli**:
   - Pełny obrót `0..2π`, przechył całej bryły z normalnymi wierzchołków do **±4°** (`_tilt_tree`), skala **0,7–1,3** w `garden_trees` i `plots` (`H` młode `3,2–6,4 m`, owocowe `2,7–6,2 m`).
   - Tint per drzewo jak ADR 0352 (`±11 %` jasności, `±5 %` odcienia + kępy `±12 %` w lokalnych metrach chunka) przeniesiony w `TEXCOORD_1` (`Kit.uv1`, `WorldPlotKit.shader`: aktywne przy `fol > 0,5 && uv1.x > 0,1`; płoty, żywopłoty, krzewy i trzciny z domyślnym `uv1.x <= 0,1` bez zmian).
- Wszystkie proporcje `WORKING_VALUE`.

### Wynik (`knyszyn-w`, czyste A/B względem `main` `5e3b465b3`, High PC 1920 × 1080, `clear` + `overcast`; `artifacts/agy-garden-var-s24/`)
- `streetscape_qa`: `trees` 808 → 808; `tris_high` 17 188 → 19 132 (**+1 944**), `tris_low` 15 428 → 15 428 (**+0**); młode pełne (164 szt.): `3 384 → 5 328` tris (20,6 → 32,5 / drzewo), owocowe (121 szt.): `5 600 → 5 600` (46,3 / drzewo).
- Visual-QA (11 kamer `garden-trees`, `clear` i `overcast`): **draw calle `dDraws = 0`**, `shadowDraws` +0, `instDraws` +0 na wszystkich 11 kamerach; `tris` sceny `+0…+1 362` (`tykocka-dw671-out`: `490 762 → 491 081`, `+319` = `+0,06 %`).
- Testy: `test_small_trees_0352.py` (5), `test_trees_0352.py`, `test_trees_0347.py`, `test_trees_0308.py`, `test_house_greenery_0163.py`, `test_horizon_0170.py`, `test_buildings_r9.py`, `test_budget_0221.py`, `test_typology_0238.py`, `test_world_v31.py`, `test_hero_bridge.py` — zielone.


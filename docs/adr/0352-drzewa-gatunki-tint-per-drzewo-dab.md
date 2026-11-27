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

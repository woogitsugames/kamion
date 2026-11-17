# QA researchu Mistrala „pętla S8 ↔ DW671 ↔ Tykocin” (P25, 2026-11-16)

Przedmiot: `research/mistral-s8-loop-s23/` w `origin/main` @ `27af3bcce` (D82; kontekst D63 — najpierw wierność sieci drogowej).
Metoda: losowa próba 25 faktów z katalogu 93 sprawdzalnych faktów + 2 dobrane jawnie; każdy sprawdzony niezależnie **wyłącznie** z: OSM API 0.6, GUGiK WMS ortofoto (StandardResolution), Dz.U. przez api.sejm.gov.pl. Bez Google, bez Mapillary, bez Panoramax. BDOT10k nie był potrzebny dla wylosowanych faktów (nie pobierany).
Wykonawca: agent QA (Claude), sesja s23. Skrypty pomocnicze i wycinki ortofoto tylko w scratchpadzie (poza repo); w tym raporcie są wyłącznie liczby.

## 1. Losowanie

- Katalog: 93 fakty w 8 kategoriach (`lim` ograniczenia/przepisy 12, `jun` węzły 15, `len` długości 16, `mop` 11, `sign` znaki 11, `dest` cele ciężarówek 11, `xsec` przekroje 12, `set` miejscowości 5). Pełna lista: Załącznik A (indeks, kategoria, fakt, wartość Mistrala, plik:linia).
- Losowanie: Python `random.seed(20261116); sorted(random.sample(range(93), 25))` →
  **[0, 1, 4, 24, 26, 27, 31, 32, 41, 43, 45, 46, 51, 55, 64, 66, 72, 73, 78, 79, 81, 82, 84, 86, 87]**.
- Pokrycie: xsec 7, len 4, mop 4, lim 3, dest 3, **jun 2, sign 2** (< 3) → dobór jawny: `random.Random(20261117).choice(...)` z niewylosowanych w kategorii → **jun #14**, **sign #54** (oznaczone „+D”). Kategoria `set` (miejscowości) nie była na liście wymaganych kategorii zlecenia — bez doboru.
- Tolerancje: szerokości ±0,3 m; długości/odległości ±2 %; nazwy, typy, tagi, liczby całkowite — dokładnie. „CZĘŚCIOWO” = liczba zgodna, ale opis/znaczenie błędne albo zweryfikowana tylko część.

## 2. Źródła i zapytania (2026-11-16, UTC)

- **OSM**: `GET https://api.openstreetmap.org/api/0.6/map.json?bbox=…` — 57 zapytań siatki 19×3 nad bbox 22,68–23,06 E × 53,10–53,22 N (20:26–20:28 UTC; 224 614 węzłów, 29 836 way, 337 relacji), UA `kamion-qa/1.0`, przerwa 1,2 s; plus `way/98599908/relations.json`. Długości/powierzchnie liczone w EPSG:2180 (pyproj). Dalej „OSM-bbox”.
- **Ortofoto**: `GetMap` z `https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/StandardResolution` (warstwa `Raster`, EPSG:2180), 30 wycinków (20:31–20:35 UTC): 40×40 m przy 0,05 m/px w stacjach przekrojów; MOP: 0,12 m/px na całym obrysie. Własna implementacja profilu poprzecznego (wzorzec metody: ADR 0272 / `ortho_xsec.py`, nie używany jako kod) **plus obejrzenie każdego wycinka** (zaznaczone krawędzie na obrazie); dokładność ±0,3 m.
- **Dz.U.**: `https://api.sejm.gov.pl/eli/acts/DU/2024/1251/text.html` (PoRD t.j.), `https://api.sejm.gov.pl/eli/acts/DU/2019/2310/text.html` (znaki i sygnały, t.j.).

## 3. Tabela weryfikacji

Ozn.: R = `research/mistral-s8-loop-s23/`.

| # | fakt | wartość Mistrala (R/plik:linia) | moja wartość | źródło | zgodne | komentarz |
|---|---|---|---|---|---|---|
| 0 | S8: `maxspeed` na way S8 | 120 na 99/99 (`SIGNS.md:10`) | 120 na 71/71 way S8 w 15 kaflach; 84/84 w OSM-bbox | OSM-bbox, filtr `highway=motorway`+`ref∋S8` | TAK | liczba way zależy od bbox (Mistral nie definiuje „bbox” dla 99) — wartość tagu zgodna wszędzie |
| 1 | S8: `maxspeed:hgv` | 80 na 99/99 (`SIGNS.md:10`) | 80 na 71/71 (kafle), 84/84 (OSM-bbox) | jw. | TAK | `toll:hgv=yes` 67/71 w kaflach — też zgodne z `junctions.json` |
| 4 | PoRD: >3,5 t poza zabudową na „pozostałych drogach” | 70 km/h, art. 20 ust. 3 pkt 2 lit. b (`SIGNS.md:22`) | 70 km/h, art. 20 ust. 3 pkt 2 lit. b | Dz.U. 2024 poz. 1251 (api.sejm.gov.pl) | TAK | w tym samym wierszu błędna podstawa dla 120 km/h („ust. 2 pkt 1 lit. a”; poprawnie ust. 3 pkt 1 lit. b; ust. 2 to strefa zamieszkania 20 km/h) — poza próbą |
| 14 +D | Węzeł Białystok Zachód: typ | „półwęzeł/trąbka (2 łącznice — jedna para)” (`junctions.json:35`) | **pełny węzeł**: 28 way `motorway_link` (3,7 km) w r. 1,5 km, 4 punkty styku z S8 (2 wyjazdy + 2 wjazdy), łącznice dochodzą do `trunk` ref `8;65` | OSM-bbox, nody `motorway_junction` 2081020070/3160890725/4236127140 | NIE | `crossroad` „Warszawska tertiary” (way 1151531618) istnieje, ale łącznice węzła w promieniu 1,5 km stykają się tylko z DK8/DK65 (trunk) |
| 24 | Węzeł Tykocin: nazwa | „Tykocin” (`junctions.json:241`) | `name=Tykocin`, `unsigned_ref=91`, `milestone=632` (nody 469876632, 1937542643) | OSM-bbox | TAK | — |
| 26 | Węzeł Tykocin: typ | „półwęzeł/trąbka (2 łącznice — jedna para)” (`junctions.json:260`) | **pełny węzeł**: 16 way `motorway_link` (2,0 km) w r. 1,5 km, 4 punkty styku z S8 (2 wyjazdy + 2 wjazdy), łącznice do ronda (way 183382922 `junction=roundabout`, tertiary) | OSM-bbox | NIE | ten sam błąd dla **wszystkich 5 węzłów** (Choroszcz, Rzędziany, Jeżewo też mają po 4 punkty styku z S8) — systematyczny; Mistral liczył tylko way zaczynające się w nodzie `motorway_junction` |
| 27 | Długość łącznicy way 424138211 (Białystok Zachód) | 126,7 m (`junctions.json:46`) | way 424138211: 126,7 m; ale łącznica trwa dalej (way 1151531626) do rozwidlenia: **261,7 m** | OSM-bbox, łańcuch `motorway_link` | CZĘŚCIOWO | liczba = długość jednego way OSM, nie łącznicy (w `note_lengths` opisana jako długość łącznicy z pasami wyłączania) |
| 31 | Długość łącznicy way 183639802 (Choroszcz) | 230,9 m (`junctions.json:116`) | 230,9 m (jedyny way łącznicy, kończy się na drodze tertiary) | OSM-bbox | TAK | — |
| 32 | Długość łącznicy way 183381873 (Jeżewo) | 119,1 m (`junctions.json:168`) | way 119,1 m; łącznica do rozwidlenia (+1467119152, 1467119153): **384,6 m** | OSM-bbox | CZĘŚCIOWO | jak #27 |
| 41 | MOP Radule: odległość od osi S8 | 134,9 m (`mop.json:22`) | centroid pola obrysu (753612,7; 593336,7) → najbliższa jezdnia S8 (way 251431129): **144,5 m**; do osi między jezdniami ~150 m | OSM-bbox, way 222577666 | NIE | 134,9 m odtwarza się tylko z centroidu Mistrala (753617,2; 593328,0) **do najbliższej jezdni**, nie do osi S8; −6,6 % vs mój pomiar (> 2 %) |
| 43 | MOP Radule: obiekt i nazwa | way 222577666, `highway=services`, „Miejsce Obsługi Podróżnych Radule” (`mop.json:8`) | `highway=services`, `full_name=Miejsce Obsługi Podróżnych Radule`, `name=MOP Radule` | OSM-bbox | TAK | pole nazwane `official_name`, w OSM to `full_name` (kosmetyka) |
| 45 | MOP Radule: toalety | `toilets=yes` (`mop.json:26`) | `toilets=yes` | OSM-bbox | TAK | — |
| 46 | MOP Radule: miejsca TIR | 12 (ESTIMATED, `mop.json:30`) | **rząd 80–100** (ESTIMATED): duży plac w obrysie MOP z 5 rzędami ukośnych stanowisk dla zestawów po ~17–21 linii | WMS ortofoto, obrys way 222577666, 0,12 m/px | NIE | niedoszacowanie ~7×; 12 przypomina liczbę **zaparkowanych pojazdów**, nie stanowisk |
| 51 | MOP Złotoria: miejsca TIR | 8 (ESTIMATED, `mop.json:61`) | **≥ 40** (ESTIMATED): kilka rzędów oznakowanych stanowisk dla zestawów; na zdjęciu stoi dokładnie 8 ciężarówek | WMS ortofoto, obrys way 916677534 | NIE | j.w. — policzone pojazdy, nie miejsca. Dodatkowo (poza próbą): w obrysie MOP jest `amenity=fuel` (way 906614318) przy `fuel_on_site: false` (`mop.json:64`) |
| 54 +D | Znak node 3054467143 | `PL:A-2` (`signs.json:29`) | `traffic_sign=PL:A-2`, `direction=forward`, `side=right` | OSM-bbox | TAK | — |
| 55 | Znak node 3012179430 | `PL:B-18` + `maxweight=10` (`signs.json:119`) | `traffic_sign=PL:B-18`, `maxweight=10`, `direction=backward`, `side=both` | OSM-bbox | TAK | — |
| 64 | Znaczenie znaku A-2 | „wjazd na pas awaryjny? — zakaz postoju/wjazdu” (`SIGNS.md:13`) | A-2 = **„niebezpieczny zakręt w lewo”** (znak ostrzegawczy) | Dz.U. 2019 poz. 2310, § 4 ust. 1 pkt 2 | NIE | błędna interpretacja przepisu; w grze dałoby zły znak |
| 66 | Cel way/984881124 | `landuse=industrial`, 17 529 m² (`destinations.json:67`) | `landuse=industrial`, 17 529 m² | OSM-bbox (pole w EPSG:2180) | TAK | — |
| 72 | Cel way/587232560 | `man_made=silo`, 511 m² (`destinations.json:986`) | `man_made=silo`, `building=yes`, 511,1 m² | OSM-bbox | TAK | — |
| 73 | Liczba celów | 68 w kaflach + 83 w pierścieniu = 151 (`RAPORT.md:11`) | w kaflach: `landuse=industrial` 25, `amenity=fuel` 4, `landuse=quarry` 1, `man_made=silo` 1 — **identycznie** jak w pliku; reszta (hale 31, zakłady 5, sklepy 2) bez jawnego kryterium | OSM-bbox, centroid w bbox kafla | CZĘŚCIOWO | 31/68 potwierdzone; kryterium „hala/zakład/cel dostaw” nieopisane → reszta niesprawdzalna bez definicji |
| 78 | S8: pas dzielący + bariera | bariera stalowa; „~4–4,8 m” (`xsec/README.md:30`, `RAPORT.md:8`), ale też „~5,27 m” (`xsec/README.md:20`); bariera `xsec/README.md:21` | bariera stalowa (prowadnica) — potwierdzona na 3 wycinkach; 8 stacji (seed 20261116): odstęp krawędzi asfaltu 3,45–4,0 m (med. 3,6), odstęp wewn. linii krawędziowych 3,8–4,85 m (med. ~4,5) | WMS ortofoto, 8 stacji S8 co 1,5 km | CZĘŚCIOWO | bariera i zakres 4–4,8 m zgodne; wartość 5,27 m (oś–oś − 7,0) zawyżona o ~0,8 m — dwie sprzeczne liczby w jednym pliku |
| 79 | DW671: mediana szerokości asfaltu | 7,4 m (`xsec/README.md:13`) | **6,95 m** (15 własnych stacji, seed 20261116; bez wylotów skrzyżowań 6,9) | WMS ortofoto | NIE | 7,4 to surowa mediana z wlotami skrzyżowań; mediana „czystych” stacji Mistrala (6,0–7,6 m) = 6,95 — zgodna ze mną. Raportowana liczba przeszacowana o 0,45 m |
| 81 | Stacja S8 way 98599908 s=25 | 10,65 m (`xsec/s8.json:7`) | 10,65 m (asfalt jezdni + pobocze, na obiekcie mostowym; między liniami krawędziowymi ~7,4 m) | WMS ortofoto (764679,8; 596090,6) | TAK | stacja leży na wiadukcie (krawężniki/bariery) — opisane w `xsec/README` jako typowy przekrój, a nie jest typowe |
| 82 | Stacja S8 way 100133887 s=525 | 10,35 m (`xsec/s8.json:56`) | 10,35 m (wzrokowo 10,3–10,9; wąska opaska wewn. ~0,5 m) | WMS ortofoto (761861,5; 595874,3) | TAK | — |
| 84 | Stacja DW671 way 97647194 s=275 | 6,95 m (`xsec/dw671.json:29`) | 6,85 m (wzrokowo 6,8) | WMS ortofoto (750913,2; 594962,6) | TAK | — |
| 86 | Stacja DK64 way 183373471 s=275 | 6,95 m (`xsec/dk64.json:51`) | 6,9 m (profil: szary od −3,5 do +3,6 → ~7,1) | WMS ortofoto (748811,0; 592527,5) | TAK | linie krawędziowe przerywane (P-7b), ~0,6 m utwardzenia za nimi |
| 87 | Stacja łącznicy way 183381865 s=25 | 7,85 m (`xsec/s8_links.json:7`) | 7,95 m (1 pas ~5,75 m między liniami + utwardzenia) | WMS ortofoto (758237,4; 594769,6) | TAK | — |

## 4. Wynik

- **Próba losowa (25)**: TAK **15/25 (60 %)**, CZĘŚCIOWO 4 (#27, #32, #73, #78), NIE 6 (#26, #41, #46, #51, #64, #79).
- **Z doborem (27)**: TAK 16, CZĘŚCIOWO 4, NIE 7 (dodatkowo #14 NIE, #54 TAK).
- Według kategorii: tagi OSM (ograniczenia, znaki jako tagi, cele, nazwy węzłów) — 100 % zgodne (to kopia OSM); pojedyncze stacje przekrojów — 5/5 zgodne; **interpretacje/wyprowadzenia** (typ węzła, długość łącznicy, miejsca TIR, znaczenie znaku, mediany, odległość MOP) — prawie wszystkie błędne lub częściowe.

### Typy błędów (systematyczne)

1. **Topologia węzłów S8 (systematyczny, krytyczny dla D63)**: wszystkie 5 węzłów opisane jako „półwęzeł/trąbka, 2 łącznice — jedna para”; w OSM każdy ma 4 punkty styku z S8 (2 wyjazdy + 2 wjazdy) i 7–33 way łącznic. Przyczyna: liczono tylko way wychodzące z noda `motorway_junction`. Węzeł Białystok Zachód łączy się z DK8/DK65 (trunk), a nie z „Warszawską”.
2. **„Długość łącznicy” = długość pierwszego way OSM** (łącznice OSM są pocięte na wiele way); faktyczne odcinki do rozwidlenia 2–3× dłuższe.
3. **Miejsca TIR na MOP** — prawdopodobnie zliczone pojazdy, nie stanowiska (Złotoria: 8 = liczba stojących ciężarówek); niedoszacowanie 5–8×. `fuel_on_site: false` przy stacji paliw w obrysie MOP Złotoria.
4. **Statystyki przekrojów bez filtra „czystych” stacji** (inaczej niż ADR 0272): mediana DW671 7,4 zamiast 6,95; pas dzielący podany dwiema sprzecznymi wartościami (4–4,8 i 5,27 m).
5. **Interpretacja przepisów**: A-2 źle zinterpretowany; błędna jednostka redakcyjna dla 120 km/h w PoRD.
6. **Konwencja L/R w `xsec/*.json` odwrócona** (poza próbą, z kodu i pomiaru): w `measure_loop_xsec.py` wektor `n = (−t_y, t_x)` wskazuje **w lewo**, a wartości dodatnie zapisano jako `_R`; pomiar potwierdza — szerokie pobocze awaryjne S8 wychodzi u Mistrala jako „L” (np. `asphalt_L = −6,35` w #81), a leży po prawej stronie kierunku jazdy. README deklaruje „L = lewo, ujemne” — sprzeczne z kodem.
7. **Niespójności wewnętrzne** (poza próbą): `mop.json` vs `destinations.json` dla tych samych stacji paliw (`dist_to_loop_road_m` 128,6 vs 16,1 dla way/1131537015; 87,4 vs 6,2 dla way/1385343897; 56,8 vs 7,9 dla way/301402242); „odległość od osi S8” to w praktyce odległość od najbliższej jezdni.

Dobre strony: surowe tagi OSM przepisane wiernie (prędkości, `maxspeed:hgv`, opłaty, znaki, cele, pola powierzchni co do m²), pojedyncze pomiary szerokości z ortofoto zgodne ±0,1 m, brak zmyślonych źródeł, statusy ESTIMATED/UNVERIFIED stosowane.

## 5. Czy budować kafle wg D63?

**Werdykt: najpierw poprawić** (dla węzłów i MOP); część przekrojowa i tagi OSM nadają się już teraz.

- D63 stawia na pierwszym miejscu wierność sieci drogowej: układ węzłów, wjazdy/zjazdy, łącznice. `junctions.json` w obecnym stanie dałby **półwęzły zamiast pełnych węzłów** na każdym z 5 węzłów — tego nie wolno brać jako wejścia.
- Generator kafli i tak czyta geometrię z OSM (`raw/osm/loop_roads.json`), więc **sieć dróg z OSM jest OK**; błędne są warstwy interpretacyjne (typy, długości, MOP).
- Szerokości: pojedyncze stacje są wiarygodne, ale mediany per grupa trzeba przeliczyć z filtrem „clean” (ADR 0272) i poprawić konwencję L/R przed użyciem do asymetrii pobocza (pas awaryjny po złej stronie byłby widocznym błędem).

### Lista poprawek przed budową (dla Mistrala / lidera)

1. `junctions.json`: przeliczyć typ każdego węzła z pełnej topologii `motorway_link` (wszystkie łącznice w promieniu ~1,5 km, liczba i kierunek styków z jezdniami S8, droga poprzeczna z faktycznego styku łącznic; Białystok Zachód → DK8/DK65, Tykocin → rondo). Usunąć „półwęzeł” dla wszystkich 5.
2. `junctions.json`: długość łącznicy = łańcuch way `motorway_link` od rozwidlenia z S8 do drogi poprzecznej (lub do rozwidlenia), z listą way; nie pojedynczy way.
3. `mop.json`: policzyć **stanowiska** (linie malarskie) na obu MOP, osobno TIR / osobowe; poprawić `fuel_on_site` (Złotoria: stacja w obrysie); ujednolicić odległość (centroid pola → oś między jezdniami) i zgrać z `destinations.json`.
4. `xsec/`: naprawić etykiety L/R w `measure_loop_xsec.py` i w danych (lub jawnie zmienić definicję w README); mediany per grupa liczyć z filtrem „clean”; usunąć sprzeczność 5,27 vs 4–4,8 m (pomiar: odstęp linii krawędziowych ~4,5 m, trawa ~3,6 m); oznaczyć stacje na obiektach mostowych.
5. `SIGNS.md`: poprawić A-2 (niebezpieczny zakręt w lewo) i podstawę 120 km/h (art. 20 ust. 3 pkt 1 lit. b PoRD).
6. `destinations.json`: opisać kryteria klas `hall`/`works`/`retail_delivery` (tag → klasa), żeby liczba 151 była odtwarzalna.

## 6. Licencje i źródła

- **Brak niedozwolonych źródeł**: w pakiecie nie ma danych z Google/Street View/Earth/3D Tiles, Bing, Apple, Yandex; Mapillary nie był używany (brak tokena — uczciwie UNVERIFIED). Google itd. występują tylko w zdaniach „nie używano”.
- Panoramax (CC BY 4.0) użyty tylko do sprawdzenia pokrycia, żadne dane nie trafiły do pakietu — bez ryzyka, ale poza listą źródeł tego QA.
- Wpis w `docs/LICENSES.md` jest (sekcja „Pakiet research `research/mistral-s8-loop-s23`”: ODbL / GUGiK / Dz.U.).
- **Drobne przecieki marek** wbrew deklaracji „bez marek”: `destinations.json:1671` zawiera tag OSM `name:ru` z nazwą sieci handlowej; `destinations.json:3031` — `source:addr` z nazwą aplikacji nawigacyjnej. Usunąć przed budową (filtr tagów `name*`, `brand*`, `operator*`, `source*`).
- Kod i dane przekrojów: żadnego piksela ortofoto w repo — zgodne z deklaracją.

## Załącznik A — katalog 93 faktów (indeksy do losowania)

| i | kat. | fakt | wartość Mistrala | R/plik:linia |
|---|---|---|---|---|
| 0 | lim | S8: maxspeed=120 na wszystkich way S8 | 120 (99/99) | `SIGNS.md:10` |
| 1 | lim | S8: maxspeed:hgv=80 | 80 (99/99) | `SIGNS.md:10` |
| 2 | lim | S8: toll:hgv=yes | 95/99 way | `SIGNS.md:10` |
| 3 | lim | PoRD art. 20: 80 km/h na drodze ekspresowej poza obsz. zabud. dla >3,5 t (Dz.U. 2024 poz. 1251, ust. 3 pkt 2 lit. a) | 80 km/h, art. 20 ust. 3 pkt 2 lit. a | `SIGNS.md:22` |
| 4 | lim | PoRD art. 20: >3,5 t na drodze jednojezdniowej poza zabud. 70 km/h (ust. 3 pkt 2 lit. b) | 70 km/h | `SIGNS.md:22` |
| 5 | lim | Dz.U. 2022 poz. 1518 § 17 ust. 1 pkt 2: szerokość pasa ruchu klasy S | 3,50 m | `SIGNS.md:26` |
| 6 | lim | Liczba way tertiary z maxweight=10 przy Choroszczy | 6 | `SIGNS.md:14` |
| 7 | lim | Łącznica 424138211 (Białystok Zachód) maxspeed | 60 | `junctions.json:48` |
| 8 | lim | Łącznica 183639802 (Choroszcz) maxspeed | 40 | `junctions.json:118` |
| 9 | lim | Łącznice 183381873/183381877 (Jeżewo): brak maxspeed w OSM | brak | `junctions.json:186` |
| 10 | lim | S8: lanes=2 na 68 way, lanes=3 na 31 | 2:68 / 3:31 | `SIGNS.md:10` |
| 11 | lim | Dz.U. 2019 poz. 2310 § 27 ust. 1: powtórzenie B-33 po skrzyżowaniu | § 27 ust. 1 | `SIGNS.md:24` |
| 12 | jun | Węzeł Białystok Zachód: nazwa węzła (motorway_junction) | Białystok Zachód | `junctions.json:7` |
| 13 | jun | Węzeł Białystok Zachód: droga poprzeczna (nazwa/klasa) | Warszawska, tertiary | `junctions.json:38` |
| 14 | jun | Węzeł Białystok Zachód: typ 'półwęzeł/trąbka (2 łącznice — jedna para)' | półwęzeł/trąbka, 2–3 łącznice | `junctions.json:35` |
| 15 | jun | Węzeł Choroszcz: nazwa węzła (motorway_junction) | Choroszcz | `junctions.json:80` |
| 16 | jun | Węzeł Choroszcz: droga poprzeczna (nazwa/klasa) | tertiary | `junctions.json:101` |
| 17 | jun | Węzeł Choroszcz: typ 'półwęzeł/trąbka (2 łącznice — jedna para)' | półwęzeł/trąbka, 2–3 łącznice | `junctions.json:99` |
| 18 | jun | Węzeł Jeżewo: nazwa węzła (motorway_junction) | Jeżewo | `junctions.json:134` |
| 19 | jun | Węzeł Jeżewo: droga poprzeczna (nazwa/klasa) | ref 671, secondary | `junctions.json:160` |
| 20 | jun | Węzeł Jeżewo: typ 'półwęzeł/trąbka (2 łącznice — jedna para)' | półwęzeł/trąbka, 2–3 łącznice | `junctions.json:157` |
| 21 | jun | Węzeł Rzędziany: nazwa węzła (motorway_junction) | Rzędziany | `junctions.json:190` |
| 22 | jun | Węzeł Rzędziany: droga poprzeczna (nazwa/klasa) | tertiary | `junctions.json:211` |
| 23 | jun | Węzeł Rzędziany: typ 'półwęzeł/trąbka (2 łącznice — jedna para)' | półwęzeł/trąbka, 2–3 łącznice | `junctions.json:209` |
| 24 | jun | Węzeł Tykocin: nazwa węzła (motorway_junction) | Tykocin | `junctions.json:241` |
| 25 | jun | Węzeł Tykocin: droga poprzeczna (nazwa/klasa) | tertiary | `junctions.json:262` |
| 26 | jun | Węzeł Tykocin: typ 'półwęzeł/trąbka (2 łącznice — jedna para)' | półwęzeł/trąbka, 2–3 łącznice | `junctions.json:260` |
| 27 | len | Długość łącznicy way 424138211 (Białystok Zachód) | 126.7 m | `junctions.json:46` |
| 28 | len | Długość łącznicy way 1151440414 (Białystok Zachód) | 120.1 m | `junctions.json:54` |
| 29 | len | Długość łącznicy way 1151531629 (Białystok Zachód) | 127.0 m | `junctions.json:62` |
| 30 | len | Długość łącznicy way 183639800 (Choroszcz) | 116.8 m | `junctions.json:109` |
| 31 | len | Długość łącznicy way 183639802 (Choroszcz) | 230.9 m | `junctions.json:116` |
| 32 | len | Długość łącznicy way 183381873 (Jeżewo) | 119.1 m | `junctions.json:168` |
| 33 | len | Długość łącznicy way 183381877 (Jeżewo) | 80.7 m | `junctions.json:175` |
| 34 | len | Długość łącznicy way 183381867 (Rzędziany) | 136.0 m | `junctions.json:219` |
| 35 | len | Długość łącznicy way 183381879 (Rzędziany) | 126.8 m | `junctions.json:226` |
| 36 | len | Długość łącznicy way 183382930 (Tykocin) | 181.4 m | `junctions.json:270` |
| 37 | len | Długość łącznicy way 536211867 (Tykocin) | 145.0 m | `junctions.json:277` |
| 38 | len | S8 w 15 kaflach: 71 way, 43,1 km jezdni (oś ~21,2 km) | 43,1 km / 21,2 km | `RAPORT.md:9` |
| 39 | len | way 888490257 (tertiary maxweight=10) długość | 676.8 m | `signs.json:1929` |
| 40 | len | way 297342246 (tertiary maxweight=10) długość | 518.9 m | `signs.json:1998` |
| 41 | len | MOP Radule: odległość od osi S8 | 134.9 m | `mop.json:22` |
| 42 | len | Kafel s8-01: bbox xmin=766731 (ADR 0203: 776971+2048·i, i=−5) | 766731 | `tiles.json:24` |
| 43 | mop | MOP Radule: way 222577666, highway=services, name | services, 'Miejsce Obsługi Podróżnych Radule' | `mop.json:8` |
| 44 | mop | MOP Radule: powierzchnia obszaru | 40582 m² | `mop.json:21` |
| 45 | mop | MOP Radule: toilets=yes | yes | `mop.json:26` |
| 46 | mop | MOP Radule: miejsca TIR (orto) | 12 | `mop.json:30` |
| 47 | mop | MOP Radule: brak stacji paliw na MOP | fuel_on_site=false | `mop.json:33` |
| 48 | mop | MOP Radule: strona S8 | północna | `mop.json:34` |
| 49 | mop | MOP Złotoria: way 916677534 highway=rest_area, nazwa 'MOP Złotoria' | rest_area, 'MOP Złotoria' | `mop.json:40` |
| 50 | mop | MOP Złotoria: powierzchnia | 38752 m² | `mop.json:53` |
| 51 | mop | MOP Złotoria: miejsca TIR (orto) | 8 | `mop.json:61` |
| 52 | mop | MOP Złotoria: odległość od osi S8 | 95.8 m | `mop.json:54` |
| 53 | mop | Stacja paliw way/301402242 (Jeżewo) — amenity=fuel, dist do drogi pętli | 56.8 m (mop.json) / 7.9 m (destinations.json) | `mop.json:89` |
| 54 | sign | Węzeł traffic_sign 3054467143 | PL:A-2 | `signs.json:29` |
| 55 | sign | Węzeł traffic_sign 3012179430 | PL:B-18 + maxweight=10 | `signs.json:119` |
| 56 | sign | Węzeł traffic_sign 2329859397 | maxspeed 60 | `signs.json:6` |
| 57 | sign | Węzeł traffic_sign 3054505447 | overtaking=no | `signs.json:51` |
| 58 | sign | Węzeł traffic_sign 3012412413 | maxspeed 50 | `signs.json:74` |
| 59 | sign | Węzeł traffic_sign 2240228458 | maxspeed 40 | `signs.json:96` |
| 60 | sign | Węzeł traffic_sign 3052003097 | PL:B-16 maxheight=3.7 | `signs.json:209` |
| 61 | sign | Węzeł traffic_sign 3052178769 | PL:B-18 maxweight=12 | `signs.json:253` |
| 62 | sign | Węzeł traffic_sign 3012179734 | maxspeed 50 | `signs.json:142` |
| 63 | sign | Liczba węzłów traffic_sign w 15 kaflach | 6 | `SIGNS.md:13` |
| 64 | sign | Znaczenie PL:A-2 (node 3054467143) wg Mistrala | 'wjazd na pas awaryjny? — zakaz postoju/wjazdu' | `SIGNS.md:13` |
| 65 | dest | Cel way/301110038 | building=industrial, 1467 m² | `destinations.json:7` |
| 66 | dest | Cel way/984881124 | landuse=industrial, 17529 m² | `destinations.json:67` |
| 67 | dest | Cel way/202427726 | landuse=quarry (żwirownia), 93822 m² | `destinations.json:98` |
| 68 | dest | Cel way/1527436046 | landuse=industrial + wastewater_plant, 3478 m² | `destinations.json:127` |
| 69 | dest | Cel node/3804148383 | shop=doityourself (cel dostaw) | `destinations.json:159` |
| 70 | dest | Cel way/1210174179 | man_made=silo, 112 m² | `destinations.json:3131` |
| 71 | dest | Cel way/906614318 | amenity=fuel, 2592 m², 24/7 | `destinations.json:4153` |
| 72 | dest | Cel way/587232560 | man_made=silo, 511 m² | `destinations.json:986` |
| 73 | dest | Liczba celów: 68 w kaflach + 83 w pierścieniu = 151 | 151 | `RAPORT.md:11` |
| 74 | dest | Strefa przemysłowa s8-01 ~47 ha 'wg planu' | ~47 ha | `RAPORT.md:11` |
| 75 | dest | Podwórza gospodarstw: 348, 266,8 ha | 348 / 266,8 ha | `destinations.json:4752` |
| 76 | xsec | S8 jezdnia 2-pas: mediana asfaltu (asfalt jezdni+pobocza) | 10,45 m (README) / 10,35 (RAPORT) | `xsec/README.md:11` |
| 77 | xsec | S8 oś–oś jezdni: mediana | 12,27 m | `xsec/README.md:19` |
| 78 | xsec | S8 pas dzielący z barierą stalową | bariera stalowa, ~4–5,3 m | `xsec/README.md:21` |
| 79 | xsec | DW671 asfalt mediana | 7,4 m | `xsec/README.md:13` |
| 80 | xsec | DK64 (way 183373471) asfalt mediana | 6,93 m | `xsec/summary.json:29` |
| 81 | xsec | Stacja s8 way 98599908 s=25.0: szerokość asfaltu | 10.65 m | `xsec/s8.json:7` |
| 82 | xsec | Stacja s8 way 100133887 s=525.0: szerokość asfaltu | 10.35 m | `xsec/s8.json:56` |
| 83 | xsec | Stacja s8 way 100133887 s=1025.0: szerokość asfaltu | 10.7 m | `xsec/s8.json:81` |
| 84 | xsec | Stacja dw671 way 97647194 s=275.0: szerokość asfaltu | 6.95 m | `xsec/dw671.json:29` |
| 85 | xsec | Stacja dw671 way 97647194 s=525.0: szerokość asfaltu | 6.8 m | `xsec/dw671.json:51` |
| 86 | xsec | Stacja dk64 way 183373471 s=275.0: szerokość asfaltu | 6.95 m | `xsec/dk64.json:51` |
| 87 | xsec | Stacja s8_links way 183381865 s=25.0: szerokość asfaltu | 7.85 m | `xsec/s8_links.json:7` |
| 88 | set | Miejscowość node/3009678168: nazwa i place | Pławuli (hamlet) | `settlements.md:16` |
| 89 | set | Miejscowość node/13574089261: nazwa i place | Szulaki (locality) | `settlements.md:17` |
| 90 | set | Miejscowość node/3009675761: nazwa i place | Nowosiółki (neighbourhood) | `settlements.md:13` |
| 91 | set | Miejscowość node/31578128: nazwa i place | Babino (village) | `settlements.md:18` |
| 92 | set | Miejscowość node/31571573: nazwa i place | Jeżewo Stare (village) | `settlements.md:26` |

Kategorie: `lim` ograniczenia/przepisy, `jun` węzły, `len` długości, `mop` MOP, `sign` znaki, `dest` cele ciężarówek, `xsec` przekroje, `set` miejscowości. Wpisy `jun` „typ … 2 łącznice” mają wartość zbiorczą „2–3 łącznice” (Białystok Zachód ma 3 wpisy `ramps`).

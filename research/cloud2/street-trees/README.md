# R5 — drzewa uliczne Białegostoku: liczby do generatora zieleni (cloud2 / street-trees)

Data: 2026-11-14 · gałąź: `research/cloud2-street-trees` · wiersze manifestu: **210** ·
obejrzane kadry: **54** (KartaView 18, Panoramax 10, Commons 26; trasa C 22, Dojlidy 10, osiedla/śródmieście 22) + 1 wykres + 7 dokumentów PDF ·
samokontrola: **42/42 PASS, 0 FAIL** (seed 20261114; w tym 1 PASS po korekcie opisu kadru R5-180).
Pakiet przerwany na polecenie lidera (limit sesji) — zbieranie zakończone na stanie opisanym niżej, luki na końcu.

## Cel i metoda
Liczby dla generatora zieleni: gatunki, wymiary wg wielkości pnia/wieku, rozstaw szpalerów, odsunięcie od krawężnika, żywopłoty, kalendarz sezonowy.
Nie powtarzam G7 (`research/g7-street-greenery`), P10 (`research/gptpro/p10-street-greenery-2`) ani M51 (`research/mistral/p10-greenery-3`) — cytuję je i uzupełniam luki.
- **OSM**: Overpass był nieosiągalny przez proxy (17:05–17:10 UTC, 3 serwery) → ekstrakt PBF woj. podlaskiego (openstreetmap.fr, stan 2026-11-13T01:06Z) + pyosmium; zapytanie równoważne w `tools/q_trees.overpassql`. Wyniki: `data/osm_*.json`, `data/row_spacing.json`.
- **Dokumenty**: Łaska 2015 (Tab. 1 i 3 w całości), NIK LBI.403.7.2023, BIP DGK-IV.271.2.2017 (zał. 2 i 3), „Zieleń w Białymstoku 2019”, Dz.U. 2022 poz. 1518, Dz.U. 2016 poz. 124.
- **Allometria**: surowe pomiary USDA Urban Tree Database (doi:10.2737/RDS-2016-0005) zagregowane własnym skryptem wg klas obwodu (jak u Łaski) i wieku.
- **Kadry**: każdy obejrzany (≤ 960 px); kierunek = `heading` KartaView / `view:azimuth` Panoramax, Commons = UNVERIFIED; ulica = najbliższa oś OSM + odległość.

## Wyniki — tabele dla generatora
Indeks wierszy manifestu wg kategorii: osm: R5-001–010; szpaler: R5-011–021, 045–046, 207, 209; gatunki: R5-022–038, 047–049, 054–062, 065–072; wymiary: R5-039–044, 050–053, 081–128, 206, 208; zywoplot: R5-063–064, 129–134, 199–205; przepisy: R5-073–080; fenologia: R5-135–144, 210; kadr: R5-145–198. Każda liczba w tabelach ma wiersz w `manifest.csv` (kolumna `przedmiot`).

### 1. Gatunki (drzewa przy głównych ulicach; Łaska 2015, inwentaryzacja 2011, 4 transekty, 606 drzew)
| Gatunek | szt. | udział | uwaga |
|---|---|---|---|
| klon zwyczajny | 295 | 48,7 % | dominant, także samosiewy |
| klon jesionolistny | 53 | 8,7 % | tylko Andersa i Raginisa (nasadzenia) |
| lipa drobnolistna | 49 | 8,1 % | najwyższe w rzędach (16–17 m) |
| śliwa domowa | 31 | 5,1 % | drzewka owocowe przy posesjach |
| żywotnik | 30 | 5,0 % | tylko Raginisa (posesje) |
| brzoza brodawkowata | 21 | 3,5 % | |
| klon jawor | 20 | 3,3 % | |
| klon tatarski | 16 | 2,6 % | tylko Andersa |
| jabłoń | 14 | 2,3 % | |
| wierzba krucha | 11 | 1,8 % | |
| jesion wyniosły | 8 | 1,3 % | **korekta P10-004** (tam 35) |
| jarząb pospolity | 8 | 1,3 % | |
| robinia | 7 | 1,2 % | |
| pozostałe 12 taksonów | 43 | 7,1 % | sosna, dąb czerwony, topole, świerki… |

Transekt **Andersa (trasa C)**, 133 drzewa: klon jesionolistny 26 %, klon zwyczajny 23 %, klon tatarski 12 %, brzoza 11 %, śliwa 8 %, jarząb 6 %, jesion 5 %, topola balsamiczna 4 %.
Miasto **nie ma inwentaryzacji** i nie ewidencjonuje gatunków → udziały powyżej to jedyne liczby; reszta to paleta dopuszczona do nasadzeń: lipy (drobnolistna, ‘Green Spire’, srebrzysta), klony (zwyczajny w odmianach, kulisty, jawor, polny, tatarski), jesiony (wyniosły, pensylwański), kasztanowce, jarzęby (pospolity, **szwedzki**), robinia tylko kulista, dęby, grusza ‘Chanticleer’, głóg, grab ‘Fastigiata’. **Platan: brak wszędzie — nie generować.**
OSM: 2549 drzew, ale `species` ma 3,2 % (głównie dęby-pomniki) — bezużyteczne do udziałów. Trasa C: 1 drzewo, Dojlidy: 5 bez gatunku.
Proponowany miks szpalerów ulicznych (WORKING_VALUE z tabeli + palety): klon zwyczajny 45 %, lipa drobnolistna 20 %, klon jesionolistny 8 % (tylko stare rzędy), jesion 7 %, brzoza 5 %, jawor 5 %, jarząb 5 %, kasztanowiec 3 %, robinia 2 %.

### 2. Wymiary
Stan faktyczny przy ulicach: wysokość 0–2 m 4,7 % · 2,1–5 m 32,7 % · **5,1–10 m 53,8 %** · 10,1–15 m 3,5 % · 15,1–20 m 5,3 %; obwód 0–50 cm 24 % · **51–100 cm 56 %** · 101–150 cm 13,5 % · > 150 cm 6,5 %.
Wysokość / średnica korony wg obwodu pnia:
| obwód cm | lipa drobnol. | klon zwycz. | jesion (pens.) | brzoza | robinia | kasztanowiec | klon jesionol. |
|---|---|---|---|---|---|---|---|
| 0–50 | 5,5 / 2,5 | 5,0 / 3,3 | 7,2 / 4,3 | 8,0 / 4,4 | 5,8 / 3,8 | 5,0 / 3,1 | — |
| 51–100 | 9,5 / 7,1 | 9,5 / 8,0 | 11,0 / 8,2 | 12,8 / 6,7 | 11,5 / 6,2 | — | 13,0 / 7,8 |
| 101–150 | 14,0 / 9,9 | 12,0 / 11,0 | 14,2 / 11,2 | 17,5 / 8,9 | 13,0 / 9,5 | 11,0 / 7,2 | 15,0 / 8,7 |
| 151–200 | 16,0 / 11,6 | 14,8 / 12,4 | 18,0 / 13,9 | 21,0 / 12,9 | 16,0 / 11,8 | — | 15,0 / 12,0 |
| 201–300 | 19,8 / 13,5 | 18,8 / 15,1 | 21,0 / 16,6 | — | 23,0 / 10,5 | 16,0 / 12,3 | 19,0 / 15,9 |

Klasa wieku → klasa obwodu: nowe nasadzenie (0–5 lat) obwód 14–16 cm, H 4–5 m, korona od 1,8–2,0 m, 3 paliki 1,5 m; młode (5–20 lat) 0–50 cm; średnie (20–40) 51–100 cm; dojrzałe (40–70) 101–200 cm; stare > 200 cm.
Lipowa (szpaler stożkowych lip w chodniku): H 8–9,5 m, korona 3,7–4,2 m, podstawa korony 2,5–3,5 m. Skrajnia: gałęzie ≥ 4,5 m nad jezdnią, ≥ 2,5 m nad chodnikiem. Jarząb szwedzki: brak danych.

### 3. Rozstaw i odsunięcie
| Parametr | Wartość |
|---|---|
| odstęp w szpalerze (800 odstępów, 111 rzędów OSM) | mediana **7,1 m**; p10 4,3; p90 15,6 |
| wg klasy ulicy (mediana rzędów) | lokalne 8,3 m · zbiorcze 7,0 m · główne 8,1 m |
| Lipowa / Św. Ojca Pio | 6,7–6,9 m / 4,4–4,6 m |
| pień od osi jezdni | mediana 6,3 m (p10 4,0; p90 11,4) |
| pień od krawężnika (oszac.) | mediana **2,5 m**; p25 1,5; p75 4,0; Lipowa ok. 1,0 m (w chodniku, krata + osłona) |
| przepisy | do 20.09.2022: pień ≥ 3,0 m od krawędzi jezdni, pas zieleni ≥ 3,0 m (§ 53); od 21.09.2022 (poz. 1518) **brak liczby** — tylko strefa bez przeszkód przy > 50 km/h (§ 26) |
| trasa C | 0 rzędów w OSM; 3 z 22 kadrów letnich mają rząd młodych drzew, zawsze za ścieżką/trawnikiem; w 2011: rzędy 2/10/15 m od jezdni |
| pielęgnacja 2017: Andersa 228 drzew, Maczka–Putry–Tysiąclecia 527 | gatunków brak |

### 4. Żywopłoty
| Parametr | Wartość |
|---|---|
| ‘Smaragd’ (10 lat) | 2,5 m × 0,7 m; sadzenie co 0,5–0,6 m |
| ‘Brabant’ (10 lat) | 3,5 m × 1,5 m; co 0,6–0,8 m; stare > 15 m |
| ligustr | krzew 2–3 m, strzyżony do 2,5 m |
| fronty domów (11 kadrów) | żywotnik 3 (27 %) · liściasty 3 (27 %) · luźne wysokie iglaki 2 (18 %) · brak 3 (27 %) |
| wysokości z kadrów | żywotnik: młody rząd 1,2–1,8 m, ściana 2,0–3,0 m; liściasty 1,5–3 m; rozstaw młodych tui w terenie 0,9–1,4 m |
Zgodne z G7 #15–19 (40 % × 70 % tuja = 28 %); żywopłoty liściaste latem wyższe niż G7 #20.

### 5. Kalendarz sezonowy
| Zjawisko | DOY (data) | status |
|---|---|---|
| pierwsze liście (brzoza) | 108 (18 IV), pudełko 103–113 | ESTIMATED z wykresu, Polska 2007–2014 |
| kwitnienie kasztanowca | 124 (4 V) | jw. |
| kwitnienie robinii | 145 (25 V) | jw. |
| kwitnienie lip | 171 (20 VI), 166–179 | jw. |
| przebarwianie kasztanowca / brzozy | 271 (28 IX) / 282 (9 X) | jw. |
| opad liści brzozy | 301 (28 X) | SOURCED (tekst) |
Kadry Białegostoku: 13 III gołe · 7–9 V liście młode · 20–22 V pełne · 4 X lipy jeszcze zielone · 6–11 XI gołe. Robocze stany gry: bezlistny 5 XI–20 IV, rozwój 20 IV–15 V, lato 15 V–25 IX, jesień 25 IX–5 XI (WORKING_VALUE).

## Co już było w repo / co nowe
| Temat | Było | Nowe w R5 |
|---|---|---|
| gatunki | G7: WORKING_VALUE; P10: sumy Łaski | pełna Tab. 1 z udziałami, korekta jesionu, paleta UM 2017, NIK: brak inwentaryzacji |
| wymiary | G7: sufity Ebben, 4 drzewa SGGW | klasy wysokości/obwodu 171 drzew, tabela obwód→H/korona, specyfikacja nasadzeń |
| rozstaw | G7/M51: brak | pomiar 111 rzędów OSM, odsunięcia, przepisy stare/nowe |
| żywopłoty | G7/M51: wysokości z kadrów | dane szkółkarskie, udziały z 11 frontów (Dojlidy i in.) |
| sezon | brak | fenologia z publikacji + datowane kadry |

## Luki
1. Brak rejestru gatunków drzew ulicznych (potwierdzone przez NIK); dokumenty przetargowe 2020/2023 są na platformie ezamawiajacy (nie otwarto).
2. Fenologia: wartości ogólnopolskie, poprawka dla Białegostoku UNVERIFIED; daty z wykresu ±3 dni.
3. Allometria z USA; kalibracja wieku na jednym drzewie (WORKING_VALUE); brak jarzębu szwedzkiego; jesion = pensylwański.
4. Odsunięcie od krawężnika zależy od założonych szerokości jezdni (±1 m).
5. Dojlidy i trasa C: 0 szpalerów w OSM; Dojlidy bez kadrów z azymutem (Panoramax/KartaView puste) — tylko Commons, kierunek UNVERIFIED.
6. Grab i berberys: brak danych szkółkarskich; gatunki żywopłotów liściastych z kadrów nierozpoznane; próba frontów n = 11.
7. Standardy zieleni Białegostoku: nie znaleziono. Geosearch Commons dla Al. Piłsudskiego nie zwrócił wyników (limit API).
8. Numer paragrafu cytatu o widoczności (wiersz „Dz.U. 2022 poz. 1518 — liczbowa odległość drzew”) niepewny (strona 22 pewna).

## Jak używać w grze
Szpaler: rozstaw 7 m (4,5 m dla gęstych młodych, 8 m ulice lokalne), pień 2,5 m od krawężnika (1 m w chodniku śródmieścia, ≥ 3 m przy 70 km/h albo za ścieżką); gatunek z miksu p. 1; wymiary z tabeli p. 2 wg klasy obwodu losowanej z rozkładu Łaski; młode nasadzenia z 3 palikami. Trasa C: bez dojrzałych szpalerów, tylko krótkie rzędy młodych drzew za ścieżką i masy zadrzewień za barierami. Wszystkie wartości ESTIMATED/WORKING_VALUE oznaczyć jako `default` niskiej pewności.

Pliki: `manifest.csv`, `sources.md`, `fetch.py` (62 pliki, 33,6 MB, sha256), `audit_20_percent.json`, `STATUS.md`, `tools/`, `data/`. Zdjęcia i PDF w `files/` (poza gitem).

## Errata lidera (s20, 2026-11-14)
Patrz `docs/reports/REVIEW-2026-11-14-s20-cloud2-r5.md` — errata obowiązuje przed użyciem danych.

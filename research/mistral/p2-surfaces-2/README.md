# M52 — P2 surfaces 2 (znaki poziome P-*, nawierzchnie Białegostoku)

Paczka badawcza M52. Gałąź: `research/mistral-p2-surfaces-2`. Kontynuacja / uzupełnienie
`research/gptpro/p2-surfaces/` (M51/P2-001…P2-094) — **bez dublowania** tamtych ustaleń.

## Zakres (6 zadań)

1. Wymiary znaków poziomych **z rysunków** załącznika nr 2 do rozporządzenia w sprawie
   szczegółowych warunków technicznych dla znaków i sygnałów drogowych
   (jednolity tekst: Dz.U. 2019 poz. 2311; PDF z eli.gov.pl, część c2):
   P-2a/b, P-3a/b, P-4, P-5, P-6 (szerokości linii, odstęp linii podwójnych, kreska/przerwa),
   P-12, P-13, P-14, P-21a/b, P-23, P-25. Dla każdej wartości: **numer rysunku + strona Dz.U.**
   Źródła wtórne (blogi, tioman.pl) odrzucone jako niepotwierdzające.
2. Zdjęcia kafla startowego **Jaroszówka** (~53,152 N 23,168 E) z poziomu jezdni — ≥10 kadrów,
   data + azymut.
3. Zdjęcia + wymiary: **azyle** (wyspy dzielące), **płytki dotykowe** (układ rzędów),
   **ścieki przykrawężnikowe i wpusty** — Białystok.
4. **Kolor dróg i pasów rowerowych** na trasie startowej (Andersa, Al. Tysiąclecia, Sokólska,
   Wileńska): gdzie czerwony asfalt, gdzie pas malowany na szarym asfalcie — pozycje + zdjęcia.
5. **Rynek Kościuszki**: rodzaj nawierzchni (kostka granitowa? wymiary, układ) — z dokumentu
   (projekt rewitalizacji, BIP) albo ESTIMATED ze zdjęcia z metodą.
6. Aktualny katalog standardów/wytycznych **ZDM/ZDiT Białystok** (nowszy niż
   „Wytyczne do projektowania” z 13.07.2018, BIP resource 99308) — link, data, zmiany.

## Ważna korekta względem starej paczki (P2)

**P-11 to PRZEJAZD DLA ROWERZYSTÓW** (szerokość 1,8 m jednokierunkowy / 3,0 m dwukierunkowy),
NIE „przebieg przejścia/azyl”. Potwierdzone tekstem rozporządzenia (Dz.U. 2019 poz. 2311,
zał. 2, rozdz. 4.2.2 — str. Dz.U. 569).

---

## Zadanie 1 — Wymiary znaków poziomych z rysunków zał. 2 (Dz.U. 2019 poz. 2311)

### Metodologia odczytu

PDF c2 (zał. 2) zawiera rysunki jako obrazy rastrowe (natywne 355–1054 px szer.).
Etykiety wymiarowe są częścią obrazu (brak ich w warstwie wektorowej). Odczyt programowy
(python + NumPy/scipy):

1. binaryzacja (ink > 90/60 w skali 8-bit),
2. detekcja komponentów glifów (connected components, `scipy.ndimage`),
3. klastrowanie glifów po znormalizowanej mapie bitowej (odległość Hamminga) — czcionka
   identyczna w obrębie rozdziałów; walidacja krzyżowa etykiet o wartościach znanych z tekstu
   (P-7a/b: 0,24 m; P-7c/d: 0,12 m — str. Dz.U. 545; P-10: 4,0 m — str. 567;
   P-11: 1,8/3,0 m — str. 569; tabela 5.3 dla P-21: str. 589),
4. odczyt per-piksel (ASCII-dump) dla glifów pojedynczych/ problematycznych,
5. weryfikacja skali: szerokości linii w pikselach vs wartości etykiet (np. P-3a: linia 12 px
   ↔ etykieta „0,12” → 0,010 m/px).

Mapowanie stron: **PDF c2 str. N = Dz.U. str. N+525**. Numeracja rysunków potwierdzona
podpisami wektorowymi pod figurami (np. „Rys. 2.2.1.6. Znak P-2a” — str. Dz.U. 536).

### Tabela linii P-* (wartości z rysunków; każda z numerem rysunku i stroną Dz.U.)

Nazwy znaków wg listy w pkt 2.2 (str. Dz.U. 531). Statusy: SOURCED (odczyt z rysunku
urządowego), ESTIMATED (metoda geometryczna), UNVERIFIED.

| Znak (nazwa wg str. 531) | Wymiar | Wartość | Rysunek | Str. Dz.U. | Status / metoda |
|---|---|---|---|---|---|
| P-2a „linia pojedyncza ciągła – wąska” | szerokość linii | **0,12 m** | 2.2.1.6 | 536 | SOURCED: etykieta wymiarowa (piksele: linia 12 px) + podpis dolny „0,12” |
| P-2b „linia pojedyncza ciągła – szeroka” | szerokość linii | **0,24 m** | 2.2.1.7 | 537 | SOURCED: etykieta + podpis dolny „0,24” (linia 22 px) |
| P-3a „linia jednostronnie przekraczalna – długa” | szerokość każdej linii | **0,12 m** | 2.2.1.8 | 538 | SOURCED: 3 etykiety „0,12” (glify [0][,][1][2]) przy wymiarówkach; linie 12 px |
| P-3a | odstęp osi linii podwójnej | **0,20 m** | 2.2.1.8 | 538 | SOURCED (podpis dolny „0,20”); pomiar pikselowy ~0,21 m (21 px × 0,010) — zgodny w granicach |
| P-3a | kreska / przerwa (linia ciągła strony z pierwszeństwem: brak; linia przerywana) | ~2,0–2,4 m / ~0,56–0,62 m | 2.2.1.8 | 538 | ESTIMATED: segmenty 224/244/171 px, przerwy 56/62 px (downsample ×2, thr 230); skala 0,010 m/px |
| P-3b „linia jednostronnie przekraczalna – krótka” | szerokość każdej linii | **0,12 m** | 2.2.1.9 | 539 | SOURCED: 3 etykiety „0,12” |
| P-3b | odstęp osi linii podwójnej | **0,18 m** | 2.2.1.9 | 539 | SOURCED (podpis dolny „0,18”, glif „8” potwierdzony wzorcem z P-6); pomiar pikselowy ~0,18–0,23 (pozycja drugiej linii zaszumiona kreszem) |
| P-4 „linia podwójna ciągła” | szerokość każdej linii | **0,12 m** | 2.2.1.10 | 540 | SOURCED: 3 etykiety „0,12” przy wymiarówkach |
| P-4 | odstęp osi linii podwójnej | **0,24 m** | 2.2.1.10 | 540 | SOURCED: podpis dolny „0,24” ([0][2][4]); geometria: [linia 10 px][przerwa 10 px][linia 10 px] → 0,12+0,12 osiowo = 0,24 ✓ |
| P-5 „linia podwójna przerywana” | szerokość każdej linii | **0,12 m** | 2.2.1.11 | 540 | SOURCED: 3 etykiety „0,12” (y225/y468/y677; glify dopasowane wzorcem do etykiet P-3a) |
| P-5 | odstęp osi linii podwójnej | **0,2 m** (podpis) | 2.2.1.11 | 540 | SOURCED (podpis dolny „0,2”, [0][,][2]); pomiar pikselowy ~0,21–0,23 m (linie x120–130 i x141–151) — zgodność przybliżona |
| P-5 | kreska / przerwa | ~1,77 m / ~0,91 m | 2.2.1.11 | 540 | ESTIMATED: segmenty lewej linii 162 px, przerwy dokładnie 83 px (y192→275, y436→519); skala 0,0109 m/px (linia 11 px = 0,12) |
| P-6 „linia ostrzegawcza” | szerokość linii | **0,12 m** | 2.2.1.12 | 541 | SOURCED: etykieta pozioma „0,12” (y493, [0][1][2]); linia 11 px |
| P-6 | przerwa | **2,00 m** | 2.2.1.12 | 541 | SOURCED: etykieta pionowa „2,00” przy wymiarówce obejmującej przerwę (86 px; rot −90°, glify [2][,][0][0]) |
| P-6 | kreska | **~4,00 m** | 2.2.1.12 | 541 | ESTIMATED: segmenty 172 px = 2 × przerwa 86 px (stosunek kreska:przerwa dokładnie 2:1 na rysunku) |
| P-6 | podpis dolny | „0,08” | 2.2.1.12 | 541 | SOURCED odczyt; UNVERIFIED semantyka (wartość nie pasuje ani do szerokości 0,12, ani do proporcji; rysunki zał. 2 są poglądowe) |
| P-12 „linia bezwzględnego zatrzymania – stop” | podpis dolny figury | **0,5 m** | 4.2.3.1 | 571 | SOURCED odczyt („0,5” + „m”); interpretacja: szerokość linii P-12 (na rys. grubość linii ~18 px przy skali figury ~36 px/m — spójne); semantyka oznaczona ostrożnie |
| P-12 | odległość od skrajnej szyny (przejazd tramwajowy) | ≥ **1,5 m** | 4.2.3.1 (tekst) | 572 | SOURCED: tekst rozporządzenia (nie rysunek) |
| P-13 „linia warunkowego zatrzymania z trójkątów” | etykiety wymiarowe | **0,25 / 0,50 / 0,25 m** | 4.2.4.1 | 572 | SOURCED odczyt („0,25” x102, „0,50” x326, „0,25” x537); przypisanie: podstawy trójkątów 0,25 m, wymiar środkowy 0,50 m — pozycje etykiet podane w manifest; semantyka poszczególnych wymiarów UNVERIFIED (rysunek bez jednoznacznych linii odniesienia przy „0,50”) |
| P-13 | podpis dolny figury | „0,2825” | 4.2.4.1 | 572 | SOURCED odczyt ([0][,][2][8][2][5] m); interpretacja: wysokość trójkąta (geometria: ~194 px przy podstawie 0,25 m ↔ ~0,28 m — spójne); oznaczono jako wysoce prawdopodobne, ale formalnie UNVERIFIED-semantyka |
| P-14 „linia warunkowego zatrzymania z prostokątów” | etykiety wymiarowe górne | **0,25 m** i **0,75 m** | 4.2.5.1 | 573 | SOURCED odczyt ([0][,][2][5] x168–236; [0][7][5] x435–500; glif „7” potwierdzony wzorcem) |
| P-14 | podpis dolny figury | „0,375” | 4.2.5.1 | 573 | SOURCED odczyt ([0][,][3][7][5] m; glif „3” odróżniony od „8” per-piksel); semantyka UNVERIFIED (prawdopodobnie wysokość prostokąta) |
| P-14 | odległości umiejscowienia | 2,0 / 0,5 / 8,0 / 2,0 / 1,5 / 2,0 / 0,5 m | 4.2.5.1 (tekst) | 573 | SOURCED: tekst rozporządzenia (umiejscowienie znaku, nie geometria prostokątów) |
| P-21a „powierzchnia wyłączona z ruchu – liniowanie wąskie” | wymiary liniowania a/b/c/d | **0,24 / 0,39 / 0,76 / 1,24 m** | 5.2.7.1 + tabela 5.3 | 588–589 | SOURCED: etykieta „0,24” na rys. 5.2.7.1 (str. 588) + tabela 5.3 (tekst, str. 589) |
| P-21b „powierzchnia wyłączona z ruchu – liniowanie szerokie” | wymiary liniowania a/b/c/d | **0,60 / 0,98 / 1,90 / 3,10 m** | 5.2.7.1 + tabela 5.3 | 588–589 | SOURCED: tabela 5.3 (tekst, str. 589) |
| P-23 „rower” | wymiary symbolu (i mini) | — | 5.2.9.1 | 596 | UNVERIFIED: rysunek 5.2.9.1 jest kadrowany — etykiety wymiarowe przy krawędziach obrazu są obcięte (glify 12 px: górna krawędź [0][1][0][0][0][6][5] x371–455; dolna [1][1][0][0][7][1][5] x270–344; dodatkowe obcięte pasy na krawędziach x0 i x591); tekst rozporządzenia odsyła wyłącznie do rysunku (str. 596) |
| P-25 „próg zwalniający” | odległość elementów odblaskowych | **1,0 m przed progiem** (min. 4 elementy) | 4.2.6.1 (tekst) | 574 | SOURCED: tekst rozporządzenia; rysunek 4.2.6.1 (perspektywa) nie zawiera etykiet wymiarowych (sprawdzono komponenty obrazu) |

Uwagi:
- Adnotacja wektorowa przy rys. 2.2.1.14 (str. 542): „Wymiary w cm” — dotyczy konstrukcji
  strzałki P-6a, nie znaków P-2…P-6.
- Podpisy dolne figur mają stały dekoracyjny człon [mała cyfra][pion][m][b]; odczytywana
  liczba zawsze przed „m”.
- Konwencja szerokości w rozporządzeniu potwierdza odczyty: P-7a/b 0,24 m; P-7c/d 0,12 m
  (str. Dz.U. 545).

---

---

## Zadanie 2 — Jaroszówka (kafl startowy): kadry z poziomu jezdni

Kafl startowy (ok. 53,152 N, 23,168 E) to **rondo Pamięci Bieżeństwa 1915 r.** (DK19 /
ul. Generała Władysława Andersa, północ Białegostoku). Pozyskano **24 kadry** (wymóg: ≥10)
z poziomu jezdni (kamery pojazdów, KartaView), wszystkie ≤1600 px, z datą, azymutem (EXIF
`heading` z API KartaView) i pozycją WGS84. Licencja KartaView: CC BY-SA 4.0 → status
REFERENCE_NOT_TEXTURE (referencja, nie tekstura).

| Sekwencja | Data | Autor | Kadry | Azymuty (ok.) | Pozycje (N, E) |
|---|---|---|---|---|---|
| 14055 | 2016-08-24 | ziozzzzz | 7 | 357/358/359° | 53.1512–53.1523, 23.1662–23.1689 |
| 2769366 | 2019-08-25 | gpsmapper999 | 6 | 302/303° | 53.1514–53.1524, 23.1663–23.1689 |
| 3686129 | 2021-06-23 | TMishaaa | 11 | 301/302/303° | 53.1513–53.1524, 23.1662–23.1693 |

Odległości kadrów od kafla: 23–127 m. Pełne metadane (id, sekwencja, indeks, lat/lon, data,
azymut, kolor pasa jezdni): manifest.csv M52-029…M52-052. Kadry z 2016 (azymut ~357°)
obejmują wjazd na rondo od południa; kadry z 2019/2021 (azymuty ~300–305°) — jezdnię,
krawężniki i linie od strony północno-zachodniej. Wszystkie pliki: `files/jaroszowka/`
w paczce ZIP (poza gitem).

---

## Zadanie 3 — Azyle, płytki dotykowe, ścieki i wpusty (Białystok)

### Azyle (wyspy dzielące)
- **Wymóg projektowy (SOURCED)**: wytyczne ZDM 2025 (BIP zasób 103311, str. 20):
  „Na wyspie dzielącej na środku jezdni należy wydzielić przejazd rowerowy”.
- **Występowanie (UNVERIFIED)**: w zbadanym obszarze centrum OSM wskazuje jeden obiekt
  `traffic_calming=island` — ul. Świętojańska (way 287037716, 53,12497 N 23,16656 E;
  ODbL, dane referencyjne). Brak kadrów KartaView w promieniu ~1,1 km od tego obiektu
  (najbliższe sprawdzone kadry: 1,15 km) → **brak potwierdzenia zdjęciowego**; wymiary i
  materiał azylów: UNVERIFIED.

### Płytki dotykowe (układ rzędów)
- **SOURCED** (wytyczne ZDM 2025, pkt II.2 — zejścia/rampy): obszar ostrzegawczy =
  **1 rząd płytek gładkich + 2 rzędy płytek profilowanych (guzowatych)**.
- Wymiary pojedynczych płytek: UNVERIFIED (źródło nie podaje).
- Kontekst OSM (bbox centrum, ODbL): 177 węzłów `tactile=yes` na 680 przejść; 10 przy
  trasie startowej, głównie skrzyżowanie Al. Tysiąclecia/Sokólska (53,1506–53,1509 N,
  23,1544–23,1550 E). Kadry przejść (z częścią z płytkami): M52-083…M52-105.

### Ścieki przykrawężnikowe i wpusty
- **Wymogi (SOURCED)**: wytyczne ZDM 2025, pkt III.11–III.13 — włazy żeliwne wg PN-EN 124,
  projektowane **w osi pasa ruchu**; studnie w jezdni z obróbką brukarską wg rys. nr 3 wytycznych.
- Konkretne wymiary wpustów: UNVERIFIED. Przykłady obiektów inżynierskich przy krawężnikach
  widoczne na kadrach `files/crossings/` (M52-083+).

---

## Zadanie 4 — Kolor dróg i pasów rowerowych na trasie startowej

**Wynik (ESTIMATED, analiza 77 kadrów KartaView z lat 2016–2021): na żadnym z kadrów
nie stwierdzono czerwonego asfaltu ani czerwonego malowanego pasa rowerowego** na badanych
odcinkach trasy startowej. Frakcja pikseli „czerwonych” w pasie jezdni < 0,8% (próg
detekcji R>G+B w medianie RGB dolnych 45% kadru); sygnały niebieskie w górnej części
kadrów = niebo (y≈277/900), nie nawierzchnia.

| Ulica | Odcinek badany kadrami | Kolor jezdni | Droga rowerowa | Status |
|---|---|---|---|---|
| Andersa (DK19) | 53,1488–53,1545 N, 23,1605–23,1754 E | szary asfalt (RGB ~[73–90]) | wydzielona droga rowerowa poza jezdnią (OSM `bicycle=no`); kolor na kadrach nierozstrzygnięty | ESTIMATED |
| Al. Tysiąclecia | przy skrzyż. z Sokólską | szary asfalt | `use_sidepath`; 1 odcinek `cycleway:right=share_busway` (buspas) | ESTIMATED |
| Sokólska (Białostoczek) | przy Al. Tysiąclecia | szary asfalt | `use_sidepath` | ESTIMATED |
| Wileńska | — | brak kadrów ≤60 m (najbliższy 348 m) | — | UNVERIFIED |

Metodologia: mediany RGB pasa jezdni + frakcje pikseli czerwonych/niebieskich per kolumna
(analiza własna, NumPy/PIL). Kadry: M52-053…M52-082 (trasa), M52-083…M52-105 (przejścia).
Dane OSM: ODbL (tylko referencja organizacyjna, nie tekstura).

---

## Zadanie 5 — Rynek Kościuszki: nawierzchnia

**Rodzaj nawierzchni (SOURCED): płyty granitowe + kostka granitowa (bruk)**.
- Tofiluk W. (2015), *Central square in Białystok — changes…*, CEE 2015;19(4):121–131,
  DOI 10.1515/ceer-2015-0058: rynek = granitowe płyty i kostka brukowa; przebudowa
  2006–2009; projekt (konkurs SARP): Zenon Zabagło; otwarcie: 7.08.2009
  (bialystok.pl, „Dekada Rynku Kościuszki”).
- Wymiary płyt: **UNVERIFIED** — żródło nie podaje; fotogrametria ze zdjęć bez punktów
  odniesienia uznana za niewiarygodną (nie ryzykujemy liczby).
- Kolor (ESTIMATED, metoda: mediana RGB centralnych 30×40% kadru, 3 zdjęcia Commons):
  [142, 125, 121] (CC0), [128, 135, 146] (CC0), [170, 171, 173] (CC BY 3.0 pl — referencja). Balans bieli zmienny
  między kadrami — traktować jako orientacyjny.
- Kadry: M52-106…M52-108 (pliki `files/rynek/` w paczce ZIP).

---

## Zadanie 6 — Aktualne wytyczne ZDM/ZDiT Białystok

- **Aktualna wersja: „Wytyczne do projektowania dokumentacji projektowej budowy, rozbudowy
  i przebudowy ulic w Białymstoku”, oznaczona „13 LIPCA 2018 R. / 2025 R.”** — BIP Białystok,
  zasób 103311 (PDF, 21 stron, 1,6 MB):
  https://www.bip.bialystok.pl/resource/103311/Za%C5%82.+nr+5_Wytyczne+do+projektowania.pdf
- Stara wersja (13.07.2018): BIP zasób 99308; kopia z SWW: zasób 99985 (22 strony).
- **Zmiany 2025 vs 2018 (SOURCED — porównanie tekstów obu PDF)**:
  1. oznaczenie wersji „13 LIPCA 2018 R. / 2025 R.”;
  2. tytuł sekcji rowerowej → „WYTYCZNE PROJEKTOWANIA I BUDOWY DRÓG DLA ROWERÓW – LOKALIZACJA”;
  3. nowe punkty w Wymaganiach ogólnych: 17 (wizualizacje przy koncepcjach), 18 (mapy
     podziału działek w wersji numerycznej), 19 (dokumentacja cyfrowa, edytowalna:
     dwg/dxf/word/excel), 24 (konsultacje rozwiązań technologicznych i materiałowych),
     27–28 (wersja robocza do zatwierdzenia; obowiązkowo: tabela robót ziemnych, wykaz
     zjazdów, przekroje normalne);
  4. uzbrojenie terenu: monitoring wizyjny wykonanych sieci;
  5. objętość: 21 vs 22 strony.

---

## Samokontrola 20% (jawny seed)

- Populacja: 116 rekordów manifestu (M52-001…M52-116).
- Próba: **24 rekordy** (⌈20%⌉), wybrane deterministycznie: `random.Random(20261113).sample(ids, 24)`.
- Kryteria (pełna lista w `audit_20_percent.json`): url_źródła i data_dostępu niepuste;
  status ∈ {SOURCED, ESTIMATED, UNVERIFIED, REFERENCE_NOT_TEXTURE}; ESTIMATED ⇒ metoda/uwagi;
  UNVERIFIED ⇒ uzasadnienie; kolor_srgb ⇒ metoda_koloru.
- Wynik: **24/24 zaliczone**, 0 problemów.

## Status prac (aktualizowany)

- [x] Gałąź utworzona z najnowszego `origin/main` (53e57d5).
- [x] PDF Dz.U. 2019 poz. 2311 część c2 pobrany z eli.gov.pl; ekstrakcja tekstu i rysunków.
- [x] Zadanie 1 — odczyt wymiarów z rysunków (tabela powyżej).
- [x] Zadanie 2 — zdjęcia Jaroszówka: 24 kadry (3 sekwencje, daty + azymuty + WGS84).
- [x] Zadanie 3 — azyle (wymóg SOURCED / występowanie UNVERIFIED), płytki dotykowe (układ rzędów SOURCED), ścieki/wpusty (wymogi SOURCED).
- [x] Zadanie 4 — kolor dróg/pasów rowerowych: brak czerwieni na 77 kadrach (ESTIMATED); Wileńska UNVERIFIED (brak kadrów).
- [x] Zadanie 5 — Rynek Kościuszki: płyty granitowe + kostka (SOURCED, Tofiluk 2015 + BIP/bialystok.pl); wymiary UNVERIFIED; kolor ESTIMATED.
- [x] Zadanie 6 — wytyczne ZDM „2018/2025”: BIP zasób 103311 + porównanie zmian vs 2018.
- [x] manifest.csv (116 rekordów), audit_20_percent.json (24/24, seed 20261113).

## Zasady

- Zakaz Google Maps / Street View / Earth / 3D Tiles.
- Źródła zdjęć: ELI/Dz.U., BIP Białystok, GDDKiA, Panoramax, KartaView, Commons, Openverse.
  Mapillary: brak tokenu → UNVERIFIED.
- Licencje komercyjne; NC/ND = „tylko referencja”; CC BY-SA = „referencja, nie tekstura”.
- Każda liczba: źródło albo UNVERIFIED/ESTIMATED z metodą.
- Pozycje WGS84; sezon i pora_dnia dla zdjęć. JPG ≤1600 px. PDF urzędowe ≤5 MB.
- Samokontrola 20% z jawnym seedem (README + audit_20_percent.json).
- Zdjęcia/binaria: `files/` (w `.gitignore`), paczka `mistral-p2-surfaces-2-files.zip`
  dostarczona poza gitem (patrz opis PR).

## Pliki

- `README.md` — ten plik (wyniki zadań 1–6 + statusy + opis samokontroli).
- `manifest.csv` — pozycje M52-001… (kolumny jak w `research/gptpro/p2-surfaces/manifest.csv`).
- `sources.md` — pełne źródła z linkami, licencjami i datami dostępu.
- `audit_20_percent.json` — samokontrola 20% (jawny seed).

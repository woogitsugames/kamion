# G3 — s8-signs: oznakowanie S8 / DK8, Białystok i okolice

**Stan badania: 12 listopada 2026 r. Materiał referencyjny dla projektu Kamion.**

Baza faktograficzna: **ODbL 1.0**; licencje fotografii są odrębne. Szczegóły: `LICENSE-DATA.md`.

Paczka zawiera **152 datowanych obserwacji tablic, paneli i pól oznakowania**, w tym 144 wycinków fotografii oraz 8 pozycji z dokumentacji BIP dostępnych wyłącznie przez link. Oddzielnie zapisano **187 obiektów OSM** z tagami kierunkowymi lub danymi węzłów. Liczby te nie oznaczają tylu unikalnych znaków w terenie: jeden kadr może przedstawiać kilka paneli, a jeden obiekt ma czasem obserwacje z różnych lat. Źródło liczebności: `manifest.csv`, `records.json`, `osm_destination.csv`.

**Znana z gry bramownica „Warszawa / Ełk / Augustów” jest potwierdzona na łącznicy z Andersa do ronda Putry.** To zespół czterech paneli; Warszawa i Ełk są na dwóch górnych panelach, a Augustów i Kuźnica na prawym dolnym. Poniżej podano dokładne rozdzielenie treści.

**Opracowanie nie stanowi kompletnej inwentaryzacji aktualnego oznakowania na listopad 2026 r.** Pokrywa główne kierunki i udokumentowane dojazdy, a brakujące przejazdy, nieczytelne fragmenty oraz niepotwierdzony stan po przebudowie oznaczono jawnie. Zdjęcia pochodzą z lat 2017–2026; z 2026 r. pochodzą tylko trzy miejskie obserwacje. Historyczne tablice nie dowodzą dzisiejszego przebiegu tras ani dostępności przejść granicznych. Źródła: daty per rekord; komunikat GDDKiA z 20.10.2026 w `sources.md`, CONTEXT-2026.

## 1. Zawartość i sposób użycia

| Plik | Zawartość |
|---|---|
| `manifest.csv` | Główny spis: jeden wiersz na obserwację określonej tablicy/panelu/pola; wszystkie wymagane kolumny i pola dodatkowe. |
| `records.json` | Te same obserwacje z pełnymi strukturami: kolorami kartuszy, surowym i obliczonym kompasem, metodą, dodatkowymi kadrami i prostokątem wycinka. |
| `files/*.jpg` | Wycinki znaków CC0 albo CC BY-SA 4.0 oraz mapa zakresu. Zdjęcia mają maksymalnie 1600 px dłuższego boku. |
| `files/G3-META001.json` | Jawne metadane użytych fotografii Mapillary: identyfikator, autor, czas, geometry, kompas, sekwencja. |
| `files/G3-META002.json` | Metadane Commons: licencja, autor, DateTimeOriginal, GPS i adres źródła. |
| `osm_destination.csv` | 174 odcinki z destination:* i 13 węzłów. To pomocnicze dane OSM, nie transkrypcje fizycznych tarcz. |
| `files/G3-OSM001…015.*` | OSM: surowe tagi i wersje, geometrie, granica/bufor, oszacowanie środka Putry, zapytania i kontrola. |
| `files/G3-L001.pdf` | Oficjalna nowelizacja wzorów znaków, Dz.U. 2026 poz. 133, 4 strony. |
| `files/G3-MAP001.jpg` / `G3-MAP002.json` | Mapa zakresu i jej dane; punkty są lokalizacjami kamer. |
| `sources.md` | Źródła, autorzy, licencje, daty dostępu, klucze, numery stron i dowody. |
| `LICENSE-DATA.md` | ODbL 1.0 dla publicznej bazy faktograficznej; odrębne zasady dla zdjęć i dokumentów. |
| `asset_manifest.csv` | Licencja, autor, źródło, rozmiar i SHA-256 każdego pliku w `files/`. |
| `audit_20_percent.json` | Odtwarzalna losowa kontrola głównego manifestu. |
| `validation.json` | Końcowa kontrola struktury, odwołań, formatów, wymiarów i spójności eksportu. |
| `osm_notes.md`, `bip_notes.md`, `s8_west_notes.md`, `dk8_north_notes.md`, `map_notes.md` | Szczegóły metod, dokumentów, rozbieżności i braków poszczególnych części. |

CSV ma kodowanie **UTF-8 z BOM**, separator przecinek i standardowe cudzysłowy CSV. `tekst_wiersze` używa `|` do rozdzielenia wierszy lub wyraźnych pól tablicy. Przy schematach węzłów informację o położeniu gałęzi należy odczytać równocześnie z `strzałki`, opisem lokalizacji i obrazem. W rekordzie S8-041 tabulator rozdziela boczne kolumny na tej samej wysokości. Numery w kartuszach i owale państw bywają zapisane przy danym wierszu; ich funkcję i kolor wyjaśniają osobne kolumny. Nie są częścią nazw miejscowości.

**Importuj `id` i `mapillary_key` jako tekst.** Długie klucze mogą zostać zaokrąglone przez arkusz kalkulacyjny. `records.json` przechowuje je jako łańcuchy. Nawiasy `[UNVERIFIED]` są komentarzem badacza i nie mogą trafić na teksturę tablicy.

## 2. Potwierdzona bramownica przy Putry

Najczytelniejsze potwierdzenie wykorzystane w paczce: **Mapillary key 465521806237924**, autor **kino**, zdjęcie **26.07.2024, 13:36:22.600 UTC**. Geotag **kamery**: **53.158600, 23.153038**, kierunek kamery z `compass_angle`: **313°**. Kierunek przejazdu: z Andersa, łącznicą ku północnemu zachodowi do ronda. Lokalizacja samej tarczy pozostaje UNVERIFIED. Źródła: [fotografia](https://www.mapillary.com/app/?pKey=465521806237924), `G3-P001–004`, `files/G3-META001.json`.

| Panel, od strony kierowcy | Wiersze i kartusze | Strzałka | Barwy |
|---|---|---|---|
| Lewy górny | `8 E 67 Warszawa` / `65 Ełk` | ↑ | Zielona tablica; 8 i 65 na czerwieni, E 67 na zieleni; białe litery. |
| Lewy dolny | `675 Centrum` | ← | 675: czarny napis na żółtym kartuszu; Centrum: niebieski napis na białym polu. |
| Prawy górny | `8 E 67 Warszawa` / `65 Ełk` | ↑ | Jak lewy górny. |
| Prawy dolny | `8 E 67 Augustów` / `19 Kuźnica PL BY` | → | 8 i 19 na czerwieni; E 67 na zieleni; PL i BY w osobnych białych owalach. |

Ukośnik w tej tabeli służy wyłącznie jako separator opisu. Właściwy zapis w `tekst_wiersze` rozdziela linie znakiem `|`. Na tych czterech panelach nie ma odległości ani widocznego numeru węzła.

Drugi niezależny materiał pokazuje tę bramownicę **03.05.2021**: Commons, **Rakoon / CC0**, `File:7204 May 2021 in Białystok.jpg`, kamera **53.158496, 23.153233**. Wtedy dolny lewy panel był przekreślony czarną taśmą, a końcowa cyfra numeru nie daje pewnego odczytu. Dlatego `G3-C002` zachowuje `67[UNVERIFIED]`, mimo że w 2024 r. widać 675. Źródła: [Commons](https://commons.wikimedia.org/wiki/File:7204_May_2021_in_Bia%C5%82ystok.jpg), `G3-C001–004`.

### Cztery podejścia do rejonu Putry

| Podejście | Dowody i zakres |
|---|---|
| Od Andersa, ze wschodu / południowego wschodu | E-1, rozdział głównej jezdni i łącznicy, czteropolowa bramownica: `G3-P001–004`, `P011–013`; dodatkowo `C001–005`. |
| Od północy, al. Tysiąclecia | E-1, tablica czasu przejazdu, bramownica: `G3-P005–010`, fotografie 2024. Literalny skrót `Kuźnica B.` na P009 zachowany. |
| Od zachodu, Maczka | E-1, rozdział pasów i bramownica dolnej łącznicy: `G3-P014–020`, fotografie 2019–2020. Zaklejonego kierunku P020 nie odtworzono z domysłu. |
| Od południa, al. Tysiąclecia | E-1 i pięć pól bramownicy: `G3-C006–011`, fotografie 2022. Starsza inwentaryzacja w planie 2014: `G3-MUN-001–003`; układów nie scalono. |

**Korekta punktu z polecenia:** `53.152000, 23.168000` leży na innym odcinku Andersa. Środek ronda obliczony z czterech ways OSM wynosi **ESTIMATED 53.159038, 23.151613**, około **1347 m** na północny zachód od wskazanego punktu. Jest to centroid geometrii i odległość geodezyjna WGS84, a nie pomiar terenu ani pozycja bramownicy. Dowód i metoda: `files/G3-OSM007.json`, `osm_notes.md`, mapa.

## 3. Pozostałe najważniejsze ustalenia

- **S8 od strony Warszawy i w stronę Warszawy:** zapisano tablice głównych jezdni przy Choroszczy, Tykocinie i Rzędzianach, tablice odległości, usług i dostępne dojazdy boczne. Część tablic pod Tykocinem w stronę Białegostoku ma czerwony kartusz **8 bez S**, choć inne ujęcia tej drogi mają S8. Zachowano wygląd zdjęć, bez dostosowywania do współczesnej numeracji. Źródła: `G3-MLY-S8-001–045`, szczególnie 028, 030–031.
- **Numery węzłów:** OSM zawiera `unsigned_ref=90/91/92/93` odpowiednio dla Rzędzian, Tykocina, Choroszczy i Białegostoku Zachód. Te tagi nie potwierdzają nadruku na znakach. Na opisanych zachodnich tablicach nie odczytano numerów węzłów. Osobne `ref=10` przy podejściu S19 i `proposed:ref=7` również nie są fotograficznym dowodem treści. Źródło: wersjonowane nodes w danych OSM oraz `osm_notes.md`, sekcja numerów węzłów.
- **Chodakowskiego — 676 i 669:** wschodni kierunek na Kleeberga ma w `C013` czytelne **676 Centrum**. Północny wlot DK65 w `MC019/MC020` z 2020 r. ma **669 Centrum**. To różne podejścia. Numer na nowszej obserwacji północnego wlotu `MC002` z 2026 r. pozostaje UNVERIFIED. Nie przenoszono czytelnego numeru między wlotami i latami.
- **Tablice na północ od Białegostoku zawierają rzeczywistą rozbieżność:** MN004 podaje **Suwałki 114**, MN009 dalej na północ **Suwałki 119**. Jednocześnie Augustów zmienia się z 83 na 80, Kowno z 239 na 236. Zachowano źródłowe liczby; 119 przeczytało niezależnie dwóch badaczy na głównej i pomocniczej klatce. Źródła: keys 876869244252986, 1009127457582864, 8391472337531180.
- **Pełne skróty i obce nazwy są istotne:** przy Osowiczach występuje `Podlaskie Muzeum Kultury Lud.`; nie rozwinięto skrótu. Historyczna E-14 z 2017 r. ma `Praha CZ 812`, bez polskiego „Praga”. Osobny nowszy, zacieniony odczyt MN017 pozostał częściowy. Źródła: MN001, MN018, MN021.
- **Piktogramy usług:** na `Radule 5 km` rozpoznano m.in. `LPG / GAZ` i D-26, symbol stacji obsługi technicznej. Nie jest to litera „i”. Tablice usług przy Złotorii mają odrębne wartości 5 km, 2000 m, 1000 m, 700 m lub 1300 m. Szczegóły i przypisanie do tablic: S8-005, 008–009, 011, 013, 016, 021, 026–027, 029, 032; wzór D-26: Dz.U. 2019 poz. 2311, s.232.
- **Wyświetlacze są migawką:** P010 ma czytelne `CENTRUM PRZEZ:`, `TYSIĄCLECIA P.P. 5 MIN`, `ŚWIĘTOKRZYSKĄ 7 MIN`. W MC015, MC021 oraz sześciu polach S8-038 wartości są nieodczytane. Nie uznano pustych lub rozmytych segmentów za „0” i nie traktowano czasów jako stałego parametru drogi.
- **Przebieg OSM wymaga rozróżnienia dróg:** przy Putry DK8 prowadzi przez Maczka, łącznicę, rondo i al. Tysiąclecia na północ. Wiadukt Andersa ma ref 65, a odcinek koło punktu użytkownika ref 19;65. „8” w kartuszu kierunkowym nie nadaje tego numeru jezdni, na której znajduje się kamera. Dowody: konkretne ways i snapshot w `osm_notes.md`.

## 4. Metoda, zakres i znaczenie statusów

Zakres przestrzenny oparto na granicy Białegostoku z **OSM relation 2910925, v45** oraz buforze **15 000 m w EPSG:2180**. Dwa końcowe rekordy, MX002/MX003 przy Przewalance, są jawnym wyjątkiem brzegowym: kamera **ESTIMATED 15 177 m od granicy, 177 m poza ścisłym buforem**; mieszczą się w interpretacji „ok. 15 km”. Metoda i przebieg dodatkowego przeglądu: `northern_extent_notes.md`, `files/G3-COV001.json`. To przybliżony zakres badania, a nie urzędowa geometria PRG. OSM pobrano 12.11.2026; podstawowy snapshot tagów ma czas **22:17:12 UTC**. Dołączono wersje obiektów, geometrie i zapytania. Progi selekcji obiektów OSM — do 250 m od osi dla destination oraz do 500 m dla węzłów — są decyzją metodyczną, opisaną w `osm_notes.md`.

Źródła badano trzema niezależnymi ścieżkami: fotograficzne Commons/Mapillary; dokumenty urzędowe i archiwa zamówień BIP; tagi i geometrie OSM. Wytypowane tablice oglądano w większych kadrach oraz w sąsiednich klatkach. Odczyt był wizualny. Nie generowano liter, nie wykonywano retuszu treści i nie wypełniano nieczytelnych pól wynikami OSM. Nie użyto Google Maps, Street View, Earth ani 3D Tiles.

| Część | Liczba obserwacji | Kierunki / ograniczenia |
|---|---:|---|
| Commons | 31 | Miasto i Putry; 14 fotografii źródłowych. Cztery rekordy nie mają geotagu. |
| Mapillary — część miejska | 21 | Porosły, Kleeberga, Chodakowskiego, Bacieczki i Maczka; oba kierunki głównych ciągów oraz wybrane wloty. |
| Mapillary — Putry | 20 | Andersa, północ i zachód; podejście od południa uzupełniają Commons/BIP. |
| Mapillary — zachodnia S8 | 45 | 21 obserwacji ku zachodowi, 19 ku wschodowi, 5 na dojazdach bocznych. |
| Mapillary — północna DK8 | 27 | Główne przejazdy na północ i południe, Osowicze, Jurowce, Katrynka i dalszy udokumentowany odcinek; szczegółowe luki w notatkach. |
| BIP | 8 | Inwentaryzacja na rysunku SOR i historyczne zdjęcia w raporcie; źródła tylko przez link. |

**Współrzędne:** `lat/lon` w spisie fotografii oznaczają kamerę. Sześć miejsc po przecinku jest formatem zapisu, a nie deklaracją centymetrowej dokładności. `pozycja_tablicy_lat/lon` pozostaje UNVERIFIED. Nie skopiowano geotagu kamery do pozycji słupa. W szczególności geotag C005 jest podejrzany względem opisanej jezdni; uwaga w rekordzie zabrania używania go jako pewnej lokalizacji obiektu.

**Kierunki:** w każdej części zachowano źródło azymutu: `compass_angle`, `computed_compass_angle` albo oszacowanie z dwóch punktów toru/osi OSM. Są to różne metody. Kierunek szerokiego kadru nie jest dokładnym azymutem promienia do wyciętego panelu. Dla panoram MC001–003 kierunek konkretnego wycinka pozostaje UNVERIFIED; oszacowany kierunek przejazdu jest osobnym polem. Dla sprzecznych kompasów części S8 również zachowano UNVERIFIED zamiast arbitralnej korekty.

**Statusy:** `SOURCED` oznacza dowód we wskazanym źródle; `ESTIMATED` — wnioskowanie z podaną metodą; `UNVERIFIED` — brak wystarczającego dowodu. Status ogólny nie zastępuje statusów pól. Pełny odczyt tekstu może współistnieć z szacowanym kierunkiem i nieustaloną pozycją tarczy. Najpierw sprawdzaj `tekst_status`, `kierunek_status`, `typ_status`, a następnie uwagi o kolorach, piktogramach i zasłoniętych częściach.

**Typy znaków:** kody E przypisano wizualnie przez porównanie z urzędowymi wzorami; nie są odczytem numeru z ewidencji zarządcy. Użyto historycznych wzorów dla dawnych fotografii. Nowelizacja Dz.U. 2026 poz. 133 wprowadza E-1c oraz zmienia znaczenie i wzór E-2d, obejmując drogi ekspresowe; §2 na s.4 przewiduje okres przejściowy dla starszego oznakowania. Nie przeklasyfikowano automatycznie zdjęć 2020/2024 na nowe kody. Nie znaleziono dowodu występowania każdego wariantu E-2a…E-2g w tym obszarze.

**OSM:** destination opisuje cele przejazdu. Średnik nie dowodzi nowej linii na tablicy, a pionowa kreska w destination:lanes rozdziela pasy. Literówki `Cetrum`, nietypowe `Ełk KAS` i powtórzone ref 8;8 pozostawiono w danych źródłowych; nie przeniesiono ich do transkrypcji tarcz. Timestamp obiektu OSM jest datą edycji, nie zdjęcia ani montażu.

### Północna krawędź zakresu

Końcowy przegląd 120 wskazanych kadrów uzupełnił spis o `Leśnictwo Rybniki`, `Przewalanka` i `Brzozówka Koronna 2` (MX001–003; dosłowny tekst z odstępami w manifeście). Dla kierunku południowego zachowała się luka wybranego przejazdu z 2024 r. między 53.279016 a 53.308277; przejrzano w niej 26 klatek historycznych z 2017 r.. Brak dalszych odczytów w tej próbce nie dowodzi braku znaków ani pełnego pokrycia zdjęciowego. Źródła i wszystkie key: `northern_extent_notes.md`, `files/G3-COV001.json`, `sources.md`, sekcja 6.

## 5. Braki i niepewności wymagające dalszych dowodów

1. **Białystok Zachód po otwarciu S19 w październiku 2026:** nie uzyskano kompletnego zatwierdzonego zestawu tarcz z dokumentacji powykonawczej ani świeżych fotografii wszystkich relacji. Komunikat GDDKiA potwierdza przebudowę, lecz nie wypełnia tej luki. Nie można na podstawie zdjęć 2024 odtworzyć pewnego stanu z listopada 2026.
2. **Łącznice i dojazdy boczne:** brak pełnych przejazdów wszystkich łącznic w obu kierunkach, szczególnie od strony Tykocina oraz Żółtek/Dzikich. Są częściowe przejazdy przy Rzędzianach i Choroszczy. Wynik zapytania API bez dalszej strony nie gwarantuje kompletności katalogu zdjęć.
3. **Małe i zasłonięte pola:** niepewna cyfra C002, zaklejony P020, rozmyty numer P013, części MC002/016/017/020 i MN005/013/014/016/017/022, drobne wyświetlacze oraz prześwietlone owale krajów S8-007. Ograniczenia opisano per pole.
4. **Data i autor zdjęć w raporcie BIP:** autor opracowania nie musi być fotografem. Data dokumentu 2016 nie została wpisana jako data wykonania zdjęcia.
5. **Pełna ewidencja znaków E-15, wszystkich powtórzeń, F-14 i wjazdów/wyjazdów miejscowości:** brak potwierdzenia kompletności. Puste pole manifestu nie stanowi dowodu nieistnienia znaku.
6. **Dokładne posadowienie i geometria tarcz:** brakuje współrzędnych słupów, wymiarów, wysokości i orientacji lica. Do pozycjonowania w świecie 1:1 potrzebny jest osobny dowód: pomiar, jednoznaczny plan albo geolokalizacja z opisanym błędem. Nie szacowano tych parametrów bez wystarczających danych.

## 6. Licencje i ograniczenia plików

- **31 wycinków Commons:** zdjęcia Rakoon, CC0. Autor i źródło zachowane mimo braku obowiązku atrybucji wynikającego z CC0.
- **113 wycinków Mapillary:** CC BY-SA 4.0. Każdy ma autora, kanoniczny link z key i informację o kadrowaniu/zmniejszeniu. Wycięte obrazy zachowują warunki tej licencji. Wyjątek techniczny MC003: dwa skraje panoramy połączono prostym przesunięciem na szwie, bez generowania treści.
- **Dane OSM:** © OpenStreetMap contributors, ODbL 1.0. Fotografie i baza OSM mają odrębne warunki; nie nadano całej paczce jednej zbiorczej licencji zastępującej prawa do źródeł.
- **Oficjalny akt prawny:** `G3-L001.pdf`, materiał urzędowy, art. 4 pkt 1 ustawy o prawie autorskim.
- **BIP z klauzulą BPBK i fotografie raportu o niejasnych prawach:** tylko linki i faktograficzny odczyt; plików PDF ani ich obrazów nie ma w ZIP. Tak samo nie dołączono fotografii GDDKiA oznaczonych CC BY-NC-ND.
- Metadane JSON i indeksy dokumentują źródła i fakty; nie zawierają wygasających adresów CDN, tokenów ani obrazów o niejasnej licencji. Zdjęcia wynikowe pokazują znaki, bez czytelnych marek producentów ciężarówek.

Podstawa każdej licencji: `sources.md`, sekcja 1 oraz metadane konkretnego pliku. Budżet pozyskania wykorzystanych materiałów: 0 zł; nie korzystano z płatnych źródeł.

## 7. Samokontrola i korekty

Główną próbę losowano **bez zwracania** z posortowanych ID, przez `random.Random(seed).sample(..., ceil(0.20*N))`. Seed: `Kamion-G3-s8-signs-2026-11-12-v1`. Wynik obejmuje **31 z 152 pozycji — 20,39%**. Pełna lista i wyniki: `audit_20_percent.json`.

Ponownie odczytano URL źródła, publiczne metadane fotografii, autora, licencję i współrzędne. Wykonano niezależny odczyt wylosowanych tablic; sprawdzono zgodność miejsca i kierunku z pełnym obrazem, podpisem dokumentu lub geometrią. Przy każdej kontroli rozróżniano pozycję kamery i tablicy. Kontrola adresu Mapillary HTTP 200 jest uzupełniona kontrolą istnienia konkretnego key w API; sam ekran aplikacji nie wystarczał.

**Wynik końcowej próby 31/152:** wszystkie 31 kontroli metadanych i linków zgodne; 28 licencji fotografii potwierdzonych, 3 pozycje BIP pozostają referencjami bez pobranego pliku. Ocena wizualna: 30 PASS i 1 wcześniejsze ostrzeżenie MC020, już skorygowane; po uwzględnieniu ograniczeń 31 PASS. Dobór przeliczono po dodaniu trzech końcowych tablic z północy: 22 ID pozostały z pierwszej próby, 9 sprawdzono dodatkowo. Ponownie pobrano metadane i sprawdzono URL wszystkich 31.

**Wynik początkowej próby 30/149 (zachowanej w files/G3-AUD005.json):** 30 pozytywnych kontroli metadanych/linków; 29 zgodnych ocen wizualnych i 1 ostrzeżenie redakcyjne, bez błędnej transkrypcji. W MC020 doprecyzowano, że brak odległości dotyczy tylko widocznego fragmentu tablicy. W 26 pozycjach fotograficznych potwierdzono licencje; 4 wylosowane pozycje z BIP zachowały status licencji UNVERIFIED i wykluczenie plików z paczki. Taki wynik nie oznacza ustalenia brakujących współrzędnych, dat ani praw.

Dodatkowa kontrola całych danych wykryła potrzebę wpisania sześciu `[UNVERIFIED]` bezpośrednio przy wartościach godzin S8-038 oraz zawężenia „brak odległości” w sześciu częściowo widocznych tablicach. Korekty zastosowano. MN023 otrzymał czytelniejszą klatkę główną; jego metadane i link zweryfikowano ponownie, bez zmiany ID w próbie. Ślad: `files/G3-AUD001–005.json`.

**Osobna próba OSM:** 38 z 187 obiektów, **20,32%**; wszystkie 38 zgodne pod względem adresów, wersji, tagów, współrzędnych i licencji. To weryfikacja danych OSM, nie fizycznego oznakowania. Wynik: `files/G3-OSM006.json`.

Końcowa walidacja obejmuje komplet kolumn, unikalność ID, zgodność key z URL i metadanymi, rozmiary JPG, sumy SHA-256, brak niedozwolonych pobrań i brak ścieżek roboczych lub danych uwierzytelniających. Wynik oraz rozmiary zapisano w `validation.json`; archiwum sprawdzono przez test CRC ZIP.

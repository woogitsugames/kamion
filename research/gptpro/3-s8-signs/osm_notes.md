> Notatka częściowa. Końcowa integracja i globalna samokontrola: README.md oraz audit_20_percent.json. Nazwy roboczych zapytań wymienione w opisie metody nie oznaczają dodatkowych plików w paczce.

# G3 – dowody OpenStreetMap: S8/DK8 i rejon Putry

## Co potwierdza ten materiał

**To zbiór danych pomocniczych, nie inwentaryzacja 187 fizycznych tablic.** `osm_destination.csv` zawiera 174 odcinki dróg z `destination:*` i 13 węzłów OSM. Poszczególne odcinki mogą opisywać ten sam ciąg drogowy i tę samą treść. Ich liczby nie wolno utożsamiać z liczbą tablic, paneli ani bramownic.

- `SOURCED` dotyczy odczytanego tagu OSM i geometrii OSM.
- `tekst_wiersze`, dokładny typ znaku, widoczne numery/kolory, piktogramy i data zdjęcia pozostają `UNVERIFIED`, jeżeli brak osobnego zdjęcia/projektu.
- Współrzędne `lat/lon` są współrzędnymi początku odcinka OSM lub węzła drogowego. **Nie są współrzędnymi słupa, tablicy ani kamery.**
- `kierunek_deg` dla ways jest `ESTIMATED`: azymut geodezyjny WGS84 od pierwszego do drugiego różnego punktu geometrii, zgodnie z kolejnością way. Nie jest pomiarem kierunku kamery. Na odcinku dwukierunkowym trzeba uwzględnić znaczenie `:forward` i `:backward`.
- `osm_timestamp` jest datą ostatniej edycji obiektu OSM, a nie datą zdjęcia, oględzin ani instalacji znaku.
- Nie zamieniono średników `;` w OSM na wiersze tablicy. Znak `|` w `destination:lanes` rozdziela pasy ruchu, a nie linie tekstu na tablicy.

## Metoda i zasięg

Odczyt 12 listopada 2026 r. Podstawowe zapytanie Overpass zwróciło 1232 obiekty, stan bazy `2026-11-12T22:17:12Z`. Źródło: `files/G3-OSM011.json` i nagłówek `osm3s` w `files/G3-OSM001.json`.

Prostokąt zapytania: południe 53.04, zachód 22.75, północ 53.36, wschód 23.23. Następnie odrzucono obiekty spoza bufora około 15 km od granicy miasta: relacja OSM [2910925](https://www.openstreetmap.org/relation/2910925), wersja 45. Bufor obliczono w EPSG:2180, w metrach. To **ESTIMATED zakres opracowania**, nie granica administracyjna potwierdzona PRG. Geometrie dróg pobrano z relacji [2107912 – S8](https://www.openstreetmap.org/relation/2107912) i [7843418 – DK8](https://www.openstreetmap.org/relation/7843418), oraz lokalnego odczytu API przy Putry.

Włączono destination na drogach głównych i łącznicach/istotnych dojazdach w odległości do 250 m od osi S8/DK8. Osobno uwzględniono wskazany przez zamawiającego fragment Andersa (DK65/DK19), mimo że nie jest on główną osią S8/DK8. Węzły OSM włączono do odległości 500 m. Wartości progów są decyzją metodyczną opracowania. Zewnętrzne końcówki bardzo długich odcinków w pliku geometrii mogą nieco wychodzić poza bufor; początki wszystkich rekordów tabeli leżą w przyjętym zakresie.

`files/G3-OSM001.json` jest wyciągiem niezmienionych obiektów z odpowiedzi Overpass, a nie kompletną pierwotną odpowiedzią. Usunięto obiekty nieistotne geograficznie/tematycznie; zachowano wszystkie tagi, wersje i geometrie wybranych elementów.

## Najważniejsze ustalenia

### Putry nie znajduje się w podanym punkcie 53.152, 23.168

Rondo jest reprezentowane przez ways [180144451](https://www.openstreetmap.org/way/180144451), [257367424](https://www.openstreetmap.org/way/257367424), [257367425](https://www.openstreetmap.org/way/257367425), [257367428](https://www.openstreetmap.org/way/257367428). Nazwa OSM: `Rondo Krzysztofa Jakuba Putry Wicemarszałka Sejmu RP`.

Centroid zamkniętego pierścienia tych odcinków: **ESTIMATED 53.159038, 23.151613**. Od punktu zadania oddalony geodezyjnie o około **1347 m**, ku NW. To wynik obliczenia, nie pomiar terenowy. Metoda i niezaokrąglone wartości: `files/G3-OSM007.json`. Geometria źródłowa: `probe_1.txt` (XML OSM API; materiał roboczy) lub indywidualne URLs OSM podane powyżej.

### Ciąg S8/DK8 i Andersa

W bieżących danych OSM zmiana `ref=S8, highway=motorway` na `ref=8;65, highway=trunk` występuje przy Białystok Zachód: jezdnia ku miastu w punkcie **53.153510, 23.030892**, jezdnia ku Warszawie **53.153654, 23.030749**. To granica tagowania OSM, **nie samodzielne potwierdzenie lokalizacji znaków D-7/D-8 ani statusu prawnego drogi**. Źródła: ways [183639794](https://www.openstreetmap.org/way/183639794) v31, [305447699](https://www.openstreetmap.org/way/305447699) v25, [197904075](https://www.openstreetmap.org/way/197904075) v25, [1379858308](https://www.openstreetmap.org/way/1379858308) v12; edycje 20–24.10.2026, utrwalone w `files/G3-OSM002.json`.

Przy Putry DK8 według OSM prowadzi ulicą Maczka, łącznicą, rondem i dalej Al. Tysiąclecia Państwa Polskiego. Sam wiadukt Andersa nad rondem ma `ref=65`; Andersa koło punktu 53.152/23.168 ma `ref=19;65`. Źródła m.in. [way 173956079](https://www.openstreetmap.org/way/173956079), [way 237183783](https://www.openstreetmap.org/way/237183783), [way 284022563](https://www.openstreetmap.org/way/284022563), [way 221240112](https://www.openstreetmap.org/way/221240112); surowe tagi w `files/G3-OSM001.json`.

### Cele przy Putry: potwierdzone tagi, nie pełny odczyt bramownicy

| OSM way | Dosłowny tag | Znaczenie dla weryfikacji |
|---|---|---|
| [173956080](https://www.openstreetmap.org/way/173956080) v25 | `destination=Warszawa;Ełk`, `destination:ref=8;65` | Cel łącznicy ku zachodowi. |
| [257367454](https://www.openstreetmap.org/way/257367454) v16 | `destination=Warszawa;Ełk`, `destination:ref=8;65` | Dalszy fragment tej relacji; nie druga pewna tablica. |
| [613026608](https://www.openstreetmap.org/way/613026608) v12 | `destination=Warszawa;Ełk`, `destination:ref=8;65` | Łącznica z ronda ku zachodowi. |
| [606396463](https://www.openstreetmap.org/way/606396463) v12 | `destination=Augustów;Kuźnica PL/BY`, `destination:ref=19` | Dojazd do ronda od Andersa. |
| [237183783](https://www.openstreetmap.org/way/237183783) v23 | `destination=Augustów;Kuźnica PL/BY`, `destination:ref=8;19` | Wyjazd Al. Tysiąclecia na północ. |
| [173956079](https://www.openstreetmap.org/way/173956079) v37 | `destination=Augustów Kuźnica;Centrum`, `destination:ref=8;19` | Dojazd od Maczka. Spacja w `Augustów Kuźnica` zachowana. |
| [173985177](https://www.openstreetmap.org/way/173985177) v29 | `destination=Lublin;Bobrowniki PL/BY`, `destination:ref=19;65` | Relacja z ronda ku Andersa. |
| [284541843](https://www.openstreetmap.org/way/284541843) v17 | `destination=Centrum`, `destination:ref=675` | Kierunek Al. Tysiąclecia ku centrum. |

Te tagi nie potwierdzają, że słowa Warszawa/Ełk/Augustów występują na jednym panelu, trzech panelach, w tej kolejności czy z konkretnymi strzałkami. Do tego należy użyć osobnego zdjęcia/projektu w głównym materiale G3.

### Numery węzłów: pułapka unsigned_ref

| Nazwa OSM | Obiekty OSM | Tag numeru |
|---|---|---|
| Rzędziany | 1856618918, 1937517092 | `unsigned_ref=90` |
| Tykocin | 469876632, 1937542643 | `unsigned_ref=91` |
| Choroszcz | 1908957192, 1940503816 | `unsigned_ref=92` |
| Białystok Zachód, S8 | 2081020070, 3160890725 | `unsigned_ref=93` |
| Białystok Zachód, podejście S19 | 4236127140 | `ref=10` |
| Białystok Północ | 1154993008, 1838303608 | `proposed:name`, `proposed:ref=7` |

Źródło: każdy node o podanym ID w `files/G3-OSM001.json`, z wersją i timestamp. URL: `https://www.openstreetmap.org/node/ID`.

`unsigned_ref` i `proposed:ref` **nie dowodzą obecności numeru na tablicy**. Także zwykłe `ref=10` wymaga odrębnego oglądu zdjęcia, aby uznać je za literalny odczyt znaku. Dokumentacja [Key:unsigned_ref](https://wiki.openstreetmap.org/wiki/Key:unsigned_ref), dostęp 12.11.2026, sekcja Description, określa numer, który nie jest wyraźnie oznakowany; cytat: „not prominently signposted”.

### Błędy i niepewności tagów

Zachowano, bez poprawiania, m.in. `destination=Warszawa;Ełk KAS` na way 221240112, `destination:lanes=Ełk|Cetrum` na way 606396503 i powtórzenia `destination:ref=8;8` przy Porosłach/Kleeberga. **Nie przenosić tych wartości automatycznie na tekstury znaków.** W szczególności `Cetrum` może być literówką mapującego; treść tablicy pozostaje UNVERIFIED bez zdjęcia.

Zapytanie z prostym kluczem `traffic_sign` nie zwróciło w tym obszarze oznakowania grupy E. Osobne zapytanie o relacje `type=destination_sign` zwróciło 0 obiektów (stan bazy 22:23:21Z). To wynik wykonanych zapytań, a nie dowód braku znaków w terenie ani pełnego braku oznakowania w OSM. Dodatkowe zbiorcze zapytania regex i `traffic_sign:forward/backward` zakończyły się HTTP 504; nie uznano ich za puste wyniki.

## Mapillary powiązane w OSM

W szerszym prostokącie odczytu znaleziono tylko jeden bezpośredni tag `mapillary`: [node 14312855853](https://www.openstreetmap.org/node/14312855853), key **1589031375553411**. Dotyczy latarni przy 53.149193, 23.108024, nie potwierdzonej tablicy. `direction=136` tego obiektu opisuje latarnię, **nie kierunek zdjęcia**. Tego key nie należy wpisywać do manifestu innych tablic.

Cztery słupki kilometrażowe mają `source=Mapillary`, lecz bez image key: nodes 8984313743, 8984313744, 8999416254, 8999416255. Nie wymyślono kluczy ani dat zdjęć. Surowy wynik: `files/G3-OSM014.json`.

## Licencja i autorstwo

Dane: **© OpenStreetMap contributors, ODbL 1.0**. API zwraca atrybuty `copyright="OpenStreetMap and contributors"` i `license="http://opendatacommons.org/licenses/odbl/1-0/"`. Licencja umożliwia wykorzystanie komercyjne przy spełnieniu jej warunków. Autor ostatniej edycji jest zachowany w metadanych, ale nie zastępuje zbiorowej atrybucji całego obiektu/danych.

- [Oficjalne warunki i atrybucja](https://www.openstreetmap.org/copyright), dostęp 12.11.2026, sekcje „OpenStreetMap licensing”, „How to credit OpenStreetMap”.
- [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/), link licencji podany przez API.
- [Znaczenie destination](https://wiki.openstreetmap.org/wiki/Key:destination), dostęp 12.11.2026; sekcje „Description”, „Lane-dependent destinations”. Dokumentacja wiki jest odrębna od bazy danych.

## Losowa samokontrola 20%

Wylosowano bez zwracania **38 z 187 rekordów (20,32%)**. Seed i komplet rezultatów: `files/G3-OSM006.json`. Dla każdego rekordu:

1. Ponownie pobrano publiczny URL obiektu OSM: wszystkie zwróciły HTTP 200.
2. Ponownie pobrano wskazaną niezmienną wersję z oficjalnego API: wszystkie HTTP 200.
3. Porównano numer wersji i literalne `destination:*`: 38/38 zgodne.
4. Sprawdzono atrybuty licencji i copyright API: 38/38 zgodne z ODbL / OpenStreetMap contributors.
5. Ponownie odczytano współrzędne node/pierwszego węzła way; 38/38 zgodne z tabelą po zaokrągleniu do 6 miejsc. Surowy odczyt współrzędnych: `files/G3-OSM010.osm`.

**Wynik: PASS 38; FAIL 0; UNVERIFIED 0 dla sprawdzanych metadanych OSM.** Nie jest to walidacja fizycznej treści ani lokalizacji tablic. Te wymagają odrębnej kontroli źródła fotograficznego/projektowego.

## Pliki zalecane do paczki głównej

- `files/G3-OSM001.json` – niezmienione wybrane elementy źródłowe, metadane wersji, geometria.
- `osm_destination.csv` – tabela danych pomocniczych, UTF-8 BOM.
- `files/G3-OSM005.json` – równoważna tabela JSON do dalszego przetwarzania.
- `files/G3-OSM002.json` i `files/G3-OSM003.geojson` – geometria identyfikująca przebieg drogi.
- `files/G3-OSM004.geojson` – granica miasta i metodyczny bufor.
- `files/G3-OSM006.json`, `files/G3-OSM010.osm` – audyt próby.
- `files/G3-OSM007.json` – obliczenie położenia ronda.
- `files/G3-OSM008.json`, `files/G3-OSM009.json` – pomocnicze obliczenia osi jezdni dla fotografii Commons. Nie są headingiem zmierzonym przez kamerę; geotagi niektórych zdjęć leżą wyraźnie poza jezdnią.
- `files/G3-OSM011.json`, `files/G3-OSM012.json`, `files/G3-OSM013.json`, `files/G3-OSM014.json`, `files/G3-OSM015.json` – pochodzenie zapytań i braki danych.

Nie ma potrzeby dodawania całych ogólnopolskich plików S8/DK8 ani roboczych, nieistotnych geograficznie rezultatów z tego katalogu. Nie używano Google Maps, Street View, Earth ani 3D Tiles. Pojedyncze nieistotne odnośniki do Google zwrócone jako cudze tagi `image` w szerszej bazie OSM odrzucono; nie otwierano ich i nie używano jako dowodów.

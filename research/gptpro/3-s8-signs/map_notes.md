# G3-MAP001 — mapa zakresu dokumentacji

Data opracowania i dostępu do danych: **2026-11-12**. Plik wynikowy: `G3-MAP001.jpg`, 1600 × 1000 px.

## Treść i metoda

Mapa zawiera dwa panele: cały obszar bufora 15 km od granicy Białegostoku wraz z jawnym uzupełnieniem granicznym zakresu „ok. 15 km” oraz powiększenie rejonu ronda Putry. To mapa zasięgu dowodów fotograficznych, nie inwentaryzacja współrzędnych fizycznych tarcz.

- Podkład jest wyłącznie wykresem geometrii lokalnych GeoJSON OSM. Nie użyto kafli map, ortofotografii ani zewnętrznego podkładu rastrowego.
- Warstwy wejściowe w WGS84 przeliczono biblioteką pyproj na EPSG:2180. Odległości i skale są wyrażone w metrach tego układu; strzałki północy wyznaczono przez projekcję kierunku rosnącej szerokości geograficznej przy stałej długości.
- Użyto wszystkich rekordów fotograficznych z `records.json`, które mają liczbowy geotag. Dane geograficzne są dokładnie wartościami `lat` i `lon` w tych rekordach. Raz rysowano każde źródłowe zdjęcie (Mapillary według key; Commons według curid). Nie przesuwano nakładających się punktów.
- Wynik: **89 zdjęć z geotagiem**, w tym **78 Mapillary** i **11 Commons**, odpowiadających **140 obserwacjom tablic/pól**. Źródłem liczebności jest podana populacja rekordów; pełna lista wejść i ich identyfikatorów jest w `files/G3-MAP002.json`.
- Brak geotagu: G3-C023, G3-C024, G3-C028, G3-C029. Nie wyznaczano tych punktów z domysłu. Rekordy dokumentacji urzędowej nie opisują lokalizacji kamery i również nie są symbolami na mapie.
- OSM_CORE jest zbiorem wybranych jezdni korytarza. Nie przedstawia całej siatki ulic ani pełnej geometrii każdego skrzyżowania.

## Graniczne uzupełnienie zakresu „ok. 15 km”

Rekordy **MX002 i MX003** pochodzą z jednego zdjęcia [Mapillary 503886228724826](https://www.mapillary.com/app/?pKey=503886228724826), autor **kino**, data zdjęcia **2024-07-26**, kamera **53.324651 N, 23.123476 E**. Źródłem wartości i kwalifikacji granicznej są oba rekordy w `records.json` oraz właściwe dane źródłowe Mapillary.

Najkrótsza odległość kamery od granicy Białegostoku wynosi **ESTIMATED 15 177 m**, czyli **177 m poza ścisłym buforem 15 000 m**. Jest to jednoznacznie opisane rozszerzenie do „około 15 km”. Metoda z rekordów: odległość punktu geometry Mapillary od poligonu OSM relation 2910925 po przeliczeniu WGS84 → EPSG:2180, zaokrąglona do 1 m; nie jest to pomiar terenowy. Ponowne obliczenie dla współrzędnych zaokrąglonych w `records.json` zapisano dodatkowo w `files/G3-MAP002.json`.

Na mapie zachowano niezmieniony obrys ścisłego bufora. Graniczne zdjęcie jest zaznaczone czerwoną obwódką i osobnym opisem; nie przesuwano go do wnętrza zakresu. MX002 i MX003 pozostają dwiema obserwacjami z tej samej pozycji kamery. Rekord MX001 dodaje drugie nowe zdjęcie wewnątrz bufora. Data dostępu do źródeł: 2026-11-12.

## Rondo Putry i punkt użytkownika

Punkt z polecenia ma współrzędne **53.152000 N, 23.168000 E**. Środek ronda jest **ESTIMATED: 53.159038 N, 23.151613 E**, według `files/G3-OSM007.json`. Zapisana metoda: centroid wieloboku złożonego z OSM ways 180144451, 257367424, 257367425, 257367428. Są to współrzędne geometrycznego środka oszacowanego z OSM, a nie punkt geodezyjny ani lokalizacja konkretnej tablicy.

Odległość pomiędzy tymi dwoma punktami przeliczono geodezyjnie na elipsoidzie WGS84 (`pyproj.Geod.inv`): **1347.307 m**, na mapie **1,35 km**. Wynik ma status ESTIMATED ze względu na szacowany środek ronda. Linia łącząca punkty nie jest trasą drogową.

## Źródła i atrybucja

1. `files/G3-OSM003.geojson`: wybrane osie jezdni. Publiczne obiekty źródłowe mają adres `https://www.openstreetmap.org/way/<osm_way_id>` zgodnie z polem właściwości. Data dostępu: 2026-11-12.
2. `files/G3-OSM004.geojson`: granica miasta z [OSM relation 2910925](https://www.openstreetmap.org/relation/2910925) i bufor, którego właściwości podają `buffer 15000m in EPSG2180`. Data dostępu: 2026-11-12. Bufor jest obszarem operacyjnym badania, nie granicą administracyjną.
3. `files/G3-OSM007.json`: obliczony centroid ronda oraz punkt z polecenia użytkownika. Źródła geometrii: [way180144451](https://www.openstreetmap.org/way/180144451), [way257367424](https://www.openstreetmap.org/way/257367424), [way257367425](https://www.openstreetmap.org/way/257367425), [way257367428](https://www.openstreetmap.org/way/257367428). Data dostępu: 2026-11-12.
4. `records.json`: geotagi i adresy zdjęć. Autorzy, daty zdjęć, klucze Mapillary i adresy Commons znajdują się w odpowiednich rekordach głównego manifestu; zwięzła lista wszystkich zdjęć użytych do punktów również w `files/G3-MAP002.json`. Data dostępu: 2026-11-12.
5. OSM: **© OpenStreetMap contributors**, [ODbL 1.0](https://www.openstreetmap.org/copyright). Commons: zdjęcia Rakoon, CC0; Mapillary: autorzy wymienieni w rekordach, [zasady CC BY-SA 4.0](https://help.mapillary.com/hc/en-us/articles/115001770409-CC-BY-SA-license-for-open-data). Mapa nie reprodukuje fotografii; wykorzystuje ich przypisane geotagi. Atrybucja fotografii jest zachowana w manifeście.

Opracowanie kartograficzne: ChatGPT dla projektu Kamion. W `files/G3-MAP002.json` zapisano sumy SHA256 czterech plików wejściowych, liczebności, zakres powiększenia i wejściowe geotagi. W pliku danych zachowano pełną listę źródłowych zdjęć wraz z powiązaniem z rekordami.

## Ograniczenia

Geotagi mają dokładność źródeł, której nie poprawiano arbitralnie. Dotyczy to również niepewnego geotagu Commons G3-C005 opisanego w manifeście. Pozycje tablic pozostają UNVERIFIED. Mapa łączy fotografie z lat 2017–2026, więc nie potwierdza aktualnej treści ani ciągłości oznakowania w listopadzie 2026.

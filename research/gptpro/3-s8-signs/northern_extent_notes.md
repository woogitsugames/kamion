# Końcowa kontrola północnego zakresu DK8 i trzy uzupełnienia

Data dostępu: **2026-11-12**. Ten dodatek nie zmienia zamrożonych rekordów MN001–MN024.

## Wynik

Dodano trzy rzeczywiste tablice odczytane na oryginalnych fotografiach Mapillary:

| ID | Tekst dokładny | Typ | Kierunek jazdy | Pozycja kamery WGS84 | Źródło |
|---|---|---|---|---|---|
| MX001 | Leśnictwo Rybniki | Lokalny drogowskaz; symbol urzędowy UNVERIFIED | S/SE, w stronę Białegostoku; grot w prawo | 53.271119, 23.120348 | [1027551232176688](https://www.mapillary.com/app/?pKey=1027551232176688), strudel, 2024-08-15 |
| MX002 | Przewalanka | E-17a, klasyfikacja wizualna ESTIMATED | NW, w stronę Augustowa | 53.324651, 23.123476 | [503886228724826](https://www.mapillary.com/app/?pKey=503886228724826), kino, 2024-07-26 |
| MX003 | Brzozówka Koronna 2 | E-4, klasyfikacja wizualna ESTIMATED; grot w prawo | NW, dojazd do skrętu w prawo | 53.324651, 23.123476 | [503886228724826](https://www.mapillary.com/app/?pKey=503886228724826), kino, 2024-07-26 |

Powyższe teksty są odczytem wskazanych tablic, nie cytatem z metadanych ani nazwy miejscowości w OSM. Trzy wycinki JPG obejrzano ponownie po eksporcie. Są bez retuszu, bez powiększania i bez logo producentów ciężarówek. Wszystkie zdjęcia są na CC BY-SA 4.0; autorzy i modyfikacje zostały wskazane w rekordach. Typ MX001 pozostaje nieustalony — nie przypisano arbitralnie symbolu E.

## Jawne odstępstwo od ścisłego bufora

Północne przecięcie geometrii DK8 z buforem 15 000 m wypada **ESTIMATED 53.322875, 23.126185**, na [OSM way337082082](https://www.openstreetmap.org/way/337082082). Źródła geometrii: `files/G3-OSM003.geojson` i `files/G3-OSM004.geojson`; dostęp 2026-11-12.

Kamera MX002/MX003 leży **ESTIMATED 15 177 m od granicy miasta, czyli 177 m poza ścisłym buforem**. Została włączona jako graniczny fragment zakresu określonego przez zleceniodawcę jako „ok. 15 km”. Kamera MX001 leży ESTIMATED 9 218 m od granicy miasta. Są to odległości kamery, nie zmierzone odległości tablic.

Metoda: najkrótsza odległość od źródłowego punktu `geometry` Mapillary do poligonu administracyjnego Białegostoku ([OSM relation2910925](https://www.openstreetmap.org/relation/2910925)), po przeliczeniu obu geometrii z WGS84 do EPSG:2180. Zaokrąglenie do metra służy jednoznaczności obliczenia; pozycje zdjęć i granica OSM nie są pomiarem terenowym. Plik granicy i jej wersja są udokumentowane w części OSM.

## Dokładny zakres dodatkowego przeglądu

Otworzono ponownie istniejące arkusze sekwencji północnych i południowych. Sprawdzono wizualnie **120 wskazanych klatek**, w tym próbki kontekstowe poza właściwą luką. Pełne klucze, daty, autorzy, orientacje i pozycje wszystkich klatek są w `files/G3-COV001.json`. Numery robocze poniżej odnoszą się do tych samych wpisów w tym pliku.

- `S07`, kino, kierunek N: klatki 0–230, co 5; arkusze obejmują przejazd przez Rybniki i leśny odcinek do szerokości ok.53.309595.
- `S02`, kino, kierunek N: klatki 0–75, co 5; przejrzano leśny odcinek od ok.53.310257 do granicznego fragmentu Przewalanki. MX002 i MX003 są odczytem klatki65.
- `S01`, strudel, kierunek S: klatki 0–70, co 5; część arkusza położona w ścisłym buforze obejmuje odcinek od ok.53.32215 do53.308277.
- `S05`, strudel, kierunek S: klatki 0–75, co 5; dla luki północnej istotne są klatki0–43, od53.279016 do53.263160. Pozostałe widoczne na arkuszu klatki stanowią kontekst wcześniej opracowanego odcinka. MX001 odczytano z klatki20 po pobraniu oryginału.
- Uzupełnienie historyczne `H03`, richlv, kierunek S, 2017-07-15: **26 klatek** sekwencji `014e6hwyqk5pnpzr8w1pr2`, indeksy0–125 co5, od53.309959 do53.278976. Na tej próbce nie znaleziono dalszych potwierdzonych tablic E. To ograniczony przegląd próbek; nie dowód nieistnienia znaków między klatkami ani dowód stanu2024/2026.

## Sprawdzenie luki w metadanych

Wykonano tylko dwa zapytania uzupełniające do publicznego API Mapillary, dla tego samego wąskiego bbox **23.117,53.278,23.131,53.310** (kolejność: zachód,południe,wschód,północ), limit2000:

1. Od2024-01-01: **254 rekordy**, bez linku następnej strony. Z tego strudel miał wyłącznie cztery zdjęcia przy północnym skraju oraz cztery przy południowym skraju. W wybranym zbiorze frontalnych zdjęć z2024 pozostaje więc luka pomiędzy53.279016 a53.308277. Są również zdjęcia kino w przeciwnym kierunku oraz quickness805; te ostatnie nie służyły tutaj do frontalnego odczytu znaków.
2. Od2010-01-01: **1501 rekordów**, bez linku następnej strony. Znaleziono starszy przejazd richlv w kierunku S i przejrzano wspomnianą próbkę26 klatek.

Parametry i wyniki liczebne zapisano w `QUERY_NOTE.json`, `QUERY_ALL_NOTE.json` i `files/G3-COV001.json`. Brak kolejnej strony API nie jest gwarancją kompletności zasobu; nie uznano braku obrazów w odpowiedzi za dowód ich nieistnienia.

## Pliki gotowe do włączenia

`records.json (MX001–003)`, `manifest.csv (MX001–003)`, `files/G3-META001.json`, `files/G3-COV001.json`, `validation.json`, `MN_EXTRA_REPORT.md`, `sources.md`, `QUERY_NOTE.json`, `QUERY_ALL_NOTE.json`, oraz `files/MX001.jpg`–`MX003.jpg`.

Nie dołączać roboczych plików z członem `PRIVATE`, pełnych fotografii ani arkuszy kontaktowych: nie są elementami końcowego dodatku. Finalne metadane i rekordy nie zawierają tokenów ani podpisanych URL.

# gptpro-p1-route-photos — zdjęcia referencyjne poziomu kierowcy, kafl wokół 53,152 N 23,168 E (Białystok)

**Projekt:** Kamion — realistyczny mobilny symulator ciężarówki z naczepą, świat Białegostoku w skali 1:1 z danych OSM i GUGiK. 
**Data opracowania:** 2026-11-13. **Status paczki:** 141 pobranych kadrów + 3 pozycje UNVERIFIED (luki).

## Cel
Zebrać zdjęcia referencyjne z poziomu kierowcy (wysokość oka ok. 2,5 m, widok wzdłuż jezdni) dla 23 ulic, 
2 rond oraz wiaduktów i łącznic S8/DK8 w kaflu wokół 53,152 N 23,168 E w Białymstoku. Dla każdej ulicy ≥ 3 ujęcia 
w obu kierunkach (początek, środek, skrzyżowanie); dla rond i wiaduktów ≥ 6 ujęć, po jednym z każdego wlotu i wylotu; 
co najmniej jedno ujęcie z drugiego sezonu.

## Metoda
1. **Geometrie ulic i obiektów** pobrano z API OSM (`api.openstreetmap.org/api/0.6/map`, 40 kafli bbox 23,080–23,270 / 53,130–53,190; ODbL). 
Z ways o nazwach ulic zbudowano łańcuchy (chainage) do klasyfikacji punktów początku/środka/skrzyżowania; 
wiadukty, mosty i łącznice S8/DK8/DK65/DK19 zidentyfikowano po tagach highway=trunk(_link)/bridge + ref.
2. **Panoramax** (panoramax.xyz, CC BY-SA 4.0): zapytania bbox API `api.panoramax.xyz/api/search`; pobieranie kadrów sd.jpg; 
azymut patrzenia z EXIF (compass) zwracany przez API; data z captured_at. Są to kadry z kamery samochodowej (transport: car) 
— poziom kierowcy.
3. **Wikimedia Commons**: API — geosearch (bbox) + 16 kategorii tematycznych (m.in. Andersa Street in Białystok, 
Krzysztof Putra Roundabout in Białystok, Overpass bridges in Białystok); licencja i autor z extmetadata 
(LicenseShortName, Artist). Pobierano wyłącznie pliki CC0 / CC BY / CC BY-SA.
4. **Mapillary — zgodnie z zasadą A**: API wymaga tokenu; agenci nie mieli tokenu ani przeglądarki, kluczy nie zgadywano. 
Pozycje potencjalne z Mapillary pozostają UNVERIFIED (zapisane jako luka).
5. **Klasyfikacja**: kadr przypisywano do ulicy przy dystansie ≤ 25 m od osi (way) i do ronda ≤ 80 m od środka; 
kadry skrzyżowań mogą być przypisane do 2+ ulic (liczone w obu — konwencja tabeli pokrycia).
6. **Obróbka**: skalowanie do maks. 1600 px dłuższego boku, JPG; pomiar jasności/ostrości/nasycenia/udziału zieleni 
i śniegu (heurystyka barw) → jakość 1–5, sezon (liście/bez liści/śnieg), pora dnia (z godziny lokalnej = UTC+1/+2), 
automatyczne odrzucanie kadrów nocnych i prawdopodobnie kontrasłonecznych (model pozycji słońca — ESTIMATED).

## Najważniejsze ustalenia
- **141 kadrów pobranych**: 50 z Panoramax (CC BY-SA 4.0, poziom kierowcy, znany azymut) + 91 z Wikimedia Commons 
(CC0 × 84, CC BY(-SA) × 7); 3 pozycje UNVERIFIED (ulice bez zdjęć w otwartych źródłach).
- **Sezony**: 89 liście / 34 śnieg / 18 bez liści — większość ulic ma ≥ 2 sezony; 4 ulice tylko 1 sezon (patrz luki).
- **Rondo Putry**: 8 ujęć, w tym 5 poziomu kierowcy ze znanym azymutem (wloty: Al. Tysiąclecia, Andersa, Maczka) + Commons; 
rondo Bieżeństwa 1915: 8 ujęć, ale wyłącznie Commons (poziom pieszy) — kierunki UNVERIFIED.
- **Wiadukty/łącznice S8/DK8**: łącznica DK8 węzeł Andersa/Maczka — 9 ujęć kierowcy w obu kierunkach; wiadukty Maczka 
nad torowiskiem (jezdnia zachodnia i wschodnia — po 3), mosty Maczka nad Białą (2 jezdnie), wiadukt Al. Tysiąclecia (DK8/DK19) — kierowca w obu kierunkach.
- **Odrzucone**: P1-091 — noc/słabe oświetlenie (mean_lum 27,5; automat). Kadry kontrasłoneczne/nocne nie trafiły do ZIP poza tym oznaczonym (kryterium automatu + kontrola).
- **Zero wyników** w Panoramax/Commons dla ulic: Stefana Batorego, Brzeska, Buska (P1-142…144).

## Tabela pokrycia (ulica × kierunek × liczba ujęć × sezony)

Konwencja: kadr skrzyżowania liczy się do każdej ulicy, którą pokrywa. „Kierunek”: azymut znany z EXIF (Panoramax, poziom kierowca) vs UNVERIFIED (Commons — API nie podaje kierunku patrzenia).

| Ulica / obiekt | Ujęcia | Kierunki | Sezony |
|---|---|---|---|
| Generała Władysława Andersa | 10 | 2 kierowca/azymut, 8 UNVERIFIED (Commons) | bez liści,liście,śnieg |
| Generała Stanisława Maczka | 20 | 10 kierowca/azymut, 10 UNVERIFIED (Commons) | bez liści,liście,śnieg |
| Aleja Tysiąclecia Państwa Polskiego | 20 | 10 kierowca/azymut, 10 UNVERIFIED (Commons) | liście,śnieg |
| Bitwy Białostockiej | 8 | 0 kierowca/azymut, 8 UNVERIFIED (Commons) | bez liści,liście,śnieg |
| Białostoczek | 8 | 0 kierowca/azymut, 8 UNVERIFIED (Commons) | bez liści,liście,śnieg |
| Kombatantów | 8 | 0 kierowca/azymut, 8 UNVERIFIED (Commons) | liście,śnieg |
| Michała Motoszko | 6 | 0 kierowca/azymut, 6 UNVERIFIED (Commons) | bez liści,liście,śnieg |
| Stefana Batorego | 0 | — | — |
| Władysława Bełzy | 4 | 0 kierowca/azymut, 4 UNVERIFIED (Commons) | liście,śnieg |
| Wileńska | 8 | 0 kierowca/azymut, 8 UNVERIFIED (Commons) | bez liści,liście |
| Sokólska | 8 | 0 kierowca/azymut, 8 UNVERIFIED (Commons) | liście,śnieg |
| Grodzieńska | 3 | 0 kierowca/azymut, 3 UNVERIFIED (Commons) | bez liści |
| Brzeska | 0 | — | — |
| Buska | 0 | — | — |
| Kowieńska | 3 | 0 kierowca/azymut, 3 UNVERIFIED (Commons) | bez liści |
| Lidzka | 3 | 0 kierowca/azymut, 3 UNVERIFIED (Commons) | bez liści |
| Olsztyńska | 0 | — | — |
| Racławicka | 3 | 0 kierowca/azymut, 3 UNVERIFIED (Commons) | bez liści,śnieg |
| Sitarska | 8 | 0 kierowca/azymut, 8 UNVERIFIED (Commons) | bez liści,liście,śnieg |
| Skidelska | 6 | 0 kierowca/azymut, 6 UNVERIFIED (Commons) | bez liści,liście |
| Wołkowyska | 3 | 0 kierowca/azymut, 3 UNVERIFIED (Commons) | bez liści |
| Łańcucka | 4 | 0 kierowca/azymut, 4 UNVERIFIED (Commons) | bez liści,śnieg |
| Świsłocka | 2 | 0 kierowca/azymut, 2 UNVERIFIED (Commons) | bez liści |
| rondo Krzysztofa Jakuba Putry | 8 | 5 kierowca/azymut, 3 UNVERIFIED (Commons) | liście,śnieg |
| rondo Pamięci Bieżeństwa 1915 roku | 8 | 0 kierowca/azymut, 8 UNVERIFIED (Commons) | bez liści,liście,śnieg |
| kładka ul. Gen. S. Maczka (DK8/DK65) | 2 | 2 kierowca/azymut, 0 UNVERIFIED | liście |
| most ul. Gen. S. Maczka (DK65) nad rzeką Białą – jezdnia zachodnia | 2 | 2 kierowca/azymut, 0 UNVERIFIED | liście |
| łącznica DK8 (węzeł Gen. Andersa/Maczka) | 9 | 9 kierowca/azymut, 0 UNVERIFIED | liście |
| obiekt inżynierski (OSM way 173956083, ref 19) | 1 | 0 kierowca/azymut, 1 UNVERIFIED | bez liści |
| most ul. Gen. S. Maczka (DK65) nad rzeką Białą – jezdnia wschodnia | 1 | 1 kierowca/azymut, 0 UNVERIFIED | liście |
| wiadukt ul. Gen. S. Maczka (DK8/DK65) nad torowiskiem kolejowym – jezdnia wschodnia | 3 | 3 kierowca/azymut, 0 UNVERIFIED | liście |
| wiadukt ul. Gen. S. Maczka (DK8/DK65) nad torowiskiem kolejowym – jezdnia zachodnia | 3 | 2 kierowca/azymut, 1 UNVERIFIED | liście |
| obiekt inżynierski (OSM way 268473388, ref 19) | 1 | 0 kierowca/azymut, 1 UNVERIFIED | liście |
| wiadukt Al. Tysiąclecia PP (DK8/DK19) nad torowiskiem kolejowym – jezdnia zachodnia | 2 | 2 kierowca/azymut, 0 UNVERIFIED | liście |

Azymuty znane (przykład): Al. Tysiąclecia — 42°/242° (oba kierunki), Maczka — 96–99°/271–273°, Andersa przy rondzie — 121°.

## Luki
1. **Brak jakichkolwiek zdjęć** (0 wyników w Panoramax i Commons; pozycje UNVERIFIED P1-142, P1-143, P1-144): 
**Stefana Batorego, Brzeska, Buska**.
2. **Drugi sezon** (wszystkie dostępne kadry z jednej pory roku — zapisane jako luka): Grodzieńska (tylko: bez liści); Kowieńska (tylko: bez liści); Wołkowyska (tylko: bez liści); Świsłocka (tylko: bez liści); Lidzka (tylko: bez liści); kładka ul. Gen. S. Maczka (DK8/DK65) (tylko: liście); most ul. Gen. S. Maczka (DK65) nad rzeką Białą – jezdnia zachodnia (tylko: liście); łącznica DK8 (węzeł Gen. Andersa/Maczka) (tylko: liście); obiekt inżynierski (OSM way 173956083, ref 19) (tylko: bez liści); most ul. Gen. S. Maczka (DK65) nad rzeką Białą – jezdnia wschodnia (tylko: liście); wiadukt ul. Gen. S. Maczka (DK8/DK65) nad torowiskiem kolejowym – jezdnia wschodnia (tylko: liście); wiadukt ul. Gen. S. Maczka (DK8/DK65) nad torowiskiem kolejowym – jezdnia zachodnia (tylko: liście); obiekt inżynierski (OSM way 268473388, ref 19) (tylko: liście); wiadukt Al. Tysiąclecia PP (DK8/DK19) nad torowiskiem kolejowym – jezdnia zachodnia (tylko: liście).
3. **Mapillary**: brak tokenu API i przeglądarki (zasada A) — kluczy nie zgadywano; potencjalnie najlepsze źródło do domknięcia luk 1–2.
4. **Kierunek patrzenia kadrów Commons**: UNVERIFIED (API Commons nie zwraca GPSImgDirection w extmetadata) — kolumna kierunek_deg pusta, w uwagach opis.
5. **Poziom kamery Commons**: głównie poziom pieszy (fotograf uliczny), nie kierowcy — zaznaczono w uwagach każdego wiersza; do kamery kontrolnej gry priorytetowo używać kadrów Panoramax.
6. **Rondo Pamięci Bieżeństwa 1915 r.**: brak kadrów poziomu kierowcy (0 ze znanym azymutem) — spełniona liczba ujęć (8), ale wyloty/wloty UNVERIFIED kierunkowo.
7. **Źródła urzędowe (BIP/ZDiT, GDDKiA, Geoportal)**: nie pobrano z nich zdjęć w tej iteracji — ewentualna dokumentacja przebudów (organizacja ruchu) do kolejnej paczki.

## 10 najlepszych kadrów do kamer kontrolnych gry

| # | id | Dlaczego |
|---|---|---|
| 1 | P1-101 | wlot ronda Putry od ul. Andersa (az 121°) — jedyny kadr kierowcy z tego wlotu; idealny na kamerę przy wjeździe na rondo |
| 2 | P1-102 | wlot ronda Putry od Al. Tysiąclecia (az 242°) — drugi kierunek wlotu, ostre światło południowe, czytelne balustrady i znaki |
| 3 | P1-120 | rondo Putry, wlot od ul. Maczka (az 113°) — trzeci wlot; geometria łuku wewnętrznego ronda z poziomu kabiny |
| 4 | P1-110 | Al. Tysiąclecia, początek (az 42°) — początkowy punkt alei; oś widokowa do kamery nadjeżdżającej od północy |
| 5 | P1-132 | Maczka, skrzyżowanie z ul. Gen. Gustawa Orlicz-Dreszera (az 271°) — skrzyżowanie z sygnalizacją w kierunku zachodnim |
| 6 | P1-096 | Maczka, środek ulicy (az 99°) — rzadkościowy kierunek wschodni; charakter zabudowy i przekroju jezdni |
| 7 | P1-094 | wiadukt Maczka nad torowiskiem, jezdnia zachodnia (az 269°) — widok wzdłuż obiektu inżynierskiego, balustrady, krzywizna |
| 8 | P1-134 | wiadukt Maczka nad torowiskiem, jezdnia wschodnia (az 93°) — ten sam obiekt z przeciwnego kierunku jazdy |
| 9 | P1-092 | most Maczka (DK65) nad rzeką Białą, jezdnia wschodnia (az 101°) — kamera na moście; rzeka i balustrady w kadrze |
| 10 | P1-122 | łącznica DK8 (węzeł Andersa/Maczka, az 273°) — organizacja ruchu na łącznicy węzła; rampa i oznakowanie |

Wszystkie 10 to kadry Panoramax (CC BY-SA 4.0, kamera samochodowa = poziom kierowcy, znany azymut → łatwe ustawienie kamery w silniku gry). 
Pamiętać o share-alike: używać jako referencji, nie jako tekstury.

## Braki i niepewności
- ESTIMATED: sezon (heurystyka barw zieleni/śniegu + miesiąc), pora dnia (z godziny EXIF), jakość 1–5 (ostrość/jasność), 
detekcja kontraśoneczności (model pozycji słońca). Wysokość kamery ~2,5 m nie jest potwierdzona w EXIF — ESTIMATED z typu nośnika (car).
- UNVERIFIED: kierunki kadrów Commons; pozycje luk (P1-142…144 podają środek ulicy z OSM, nie zdjęcie).
- Kadry Commons pochodzą w większości od jednego fotografa (seria „July 2020/November 2020 in Białystok”, stąd sezonowa równomierność); 
drugi sezon zapewniony dzięki Panoramax (2019-08/09 = liście, 2019-12–2020-01 = śnieg) i serii zimowej Commons.

## Samokontrola (20 % z seedem)
- **Seed losowania:** 20261113 (`random.sample`, moduł `random` Pythona).
- **Zakres:** losowanie z ALL pozycji manifestu (144), nie tylko pobranych — wylosowano 29 pozycji (wymóg ≥ 20 %).
- **Wynik: 29/29 OK, 0 FAIL.**
- Sprawdzono dla każdej wylosowanej pozycji: (1) plik files/<id>.jpg istnieje, > 20 KB; (2) url_źródła odpowiada HTTP 200; 
(3) licencja pobrana z API zgodna z manifestem (Commons: extmetadata; Panoramax: properties.license); 
(4) współrzędne: dystans do way ulicy z OSM ≤ 120 m; dla Panoramax dodatkowo zgodność z API < 0,0005°.
- Szczegóły w `audit_20_percent.json` (lista id, wyniki poszczególnych checków).
- Uwaga procesowa: pierwotny skrypt audytu miał 2 błędy (zamiana lon/lat w dystansie; podwójne kodowanie URL tytułów Commons) 
fałszujące wynik FAIL — poprawiono i powtórzono pełny audyt; finalny wynik powyżej pochodzi z poprawionego skryptu.

## Licencje i wykorzystanie
- Panoramax: **CC BY-SA 4.0** — share-alike: używać jako referencji/kamer kontrolnych, nie jako tekstur; atrybucja „stanton / Panoramax” obowiązkowa.
- Wikimedia Commons: CC0 (84), CC BY 3.0/3.0 pl (3), CC BY-SA 3.0 (3), CC BY-SA 4.0 (1) — autorzy w manifeście (kolumna autor).
- OSM (geometrie): ODbL, © OpenStreetMap contributors.
- Wszystkie pobrane pliki mają licencję dozwoloną do użytku komercyjnego; brak plików NC/ND w ZIP; nie wykryto marek producentów ciężarówek w kadrach referencyjnych (kadry uliczne, pojazdy przypadkowe — nie stanowią promocji marki).

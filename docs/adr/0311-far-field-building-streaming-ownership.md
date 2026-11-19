# ADR 0311 — Far-field poza korytarzem streamingu

Status: Accepted (implementacja źródłowa, 2026-11-19); walidacja Windows/obrazu po przebudowie otwarta.

## Problem

ADR 0085 kompresuje położenie obiektów spoza kafla do pasa ≤660 m od jego granicy.
Wykluczenie tylko własnego kafla nie chroni dróg sąsiada. Budynek odległy o kilka
kilometrów może przykryć DK65 i zniknąć po przejściu sąsiada do Ready. Dowód właściciela:
`owner-01-dk8-wiadukt.webp`, faktycznie DK65/Ełcka, `dk65-04`, t1200→1210
(raport `artifacts/drive-review-s24/REPORT.md` w repo właściciela).

## Decyzja

- Zarejestrowane bbox z `regions.REGIONS` należą do prawdziwych kafli od początku,
  również przed importem, przy niedostępnej scenie lub przekroczonym budżecie pamięci.
- Dodatkowo rezerwujemy ≥400 m od tras `Data/Regions/*/route_start.json` (`points_en`,
  lokalne EN przeliczone przez origin). To WORKING_VALUE równe domyślnemu promieniowi
  ładowania: 25 m/s × (8+1+1) s + 150 m. Nie jest gwarancją dla dowolnej prędkości;
  pełny bbox sąsiada pozostaje niezależnym zabezpieczeniem. Bufor uwzględnia błąd cięciw.
- Odrzucamy cały obrys prostokąta przed i po kompresji, przed rozdzieleniem na sektory
  i skyline. Ta sama lista trafia do masek apron. Istniejąca kontrola pełnego obrysu
  źródłowego przy ekstrakcji pozostaje. Nowa polityka działa po cache GIS, bez zmiany
  danych źródłowych i bez potrzeby ponownej ekstrakcji BDOT/OSM.
- QA/manifest zachowują liczniki źródłowe, a `streaming_building_policy` zapisuje
  osobno source/retained/excluded oraz hashe registry i tras (LF/CRLF znormalizowane).
- Runtime od rejestracji kafla ukrywa kierunkowe sektory w stronę każdego sąsiada
  grafu, także diagonalnego. Ich widoczność nie zależy od Loading/Ready/Unloading.
  Zamknięcia i apron nadal zależą od gotowości scen. Tryb bez streamera pozostaje
  obsługiwany przez generator; stała rezerwacja dotyczy także planowanych kafli.
- Dachy i nieokienne pasy pod dachem istnieją również na Low. Biura dostają osobny
  pas pod dachem. Domy zachowują dachy dwuspadowe, hale/bloki/biura dachy płaskie;
  nie wymyślamy spadzistych dachów dla hal. Palety główne pochodzą z `materials.M`,
  używanego przez prawdziwe kafle; geometria nie dodaje materiałów ani tekstur.

## Konsekwencje i walidacja

Celowo mniej zastępczego tła po stronie planowanego, jeszcze niedostępnego kafla.
Nie jest to cross-fade ani rozwiązanie popu zwykłych chunków. Skyline poza korytarzem
pozostaje osobną warstwą; jego pojawienie przy ładowaniu całej sceny nie jest rozwiązane.
Nie zmieniamy opóźnień streamingu, fizyki ani wysokości budynków GIS.

Testy pytest sprawdzają obrys przed/po kompresji, trasę rzeczywistego korytarza,
skyline, zmianę wejścia po cache, dachy i integrację masek/QA. Wspólne testy EditMode
sprawdzają stałą widoczność podczas całego cyklu sąsiada; można wykonać je runnerem
.NET bez Unity. Wyniki i zakres przebudowy: `docs/reports/farfield-blocks-cli-s24.md`.
Budżet trójkątów i końcowy obraz wymagają pomiaru po regeneracji; lokalnie jej nie wykonano.

# DK65, kafel dk65-09 — pasy przydrożne i układ koron

Odczyt i osobny ogląd 2026-11-16, bez dokładnej godziny. **1 nowy pobrany kadr ortofoto WMS, 0 link-only fotografii, 0 nowych zdjęć ulicznych.** To nowa bitmapa szerszego wycinka znanego punktu, nie nowy nalot ani niezależna druga ekspozycja zdjęcia.

## Dlaczego ten punkt

Przejrzano `tiles_wgs84.json`, `km_points.json`, manifest K1 i główny 04. W K1 kafle dk65-03, dk65-09 i dk65-11 mają po 2 wpisy z dokładnie takim oznaczeniem kafla. W dk65-09 są K1-020 — wąski kadr 80 × 80 m — i K1-054 — rekord sprawdzenia pokrycia ulicznego, nie przyjęta fotografia uliczna. Nie znaleziono dodatkowego jawnego oznaczenia dk65-09 lub km 21.65 w głównym manifeście 04. **To selekcja jednego ze słabiej opisanych fragmentów na podstawie indeksu; wpisy bez oznaczenia kafla mogą obejmować sąsiedztwo, więc nie jest to pełny przestrzenny spis wszystkich zdjęć.** Kafel 11 otrzymał już m.in. nowe kadry KS20; tego celu nie powtarzano.

Punkt centralny to istniejący K1 **km trasy 21,65**, EPSG:2180 E 764597,1 / N 607326,7, WGS84 53,26498 N / 22,969139 E. Lokalny K1 wskazuje way 27718745, ref=65. **Nie jest to państwowy kilometraż DK65 ani GPS aparatu.** Środek leży w dk65-09; wschodni fragment większego wycinka przechodzi przez granicę kafla w stronę dk65-08.

## Co rzeczywiście widać

SOURCED [osobny ogląd `04-T09V26-01.jpg`]: szara jezdnia przecina obraz ukośnie od północnego zachodu do południowego wschodu. Po stronie południowo-zachodniej jest długa jasna wstęga przy krawędzi asfaltu, za nią szeroki otwarty pas o trawiastej/brunatnej powierzchni, drobnych zielonych plamach i miejscami powtarzalnym układzie małych skupień. Dalej zaczyna się zwarty kompleks większych koron. Nie określono, czy drobne plamy odpowiadają drzewkom, krzewom lub innemu pokryciu.

Po stronie północno-wschodniej duże korony tworzą nieregularny pas pomiędzy drogą a polami. Jego szerokość wizualnie się zmienia; między koronami są przerwy i różne odcienie zieleni. To nie dowód projektowanej regularnej alei ani konkretnego gatunku. Jasna prosta linia w polu dochodzi do obrzeża tego pasa, lecz dalszy przebieg pod koronami i połączenie z jezdnią są niewidoczne. **Zjazd w tym miejscu pozostaje UNVERIFIED.**

**UNVERIFIED:** rów jako obiekt o określonym przekroju, jego głębokość i połączenia, rura lub czoło przepustu, rodzaj materiału jasnego pasa, rozstaw pni, wysokości, gatunki, granica pasa drogowego i bieżący stan robót. Nie utożsamiono cienia ani barwnej wstęgi z odwodnieniem. Nie przeniesiono gatunku SO z innych danych BDL na widoczny pas koron. Brak czytelnych cienkich linii jezdni na tym rastrze nie dowodzi braku oznakowania w terenie.

## Skala i datowanie

SOURCED [parametry żądania]: WMS 1.1.1, EPSG:2180, bbox **[764457.1, 607186.7, 764737.1, 607466.7]**, 800 × 800 px. Obszar 280 × 280 m daje **0,35 m/px w żądanym rastrze mapy**. To nie dokładność ortofotomapy ani natywna rozdzielczość fotografii. Nie wykonywano nowych pomiarów odległości; nie podajemy metrów ze wzrokowego wrażenia.

Data nalotu i jednolitość aktualnej mozaiki WMS są UNVERIFIED. Nie przypisano nowemu wycinkowi datowania starego arkusza K1 i nie nazwano go stanem 2026. Góra obrazu to północ siatkowa EPSG:2180, nie ustalony kierunek aparatu względem północy geograficznej/magnetycznej.

Źródło i zasady wykorzystania: GUGiK, [oficjalna dokumentacja ORTO](https://www.geoportal.gov.pl/pl/dane/ortofotomapa-orto/), wskazany tam WMS HighResolution i bezpłatne/dowolne wykorzystanie danych. Nie przypisano fikcyjnej CC. Pełne żądanie, SHA256 i indeks selekcji są w `sources.json`.

Wystarczył jeden GetMap, HTTP 200 image/jpeg, User-Agent `Mozilla/5.0`. Kanoniczny plik 800 × 800 px / 195 563 B znajduje się tylko w `files/`, w limicie gita; **nie utworzono identycznej kopii raw**. We własnym raw R26 zapisano wyłącznie metadane żądania. Bez Chrome, Mapillary API, OSM API, Overpass, Commons, Flickr, Google i obrazów AI. Parenty, kod gry i git bez zmian.

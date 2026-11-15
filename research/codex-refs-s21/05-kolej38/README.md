# 05 — Linia38: elektryfikacja i stan zastany kontra projekt — WIP

3 rekordy dokumentacyjne, 0 fotografii terenowych pobranych / 0 kadrów link-only. Nie kopiowano do repo dokumentów PKP ani renderu ich stron. W manifeście odnośniki i własne parafrazy danych.

## Ustalenia

05-D01/02: SOURCED [PKP PLK, Id12, stan07.09.2026, tabela6,s123 drukowana = strona121 PDF]. Sprawdzono pełny render strony i kontekst sąsiednich wierszy37/39/40. Elektryfikacja jest cechą istniejącego odcinka. Dla napięcia3kV źródło to nie daje potwierdzenia: UNVERIFIED. W korytarzu Knyszyna nie przyjmować pełnej dwutorowości tylko z planów inwestycji.

05-D03: SOURCED [PKP PLK,15.09.2026, Więcej Rail Baltiki]. Docelowy drugi tor i zastępowanie przejazdów to zakres modernizacji, nie potwierdzenie wykonania w listopadzie2026.

## Luki

Kategorie konkretnych przejazdów A–D, aktualne urządzenia i rogatki, znakiG-3/G-4, materiał nawierzchni, rozstaw i typ słupów oraz wizualny stan podsypki — UNVERIFIED; brak nowego kadru terenowego. Stan energetyczny odcinka podczas robót i zamknięcia ruchu nie wynikają z ewidencyjnej cechy „zelektryfikowana”.

## Odczyt i ograniczenia

StarszyURL Id12 z lutego2025 zwraca404; aktualny odnaleziono przez oficjalny katalog instrukcji PKP. Lokalny transfer aktualnegoPDF był krótszy niż nagłówekContent-Length; zapisano bajty poza gitem, Poppler ostrzegł o strukturzeXRef, ale wyrenderował czytelną pełną stronę123. Ta strona została obejrzana; nie poświadczono integralności całegoPDF. Serwer web odczytał dokument255stron i ten sam wiersz. `data/source-read.json` rejestruje tę sytuację. Pojedyncze zapytanie Overpass o tagi linii38 zwróciło406, bez powtarzania i bez wnioskowania z braku odpowiedzi.

## Reguły kategorii i znaków

`regulations.csv`: 7 wpisów z §6, §80 i §81 rozporządzenia MI z09.07.2025, Dz.U.2025poz.1105. Pełne strony3,19,20 obejrzane osobno. ELI przy odczycie15.11.2026 oznacza akt jako obowiązujący, wejście27.08.2025; metadane w `data/eli-2025-1105-status.json`. Według ELI zastąpił m.in. rozporządzenie2015poz.1744 i jego wymienione zmiany. Reguły w tabeli nie przypisują kategorii konkretnym przejazdom. Brak geometrycznych wymiarów samych znaków i rogatek.

## Historyczny kadr stacji

05-P01: ponownie obejrzana fotografia K1-P32 z2013r. SOURCED [obraz, link w manifeście] — poprzeczna brama kratowa sieci trakcyjnej, ukośne wsporniki, podwieszenia i przewody, latarnie peronowe, ciemne podkłady i miejscowa roślinność w torowisku. Typ podkładów i uziarnienie podsypki UNVERIFIED. To 1 miniatura istniejącego kadru,0 nowych pobrań zdjęć; nie jest kadrem przejazdu ani potwierdzeniem wyglądu stacji po modernizacji2026.

## OSM — punkty dalszego poszukiwania, nie inwentaryzacja

05-O01…O03 zachowują identyfikatory trzech węzłów przejazdowych blisko korytarza z istniejącego zapytania K1. Ich tagi nie zawierają wystarczających danych do A–D; brak tagu rogatki nie dowodzi braku rogatki. 05-O04 rozdziela tagi istniejącego napięcia i proposed na moście. Dane, identyfikatory, czasy edycji i hash źródła w `data/osm-crossing-and-voltage-evidence.json`. To ponowne wykorzystanie otwartych danych K1, bez nowego zapytaniaOverpass i bez nowych fotografii. Napięcie3000V jest SOURCED jako tag OSM, ale pozostaje niepotwierdzone niezależnym dokumentem zarządcy. Proponowane25000V nie są dowodem wykonania.

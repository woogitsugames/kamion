# ADR 0111 — dowody porównań zdjęcie | render bramki 3

## Zakres
Sesja 4, dziedzina sbs: narzędzie, pozy kamer, rejestr źródeł, adnotacje i artefakty. Bez zmian kodu świata, shaderów i runtime.

## r1 — wiarygodność i kompletność dowodów
Gałąź gpt-sbs-r1; renderowany i walidowany kod d0dca81e, baza świata main 4c9905b1. Pełny świeży import i zestaw z jednej epoki. Narzędzie i kompletność pakietu otrzymały PASS niezależnego recenzenta. Kalibracja pozostaje częściowa, a bramka jakości świata UNVERIFIED.

Klasy pozy: A — dobrze dopasowana, B — przybliżona, C — odrzucona lub niesprawdzona. Brak pola oznacza C; nieznane wartości są błędem. Domyślna kompozycja dopuszcza wyłącznie A/B. Sześć błędnych J1, osiem przesuniętych J2, 2948 i dwa nowe Commons pozostają C. Nie awansowano żadnej pozy na podstawie samej hipotezy lub histogramu.
Zestaw liczy 42 zdjęcia: 40 Mapillary oraz Commons cm109685822 (Rakoon, CC0, około 230 m G3-A) i cm92458760 (Rakoon, CC BY 3.0, około 249 m). Geotagi tych dwóch źródeł nie stanowią potwierdzonego pokrycia. Pierwsze 300 m nadal bez zaakceptowanej pary; 0–200 m bez kandydatów lokalnych. Pierwsza próba dodatkowego pobrania Mapillary zakończyła się błędem DNS.
Bieżący podział: 25 B, 17 C, brak A. Powstało 168 renderów w Low/High × clear/overcast, 100 arkuszy B i 68 jawnych wykluczeń w czterech stanach. 28 stron przeglądu obejmuje wszystkie B. Oddzielnie zachowano 144 diagnostyczne warianty i 16 galerii.

Horyzont 2948595898752384 wyznaczono z przecięcia dwóch wskazanych krawędzi jezdni: 0,5249381 wysokości kadru. Spadek jezdni, kierunek i roll nadal są WORKING_VALUE. Dla 326454 wariant z horyzontem około 0,891 i heading +5 stopni poprawia punkt zbiegu, lecz recenzent potwierdził potrzebę pozostawienia C. Próby XY, oryginalnego GPS, heading oraz FOV nie dały dostatecznej podstawy do zatwierdzenia pozostałych C.

## Integralność i adnotacje
Capture zapisuje po Acquire SHA kamer, referencji, świata i specyfikacji materiałów, commit gałęzi, bazę main, czas, tier, światło, wymiary i SHA każdego renderu. Po renderze ponownie sprawdzamy wejścia. Kompozycja odrzuca nieukończone, zmienione albo mieszane epoki, tiery, światło i obrazy. Dawne rekonstrukcje wymagają jawnego --historical; --inputs wskazuje migawkę. Archiwum inputs.zip zachowuje pierwotne bajty niezależnie od konwersji końców linii w gicie.
Sbs_landmarks.json jest osobnym rejestrem punktów, więc późniejsza adnotacja nie zmienia wejść renderu. Punkty wiążą się z poprawnymi SHA zdjęcia i renderu; zmiana obrazu daje STALE, brak SHA — UNBOUND_IMAGES, jeden punkt — INSUFFICIENT_ANCHORS. Obliczany błąd w pikselach pozostaje ręcznym WORKING_VALUE i nie awansuje klasy. Nadal potrzeba 2–3 potwierdzonych kotwic do kalibracji C.
Fotometria wszystkich obecnych kadrów pozostaje wyłączona do weryfikacji masek i zgodności oświetlenia. Histogramy mają charakter diagnostyczny, nie stanowią pomiaru albedo ani wyniku bramki. Licencje, autorzy, URL i SHA są rejestrowane osobno dla każdego zdjęcia. Zdjęcia nie trafiają do builda ani gita.

## Limity zasobów
Ciężkie generacje, fidelity, testy oraz duże kompozycje korzystają z puli heavy, maksymalnie 3, z właścicielem równym bieżącej gałęzi i Release w finally. Pełny GIS tylko na końcu rundy przez -EndOfRound. Unity ma osobną pulę maksymalnie 4 i właściciela gpt-sbs, z osobnym Acquire/Release przed każdym importem, testem i renderem. Korzystamy z aktualnego skryptu z main bez edycji wspólnej implementacji. Duży próg stale zapobiega automatycznemu usuwaniu cudzych slotów; sprawdzanie co 7 s, a po długim oczekiwaniu GIS co 1 s, nie zmienia limitów.

## Walidacja końcowa r1
SBS: 40/40. EditMode: 261/261. Końcowy GIS: 523 passed, 1 xfailed, 663,68 s. Generacja świata: kod 0, 918 s, brak fallback=True; SHA 64/64 GLB zgodne z manifestem. PBR: kod 0, 734 s oraz 1 s uzupełnienia brakującej lokalnie warstwy zdjęcia asfaltu. Import: 64 chunki, Low+High. Audyt końcowy: wszystkie 168 renderów i 100 arkuszy spójne, jeden HEAD d0dca81e.
W 42 identycznych kadrach Low overcast przed i po zmianach narzędzia estymacje draws geometrii, draws instancji i trójkątów nie zmieniły się. Pełne 168 wierszy zachowano osobno, bez ukrywania instancji. Są to estymacje CPU edytora przed batchingiem, nie liczniki GPU ani pomiar A16. Nie wykonywano testów telefonu. Produkty generatorów poza domeną sbs nie zostały zacommitowane; przywrócono ich wersje z HEAD po zapisaniu dowodów.

## Kolejne rundy
Ten sam worktree, gałęzie gpt-sbs-r2 i następne, merge main przed rundą, bez scalania do main i bez pushowania. R2: nowe metryki i raport HTML z trendem oraz odświeżanie wszystkich par około co 6 h. R3: ranking odstępstw dla sesji. Dalszy największy problem sbs: kalibracja C, w tym możliwy zły poziom jezdni przy mostach i brak początku trasy. Praca trwa do około 12.11.2026, 21:31 Europe/Warsaw.

## r2 — metryki obrazu i raport D51
Formalna recenzja świata po r1, REVIEW-2026-11-11-s11-sbs-r1-D51.md, zmieniła stan bramki z nieocenionego na FAIL: 12 kadrów rozpoznawalnych, 11 częściowych i 2 nierozpoznawalne. Raport zachowuje ten wynik i pełną kohortę 25 B, w tym cztery zastrzeżenia pozy. Nie ukrywa negatywnych ocen przez samo usunięcie kadru.

Metryki v2 dodają kontrast RMS, kontrast percentylowy, gradient przy szerokości do 640 px i maski próbek z wyłączeniami. Domyślne heurystyki nieba/asfaltu pozostają orientacyjne. Ręczna kwalifikacja wymaga obu SHA, notatki kontroli i zgodnego światła; nie zmienia klasy pozy ani D51. Małe próbki trzech Low-clear r1 sprawdzono na nakładkach. Różny kierunek słońca i cienie ograniczają interpretację; to diagnostyka obrazu, nie pomiar albedo.

Trend wymaga identycznego zdjęcia, pozy, masek, definicji metryk, tieru, światła oraz rozdzielczości źródła, analizy i gradientu. Próbki niesprawdzone lub C są wykluczone. Brak zgodnych danych jest jawnym brakiem trendu, a nie zerową różnicą. Ocenę D51 można przypisać bieżącej parze tylko po zgodności poprawnych SHA zdjęcia i renderu. Brak jawnie wskazanego pliku recenzji jest błędem; domyślnym źródłem jest repozytoryjny sbs_recognition.json.

Raport HTML jest lokalny, bez zasobów sieciowych; zawiera źródła, licencje, epokę, wybór rundy i stanu oraz osobny przełącznik diagnostyki C. Diagnostyka musi zgadzać się z epoką pomiarów i nie może awansować wykluczonego kadru. Końcowy raport r1/r2 sprawdzono przy 1280×960 i 390×844, łącznie z historią, przełącznikami i 42 kartami C. Naprawiono zawijanie długich opisów; szerokość dokumentu 390 px przy viewport 390 px. Konsola bez błędów i ostrzeżeń.

Walidacja r2: generator kod 0, 457 s, bez fallback=True; import 64 chunków Low+High; EditMode 261/261; testy SBS 78/78; pełny GIS 561 passed, 1 xfailed, 620,06 s. Audyt sprawdził rzeczywiste bajty 128 GLB, 168 raw, 100 B, 168 arkuszy diagnostycznych, ZIP wejść i 168 wierszy liczników. Własny przegląd objął 100 B; niezależny przegląd narzędzia/kompletności PASS, bez nowego zaliczenia świata. Kod GIS e386b929, render b9b5574e. Oba warianty siatek zgodne z r1; wszystkie delty liczników Low/High równe 0, bez pomiaru GPU/telefonu.

Trend r2 obejmuje trzy zgodne Low-clear, mediany zmiany błędu 0; pozostałe stany bez porównywalnych próbek. Ostatnia formalna ocena pozostaje r1 FAIL 12/11/2. Diagnostyka 182: 16 hipotez, nadal C; zapytanie początku trasy nie dostarczyło nowego kandydata do 300 m. Produkcyjne pozy nie zmieniły się. Osiem pochodnych generatora przywrócono po końcowym GIS; wejścia dowodów zachowano w migawce. Main otrzymał w trakcie walidacji nowe scalenia (w tym 0125), których obrazy r2 nie przedstawiają. R3 zaczyna od aktualnego main: świeży świat, ranking i diagnostyka wskazanych pozy G3-B.

## r3 — aktualna baza świata, ranking i historia ocen (walidacja trwa)

Baza świata main 9874d98c zawiera 0125 i scalone domeny r1. Późniejszy merge main 14ccbaf1 zmienił wyłącznie obsługę integracji i slotów. PBR i świat wygenerowano ponownie bez fallback=True, import obejmuje 64 chunki Low+High, EditMode 317/317. Pełna nowa seria 168 raw pochodzi z jednego HEAD 62d45b92, z kamerami i zdjęciami takimi samymi jak w r2. Przerwa w wykonaniu 03:42–09:04 oznaczała pominięcie planowanego odświeżenia około 06:19; uzupełniono je pełną serią 09:06–09:09. Przyczyna przerwy nie została ustalona.

Niezależny pełny przegląd 25 B Low-overcast dał FAIL: 13 rozpoznawalnych, 11 częściowych, 1 nierozpoznawalny. Własny przegląd obejmuje pozostałe 75 B (Low-clear i oba High), z zapisanymi SHA. Ranking docs/refs/sbs-priorities.md odróżnia brakujące najbliższe podpory od istniejących dalszych, obecne tablice/ekrany od niewłaściwej projekcji oraz LOD portalu od błędu kamery. Nie przypisuje przyszłych poprawek innych domen do naszej bazy.

Przeprowadzono 18 pierwszych prób oraz drugą serię 30 zaplanowanych prób, z czego 28 wyrenderowano, a dwie odrzucono przed renderem z braku bezpiecznie ustalonej powierzchni. Dla dwóch kamer zastosowano połączoną oś jezdni i ciągłość wysokości rzeczywistego asfaltu GLB, zamiast cofania po kierunku spojrzenia na pobocze. Wszystkie próby nadal C: żadna nie ma dwóch jednoznacznych, niezależnych kotwic. Portal ma wymiary robocze modelu; jego skala nie jest pomiarem pozy. Konflikt pionowej projekcji dalszej drogi i portalu zapisano do minimalnej kolejnej próby pitch przy stałym XY.

Raport obsługuje wersjonowany rejestr ocen D51. Dokładne przypisanie wymaga obu SHA zdjęcia i renderu; w przeciwnym razie wolno pokazać tylko ocenę ze snapshotu danej rundy z jawnym zastrzeżeniem. Przy braku snapshotu lub kamery pokazuje brak oceny. Starsze piksele nie dziedziczą przyszłego uzasadnienia. Niezależny przegląd kodu bafa7544 PASS. Podgląd z nową oceną sprawdzono na 12 kombinacjach runda/stan i szerokościach 1280/390 px, bez przepełnienia; konsola bez błędów/ostrzeżeń, C=42. Zapisany kandydat rejestru nie został jeszcze wprowadzony do Data do czasu testów.

Nowe rendery unieważniły wcześniejsze maski: r3 ma zero kwalifikowanych próbek fotometrycznych. Trend r2→r3 jest NO_COMPARABLE_SAMPLES, nie zerową zmianą. Estymacje wszystkich 168 kamer zapisano osobno od pomiarów telefonu, których nie wykonywano. Maksimum Low wynosi 810 draws (445 statycznych + 365 instancji), High 1376 (945 + 431). Delty versus r2 obejmują zintegrowane zmiany świata, nie izolowany koszt narzędzia SBS: Low −17…+29, High −33…+49.

Stan tej sekcji: walidacja trwa. Pojedynczy pytest raportu oczekuje na heavy; audyt rzeczywistych 128 GLB, fidelity i końcowy pełny GIS nie zostały jeszcze wykonane w r3. Dostawy do main/artifacts są oznaczone PRESTAGE_NOT_FINAL_DELIVERY. Brak końcowego REPORT.md oraz brak merge/push. Wymagane wyniki zostaną dopisane po ich rzeczywistym zakończeniu.

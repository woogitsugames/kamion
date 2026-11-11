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
Ciężkie generacje, fidelity, testy oraz duże kompozycje korzystają z puli heavy, maksymalnie 3, z właścicielem równym bieżącej gałęzi i Release w finally. Pełny GIS tylko na końcu rundy przez -EndOfRound. Unity ma osobną pulę maksymalnie 4 i właściciela gpt-sbs, z osobnym Acquire/Release przed każdym importem, testem i renderem. Korzystamy z aktualnego skryptu z main bez edycji wspólnej implementacji. Duży próg stale zapobiega automatycznemu usuwaniu cudzych slotów; sprawdzanie co 7 s nie zmienia limitów.

## Walidacja końcowa r1
SBS: 40/40. EditMode: 261/261. Końcowy GIS: 523 passed, 1 xfailed, 663,68 s. Generacja świata: kod 0, 918 s, brak fallback=True; SHA 64/64 GLB zgodne z manifestem. PBR: kod 0, 734 s oraz 1 s uzupełnienia brakującej lokalnie warstwy zdjęcia asfaltu. Import: 64 chunki, Low+High. Audyt końcowy: wszystkie 168 renderów i 100 arkuszy spójne, jeden HEAD d0dca81e.
W 42 identycznych kadrach Low overcast przed i po zmianach narzędzia estymacje draws geometrii, draws instancji i trójkątów nie zmieniły się. Pełne 168 wierszy zachowano osobno, bez ukrywania instancji. Są to estymacje CPU edytora przed batchingiem, nie liczniki GPU ani pomiar A16. Nie wykonywano testów telefonu. Produkty generatorów poza domeną sbs nie zostały zacommitowane; przywrócono ich wersje z HEAD po zapisaniu dowodów.

## Kolejne rundy
Ten sam worktree, gałęzie gpt-sbs-r2 i następne, merge main przed rundą, bez scalania do main i bez pushowania. R2: nowe metryki i raport HTML z trendem oraz odświeżanie wszystkich par około co 6 h. R3: ranking odstępstw dla sesji. Dalszy największy problem sbs: kalibracja C, w tym możliwy zły poziom jezdni przy mostach i brak początku trasy. Praca trwa do około 12.11.2026, 21:31 Europe/Warsaw.

## r2 — metryki obrazu i raport D51 (w trakcie)
Formalna recenzja świata po r1, REVIEW-2026-11-11-s11-sbs-r1-D51.md, zmieniła stan bramki z nieocenionego na FAIL: 12 kadrów rozpoznawalnych, 11 częściowych i 2 nierozpoznawalne. Raport zachowuje ten wynik i pełną kohortę 25 B, w tym cztery zastrzeżenia pozy. Nie ukrywa negatywnych ocen przez samo usunięcie kadru.

Metryki v2 dodają kontrast RMS, kontrast percentylowy, gradient przy szerokości do 640 px i maski próbek z wyłączeniami. Domyślne heurystyki nieba/asfaltu pozostają orientacyjne. Ręczna kwalifikacja wymaga obu SHA, notatki kontroli i zgodnego światła; nie zmienia klasy pozy ani D51. Małe próbki trzech Low-clear r1 sprawdzono na nakładkach. Różny kierunek słońca i cienie ograniczają interpretację; to diagnostyka obrazu, nie pomiar albedo.

Trend wymaga identycznego zdjęcia, pozy, masek, definicji metryk, tieru, światła oraz rozdzielczości źródła, analizy i gradientu. Próbki niesprawdzone lub C są wykluczone. Brak zgodnych danych jest jawnym brakiem trendu, a nie zerową różnicą. Ocenę D51 można przypisać bieżącej parze tylko po zgodności poprawnych SHA zdjęcia i renderu. Brak jawnie wskazanego pliku recenzji jest błędem; domyślnym źródłem jest repozytoryjny sbs_recognition.json.

Raport HTML jest lokalny, bez zasobów sieciowych; zawiera źródła, licencje, epokę, wybór rundy i stanu oraz osobny przełącznik diagnostyki C. Diagnostyka musi zgadzać się z epoką pomiarów i nie może awansować wykluczonego kadru. Podgląd starych danych r1 obejrzano przy 1280×960 i 390×844. Nowy świat i końcowe testy r2 pozostają w toku; ten zapis nie oznacza zakończenia rundy.

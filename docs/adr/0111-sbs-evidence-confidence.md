# ADR 0111 — wiarygodność porównań zdjęcie | render bramki 3

## Zakres
Sesja 4, dziedzina sbs. Zmiany dotyczą narzędzia, danych pozy kamer i dowodów. Nie zmieniamy geometrii świata ani ustawień runtime.

## r1 — klasyfikacja pozy
Wprowadzono jawne pose_confidence: A — dobrze dopasowana, B — przybliżona, C — odrzucona lub niesprawdzona. Brak pola oznacza C. Domyślny zestaw dowodowy obejmuje tylko A i B; klasy C można składać diagnostycznie przez --include-rejected. Klasa B nie oznacza zaliczenia bramki.
Sześć błędnych par J1 pozostaje C do potwierdzonej kalibracji. Osiem przesuniętych par J2 i horyzont 2948 również początkowo wyłączono. Przygotowano 72 próby J2 na siatce XY −5,5/0/+5,5 m, przy stałym kierunku i wysokości. Nie przypisujemy rozbieżności GPS ani geometrii bez obejrzenia świeżych wyników.
Horyzont 2948595898752384 wynika z przecięcia dwóch zaznaczonych krawędzi jezdni w wyprostowanym zdjęciu: 0,5249381 wysokości kadru. To pomiar punktu zbiegu wybranych odcinków, nie geodezyjnego poziomu. Spadek drogi i roll pozostają WORKING_VALUE.

## Źródła i metryki
Zestaw zawiera 40 zdjęć Mapillary oraz dwa lokalne zdjęcia Commons: cm109685822 (Rakoon, CC0, około 230 m G3-A) i cm92458760 (Rakoon, CC BY 3.0, około 249 m). Kandydaci Commons mają klasę C: miniatury nie zawierają EXIF, a kierunek, FOV i wysokość wymagają kalibracji. Odcinek 0–200 m nadal bez zdjęć. Pobranie dodatkowych referencji Mapillary nie powiodło się z powodu DNS.
Bieżący podział: 25 par B, 17 par C, brak par A. Fotometria jest wyłączona do sprawdzenia masek nieba, asfaltu i maski samochodu. Zachodów słońca nie porównujemy fotometrycznie z dniem. Epoka danych świata pozostaje UNVERIFIED; zdjęcia sprzed 2020 r. mają ostrzeżenie historyczne.
Licencje i SHA są zapisane osobno dla każdego zdjęcia. Zdjęcia pozostają poza gitem i buildem. Cache rektyfikacji zależy od SHA źródła i parametrów obiektywu.

## Integralność renderów
Dla każdej grupy proporcji obrazu zapisujemy SHA kamer, referencji, manifestu świata i specyfikacji materiałów, commit gałęzi, bazę main rzeczywiście zawartą w gałęzi, obserwowany tip main, czas, tier, światło i SHA renderów. Kompozycja odrzuca stary, nieukończony lub podmieniony zapis. Starsze materiały bez rejestru mają status UNVERIFIED. Arkusze mają szerokość 960 px i jawne zastrzeżenia fotometrii.

## Limity zasobów
Ciężkie generacje, fidelity i pojedyncze pliki pytest korzystają z puli heavy (maksymalnie 3), z właścicielem równym bieżącej gałęzi oraz Release w finally. Pełny GIS uruchamiamy tylko na końcu rundy, z jawnym -EndOfRound. Unity ma oddzielną pulę maksymalnie 4 i właściciela gpt-sbs; każdy import, test i render ma osobne Acquire/Release. Efekty uboczne ustawień Unity są cofane.
Używamy aktualnego skryptu slotów z main bez edycji wspólnej implementacji. Sprawdzanie kolejki co 7 s nie zmienia limitów. Długi próg stale zapobiega automatycznemu usuwaniu cudzych slotów przez nasze wywołania.

## Walidacja w toku
Testy SBS: 16/16. Generacja świata: kod 0, 918 s, brak fallback=True. Generacja PBR: kod 0, 734 s oraz 1 s uzupełnienia warstwy ze zdjęcia asfaltu. SHA 64/64 GLB zgodne z manifestem.
Wstępny pełny GIS przed odtworzeniem produktów: 487 passed, 6 failed, 1 xfailed. Po generacji kontrola wcześniejszych problemów i SBS: 18 passed. Odtworzone fidelity: 9 passed, 1 xfailed. Końcowy pełny GIS nastąpi wyłącznie na końcu rundy.
Skopiowane sceny Unity miały datę 17:11, więc przygotowano świeży świat. Import rozpoczęto 11.11 około 22:25 po uzyskaniu slotu. EditMode, świeże rendery i ocena wizualna nadal nie są zakończone. Nie deklarujemy PASS bramki ani wyników telefonu.

## Dalsza praca
Cel czasowy: około 12.11.2026, 21:31 Europe/Warsaw, czyli 24 godziny od rozpoczęcia. Runda r1 wymaga świeżych dowodów i REPORT.md. Następne rundy prowadzone będą w tym samym worktree, na kolejnych gałęziach z merge main, bez scalania do main i bez pushowania.

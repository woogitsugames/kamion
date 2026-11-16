# ADR 0227 — Knyszyn: rozpoznawalność Rynku z wysokości oczu

Status: WIP, 2026-11-15. Wymaga porównania kadrów, budżetu po zmianach i weryfikacji lidera.

## Kontekst
Właściciel nie rozpoznaje Knyszyna z poziomu ulicy. Zdjęcia 1–11 są lokalne, wyłącznie jako referencja (`Data/raw/refs/owner-knyszyn-2026-11-15/`); nie są teksturami. D65: latem, białe LED. Decyzje właściciela i kolejność w `docs/owner/KNYSZYN-OWNER-FEEDBACK-S21.md`.

Orto GUGiK 2025 i fotografie właściciela pokazują skwer z trawnikami i pojedynczymi drzewami liściastymi. Płyta fontanny leży w zachodnim parku, około 93 m od dotychczasowej kamery na wschodnim placu (ESTIMATED przez dopasowanie dwóch wycinków ortofoto; dokładna pozycja i kadry wymagają kontroli). Mechanizm lasu dla BDOT `20029180-A4BE-5C99-E053-CC2BA8C01CFC` generuje również leśną osłonę HLOD, nieadekwatną do parku.

## Decyzja robocza
Lokalny `park_replacement` usuwa las, jego obrzeże i maskę podłoża leśnego wyłącznie dla wskazanego obrysu; osobne authored punkty drzew i `open_ground` zachowują trawnik. Położenia koron, szerokości alejek oraz proporcje fontanny są ESTIMATED/WORKING_VALUE. Płyta jest płaska, bez niecki; nawierzchnia tymczasowo wykorzystuje istniejący materiał. Kamera wschodniego placu została przemianowana, a kamery 03–08 mają wstępne szacowane pozy na wysokości 1,7 m. Widok i umiejscowienie wymagają porównania z referencjami.

Kościół i urząd: osobne generatory wpięte w stage, obrysy BDOT i wysokości GUGiK; dachy i okna dopasowane do obrysów, detale WORKING_VALUE. Mała architektura i sucha fontanna z obwódką/dyszami wpięte; strumienie OPEN, sylwetka króla PROXY_NOT_APPROVED. Rendery r1 i r2 obejrzano: wynik nadal FAIL; r2 usunęła widoczny uskok nawierzchni w porównanych kadrach, ale drzewa, figura, suche dysze oraz pozycje kamer wymagają poprawek.

## Budżet i walidacja
Baseline i r2: `artifacts/knyszyn-rynek-0227/before/` i `r2/`; zestawienia 01–11 pozostają lokalne w `compare/r2/High-clear/`. Low: maksimum sumy szacowanych draw calls siatek i instancji 500 → 486, lecz na wspólnych kamerach wzrost do +6; warunek bez pogorszenia FAIL. High: maksimum trójkątów z instancjami 1 258 099 → 1 256 983, poniżej 2 mln. To szacunek edytora, nie pomiar telefonu. Po scaleniu main potrzebna kolejna przebudowa i powtórne pomiary. Pełne pytest GIS i EditMode OTWARTE.

## Otwarte
- Rozpoznawalność z oczu, pary zdjęcie–render i weryfikacja lidera/właściciela; minimum trzy iteracje.
- Targowica: lokalny OSM marketplace way 704368699 około 1 km od wschodniego placu, ortofoto 2025 pokazuje tam grunt i wyspy bez czterech wiat; lokalizacja i wymiary nowszych zadaszeń niepotwierdzone.
- Rondo: PR #97 nie w main; ortofoto 2025 sprzed przebudowy, wymiary aktualnej wyspy/opaski niezmierzone. Nie przedstawiać wartości roboczych jako pomiarów.
- Pomnik króla i obelisk to prawdopodobnie osobne obiekty; geolokalizacje ESTIMATED.
- Telefon i niezależny przegląd wizualny: do lidera, bez adb w tym zadaniu.

- Wierzba płacząca z opisu właściciela: brak potwierdzonego prototypu w istniejącej bibliotece drzew; nie jest jeszcze odwzorowana. Wymaga zasobu i oceny na renderze.

## Iteracja r3
Trzecia przebudowa i cztery warianty renderów zakończone; lokalne pary zdjęcie–render w `compare/r3/High-clear/` i `Low-clear/`. Wynik wizualny FAIL: pozycje kamer 02/07 i osadzenie placu pomnika wymagają korekt, drzewa są zbyt rzadkie, brak strumieni. Low bez pogorszenia FAIL (największy wzrost na wspólnej kamerze +6 szacowanych draw calls z instancjami, +1644 tris). High max 1 229 621 tris z instancjami, poniżej 2 mln; max suma draw calls 838→844. Szczegóły `AUDYT.md`. Kolejna iteracja obejmie przygotowane wejścia urzędu i próbę dwóch koron lip; efekty i budżet niezweryfikowane.

## Iteracja r4
R4 z lokalną próbą dwóch koron, wejściami urzędu i placykiem pomnika: cztery warianty ukończone, pary zdjęć lokalnie. Wizualnie FAIL: dach portyku niewidoczny w obu profilach; plac ciągły i kamera na osi, ale park nadal odbiega od zdjęć. Low na wspólnej kamerze +6 szacowanych draw calls i +1704 tris z instancjami; High max 1 229 693 tris. Pełny GIS 1410 passed, 2 failed: test nazwy poprawiony kierunkowo, raport fidelity po zmianach main przeliczany. EditMode otwarty.

## Iteracja r5 i walidacja
Dach skrzydła kultury jest widoczny po poprawce geometrii; jego kształt i lukarny nadal wymagają pracy. Ocena całości FAIL. Low bez pogorszenia FAIL: max wzrost na wspólnych kamerach +6 szacowanych draw calls z instancjami, +1825 tris; High max 1 229 814 tris. EditMode 626 passed, 2 skipped; pełny GIS wymaga ponowienia po usunięciu dwóch błędów wykrytych w poprzednim przebiegu. Targowica: właściciel potwierdził plac po drugiej stronie Jagiellońskiej od nr 50, kandydat OSM way 704368699; brak zdjęć dronowych i pomiarów wiat, niezintegrowany prototyp nie jest źródłem ich położeń.

## Iteracja r6
R6: lukarny osadzone niżej; cztery warianty i lokalne porównania wykonane. Wizualnie FAIL: kalenica i lukarny nadal odbiegają od zdjęć. Low bez pogorszenia FAIL (max wzrost wspólnej kamery +6 draws z instancjami i +1825 tris), High max 1 229 814 tris.

## Iteracja r7
R7 po scaleniu main: cztery warianty i lokalne porównania wykonane; daszki i szprosy czytelne w kadrze 02, całość nadal FAIL wizualnie. Low bez pogorszenia FAIL (na wspólnych kamerach wzrost do +6 draws z instancjami i +1832 tris), High max 1 229 853 tris. GIS po poprawce far_field w toku.

## GIS po scaleniu main
Pełny `pytest tests/gis -q`: 1472 passed, 33 skipped, 3 xfailed; exit 0. Poprawiono błędny odczyt terenu far field dla niestandardowego out_root oraz fallback R16; testy syntetyczne 10 passed. EditMode: 626 passed, 2 skipped, wykonany przed ostatnim scaleniem main, więc powtórzyć na stanie końcowym.

## Iteracja r8
Trzynaście próbnych koron daje bardziej liściasty park, ale widoczne szwy, powtarzalność oraz częściowe zasłanianie urzędu oznaczają FAIL naturalności. Cztery warianty ukończone, pary zdjęć lokalnie. Low nadal FAIL: max +5 szacowanych draws i +1832 tris z instancjami na wspólnych kamerach; max sumy draws 500→487. High max 1 230 049 tris, max draws 838→844. Wariant pozostaje roboczy do poprawy i pomiaru.

## Iteracja r9 — wariant odrzucony
Równoległe karty koron wyeliminowały część szwów, ale z niektórych kierunków zanikają do wąskich pionowych pasów. FAIL w High i Low; zmiana kodu i danych wycofana, dowody lokalne `compare/r9/` i kamery boczne R9. Low w tej próbie nadal FAIL względem baseline (+5 draws i +1832 tris na wspólnych kamerach); High max 1 229 989 tris. Konieczna kolejna przebudowa po wycofaniu.

## Iteracja r10 — wariant odrzucony
Objętościowa próba małych kart nie zniknęła w badanych kierunkach, ale dawała pasy i ciemne kliny, przypominając bardziej wierzby niż lipy. FAIL w obu profilach, wycofana; dowody lokalne `compare/r10/` i osiem kierunków. Low nadal FAIL: +5 draws i +1832 tris na wspólnych kamerach; High max 1 230 169 tris. Wymagana przebudowa po cofnięciu.

## Iteracja r11 i porównywalność budżetu
Po scaleniu ADR 0219 poprawne dane far-field pokrywają Knyszyn; w kadrach Rynku 03–08 nie widać istotnej zmiany poza małym fragmentem tła. Cztery warianty i pary wykonane. High max 1 250 405 tris; Low max wzrost wspólnej kamery +63 draws i +37788 tris z instancjami względem pierwotnego baseline. Jednak ADR 0262 zmienił start ciężarówki 12→90 m: w problematycznym kadrze pojawiła się pełna naczepa zamiast szarej atrapy. Części kosztu nie rozdzielono pomiarem; nie przypisywać całej różnicy far-field ani uznać budżetu Low za spełniony.

## Iteracja r12
Dwie lokalne lipy 3D mają pełniejsze sylwetki bez centralnego szwu, lecz ciemne grube kępy pozostają FAIL. W porównaniu z tym samym stanem r11 draws bez zmian, ale na wspólnej kamerze +2044 tris Low i High; High max 1 252 449. R13 przywraca poprzednie Low, zachowuje trial High i dodaje przybliżenia pomników; przejście LOD wymaga oceny.

## Iteracja r13
Wskazówka zegara widoczna, ale rzeźba króla i ptak na obelisku nadal nieczytelne; FAIL wizualny, PROXY_NOT_APPROVED. R13 vs r11 przy tym samym stanie sceny: draws bez zmian, max +14 tris Low i High na nowym kadrze; High max 1 250 419 tris. Low względem pierwotnego baseline nie jest potwierdzony z powodu zmiany pozycji pojazdu. GIS trwa; wykryto brak lokalnych instancji regionu C i cache starej wersji, planowane odtworzenie danych.

## Iteracja r14 — budżet edytora

Low względem pierwotnego before: **FAIL** warunku bez pogorszenia. Dla 50 kamer o tych samych nazwach największy wzrost sumy szacowanych draw calls siatek i instancji to 240 → 303 (+63) na `dk65-inlet-south`; 34 kamery mają wzrost. Największy wzrost sumy tris to 272 290 → 310 078 (+37 788) na `truck-side`. Względem r11 wszystkie 70 wspólnych kamer Low ma draws i tris bez wzrostu; `rynek-owner-08`: 351 → 351 draws, 295 908 → 295 902 tris.

High: **PASS** limitu 2 mln tris na kamerę, maksimum 1 250 399 z instancjami na `cab-mirror-front`; maksymalna suma szacowanych draws to 848 na `tykocka-into-town`. Clear i dusk dają identyczne wartości geometryczne. Są to szacunki CPU edytora przed SRP batchingiem, nie pomiary GPU ani telefonu; shadow draws są osobnym wskaźnikiem.

Before zawiera 51 kamer, r14 70; 50 ma te same nazwy. Dawna błędnie nazwana `rynek-fountain` nie występuje już pod tą nazwą; zgodność pozycji `plac-wschodni-from-east` nie została tu zweryfikowana. Porównanie ograniczają także zmiany main: ADR 0219 uzupełnił właściwe dane far-field, a ADR 0262 zmienił pozycję startu ciężarówki. Nie zmierzono osobnego wkładu tych zmian, więc nie przypisujemy im całości wzrostu ani nie uznajemy Low za spełnione. Szczegóły i ścieżki statystyk są w `artifacts/knyszyn-rynek-0227/AUDYT.md`.

## Iteracja r15 — próba koron i budżet

Próba rozjaśnienia koron nie przeszła przeglądu i została wycofana. Rendery r15 dokumentują tę próbę, nie stan po jej wycofaniu; potrzebna kolejna przebudowa i ocena.

W r15 **High PASS** limitu 2 mln tris na kamerę: maksimum 1 250 401 z instancjami (`cab-mirror-front`). **Low FAIL** względem before: największy wzrost sumy szacowanych draws siatek i instancji 240 → 303 (+63, `dk65-inlet-south`), na 34 z 50 kamer o tych samych nazwach wystąpił wzrost. Największy wzrost sumy tris 272 290 → 310 078 (+37 788, `truck-side`).

R14 → r15: 70 wspólnych kamer, draws i szacowane shadow draws bez zmian; tris wzrosły na 37 kamerach, maksymalnie o 22 w Low i High. Przyczyna nie została osobno zmierzona. Clear i dusk mają te same wyniki geometryczne. Jak w r14 są to szacunki CPU edytora, nie pomiary GPU; ograniczenia porównania z before pozostają aktualne. Szczegóły w `artifacts/knyszyn-rynek-0227/AUDYT.md`.

## Iteracja r16 — wynik i ograniczenia

Eksperyment obwodowych koron wycofano po nieudanej ocenie; rendery r16 pokazują stan przed wycofaniem i nie potwierdzają obecnego stanu. Poprawiono styk korony pomnika, ale łańcuch pozostaje OPEN, a sylwetka króla PROXY_NOT_APPROVED. Potrzebna nowa przebudowa i ocena wizualna.

High **PASS** limitu 2 mln tris na kamerę: maksimum 1 250 401 z instancjami (`cab-mirror-front`). Low **FAIL** względem pierwotnego before: maksymalny wzrost sumy szacowanych draw calls 240 → 303 (+63, `dk65-inlet-south`); wzrost na 34 z 50 kamer o tych samych nazwach. Maksymalny wzrost tris 272 290 → 310 078 (+37 788, `truck-side`).

R15 → r16: dla 70 wspólnych kamer draws i szacowane shadow draws bez zmian, a największy wzrost to 1 tris w Low i High; przyczyny różnic nie zmierzono. Clear i dusk mają identyczne dane geometryczne. To szacunki CPU edytora, nie pomiary GPU; ograniczenia porównania z before opisane dla r14 nadal obowiązują.

## Iteracja r17 — budżet edytora

R17 obejmuje 70 kamer w każdym wariancie. High **PASS** limitu 2 mln tris na kamerę: maksimum 1 250 401 z instancjami (`cab-mirror-front`), maksimum 848 draws (`tykocka-into-town`). Low **FAIL** względem pierwotnego before: 34 z 50 kamer o tych samych nazwach ma wzrost sumy szacowanych draws, maksimum 240 → 303 (+63, `dk65-inlet-south`); największy wzrost tris 272 290 → 310 078 (+37 788, `truck-side`).

R16 → r17: na 70 wspólnych kamerach draws i shadow draws bez zmian, wzrost tris maksymalnie o 1; R14 → r17 również bez wzrostu draws, maksymalny wzrost tris +22. Przyczyn różnic tris nie zmierzono. Dwie dodatkowe kamery diagnostyczne planowane do r18 nie mają baseline before ani r17 i wymagają osobnego raportowania. Ograniczenia porównania z before i zmian main opisane dla r14 pozostają aktualne; są to szacunki CPU edytora, nie pomiary GPU.

## R18 — diagnostyka budżetu jednej kamery

Dla `dk65-inlet-south` Low-clear, w tej samej scenie, szacowana suma draws siatek i instancji wynosi 303 w pełnej scenie, 240 bez ciągnika i naczepy, 299 bez far-field oraz 236 bez obu. Odpowiada to 63 draws pojazdu i 4 drawom far-field w tym konkretnym ujęciu. To diagnostyczny szacunek CPU edytora przed SRP batchingiem, nie pomiar GPU; formalny wynik nadal obejmuje pełną scenę.

Zbieżność wyniku 240 bez pojazdu z pierwotnym before nie dowodzi przyczyny całej regresji: dawnej sceny nie rozbito w porównywalny sposób. Low względem before pozostaje **FAIL**. Szczegółowe liczby i ograniczenia w `artifacts/knyszyn-rynek-0227/AUDYT.md`; tymczasowy kod diagnostyki runnera przywrócono po pomiarze.

## Iteracja r18 — pełny budżet

Cztery warianty obejmują po 72 kamery; clear i dusk mają identyczne wartości geometryczne. Na 70 kamerach wspólnych z r17 draws, tris, shadow draws i liczba rendererów są identyczne. High **PASS**: maksimum 1 250 401 tris z instancjami (`cab-mirror-front`), maksymalnie 848 draws (`tykocka-into-town`). Low względem before nadal **FAIL**: 34 z 50 kamer o tych samych nazwach ma wzrost draws, maksymalnie 240 → 303 (+63, `dk65-inlet-south`); maksymalny wzrost tris 272 290 → 310 078 (+37 788, `truck-side`).

Nowe kamery bez baseline before i r17: `rynek-king-back-0227` Low 364 draws / 340 477 tris, High 594 / 847 374; `rynek-king-profile-0227` Low 273 / 270 450, High 372 / 473 360. To szacunki CPU edytora z instancjami przed SRP batchingiem, nie pomiary GPU ani telefonu. Ograniczenia porównania i diagnostyka `dk65-inlet-south` pozostają aktualne.

## Iteracja r19 — budżet edytora

R19 obejmuje 72 kamery w każdym wariancie; clear i dusk mają identyczne wyniki geometryczne. High **PASS**: maksimum 1 250 401 tris z instancjami (`cab-mirror-front`), maksimum 848 draws (`tykocka-into-town`). Low względem before nadal **FAIL**: wzrost draws na 34 z 50 kamer o tych samych nazwach, maksymalnie 240 → 303 (+63, `dk65-inlet-south`); maksymalny wzrost tris 272 290 → 310 078 (+37 788, `truck-side`).

R18 → r19: 70 z 72 kamer bez zmian liczby rendererów, draws, shadow draws i tris; dwa kadry pomnika przestawiono. `rynek-king-back-0227` Low 364 / 340 477 → 359 / 292 593, High 594 / 847 374 → 620 / 832 620; `rynek-king-profile-0227` Low 273 / 270 450 → 450 / 338 213, High 372 / 473 360 → 641 / 796 017 (draws / tris z instancjami). Nie mają baseline before, a zmiana kadru ogranicza porównanie. To szacunki CPU edytora przed SRP batchingiem, nie pomiary GPU ani telefonu. Szczegóły w `artifacts/knyszyn-rynek-0227/AUDYT.md`.

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

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

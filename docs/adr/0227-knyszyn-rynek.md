# ADR 0227 — Knyszyn: rozpoznawalność Rynku z wysokości oczu

Status: WIP, 2026-11-15. Wymaga porównania kadrów, budżetu po zmianach i weryfikacji lidera.

## Kontekst
Właściciel nie rozpoznaje Knyszyna z poziomu ulicy. Zdjęcia 1–11 są lokalne, wyłącznie jako referencja (`Data/raw/refs/owner-knyszyn-2026-11-15/`); nie są teksturami. D65: latem, białe LED. Decyzje właściciela i kolejność w `docs/owner/KNYSZYN-OWNER-FEEDBACK-S21.md`.

Orto GUGiK 2025 i fotografie właściciela pokazują skwer z trawnikami i pojedynczymi drzewami liściastymi. Płyta fontanny leży w zachodnim parku, około 93 m od dotychczasowej kamery na wschodnim placu (ESTIMATED przez dopasowanie dwóch wycinków ortofoto; dokładna pozycja i kadry wymagają kontroli). Mechanizm lasu dla BDOT `20029180-A4BE-5C99-E053-CC2BA8C01CFC` generuje również leśną osłonę HLOD, nieadekwatną do parku.

## Decyzja robocza
Lokalny `park_replacement` usuwa las, jego obrzeże i maskę podłoża leśnego wyłącznie dla wskazanego obrysu; osobne authored punkty drzew i `open_ground` zachowują trawnik. Położenia koron, szerokości alejek oraz proporcje fontanny są ESTIMATED/WORKING_VALUE. Płyta jest płaska, bez niecki; nawierzchnia tymczasowo wykorzystuje istniejący materiał. Kamera wschodniego placu została przemianowana, a kamery 03–08 mają wstępne szacowane pozy na wysokości 1,7 m. Widok i umiejscowienie wymagają porównania z referencjami.

Kościół i urząd: przygotowane osobne generatory, obrysy BDOT i wysokości GUGiK; detale WORKING_VALUE, jeszcze niezintegrowane ani nieobejrzane w silniku.

## Budżet i walidacja
Baseline edytora po 0216: 51 kamer na wariant, Low max `drawsEst` 429 i `trisExact` 370158; High max `drawsEst` 760 i `trisExact` 1237074. Statystyki edytora mają osobne wiersze instancji; nie są pomiarem telefonu ani pełnym bilansem bez ich uwzględnienia. Porównanie po zmianach OTWARTE. Rendery `artifacts/knyszyn-rynek-0227/before/`; r1 w kolejce. Testy kierunkowe: park 1 passed, kościół 3 passed, urząd 3 passed. Pełne pytest GIS i EditMode OTWARTE.

## Otwarte
- Rozpoznawalność z oczu, pary zdjęcie–render i weryfikacja lidera/właściciela; minimum trzy iteracje.
- Targowica: lokalny OSM marketplace way 704368699 około 1 km od wschodniego placu, ortofoto 2025 pokazuje tam grunt i wyspy bez czterech wiat; lokalizacja i wymiary nowszych zadaszeń niepotwierdzone.
- Rondo: PR #97 nie w main; ortofoto 2025 sprzed przebudowy, wymiary aktualnej wyspy/opaski niezmierzone. Nie przedstawiać wartości roboczych jako pomiarów.
- Pomnik króla i obelisk to prawdopodobnie osobne obiekty; geolokalizacje ESTIMATED.
- Telefon i niezależny przegląd wizualny: do lidera, bez adb w tym zadaniu.

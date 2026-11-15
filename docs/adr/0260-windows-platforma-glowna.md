# ADR 0260 — Windows jako platforma główna (D73)

## Kontekst
Właściciel 15.11 (s22): wersja telefonowa okazuje się za ciężka (A16 Low ok. 30 fps w regionie C przy GPU blisko limitu; APK korytarza d67-full 1 821 MB). D56 przewidywał pełną wersję PC z kierownicami dopiero po bramce 3.

## Decyzja
- Platforma główna: **Windows Standalone x64**, ten sam projekt Unity 6000.3.28f1 URP (moduł windowsstandalonesupport zainstalowany).
- Telefon (Android, potem iOS) = wersja późniejsza, lżejsza; kod i dane pozostają wieloplatformowe (wejście za warstwą sterowania, tiery jakości jako dane).
- Bez zmiany silnika (rozważony Unreal 5 — odrzucony: przepisanie fizyki, importerów, narzędzi).

## Konsekwencje
- CLAUDE.md: zasada 2 i DoD przestawione na PC; mobilne bramki odroczone, nie usunięte.
- Potrzebne: wejście BuildCommands.BuildWindows + scripts/build-windows.ps1 (z -Regions, ADR 0229), tiery High/Ultra pod PC, sterowanie klawiatura/pad/kierownica.
- Budżety PC i bramki (docs/03) do zdefiniowania po wskazaniu referencyjnego PC przez właściciela; do tego czasu WORKING_VALUE. Maszyna deweloperska (RTX 5070) NIE jest referencją.
- PR-y czysto mobilne (#110 cienie Low, #111 A/B GPU A16, #116 zrzuty A16) — niższy priorytet, nie zamykane.

## Budżet
Bez zmian w kodzie w tym ADR.

## Walidacja
Pierwszy build Windows + jazda po Knyszynie (dowód: zrzut, log) — do zrobienia.

## Otwarte
Referencyjny PC i docelowy FPS; kolejność wejść (klawiatura / pad / kierownica FFB).

## Uzupełnienie (D74)
Klasy sprzętu PC przyjęte wg ETS2/ATS: minimalna (i5-6400/R3 1200, GTX 660/RX 460/HD 630 2 GB, 8 GB RAM, Low 1080p 30 fps WORKING_VALUE) i zalecana (i5-9600/R5 3600, GTX 1660/RX 590, 12 GB RAM, High 1080p 60 fps WORKING_VALUE). Szczegóły: docs/11 D74.

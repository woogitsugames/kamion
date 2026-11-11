# ADR 0119 — DK8 przy Putry, powierzchnie i geometria pod pomostem

## Runda r2 — 12 listopada 2026, w toku

Sesja 7, gałąź gpt-landmarks-r2. Początek od rundy remizy cb699d74 i merge main
2c3939b2. Konflikt wygenerowanego streetscape_qa przyjęty z main; przed zmianą
powstaje świeży świat i porównanie kamer. Własny worktree pozostaje ten sam.

Zakres obejmuje wyłącznie część pod pomostem w hero_bridge.py i jej konfigurację.
Pomost, kapa, bariery, ekrany, jezdnie i pliki Claude nie są przedmiotem zmian.
Schody mają wymiary WORKING_VALUE i niepotwierdzone połączenie z chodnikiem;
według recenzji HIL przecinają ekran i kończą się na ścianie. Kandydat: jawna
flaga wyłączająca ich generację również przy wczytaniu starego spec.

Referencja: Rakoon, Commons 7204 May 2021 in Białystok, CC0. Pozyskano oryginał
5520×3680, SHA-1 61364bef59ec622ecf0a89e5a4c6e9cf6678504a zgodne z Commons.
Natywne kadry pokazują szare pionowe ścięcia przy ochrowych płaszczyznach filarów.
Rozrzut mieszanych ROI nie jest miarą samego zabrudzenia: wyodrębnione płaszczyzny
mają Y sd około 6,6–10,0, a dużą różnicę jasności daje światło pod pomostem.
Odtworzenie powierzchni ścięć i ocieplenie stosunku R/G należy ocenić na świeżych
renderach, zamiast podnosić szum całej farby. Parametry bez pomiaru pozostają WORKING_VALUE.

Kamery: wszystkie dotychczasowe kontrolne oraz dziewięć własnych kadrów detalu,
skopiowanych i połączonych z wcześniejszych dowodów viaduct-r10, bez zmian kamer
sesji sbs. Low/High, overcast/clear, stała kolejność i rozdzielczość przed/po.
Budżet: draws Low +0, instancje osobno, suma trójkątów najwyżej +2% w każdej kamerze.
Testy pojedynczego pliku w trakcie, pełny GIS na końcu. Python heavy i Unity
mają oddzielne wymagane sloty; nie uruchamia się generatora po cichu z importu.

Stan: przygotowanie baseline. Wyniki wyglądu, testów i budżetu po zmianie UNVERIFIED.

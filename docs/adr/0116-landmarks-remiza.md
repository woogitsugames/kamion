# ADR 0116 — Remiza JRG2, zgodność z fotografią 7197

## Runda r1 — 11 listopada 2026, stan roboczy

Sesja 7, gałąź `gpt-landmarks-r1`, worktree `.claude/worktrees/gpt-landmarks`.
Punktem wyjścia jest main `5f2aa277`. Poprzedni model remizy r7 jest już scalony.
Źródło porównania: fotografia Commons „7197 May 2021 in Białystok.jpg”, Rakoon, CC0;
atrybucja i pochodzenie są opisane w ADR 0070 oraz LICENSES.

Celem są ciemne i gęste iglaki, gradient górnych i dolnych tafli łuków, zacieki mające
źródło w obróbkach oraz usunięcie fasetowania tui na Low. Bazowy pigment tynku pozostaje
zgodny z D48. Zmiany wyłącznie w generatorze i danych remizy; bez globalnej kalibracji światła.

Najpierw świeży generator, import i baseline czterech kamer remizy w Low/High, clear/overcast.
Po zmianie powtórzenie tych kadrów, a przed raportem pełny zestaw kamer trasy i testy GIS/EditMode.
Statystyki siatek i instancji są raportowane osobno. Budżet Low: brak wzrostu draws, suma
trójkątów najwyżej +2%. Statystyki edytora nie stanowią pomiaru GPU na A16.

## Stan eksperymentu r1

Baseline zakończony: 48 kamer w każdym z czterech warunków, łącznie 192 PNG.
Kandydat ma wygładzone normalne istniejących tui Low, mocniejszy gradient szkła hali,
szersze dwa iglaki i gęstszy rdzeń. Paleta iglaków mieści się w nowej, wcześniej
nieużywanej komórce tego samego atlasu. Bazowy pigment tynku D48 jest zachowany.
Pas zacieków o autorskiej głębokości 1 m podąża za obróbką łukowego dachu;
kontrola geometrii sprawdza zarówno jego krzywiznę, jak i odsunięcie od otworów.

Wygenerowany GLB: LOD0 9344 → 9392 trójkąty, LOD1 2828 → 2860, LOD2 164 → 164.
Liczba prymitywów pozostaje 3/2/1. Są to liczby modelu; pełny budżet kamer po zmianie
pozostaje do sprawdzenia. Kanał alfa całej mapy jest identyczny z bazą, podobnie
jak RGBA poza istniejącą komórką igliwia. Skany i licencje pozostają dotychczasowe.

Pojedynczy zestaw GIS `test_fire_station_r7.py`: 6/6, przez pulę `heavy`.
Pełny GIS i EditMode dopiero na końcu strojenia rundy. Każda generacja i test
Pythona o dużym koszcie zajmują slot `heavy`; import nie uruchamia generatorów po cichu.

Osobna diagnostyka plamy przy maszcie: mediana Y wybranego ROI na High wynosi
114,83, po wyłączeniu cieni bezpośrednich 131,12; sąsiedni tynk 131,19.
Wyłączenie ambient GI albo SSAO pozostawia 114,83. Dodatkowy promień CPU od tego
punktu ku słońcu presetu overcast trafia w komórkę atlasu flagi po 6,76 m;
promienie z jasnych miejsc obok nie trafiają w przeszkodę. Źródłem jest flaga.
Nie dodano do albedo kompensującej jasnej plamy.
Dowody i dokładne ROI są w `artifacts/landmarks-r1/wall-patch-diagnostics.json`.
Geometria przeszkody: `artifacts/landmarks-r1/shadow-occluder.json`.

Ocena wyglądu kandydata w Unity, końcowe wartości barw i pełny budżet: UNVERIFIED,
import i porównanie fokusowe w toku.
Telefon i niezależna recenzja pozostają po stronie lidera. Nie deklaruje się zamknięcia bramki 3.

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

Wynik wizualny, wartości barw i zgodność budżetu: UNVERIFIED, baseline w przygotowaniu.
Telefon i niezależna recenzja pozostają po stronie lidera. Nie deklaruje się zamknięcia bramki 3.

# ADR 0108 — światło, niebo, ekspozycja i post

## Runda r1 — w toku, 11 listopada 2026

Bazą jest main 4c9905b1, gałąź gpt-light-r1, worktree .claude/worktrees/gpt-light. Okno pracy: 11 listopada 2026 21:30–12 listopada 2026 21:30 czasu Warszawy.

P0: porównać RCAS 0 / 0,25 / 0,5 / 0,75 przy wyłączonym ditheringu przed LUT. Kryteria recenzji: RMS nieba ≤ 0,6 poziomu oraz szczegół asfaltu ≥ 90% stanu sprzed wyłączenia RCAS. Wyniki tej rundy pozostają UNVERIFIED do pomiaru PNG.

Niebo clear nie ma obecnie chmur: Sky.shader mnoży wynik CloudDeck przez overcast, a CreateClear ustawia overcast=0 i cloudContrast=0. Plan: osobny parametr pokrycia jasnego nieba w danych presetu, wykorzystanie istniejącej tekstury i przebiegu skybox. Chmury nie będą zmieniały ekspozycji gruntu ani natężenia słońca. To uproszczenie wizualne, nie symulacja pogody. Wartości pokrycia i barwy będą WORKING_VALUE do porównania z fotografiami.

Low: brak nowego przebiegu, zmiany skali, geometrii i liczby instancji. Koszt GPU dodatkowych obliczeń nieba na A16 pozostaje UNVERIFIED; urządzeń używa lider.

Komin na photo-biezenstwa-ground: uwaga przekazana w tym ADR i przyszłym REPORT właścicielowi landmarków. Nie zmieniam rotacji instancji. Pieprz ścian jest przypisany w recenzji do shadera ścian; nie maskuję go globalnym rozmyciem.

Przewidywane styki integracji: addytywna polityka High w QualityProfileApplier, presety LightingPreset i Sky.shader. ProjectSettings, Packages, sceny i pliki pozostałych dziedzin pozostają poza zmianą.

# SBS r3 — ranking i kalibracja G3-B

Start 12.11.2026 około 02:42 Europe/Warsaw. Ten sam worktree .claude/worktrees/gpt-sbs. Gałąź gpt-sbs-r3 utworzona od zamkniętej gpt-sbs-r2 962ad111; merge main 9874d98c zakończony bez konfliktów jako 31988772. Main zawiera ADR 0125 i rundy r1 innych dziedzin. Nie scalano do main i nie pushowano.

R2: 561 passed, 1 xfailed; EditMode 261; 168 raw, 100 B, 168 diagnostycznych arkuszy; dostawa do main potwierdzona receipt. Nie jest obrazem nowych scaleń. R3 odtwarza materiały i świat, potem importuje przed renderami. Wszystkie ciężkie zadania w heavy gpt-sbs-r3 (max 3), Unity w gpt-sbs. Pełny GIS dopiero na końcu rundy, podczas pracy pojedyncze pliki.

Zakres: docs/refs/sbs-priorities.md dla wszystkich sesji oraz własne narzędzia/dane SBS. Priorytet wskazany przez recenzję 0125: 275528/837235 cofnięcie 12–20 m, 328135/297817 wspólna próba około 45 m, 180137 pozycja, 494288 kurs. Liczby to hipotezy. Zanim zmieni się produkcyjne pozy, diagnostyka C, porównanie co najmniej dwóch niezależnych trwałych kotwic i niezależny krytyk. Nie ukrywać negatywnych kadrów ani nie przenosić starego D51 na nowe SHA.

Obejrzany materiał wstępny jest zapisany w r2/PRE-R3-VISUAL.md. 297817 ma portal daleko w tle; porządek zdjęć 297817 przed 328135 o 2678 ms jest zgodny ze zbliżaniem do portalu. Nie znaleziono dowodu zamiany ID. Świat, znaki, runtime i pliki Claude są poza zakresem edycji. Pochodne generatorów po walidacji ponownie przywrócić, zachowując wejścia dowodów.

Zapisano wejściowy ranking docs/refs/sbs-priorities.md: 10 tematów rozpoznawalności i zadania dla wszystkich 10 dziedzin, ze źródłem i stanem potwierdzenia. Ranking odróżnia r1/r2, recenzję 0125 i oczekujący render r3; nie sumuje ocen z różnych epok. Generator bazowy czeka na heavy, uchwyt 1171.

Przygotowano make-gantry-probes.py, jeszcze bez uruchomienia: 18 hipotez C dla czterech kamer naziemnych. Grobin: 0/-12/-16/-20/-28 m, zsolt: 0/-30/-45/-60 m wzdłuż własnego kursu siatki. Wariant 0 zachowuje dokładną kamerę; przesunięte użyją NMT+2,2 m, stałych yaw/FOV/pitch i dwóch natywnych proporcji 16:9/4:3. Skrypt wymaga zgodnej ukończonej migawki świata r3 i sprawdza SHA zdjęć oraz niezmienność produkcyjnych źródeł. Nie obejmuje kamer na wiadukcie, gdzie NMT nie jest wysokością pokładu.

Przygotowano wrapper importu (kopię sprawdzonego r2) i render-gantry-probes.ps1: dwie natywne proporcje, osobne Acquire/Release Unity przed każdym uruchomieniem, wymagany receipt poprawnego importu, migawka pięciu wejść i kontrola SHA/HEAD przed i po. Parser PowerShell bez błędów. Żaden z tych wrapperów nie został jeszcze uruchomiony; bazowa generacja nadal czeka na heavy.

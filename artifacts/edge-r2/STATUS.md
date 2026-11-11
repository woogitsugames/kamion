# Status edge r2
Start: 11 listopada 2026, 23:43 CET. Pierwotny termin sesji: 12 listopada 2026, około 21:31 CET.
R1 zakończona i skopiowana do main: 1003 pliki, ponad 2,15 GB; ostatni commit 5b221381. Kod geometrii r1 pozostaje w tej gałęzi.
Gałąź gpt-edge-r2 utworzono od r1 i scalono main (merge 54bb70ca). Historyczną, czystą i scaloną gpt-edge-r2 @027e7589 zachowano jako gpt-edge-0085-r2-archive, bez usuwania jej worktree ani danych.
Cel: rzeczywiste wysokości dalekiej zabudowy z przypiętego LoD1; parser produkcyjny nadal zwraca 0, prototyp znalazł 36971 rekordów i 5390 dopasowań. Zgodnie z nową D51 priorytetem jest rozpoznawalna sylwetka, położenie i proporcje, a nie drobna korekta materiałów.
Po merge zestaw sbs ma 25 B i 17 C; w porównaniach fotograficznych r2 odrzucamy C. Budżet raportujemy dla wszystkich kamer, także diagnostycznych. Pozy B pozostają przybliżone.
Ciężkie operacje wyłącznie przez centralny -Pool heavy, właściciel bieżąca gałąź; pełny GIS tylko na końcu. Unity osobno pod gpt-edge, release w finally. Bez main merge, push i telefonów.
Następny krok: dostosować własne skrypty do katalogu r2, zamrozić kamery/klasy i wykonać bazowe rendery przed zmianą parsera.
Krok 2: skrypty r2 mają własny STATUS, centralne pule, limitów nie podnoszą i nie usuwają cudzych starych slotów. Kamery: 42 aktualne sbs + własne ujęcie DK8 + kontrolne sceny; w zdjęciach akceptowane tylko A/B, C wykluczone, SHA zdjęć kontrolowane. Capture zapisuje i sprawdza SHA wejść po pobraniu slotu. Merge main nie zmienił geometrii świata, więc bazą jest lokalny wygenerowany i sprawdzony świat z r1. Następny krok: pwsh artifacts/edge-r2/validate.ps1 -Phase Before.
2026-11-11T23:51:14.3738539+01:00 Zapisano rendery before/Low-clear wszystkich kamer; ocena PNG i budżetu nadal w toku.
2026-11-11T23:51:49.8820657+01:00 Zapisano rendery before/Low-overcast wszystkich kamer; ocena PNG i budżetu nadal w toku.
2026-11-11T23:52:30.1063581+01:00 Zapisano rendery before/High-clear wszystkich kamer; ocena PNG i budżetu nadal w toku.

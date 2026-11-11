# Status edge r2
Start: 11 listopada 2026, 23:43 CET. Pierwotny termin sesji: 12 listopada 2026, około 21:31 CET.
R1 zakończona i skopiowana do main: 1003 pliki, ponad 2,15 GB; ostatni commit 5b221381. Kod geometrii r1 pozostaje w tej gałęzi.
Gałąź gpt-edge-r2 utworzono od r1 i scalono main (merge 54bb70ca). Historyczną, czystą i scaloną gpt-edge-r2 @027e7589 zachowano jako gpt-edge-0085-r2-archive, bez usuwania jej worktree ani danych.
Cel: rzeczywiste wysokości dalekiej zabudowy z przypiętego LoD1; parser produkcyjny nadal zwraca 0, prototyp znalazł 36971 rekordów i 5390 dopasowań. Zgodnie z nową D51 priorytetem jest rozpoznawalna sylwetka, położenie i proporcje, a nie drobna korekta materiałów.
Po merge zestaw sbs ma 25 B i 17 C; w porównaniach fotograficznych r2 odrzucamy C. Budżet raportujemy dla wszystkich kamer, także diagnostycznych. Pozy B pozostają przybliżone.
Ciężkie operacje wyłącznie przez centralny -Pool heavy, właściciel bieżąca gałąź; pełny GIS tylko na końcu. Unity osobno pod gpt-edge, release w finally. Bez main merge, push i telefonów.
Następny krok: dostosować własne skrypty do katalogu r2, zamrozić kamery/klasy i wykonać bazowe rendery przed zmianą parsera.

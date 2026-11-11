# G P2 — niezależny przegląd Low

Obejrzano wszystkie 14 par Low clear/overcast: siedem kamer na warunek, dwie plansze pełnych kadrów oraz dziesięć par wycinków w natywnej skali. Referencją sześciu istniejących kamer jest r4-focus-r1 (już z P0 brudu); dodatkowy tył porównano z ważnym r4-rear-controls-v2/level3, czyli kontrolą w tej samej pozie, nie historycznym R3.

Wizualnie P2 PASS w tym zakresie. Numery są czytelne i nieodwrócone. Cztery czarne hatchbacki pokazują BI 4913N, BIA 1711A, BI 98243 i BI 47938. Jeden numer może pozostać oryginalny: dostępnych jest 27 istniejących komórek, bez gwarancji globalnej unikalności. Kamera g_dirt_level_3 sama nie pokazuje tablicy, więc nie dowodzi czytelności. Nie zaobserwowano nowych zmian karoserii, kół, szkła ani otoczenia.

ROOT niezależnie porównał 28 par pakietów: pozy, macierze, hierarchie pojazdów i regionu, projekcje oraz pola pipeline są identyczne. Dodatkowy tył ma oczekiwaną różnicę paintMaterials: stary kontrolny shader i klony QA, zamiast produkcyjnych materiałów; nie nazywamy tego pełną identycznością materiałów. Wszystkie 28 porównań liczników estymowanych ma zerowe różnice w dziewięciu polach. To estymaty edytora, bez pomiaru GPU telefonu.

Otwarte przed pełnym AFTER: niezależny High14, końcowe metadane G i poprawka trwałości MotionVectors. Standardowy Lit CustomEditor rozpoznaje owned shader jako Unknown i włącza pass przy walidacji; G usuwa tylko to powiązanie z generowanym shaderem. Stare pakiety focus nie potwierdzają docelowego disabled pass. Krótki replay Low/High ma potwierdzić stan i brak zmiany obrazu. Dopiero potem decyzja o pełnym368/testach.

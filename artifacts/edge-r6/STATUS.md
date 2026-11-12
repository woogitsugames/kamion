Runda 6 rozpoczęta po zweryfikowanej dostawie r5. Gałąź gpt-edge-r6, merge main dcf1b4e18fd76f449888033b64238493ce329609 z main 863a25b938ae5d53f0df2f966c0ed951f2595f65, bez konfliktów.
Zakres: wyłącznie edge. Najpierw nowy pełny baseline i maska problemu apron NW/styku kurtyn. Regionalne budynki, roślinność, portale, bariery i źródła Claude pozostają poza edycją.
Main wnosi recenzowane pozy G3-B i poprawki światła; macierz dowodowa zostanie odtworzona z bieżących kanonicznych plików, bez zmiany kalibracji.
Źródła generatora map materiałów i materials_spec są identyczne z r5, więc wykorzystujemy sprawdzony cache R4; import sprawdzi wszystkie mapy. Zmiany materials.py zostaną uwzględnione przez pełny build_world.
Każdy ciężki Python pod centralnym heavy z właścicielem gpt-edge-r6; Unity pod centralnym slotem gpt-edge. FIFO bez Priority, bez kasowania cudzych slotów. Deadline bez zmian: 12.11.2026 21:31:27 CET.

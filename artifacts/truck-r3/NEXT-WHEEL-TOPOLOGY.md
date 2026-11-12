# Dalsza diagnoza felg po zamknięciu r3

To odczyt źródeł i propozycja następnej próby, bez zmiany produktu i bez nowego generatora. Najpierw kolejna gałąź, merge main i świeży baseline. Nie traktować samego wzrostu ratio jako zamknięcia P1.

W chassis.py wheel tworzy pierścień tarczy z profilu lathe i wycina dziesięć otworów Boolean EXACT, po 16 segmentów na cutter. Naczepa trailer_build.py wheel używa dziesięciu otworów o 10 segmentach. a6_export decimate_pieces poddaje te tarcze ogólnemu COLLAPSE z limitem pola powierzchni; ochronę cylindrycznych kolumn mają tylko tyre/rim, nie perforowana tarcza. v3 poprawia jej budżet, ale nie zabezpiecza regularności każdego otworu. To zgodne z nadal nierównymi obrysami na flat, bez dowodu na konkretną błędną ścianę.

Źródłowe LOD1_DROP usuwa nut/washer, a LOD2 dziedziczy tę listę. Ciemne drobne ślady w obrębie rozstawu śrub mogą być śladem wspólnego bake, niekoniecznie dodatkową dziurą. Trzeba osobno porównać flat i albedo w tej próbce; nie utożsamiać wszystkich ciemnych kropek z geometrią.

Najbardziej uzasadniony następny eksperyment to redukcja zachowująca pętle dziesięciu otworów i regularny obrys tarczy. Wyznaczyć rzeczywiste granice na oryginalnym GAME mesh, potem sprawdzić wybiórczą redukcję pętli/retopologię i przeniesienie UV. Nie wolno mostkować chartów ani zwiększać limitu całego pojazdu. Samo zablokowanie wszystkich oryginalnych wierzchołków otworów może ponownie przekroczyć budżet; najpierw zmierzyć próbę pod heavy na cache, bez instalowania częściowych plików.

Weryfikacja: ta sama kamera Low clear/overcast, flat i końcowy materiał, pary v3|próba, zdjęcie jako odniesienie formy. Następnie cały Low, High jeśli mapy zmienione, wszystkie kamery i test osi. Zachować istniejące naprawy UV i piast. Pozostałe większe cele sesji to lakier/dach i szyba, więc po nowym baseline porównać ich wagę z P1 kół.

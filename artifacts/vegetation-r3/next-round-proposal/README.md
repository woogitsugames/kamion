# Propozycja do kolejnej rundy — nie jest wdrożona

leaf-core-proposal.patch i plantings_leaf_core.py są przygotowaniem następnego eksperymentu. Nie zmieniono produkcyjnego plantings.py. Nie wykonano dla propozycji testów GIS, generatora świata ani renderu Unity. Nie ma akceptacji wizualnej ani budżetu GPU.

Tylko berberis_red otrzymuje flagę leaf_core. Istniejąca geometria wewnętrznej warstwy używa już obecnego materiału hedge_shell_berberis zamiast pełnego rdzenia PBR. UV otrzymuje skalę HEDGE_TILE_M i osobną fazę, aby listki nie pokrywały się dokładnie z powłoką zewnętrzną. Pozostają te same pozycje, indeksy, warstwy i liczba części siatki. Potencjalne zwiększenie kosztu alpha overdraw wymaga pomiaru; mniejsza liczba użytych nazw materiałów nie dowodzi liczby wywołań.

Mała analiza geometryczna pojedynczej grządki 8 × 1,3 m, uruchomiona w około 0,8 s: berberys 1362 trójkąty przed i po, dokładnie te same pozycje i indeksy. Privet 1014, hornbeam 996, thuja 980 trójkątów; ich materiał, UV i geometria są dokładnie niezmienione. To analiza syntetycznej geometrii, nie test rzeczywistego świata.

Rozszerzenie analizy na cztery rzeczywiste obrysy grządek z overrides.yaml daje 18 402 trójkąty przed i po oraz te same pozycje i indeksy. Obrysy i ziarna są te same co w producentach, ale teren w tej małej analizie jest płaski z=0. Nie jest to kontrola geometrii ani kolizji po rzeczywistej regeneracji świata. Cała rozszerzona analiza trwała około 1,1 s; nie uruchamiała generatora świata ani testów GIS.

Przed użyciem: zamknąć r3, utworzyć kolejną wolną gałąź i scalić main. Zweryfikować hash bazowego plantings.py z geometry-study.json; przy driftach ponownie opracować zmianę. Dotychczasowy test nieprzezroczystego rdzenia berberysu trzeba dostosować do nowego kontraktu, zachowując sprawdzanie wysokości i ochronę innych gatunków. Testy GIS zawsze przez heavy. Następnie pełny generator w heavy, import i probe Low/High przy rondzie przez Unity slot, porównanie z rzeczywistym CC0 zdjęciem Rakoon z 2020-11-02. Słaby lub pusty żywopłot oznacza odrzucenie, nie automatyczną akceptację braku pełnego rdzenia.

Nie zwiększać teraz losowych przerw ani tworzyć grubych wypukłych kiełbas — wcześniejsze iteracje odrzucono właśnie za taki wygląd. Bliskie zdjęcie pokazuje niski, gęsty pas o drobno nieregularnej powierzchni. Po przyszłej zmianie sprawdzić także geometrię węzłów road_collision i terrain_lod2 oraz pełną macierz kamer i kosztów, jeśli kandydat przejdzie probe.

# ADR 0118 — Materiał nawierzchni

## r1 — Low, ślady kół i widoczność istniejących napraw

Stan r1: zakończona, ocena wizualna warunkowa, bez pełnego PASS; koszt GPU A16 UNVERIFIED.

Bazą jest gpt-surface-wear scalone do aktualnego main w worktree gpt-asphalt. Recenzja 0099 wykazała brak zmiany asfaltu w kamerach trasy, pomijanie spękań przez Low i ukryty mnożnik przetarcia farby w importerze.

Zmiany będą sterowane osobnym blokiem danych materiału. Istniejące materiały bez tego bloku muszą zachować dotychczasowe działanie. Shader nawierzchni używany przez asfalt to WorldPBR, a nie starszy WorldSurface. Zmiany wspólnego shadera i importera obejmą wyłącznie warstwy asfaltu i farby za flagą danych. Nie zmieniamy geometrii dróg, ustawień jakości ani kontraktu liniowego _Tint.

Pierwszy wariant: obecna maska spękań na Low z jedną próbką koloru, bez próbkowania normalnej spękań; mocniejszy kontrast istniejącego pola kół i korekta tonu starego asfaltu. Wartości są WORKING_VALUE. Naprawy i olej już są generowane — baseline roads_qa podaje 316 łat i 286 plam, więc najpierw badamy ich widoczność zamiast zwiększać liczby w ciemno.

Dowody będą obejmować te same kamery przed i po w Low/High clear/overcast, zdjęcia ze wskazanych par sbs i osobne liczniki instancji. A16 pozostaje UNVERIFIED, ponieważ sesja nie używa telefonów. Bez potwierdzenia obrazu i budżetu zmiana nie otrzyma PASS.

Instrukcja właściciela z 2026-11-11 ~22:20: każdy ciężki producent Pythona i pytest GIS/physics/gate3 korzysta z puli heavy (max 3). Pełny GIS dopiero na końcu rundy; w trakcie rundy tylko konkretne pliki. Import nie może uruchamiać ukrytego build_all/build_world bez heavy. Własne runnery stosują aktualny skrypt slotów z main bez edycji wspólnego skryptu.


Wariant r1a: Low na starym asfalcie próbkuje istniejącą maskę spękań oraz istniejące foto-albedo w pobliżu kamery, bez dodatkowych normalnych warstw. Flagi są w asphalt_wear. Dla decal_patch blok asphalt_patch_seam w danych włącza szew 25 mm i rozrzut tonu zależny od wieku (WORKING_VALUE). yard_wear normalizuje wyłącznie UV0 całych dekoracyjnych łat PRZED cięciem na chunki; pozycje, indeksy, UV1, farba i wzory placu Kwadrat pozostają identyczne. Shader wyznacza fizyczną szerokość szwu z pochodnych powierzchni, bez tekstury i bez nowego przebiegu. Materiały bez flag zachowują poprzednie ścieżki. Low na starej drodze: dwie dodatkowe próbki; Low łaty: jedna próbka foto-albedo i ALU szwu. Koszt mobilnego GPU jest UNVERIFIED, do oceny lidera po integracji.

### r1b — świeża farba, podłoże i olej w miejscach zatrzymania
Kontrola r1a wykazała za mocne przetarcie na nowej nawierzchni. Materiał jezdni jest odczytywany przed chunkowaniem z jej trójkątów na zgodnym poziomie wysokości; próbki w wierzchołkach, środkach krawędzi i trójkątów muszą być jednoznacznie podparte nowym asfaltem. UV1.y farby dostaje +4: [4,5) podłużna, [6,7) poprzeczna; część ułamkowa wieku i UV1.x pola pasa pozostają bez zmian. Wartownik (-1,5) nie jest klasą nowej nawierzchni. Świeża nawierzchnia ma jawne mnożniki zużycia 0/0 w danych, a stara zachowuje 0,85 wheel_wear. Pod farbą odtwarzane są ślady kół starego asfaltu, aby odsłonięte miejsca miały kolor faktycznego podłoża. Olej źródeł oil:j... ma skalę 1,15 w dotychczas nieużywanym UV1.x; plamy placów, bram i przystanku zachowują stare dane. Próba przesunięcia foto-detalu o jeden mip nie zmieniła drobnego wzoru przy krawężniku i została cofnięta. Wyłączenia foto-detalu, spękań, normalnej oraz brudu rynsztoka również nie usunęły wzoru. Przyczyna pozostaje nieustalona; nie raportujemy jej jako naprawionej. Modulacja śladu używa metrowej skali macro.g zamiast drobnej macro.a; zachowuje średnią amplitudę 0,825. Bez nowych kanałów wierzchołków, geometrii, materiałów, tekstur ani przebiegów; wszystkie wartości wyglądu pozostają WORKING_VALUE do sprawdzenia w renderach.


### Wynik końcowy r1 / candidate2
Kod produktu: 53e403c964cbb62e028c27eabd6d78ec1c27e3f5. Porównano 312 par z 78 kamer w Low/High clear/overcast, osobno mesh i instancje: wszystkie liczniki delta 0. Obejrzano 28 contact sheets i 14 większych arkuszy. Importer: geometria bez wzrostu bajtów, tekstury ASTC 40 667 737 bajtów bez wzrostu. Są to estymacje widoczności i alokacji, nie czas GPU. Low overcast ślad/środek: baseline 1,045/1,033, candidate2 0,970/0,972. Referencja jednego zdjęcia około 0,67, więc docelowego kontrastu nie potwierdzono. Niezależny krytyk: warunkowe, bez pełnego wizualnego PASS; stara łata zbyt regularna i płaska, część nowej farby nadal zużyta. EditMode 275/275 passed. Końcowy GIS 521 passed, 1 xfailed; odtworzono metadane producenta, audyt 196 plik/SHA bez rozbieżności. Fidelity exit 0. Physics/gate3 47 passed, 1 znana porażka odtwarzalności top_speed_flat_comb.json; źródeł fizyki nie zmieniano. A16 UNVERIFIED.



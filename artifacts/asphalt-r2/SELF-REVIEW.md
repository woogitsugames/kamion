# Samokontrola materiałów — r2 / candidate

Obejrzano zbliżenia Low-overcast po imporcie oraz osiem natywnych par wycinków (dwie kamery × Low/High × clear/overcast). Na kostce pozostały widoczne ziarno i ciemne spoiny; zmiana mokrych plam jest subtelna i nie usuwa wszystkich ciemniejszych obszarów. Na obrzeżu widać ciemniejsze podziały, szczególnie w Low-overcast, bez mocnego ciągłego pasa brudu. Low pozostaje bardziej miękki niż High, co nie zostało naprawione tą zmianą. Nie potwierdzamy stabilności w ruchu ani zgodności fotometrycznej z Mapillary.

Kamery przed/po mają identyczne view, projection, rootToWorld, position, fov i aspect w 328 snapshotach. Zmiana nie korzysta z UV1 obrzeża/chodnika: próbka źródłowa paved ma (0,50), więc nie wolno udawać znanej odległości od brzegu. Osiem pełnych par oraz wszystkie kamery trasy będą ocenione po zestawieniu końcowych kontaktów.

Import: 22 kategorie geometrii delta 0, ASTC bez wzrostu, liczby instancji i colliderów bez zmian. Raport nie mierzy uniformów: nowy float4 w CBUFFER zwiększa deklarację stałych WorldPBR o 16 bajtów przed wyrównaniem, a gałąź sterowana uniformem dodaje ALU materiału krawężnika. Brak nowych fetchów, keywordów i przebiegów nie oznacza zmierzonego kosztu GPU. A16 UNVERIFIED.

W trakcie: pełne liczniki 82 kamer, audyt 128 GLB i niezależna końcowa ocena. Brak pełnego PASS na tym etapie. D51: materiał nie blokuje route Gate3.

Runda 3, edge, gałąź gpt-edge-r3. Stan walidacji: 7b798ee6828e5f5fded07f73891fe3d74f6725cd; poprawka C#: 16199d31a2b2fe38889cd15338fa4f79f22dd8c4. Baza main: 2c3939b2.
Poprawiono wagę narożników apron: średnia i okno wygładzania korzystają z 512 unikalnych próbek zamiast 528 wpisów z kopiami wachlarzy. Obliczenia wyłącznie przy imporcie.
W 5676 punktach maksimum Python−Unity spadło z +1,4267 do +0,8907 m, p95 abs z 0,1733 do 0,1413 m; próbek >+0,8 m jest 1 zamiast 40. Rozbieżność nie zniknęła całkowicie.
Podstawy kurtyn powyżej +0,05 m: Low 137→1, High 777→7; maksima odpowiednio +0,9182→+0,2053 i +0,9267→+0,3774 m. Próg jest WORKING_VALUE; widoczność szwu i alfa tekstury pozostają niezweryfikowane.
Audyt V=0 omyłkowo mierzył korony; zachowano go z oznaczeniem INVALID. Potwierdzony audyt używa V=1 surowego glTF i ma udane powtórzenie pod heavy.
Dwa testy stoków: Red 2 oczekiwane porażki, Green 2 zaliczenia tego samego pliku testu. Pełne EditMode: 297/297, bez pominięć.
Końcowy GIS pod heavy: 591 passed, 1 xfailed, 0 failed, 797,91 s. Pierwszy przebieg urwał restart komputera; zachowano log bez wyniku i wykonano pełne powtórzenie.
GIS sprawdzono na świeżej pełnej regeneracji, przed odtworzeniem cudzych metadanych. Oba własne pola far-field były zgodne z bazą; po kontroli SHA przywrócono uboczne pliki. Audyt 64 GLB dotyczy plików CLI; niezależność budowy pytest sprawdza zaliczony test deterministyczności, nie dodatkowa kopia tych plików.
Before i After: po 368 PNG, 92 kamery w czterech konfiguracjach. Wszystkie 184 Low: delta draws 0, także osobno statyczne, instancje i cienie; delta sumy zaokrąglonych trisK 0. Dane każdej kamery w all-cameras.csv.
Zachowano 100 par zdjęcie–render do 960 px dla 25 pozy B z atrybucją; 17 C wykluczono z oceny fotograficznej. Fotometria i dokładna poza B pozostają UNVERIFIED.
Apron: 6572 wierzchołki, 10128 trójkątów trawy i 840 asfaltu; 35 kontynuacji, minimum prześwitu 0,0403 m. Oba źródłowe GLB far-field zachowały SHA. Normalne i tangenty mogą zmienić się z wysokościami.
Obejrzane zwykłe north/east są wizualnie bliskie bazie; statywy NW zasłania płot lub HLOD. Jakość fotograficzna i wizualne zamknięcie szwu: PARTIAL, bez ogólnego PASS.
Pakiet next-round-review rozdziela dalekie tło od 10 regionalnych bloków ≥25 m w FOV każdego wskazanego kadru. ID i pozycje są kandydatami źródłowymi, nie dowodem brakującej siatki ani identyfikacją fotografii. Regionalnych budynków nie dublowano.
Low ma far clip 900 m. Fotograficzne High jest ograniczone authored Gate3 do 1400 m mimo profilu 2500 m; nie zmieniono kamer ani SBS.
Nie zmieniono shaderów, mgły, profili jakości, geometrii barier i źródeł innych dziedzin. Build_world po poprawce: 424,4 s, bez fallback=True. Brak pomiaru GPU telefonu; bez adb, push i merge do main.
Konflikty integracji: własny WorldEdgeBuilder.cs, jego testy i sekcja r3 ADR 0121; po scaleniu lider regeneruje pochodne. Dane własnej siatki After, XML i logi są w tym pakiecie.
Następna runda: merge aktualnego main i diagnoza szarego klina przy nowych chmurach w 2948/303305 przez maski Apron/FarField. Obecny podgląd pochodzi z light-r1, nie jest świeżym renderem main; 2948 ma klasę C wyłącznie do diagnostyki.

# Roboczy opis r4 — runda otwarta, nie scalać na tej podstawie

To materiał do przyszłego REPORT.md, nie zgłoszenie gotowości. Gałąź: gpt-vegetation-r4. Baza po scaleniu main do własnej gałęzi: c3cf303d, pierwotnie 7c9b4ca6. Ostatni zapis przed tym szkicem: 27040111. Ostateczny SHA, decyzja o kodzie, walidacja końcowa i kopia artefaktów pozostają do uzupełnienia. Sesja dotyczy wyłącznie vegetation; nie było push ani scalania do main, telefonów lub adb.

## Problem i świeży punkt odniesienia

Berberysy na rondzie wyglądają jak bordowe belki z dużymi płaskimi fasetami, a fotografia pokazuje niskie, przycięte krzewy z drobną strukturą liści. Zdjęcie Rakoon, CC0, 2 listopada 2020 r., jest odniesieniem wyglądu. Data, autorstwo, licencja i hash znajdują się w berberis-reference.json. Zgodność pozy i sezonu nie stanowi kalibracji wymiarów; wartości wysokości, szerokości i pokrywy są WORKING_VALUE.

Po zmianach świata i światła na main wykonano nowy baseline: 368 PNG, w tym 67 kamer kontrolnych i 25 fotograficznych B, każda w Low/High oraz clear/overcast. Autor obejrzał wszystkie 40 arkuszy baseline. Nie przenoszono PNG z wcześniejszych rund. Materiały ukończyły się w 446 s, World baseline w 614,8 s. Piny obejmują 130 GLB, 64 pliki instancji, 617 wejść produkcji i dekodowaną kolizję 64 Low chunków. Było dostępnych 15 Megascans, bez fallback.

Runda rozpoczęła się około 03:05. Poprzednia sekwencja oczekująca na heavy przestała być dostępna, a proces nie istniał; po wznowieniu około 09:06 sprawdzono stan i nie powtarzano ukończonych materiałów. Około pięciogodzinna przerwa nie jest raportowana jako ciągła praca ani powód przedłużenia terminu sesji. Szczegóły są w session.json i STATUS.md.

## Przeprowadzone próby

| Próba | Zmiana i rzeczywisty wynik | Decyzja |
|---|---|---|
| A | Wewnętrzna warstwa berberysu używa istniejącego materiału alpha shell i UV w skali liści. Po poprawieniu dawnych selektorów materiałów 18 testów przeszło w 3,27 s. World 538,6 s, 18 402 tris nasadzeń, import i 16 ujęć ukończone. | Autor i krytyk obejrzeli osiem arkuszy. Boki drobniejsze, ale duża płaska pokrywa i belka pozostały. Odrzucona jako końcowa. |
| B, pierwotny loft | Mała analiza wykazała osiem samoprzecinających cap-ringów, awaryjne ear_clip i krawędzie 16,2–19,7 m. Próba poprawnych ringów łączonych równymi indeksami dała 8 failed, 19 passed w 4,16 s: skrzyżowane paski. | Generator nie został uruchomiony. Odrzucona przed renderami. |
| B2 | Dokładne offsety z zachowaniem narożników, niezależne liczby punktów, lokalne CDT pasów z otworem i capów, spójny podział próbek na wspólnych krawędziach, szwy UV, bez XY bulge nowej ścieżki. 33 testy przeszły w 10,29 s; World 534,6 s; 20 347 tris; kolizja, import i 16 ujęć ukończone. | Autor i krytyk obejrzeli osiem arkuszy. Duże fasety znikły, ale wierzch nadal był gładką pokrywą. FAIL końcowego realizmu. |
| C / B3 | Deterministyczne próbki z jitterem i minimalnym odstępem, niezależne od wierzchołków capu. Korzenie na rzeczywistych trójkątach, istniejący atlas i materiał pędów. 40 testów przeszło w 11,56 s; World 515,6 s; 21 697 tris; kolizja, import i 16 ujęć ukończone. | Autor i krytyk obejrzeli wszystkie 16 arkuszy baseline–C i B2–C. PARTIAL dla poprawy środka korony, FAIL końcowego realizmu: sterczące pędy na nadal gładkim blacie. |
| D | Przy tych samych korzeniach i liczbie kart niższa, bardziej pochylona pokrywa, większa powierzchnia widoczna z góry i głębiej schowane podstawy. Lekka analiza daje nadal 21 697 tris. | Sekwencja 24975 czeka na heavy. Nie ma jeszcze wyniku 41 testów, World D ani renderów. |

Próby nie zmieniały tekstur ani shaderów. Produkcyjna zmiana dotyczy plantings.py. Nowa ścieżka jest za danymi berberysu; pozostałe rodziny zachowują dotychczasową ścieżkę. D dodaje parametry pochylenia i zagłębienia pokrywy, a domyślne zagłębienie pędów brzegowych i innych rodzin pozostaje 25%. Nowe testy sprawdzają ważność i pokrycie siatki, brak nakładania, rzeczywisty prześwit core–shell na wspólnym podziale, ciągłe korzenie, rozstaw pokrywy i wysokość na rzeczywistych ścianach. Test płaskiej próbki D nie jest dowodem zachowania całej karty na lokalnym reliefie.

## Ograniczone pomiary i kontrola pochodzenia

W próbie C jedynym zmienionym źródłem jest plantings.py, a wynikami geometrii chunk_6_6 Low/High oraz metadane QA/manifest. Wszystkie 64 pliki instancji, dekodowane wejścia kolizji i far-field GLB pozostały identyczne. Cztery nasadzenia zachowały powierzchnię 94,3 m² i dane wysp; wzrosła jedynie jawnie dopuszczona liczba trójkątów. To dowód zachowania wejść geometrii kolizji, nie pomiar PhysX w ruchu.

W 16 wierszach małej próby C maksymalny przyrost Low względem baseline wyniósł 0 draws i 1,020408% trisK; względem B2 0 draws i 0,337838% trisK. Statyczne i instancjonowane wywołania są zapisane osobno w plikach porównań. To nie pełny budżet 67 kamer, nie pomiar czasu GPU i nie dowód braku migotania. Nie przenosić tych wyników na D przed pomiarem D.

Osiem kontrolnych PNG C jest bajtowo identycznych z B2. Sześć jest identycznych z baseline, a dwa High remizy zachowują wcześniejsze różnice po sześć pikseli. Autor obejrzał oba arkusze różnic B2; nie stwierdził makroskopowej zmiany, ale przyczyna mikroróżnic pozostaje niepotwierdzona. Nie raportować ośmiu identycznych PNG względem baseline.

## Dowody wizualne

Wszystkie poniższe arkusze mają szerokość 960 px. Zawierają rzeczywistą fotografię, pełny kadr i stały wycinek; zdjęcie i render nie mają potwierdzonej tej samej pozy.

- [C względem baseline, Low overcast, podejście do ronda](berberis-review-probe-c/Low-overcast-g3a-rondo-bie-approach.jpg).
- [C względem baseline, High clear, widok z poziomu gruntu](berberis-review-probe-c/High-clear-photo-biezenstwa-ground.jpg).
- [Sama zmiana pokrywy B2–C, High clear](berberis-review-probe-c-vs-probe-b/High-clear-g3a-rondo-bie-approach.jpg).

Pełne oceny autora i niezależnego krytyka są w SELF-REVIEW-probe-a/b/c.md oraz VISUAL-CRITIC-probe-a/b/c.md. Próba D będzie wymagała nowych arkuszy i nowej oceny. Nie zastępować zdjęć oceną samych testów, triangulacji lub liczby kart.

## Co pozostaje otwarte

Nie ma zaakceptowanej końcowej wersji r4. D musi jednocześnie ograniczyć sterczące pędy i zakryć gładkie odstępy, bez dużych płatów, rzędów, unoszenia podstaw i pogorszenia kosztu. Jeżeli przejdzie małą próbę, potrzebne są pełne świeże after, obejrzenie wszystkich arkuszy, koszty wszystkich kamer, końcowy GIS przez heavy i EditMode przez Unity slot. Pełny GIS nie był uruchamiany w trakcie prób. Nie ma jeszcze tych wyników ani końcowej kopii robocopy r4.

Przed zamknięciem trzeba zachować dowody skutków ubocznych generatora, a następnie przywrócić jawne pliki cudzych dziedzin i wspólne ustawienia Unity, bez commitowania ich zmian. Snapshoty dużych JSON nie mają być dodawane do gita. Finalny REPORT musi podać rzeczywisty końcowy SHA, decyzję o kodzie, wynik walidacji i wynik robocopy. Potencjalne konflikty kodu dotyczą plantings.py i testów nasadzeń; ADR 0109 wymaga zachowania sekcji wcześniejszych rund. Dane geometrii dróg i overrides.yaml nie były poprawiane.

Problem B8 nie został odblokowany: świeża recenzja main batch D nadal ocenia pozę 297817 jako PARTIAL. Nowych drzew w pasie dzielącym nie wolno mapować z tej niezgodnej pozy. Badanie poboczy pozostaje w VERGES-RESEARCH.md i NEXT-ROUND-INPUTS.md; r4 nie jest rozwiązaniem tych osobnych problemów.

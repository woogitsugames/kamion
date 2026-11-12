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
Kod produktu: 53e403c964cbb62e028c27eabd6d78ec1c27e3f5. Porównano 312 par z 78 kamer w Low/High clear/overcast, osobno mesh i instancje: wszystkie liczniki delta 0. Obejrzano 28 contact sheets i 14 większych arkuszy. Importer: geometria bez wzrostu bajtów, tekstury ASTC 40 667 737 bajtów bez wzrostu. Są to estymacje widoczności i alokacji, nie czas GPU. Pomiar kontrastu renderu z r1 został wycofany: narzędzie błędnie odtwarzało anchor z wysokości kamery zmienianej przez seat=road. Wymagana jest rzeczywista rootToWorld; brak jej w starych zapisach oznacza UNVERIFIED. Patrz artifacts/asphalt-r1/CORRECTION-2026-11-12.md. Pomiary samej fotografii około 0,67 pozostają oddzielnym pomiarem obrazu. Niezależny krytyk: warunkowe, bez pełnego wizualnego PASS; stara łata zbyt regularna i płaska, część nowej farby nadal zużyta. EditMode 275/275 passed. Końcowy GIS 521 passed, 1 xfailed; odtworzono metadane producenta, audyt 196 plik/SHA bez rozbieżności. Fidelity exit 0. Physics/gate3 47 passed, 1 znana porażka odtwarzalności top_speed_flat_comb.json; źródeł fizyki nie zmieniano. A16 UNVERIFIED.



## r2 — krawężniki i kostka jako materiał

Stan końcowy: runda zakończona, candidate2 ma PASS ograniczonej poprawy materiałowej; jedna znana porażka physics/gate3 jest ujawniona, GPU A16 UNVERIFIED. Bazą jest merge main 4992c434. D51 określa rozpoznawalność trasy jako priorytet bramki 3; ocena drobnych materiałów w tej rundzie nie jest blokadą tej bramki.

Zakres pozostaje materiałowy. Istniejący generator zapisuje UV1 długości i odległości od rynsztoka dla profili krawężników/chodników, a zestawy mają maskę fug Var.B. Zbadamy wykorzystanie tych danych do brudu przy krawędzi i czytelniejszych fug. Źródła roads, geometria i ustawienia jakości pozostają poza zmianą. Materiały bez nowych flag muszą zachować dotychczasowe działanie; brak UV1 nie może być interpretowany jako poprawne dane brzegu.

Przed wyborem parametrów potrzebne są cztery serie baseline, oględziny roboczych zbliżeń poza Kwadratem i referencje w aktualnych pozach SBS z main. Mierzymy zmiany w tych samych polach obrazu Low/High clear/overcast oraz wszystkie liczniki kamer i instancji. Wartości wizualne będą WORKING_VALUE, koszt A16 bez telefonu pozostaje UNVERIFIED. Kontrakty _Tile, liniowego _Tint i weather/runoff zostają zachowane.



### r2a — kandydat materiałowy
Oględziny poprawionego zbliżenia wykazały już czytelne fugi kostki i duże mokro wyglądające plamy. Parametry ground_grime dotyczą tylko sidewalk_paving: damp_darkening 0,42 → 0,18, threshold 0,62 → 0,65, joint_dirt bez zmian 0,45, gloss 0,5 → 0,15. Krawężnik opt-in kerb_wear: joint_dirt 0,35, mineral_film 0,16, threshold 0,55. Wartości WORKING_VALUE. Oba efekty używają już próbkowanych tekstur: brak nowych odczytów, wariantów słów kluczowych, przebiegów lub kanałów UV. Nie wykorzystujemy niepełnego UV1 (0,50) do udawania brudu przy brzegu. Profile, pozycje, indeksy i dane geometrii bez zmian; wymagany audyt wszystkich GLB oraz liczników kamer. Zdjęcia SBS mają niedopasowaną pozę i służą tu wyłącznie za przykład materiału, bez kalibracji fotometrycznej.


### r2b — zachowanie obszaru Kwadrat
Read-only kontrola overrides ujawniła, że top wysepki bramy używa sidewalk_paving. Wariant candidate1 nie jest końcowym wynikiem: nowy materiał musi wyłączyć także współdzielone ID na chronionym obszarze. Flaga ground_wear_exclude_local_en=[400,-700,850,-250] obejmuje punkty Kwadrat i bramę z buforem; wewnątrz kerb_wear ma wagę zero, a ground_grime używa oryginalnych współczynników. Osiem metrów przejścia jest wyłącznie na zewnątrz. Fragment używa TransformWorldToObject, aby wykluczenie zachować po floating origin. Nowe odczyty tekstur/przebiegi/UV: zero; całe r2 deklaruje teraz trzy dodatkowe float4 (48 bajtów stałych przed wyrównaniem), sprawdzanie zakresu i ALU dla aktywnych flag. GPU A16 UNVERIFIED. Nie zmieniono overrides, dróg, geometrii ani assetów Kwadrat. GPU readback rzeczywistego bloku HLSL testuje punkt Kwadrat, publiczny probe i brak scope z przesunięciem obiektu: EditMode 312/312 passed, zero skipped. Finalne kamery Kwadrat muszą zostać porównane z baseline przed publikacją.


### r2c — zakończona kontrola materiału, oczekiwanie na końcowe testy
Wybrano candidate2. Baseline i kandydat mają 82 kamery × cztery warunki, 328 zgodnych par oraz identyczne rzeczywiste macierze i rozmiary RT. Wszystkie 2952 liczniki, w tym osobne liczniki instancji, mają deltę zero. Audyt 128 GLB i 7315 prymitywów: identyczne atrybuty, indeksy i hierarchie; 22 kategorie bajtów importu bez wzrostu, ASTC 40 910 657 B bez zmiany. Są to dowody geometrii i estymacji widoczności, nie czasu GPU.

Samodzielnie obejrzano 60 arkuszy obejmujących wszystkie pary. Niezależny visual-critic: PASS ograniczonej poprawy materiału candidate2; brak zatwierdzenia pełnego realizmu, stabilności w ruchu i Gate3. Publiczna kostka ma słabsze duże plamy, obrzeże czytelniejsze spoiny. Jasne punkty High i regularność kostek pozostają ograniczeniami. Chroniona brama: candidate2 zmienia o ponad 2 poziomy RGB 0/7/4/6 pikseli całych czterech obrazów wobec 9996/9240/8820/8828 w odrzuconym candidate1. Nie jest to deklaracja identyczności całych obrazów ani dowód całego obwodu wyłączenia.

Końcowy GIS: 604 passed, 1 oczekiwany xfailed, exit 0, 1224,78 s; po odtworzeniu metadanych producenta audyt 196 odwołań/SHA bez rozbieżności. Physics/gate3, fidelity i końcowy EditMode pozostają w sekwencji walidacji; raport końcowy i przekazanie rundy nastąpią po odczytaniu ich wyników. Narzędzia hosta były niedostępne od około 03:44 do 09:04; nie zaliczamy tego jako ciągłej pracy. Wznowiono tylko brakującą walidację, zachowując ukończone rendery i audyty.

### Wynik końcowy r2 / candidate2

Końcowy EditMode312/312 passed, bez pominięć i porażek. GIS604 passed,1 oczekiwany xfailed,exit0. Physics/gate3:47 passed,1 znana porażka odtwarzalności top_speed_flat_comb.json,exit1; wejścia tego testu i dims.json bez zmian względem bazy. Fidelityexit0 po229,3s; wygenerowane zmiany obejmują tylko17 ścieżek nakładek, bez zmian metryk. Wskaźniki narzędzia nadal wykazują niezweryfikowane pasy i brakujące wyspy/drogi, więc exit0 nie jest zatwierdzeniem Gate3. Końcowy audyt196 odwołań/SHA bez rozbieżności. Wszystkie60 obejrzanych arkuszy ponownie zgodne SHA. Ustawienia Unity przywrócone, własne sloty zwolnione. Pełny raport i wszystkie328 par/2952 liczniki w artifacts/asphalt-r2/REPORT.md; przekazanie wyłącznie przez robocopy artifacts, bez merge do main i bez push. Następna runda obejmuje materiały placów przemysłowych poza Kwadratem po świeżym merge main i nowym baseline.

## r3 — place przemysłowe poza Kwadratem

Runda rozpoczęta po przekazaniu r2, od gałęzi gpt-asphalt-r3 i merge main0023f39d. Zachowano unię wspólnych materiałów0118/0119/0120. Baseline wymaga nowej generacji materiałów i świata; poprzednie GLB oraz kamery r2 nie są dowodem nowego main. Własne źródła produktu r3 nie zostały jeszcze wybrane.

Referencja zewnętrznego placu PCRT: Rakoon, 2020-07-11, CC BY3.0, oryginał i SHA w backlog-r3-references odziedziczonego r2. Pokazuje zazębiającą się kostkę i umiarkowane spoiny. Nie ma GPS tej fotografii ani dopasowanej pozy; sąsiednie geotagi i pobliski obrys BDOT z opisem asfaltu wymagają wyjaśnienia. Nie traktujemy tego jako licencji na globalną zmianę asfaltu albo geometrii.

Sonda materiału jest tylko do odczytu, obejmuje lokalne E280–395/N−560 do−300 poza konserwatywną granicą Kwadrat, wymaga świeżego producenta i SHA GLB. Wybór wyglądu nastąpi po odczycie i renderze. Plan capture będzie zawierał rzeczywiste native i pomocnicze ID; audyty muszą sprawdzać cały ten zbiór oraz dziewięć liczników każdej kamery, w tym instancje. Wartości materiału WORKING_VALUE, GPU A16 UNVERIFIED, bez telefonu.

### r3a — synchronizacja z naprawą lidera ADR 0131

Próby diagnostyczne na pierwszej bazie 0023f39d wykazały, że jasne zawijasy ronda pochodzą z warstwy CRACKS, a nie PHOTO_DETAIL. Osobne ablacje rozdzieliły duże plamy kostki posesji (yard_paving/yard_behaton) i jezdni publicznej (road_paving); wyłączenie sidewalk_paving nie usuwało tych ostatnich. To kontrole tymczasowymi MaterialPropertyBlock, nie kandydat produktu ani dowód budżetu rysowania.

Po feedbacku z 13:45 włączono main 11db0552 przez merge e5eb5902. Zawiera naprawę lidera ADR0131: połysk zalewki = smoothness asfaltu +0,06 zamiast 0,55. Nie dublujemy tej poprawki i nie przypisujemy sobie jej rezultatu. Kształt pętli/kropek oraz czytelność ciemnej zalewki pozostają P2. Dotychczasowe PNG i logi oznaczono jako pre0131; nie stanowią baseline nowego produktu. Pierwotny zakres przemysłowych placów poza Kwadratem pozostaje aktualny.

Generowane konflikty i street_props przyjęto z main do regeneracji. Konflikt materials.py był przeniesieniem tego samego bloku r2; zachowano jedną kopię oraz aktualne definicje filarów i znaków. Merge nie zmienił żadnego źródła _src generatora materiałów, a wszystkie Medium PNG są świeższe od źródeł: cache ponownie wykorzystany, bez zbędnego build_all. Nowy World wymaga heavy. Import, sonda i analiza odrzucają dawne sukcesy: wymagają complete=true, exit=0 i dokładnego SHA nowego manifestu w baseline-producer-progress.json. Wybór produktu nastąpi po nowym baseline i ocenie placu. Dziewiąty jawny rekord materiału w opt-in QA to road_paving; końcowe audyty wymagają dokładnego kompletu identyfikatorów.

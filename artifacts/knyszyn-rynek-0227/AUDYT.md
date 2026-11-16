# Audyt Knyszyna — stan roboczy

Zdjęcia właściciela są lokalne i nie stanowią tekstur ani materiału do publikacji. Położenia kadrów bez GPS są ESTIMATED.

| Zdjęcie | Co widać | Co jest w danych gry | Różnica / stan weryfikacji |
|---|---|---|---|
| 20240730_190331 | Pionowe strumienie fontanny w płaskiej płycie, kostka w łukach, wysokie drzewa | Override `rynek-fountain-plate` tworzy płytę; `rynek-plaza-east` używa `yard_paving` | Strumienie i kostka łukowa nie są modelowane według opisu override; render baseline oczekuje na import. |
| 20240730_190828 | Szeroki plac z łukami kostki, fontanna, drzewa i monument | Granica placu i las parkowy jako authored overrides | Należy porównać kształt, monument, drzewa oraz nawierzchnię na renderze. |
| IMG20240729165956 | Prostokątna płyta fontanny, centralny wysoki strumień i niższe dysze, ciemne obrzeże | `yard_slabs`, brak geometrii wody według override | Układ dysz, obrzeże i materiał do sprawdzenia; wymiary WORKING_VALUE. |
| 20250729_182511 / 182513 / 182516 | Kremowo-szara elewacja, białe okna, czerwone rynny, dach i lukarny | Zabudowa generowana z BDOT/LoD; przypisanie konkretnej bryły jeszcze nieustalone | Lokalizacja i fasada ESTIMATED, wymagają dopasowania do ortofoto oraz renderu. |
| 20251031_122316(0) | Ta sama zabudowa z ulicy, chodnik, słupy i przewody | Generator ulic i zabudowy | Kadr i lokalizacja niezweryfikowane; porównanie po ustaleniu położenia. |

K1 podaje fontannę OSM 32 m² (~6 × 6 m), natomiast istniejący override przyjmuje ~9 × 7 m. Nie rozstrzygnięto rozbieżności bez pomiaru i dokładnego dopasowania ortofoto.
`paved.collect` obsługuje authored polygons w kolejności wpisów: `rynek-plaza-east` wyprzedza w pełni zawartą płytę fontanny, więc odejmowanie zajętej powierzchni usuwa płytę. Wniosek z kodu, do potwierdzenia renderem baseline; właściwa kolejność to najpierw detal, potem plac.

**P0 — położenie fontanny:** wycinki GUGiK `J_rynek_W_north.jpg` oraz `J_rynek_knyszyn_north.jpg` pokazują, że kwadratowa płyta znajduje się na okrągłym placu w zachodnim parku, a nie na wschodnim placu po drugiej stronie Grodzieńskiej. Korelacja wspólnego fragmentu obu wycinków (`align.py`, 0,1 m/px) daje orientacyjny środek fontanny EPSG:2180 ~760943,5 / 612382,3 (ESTIMATED, wymaga kontroli naroży i OSM). Dotychczasowy override ~761035,7 / 612396,9 leży około 93 m dalej. Wcześniejsze przypuszczenie o samej kolejności nakładających się pól pozostaje prawdziwe dla tego błędnego położenia, lecz nie rozwiązuje lokalizacji.

## Korekta geometrii do r2
Niezależne dopasowanie ortofoto: przesunięcie wycinków 1000/248 px, korelacja 0,929. Środek centralnego placyku wstępnie EPSG:2180 (760941, 612388), promień ~12 m, niepewność ±3–5 m; płyta fontanny (760943,5; 612382,3) nie leży w środku. Ośmiokąt roboczy: (760941,612400), (760949,5,612396,5), (760953,612388), (760949,5,612379,5), (760941,612376), (760932,5,612379,5), (760929,612388), (760932,5,612396,5). Krawędzie zasłonięte koronami; to ESTIMATED.
Osie alejek ESTIMATED: SW (760883,612375)–(760930,612383); NE (760950,612385)–(760980,612393); NW (760905,612411)–(760935,612391); N (760940,612420)–(760939,612397). Wymagają porównania renderu i oryginalnego ortofoto.

## Pierzeja — audyt zdjęć i adresów
Zdjęcia 3/4 potwierdzają urząd `bdot:2002917F-46DC-5C99-E053-CC2BA8C01CFC` i skrzydło kultury `bdot:2002917F-4817-5C99-E053-CC2BA8C01CFC`: jasny krem, żółte opaski, czerwony dach z lukarnami. Zdjęcia 5–7: kościół `bdot:2002917F-8DAE-5C99-E053-CC2BA8C01CFC`, biały, czerwony dach i hełm. Identyfikacja SOURCED obrysem i zdjęciem, proporcje detali ESTIMATED.

Pary adres OSM → obrys BDOT (położenie SOURCED, wygląd poszczególnych fasad UNVERIFIED): Rynek 1 → `2002917F-3002-5C99-E053-CC2BA8C01CFC` (LoD1 7,50 m); Rynek 2 → `2002917F-3031-5C99-E053-CC2BA8C01CFC` (5,98 m); Rynek 3 → `2002917F-3066-5C99-E053-CC2BA8C01CFC` (6,77 m); Rynek 4 → `2002917F-2D30-5C99-E053-CC2BA8C01CFC` (7,79 m); Rynek 5 → `2002917F-3078-5C99-E053-CC2BA8C01CFC` (6,18 m); Rynek 9 → `2002917F-2E16-5C99-E053-CC2BA8C01CFC`. K1-P19 może pokazywać Rynek 9, lecz geotag dotyczy aparatu, a azymut i aktualność fasady są UNVERIFIED. Nie przypisywać kolorów po samym geotagu ani niejednoznacznym tytule K1-P02.

## Zdjęcia właściciela 15.11 — mapa porównań (WIP)

| Zdjęcie | Co widać | Kamera planowana | Stan porównania |
|---|---|---|---|
| 1 | Urząd i pomnik od ulicy | `rynek_owner_01` | Brak renderu po zmianach; ujęcie aparatu ESTIMATED. |
| 2 | Urząd i portyk od dziedzińca | `rynek_owner_02` | Brak renderu po zmianach; sprawdzić skrzydła L, kolumny i schody. |
| 3 | Trawnik, lipy i urząd | `rynek_owner_03` | Baseline z góry pokazuje zwarty las; po zmianach brak renderu z tego miejsca. |
| 4 | Sucha fontanna i obelisk ku urzędowi | `rynek_owner_04` | Dawna kamera patrzyła na plac wschodni; nowy kadr wymaga dopasowania. |
| 5 | Działająca fontanna i kościół | `rynek_owner_05` | Dysze i obwódka przygotowane; strumienie OPEN, brak renderu. |
| 6 | Główna aleja w stronę kościoła | `rynek_owner_06` | Kamera szacunkowa, należy dopasować jej pozycję i oś. |
| 7 | Alejki, obelisk i kościół z boku | `rynek_owner_07` | Brak renderu; położenie i azymut kamery ESTIMATED. |
| 8 | Pomnik króla, blok i maszt | `rynek_owner_08` | Sylwetka PROXY_NOT_APPROVED; brak renderu i weryfikacji rozpoznawalności. |
| 9 | Rondo z góry | `rondo_owner_09` | Kadr drona ESTIMATED; opaska z #97 nie jest scalona, wymiar rzeczywisty UNVERIFIED. |
| 10 | Rondo i otoczenie z drona | `rondo_owner_10` | Brak renderu; punkt, wysokość i kierunek ESTIMATED. |
| 11 | Rondo i DK65 z drona | `rondo_owner_11` | Brak renderu; punkt, wysokość i kierunek ESTIMATED. |

Pary są przygotowywane wyłącznie lokalnie przez `compare.py`; nie zamieszczać zdjęć ani wyników par w Git. Lokalne zdjęcia targowicy `Data/raw/refs/owner-knyszyn-2026-11-15/12-targowica-pion.jpg`, `13-targowica-ukos.jpg`, `14-targowica-wiaty-poziom.jpg` pokazują trzy blisko ustawione wiaty i czwartą z większym odstępem; ich dachy zostały następnie zidentyfikowane w ortofoto 2025 (zob. korektę R24), a słupy i wysokości pozostają szacunkowe. Zdjęcia służą wyłącznie jako referencja, poza Git.

## Wierzba płacząca — analiza techniczna
Istniejące `tree_shrub` w module brzegowym nie jest dorosłą wierzbą płaczącą. Osobny prototyp wymaga LOD0/LOD1, impostora i materiału drobnych liści oraz weryfikacji wizualnej; koszt i pozycja UNVERIFIED. Ścieżka authored `points_en` losuje obecnie wariant 0–2 bez ograniczenia `NVAR`, więc jeden wariant wymaga poprawki doboru indeksu; dodanie gatunku do globalnych mieszanek zmieniłoby dotychczasowe losowania i nie jest potrzebne. Nowy zasób wymaga wpisu licencyjnego i pomiaru Low/High.

## Iteracja r1 — ocena 15.11, editor

Rendery Low/High × clear/dusk: `artifacts/knyszyn-rynek-0227/r1/`; lokalne pary 01–11: `artifacts/knyszyn-rynek-0227/compare/r1/High-clear/` (zdjęcia poza Git). **FAIL**, nie jest to ocena właściciela ani pomiar telefonu.

- W 03–07 zwarta ściana lasu zniknęła, ale korony wyglądają jak spłaszczone sosny, nie lipy; zdjęcia wskazują większe pełne korony i gęstszy układ. Trzy punkty odrzucone przez maskę.
- W 04/05 centralny plac ma widoczny podest i ciemne krawędzie, fontanna zlewa się z nawierzchnią i nie ma strumieni; plac nie jest równo z trawnikiem. Ujęcie 06 nie jest na osi alei.
- 03: część ścian urzędu jest ślepa, kolumny nie tworzą loggii ze zdjęcia; kamery 01/02 wymagają dostrojenia. 08: sylwetka króla jest zastępczym słupkiem, nie figurą.
- 05–07: kościół ma rozpoznawalny kolor i wieżę, ale bryła jest zbyt uproszczona; kąty zdjęć i pierzeje wymagają korekty.
- 09–11: widoczny pierścień ronda nie ma jasnej dwustrefowej wyspy i długich azylów; kamera 09/10 ma inny obrót i perspektywę niż zdjęcie. Zakres ronda wymaga #97 i danych zgodnych z nowym stanem.
- Szacowane draws edytora Low: maksimum 429 → 440 (`tykocka-into-town`); na wspólnych kamerach największy wzrost 14 (`cab-mirror-front`). High max 760 → 774. Mesh `trisExact` Low max 370158 → 368247, High 1237074 → 1237336; instancje są w osobnych wierszach. Low bez pogorszenia NIE spełnione. Szczegóły: `budget-r1.py`, `before/*/stats.txt`, `r1/*/stats.txt`.

## Fontanna — analiza animacji
Istniejący `WorldWater.shader` jest nieprzezroczysty i przeznaczony do tafli, a dostępny `blend` importera tworzy statyczny materiał. Nie znaleziono ścieżki animowanych półprzezroczystych pionowych strumieni wyłącznie danymi `tools/worldgen`. Konieczne byłyby osobny shader, materiał i ścieżka warstwy/importu, zachowanie UV oraz test faz, stripowania i kosztu Low/High; sortowanie, migotanie i overdraw są niezweryfikowane. Obecna fontanna pozostaje sucha (`water_jets=OPEN`), także latem. Bez osobnej implementacji i walidacji nie twierdzić, że strumienie działają.

## Iteracja r2 — ocena 15.11, editor

Zestawienia 01–11 lokalnie: `compare/r2/High-clear/`; zdjęcia właściciela i pary poza Git. Cztery warianty Low/High × clear/dusk ukończone; ocena całości FAIL. Widoczny uskok placu fontanny zniknął w kadrach 04/05; drzewa nadal mają zbyt rzadkie korony, figura króla jest prowizoryczna, a fontanna bez strumieni. Kamera 02 zasłonięta pniem, 07 obeliskiem, 03 wymaga dopasowania alei, 08 placyku i układu zegara. Kamery 09–11 i układ ronda różnią się od fotografii. Low: maksimum drawsEst z instancjami 500→486, lecz najgorszy wzrost dla wspólnej kamery +6; High max suma trójkątów 1 258 099→1 256 983. Po scaleniu origin/main b5dca11f wymagana przebudowa.

## Iteracja r3 — ocena 15.11, editor

Cztery warianty zbudowane i wyrenderowane; 62 kadry/wariant. Lokalne zestawienia 01–11: `compare/r3/High-clear/` i `Low-clear/`. Ocena FAIL: 07 nie jest już zasłonięta obeliskiem, ale kamera nie leży na osi alejki; 02 jest zbyt blisko portyku; plac pomnika znika częściowo pod trawnikiem, a czerwony pas wystaje. Wierzba nie została włączona, prototyp r4 oceniony FAIL. Low: maksimum sumy szacowanych draw calls 500→486, lecz maksimum wzrostu na wspólnych kamerach +6 i trójkątów z instancjami +1644; warunek bez pogorszenia FAIL. High: maksimum trójkątów z instancjami 1 258 099→1 229 621 (<2 mln), maksimum sumy draws 838→844. Statystyki po scaleniu b5dca11f, są szacunkami edytora, nie pomiarem telefonu.

## Iteracja r4 — ocena 15.11, editor

Cztery warianty ukończone, 62 kadry/wariant; lokalne pary 01–11 `compare/r4/High-clear/` i `Low-clear/`. FAIL: plac pomnika jest ciągły i kamera 07 na osi alejki, ale w 02 dach skrzydła portyku nie jest widoczny w High ani Low; figura, drzewa, fontanna i rozpoznawalność nadal wymagają pracy. Wariant dwóch koron częściowo wypełnia ujęcie 04, inne drzewa w 05 nadal przypominają sosny. Low: max suma szacowanych draw calls 500→485, na wspólnej kamerze max wzrost +6, trójkątów z instancjami +1704; FAIL. High: maksimum trójkątów z instancjami 1 258 099→1 229 693 (<2 mln), suma draw calls max 838→843. To szacunki edytora. GIS: 1410 passed, 43 skipped, 4 xfailed, 2 failed; test nazwy kamer poprawiony i kierunkowo przechodzi, raport fidelity regionu C przeliczany.

## Iteracja r5 — ocena 15.11, editor
Cztery warianty ukończone; pary 01–11 lokalnie `compare/r5/High-clear/` i `Low-clear/`. Dach portyku widoczny w obu profilach, wcześniej odrzucany przez culling; pozostaje pofalowana kalenica, pudełkowe lukarny i ciemna loggia. Całość FAIL. Low: max suma szacowanych draw calls 500→485, max wzrost wspólnej kamery +6 i trójkątów z instancjami +1825; High max trójkątów z instancjami 1 258 099→1 229 814 (<2 mln), max suma draw calls 838→843. EditMode 626 passed, 2 skipped. Pełny GIS przed poprawką kamery i przeliczeniem fidelity: 1410 passed, 2 failed; oba testy kierunkowe przechodzą, wymagane ponowienie pełnego zestawu. Historycznie przypisano targowicę do sąsiedniego `OSM way/704368699` i usunięto niepodłączony prototyp; przypisanie okazało się błędne po poszerzeniu wycinka ortofoto — zob. korektę R24.

## Iteracja r6 — ocena 15.11, editor
Cztery warianty ukończone; porównania 01–11 lokalnie w `compare/r6/High-clear/` i `Low-clear/`. Lukarny niższe niż r5, ale w obu profilach wciąż wyglądają jak białe pudełka, daszki mało czytelne, kalenica faluje; FAIL wizualny. Low max suma szacowanych draw calls 500→485, na wspólnej kamerze wzrost do +6 i trójkątów z instancjami +1825; High max tris z instancjami 1 258 099→1 229 814, suma draw calls max 838→843. Szacunki edytora.

## Iteracja r7 — ocena 15.11, editor
Po synchronizacji origin/main cztery warianty ukończone, porównania 01–11 lokalnie `compare/r7/High-clear/` i `Low-clear/`. W kadrze 02 czerwone daszki i podziały szyb są czytelniejsze w obu profilach (PASS wyłącznie dla tej poprawki), ale falująca kalenica i elewacja nadal odbiegają od zdjęcia; całość FAIL. Low max suma szacowanych draw calls 500→485, wzrost wspólnej kamery do +6 i trójkątów z instancjami +1832; High max 1 258 099→1 229 853 tris z instancjami, max suma draws 838→843. Szacunki edytora.

## Iteracja r8 — ocena 15.11, editor
Cztery warianty ukończone; pary lokalne 01–11 `compare/r8/High-clear/` i `Low-clear/`. Trzynaście próbnych koron daje wyraźnie bardziej liściasty park i widoczny kościół, lecz korony są niemal identyczne, mają ciemne pionowe szwy i częściowo zasłaniają urząd; naturalność High/Low FAIL, wariant roboczy. Low max suma szacowanych draw calls 500→487 (R7 485), wzrost na wspólnych kamerach max +5 (R7 +6) i +1832 tris z instancjami; High max 1 258 099→1 230 049 tris z instancjami, max suma draws 838→844. Warunek Low bez pogorszenia nadal FAIL.

## Iteracja r9 — ocena 16.11, editor
Cztery warianty ukończone, 64 kadry/wariant, zdjęcia 01–11 lokalnie `compare/r9/High-clear/` i `Low-clear/`; kamery `rynek-crown-side-90/270` badają karty pod innymi kątami. Równoległe karty usunęły część ciemnych szwów, ale korony w 04 i 07 zwęziły się niemal do pionowych linii: FAIL w Low i High. Wariant wycofano z kodu i danych, obrazy zachowano jako dowód. Low max suma draws 500→487, wzrost do +5 draws i +1832 tris na wspólnych kamerach; High max 1 229 989 tris z instancjami, draws max 838→844. Wymagana przebudowa po wycofaniu.

## Iteracja r10 — ocena 16.11, editor
Cztery warianty ukończone, 70 kadrów/wariant; pary 01–11 lokalnie `compare/r10/High-clear/` i `Low-clear/` oraz osiem azymutów `rynek-crown-side-*`. Próba mniejszych kart nie znika jak R9, ale w obu profilach tworzy pionowe pasy, ciemne kliny i sylwetki jak wierzby; wizualnie gorsza od R8, FAIL, kod i dane cofnięte. Low max suma draws 500→487, wzrost do +5 draws i +1832 tris na wspólnych kamerach; High max 1 230 169 tris z instancjami, max suma draws 838→844. Wymagana przebudowa po cofnięciu.

## Iteracja r11 — ocena 16.11, editor
Po scaleniu ADR 0219 generator dobiera powiaty 2008/2002 dla pierścienia Knyszyna: 0→769 budynków i 0→505 poligonów lasu w QA; cztery sektory far-field wypełnione. W kadrach Rynku 03/04/07/08 obraz identyczny pikselowo z r8, w 05/06 różni się mały fragment tła; nie ocenia to całego pierścienia. Cztery warianty r11 zakończone; pary 01–11 lokalnie. High max 1 250 405 tris z instancjami (<2 mln), max draws 838→848. Low max suma draws 500→489, lecz na wspólnym `dk65-inlet-south` wzrost +63; tris max wzrost +37788. Porównanie niejednorodne: ADR 0262 zmienił start Knyszyna 12→90 m, baseline pokazuje szarą atrapę, r11 pełną ciężarówkę w polu widzenia. Mesh renderery w tym kadrze 31→71, mesh draws 199→264, shadow draws 2→56; cztery sektory far-field mają maks. dwa submeshe każdy i nie tłumaczą same +65. Dokładny podział kosztu niezmierzony. Warunek Low bez pogorszenia wobec zadanego baseline niepotwierdzony; bieżący całkowity koszt rzeczywisty w edytorze, wymagane kontrolowane porównanie tego samego stanu pojazdu i decyzja integratora.

## Iteracja r12 — ocena 16.11, editor
Cztery warianty i lokalne pary 01–11 ukończone. Dwie lokalne lipy 3D mają bardziej nieregularną bryłę i brak pojedynczego wielkiego szwu, ale liście tworzą ciemne, grube plamy; wizualnie nadal FAIL, pozostałe korony bez zmiany. Przy tym samym stanie main/pojazdu co r11, wspólne kamery: draws z instancjami bez zmiany, max wzrost 2044 tris Low i High. Low nie spełnia wymagania braku pogorszenia; High max 1 252 449 tris z instancjami (<2 mln). W kolejnej próbie Low przywrócony do identycznej geometrii garden_trial, High pozostaje 3D; różnica LOD wymaga oceny.

## Iteracja r13 — ocena 16.11, editor
Cztery warianty i lokalne pary 01–11 ukończone. W kadrze 08 pojawiła się wskazówka zegara, lecz tarcza ginie w cieniu; figura króla nadal geometryczna i nierozpoznawalna, ptak na obelisku nieczytelny w 04/07. Ocena całości FAIL, proxy niezatwierdzone. W porównaniu z tym samym stanem sceny r11 draws bez zmian, max +14 tris Low/High w nowym kadrze `rynek-owner-08`; proponowana optymalizacja masztu Low wymaga weryfikacji. Wobec pierwotnego baseline Low max +63 draws i +37788 tris na wspólnych kamerach przy zmienionej pozycji pojazdu (nieporównywalność patrz r11); High max 1 250 419 tris z instancjami. Pełny GIS trwa, lokalny snapshot C wymaga uzupełnienia brakujących instancji oraz ponownej ekstrakcji cache schema 12.
## Iteracja r14 — budżet, editor

Źródło: `before/{Low,High}-{clear,dusk}/stats.txt`, `r11/{Low,High}-{clear,dusk}/stats.txt` i `r14/{Low,High}-{clear,dusk}/stats.txt`. Poniżej suma szacunków siatek i instancji (`drawsEst` + draws instancji, `trisExact` + trianglesExact instancji); cienie raportowane są osobno i nie są dodawane do draw calls. To szacunki CPU edytora przed SRP batchingiem, nie liczniki GPU ani pomiar telefonu. Wyniki geometryczne clear i dusk są takie same.

| Porównanie | Wynik |
|---|---|
| Low, r11 → r14 | Wszystkie 70 kamer o tych samych nazwach: brak wzrostu sumy draws i tris. `rynek-owner-08`: 351 → 351 draws, 295 908 → 295 902 tris. `dk65-inlet-south`: 303 → 303 draws, 162 224 → 162 004 tris. |
| Low, before → r14 | **FAIL** wymagania bez pogorszenia: 34 z 50 kamer o tych samych nazwach ma większą sumę draws; maksimum wzrostu `dk65-inlet-south` 240 → 303 (+63). Największy wzrost tris: `truck-side` 272 290 → 310 078 (+37 788); 42 z 50 kamer ma więcej tris. |
| High, r14 | **PASS** limitu 2 mln tris na kamerę: maksimum 1 250 399 z instancjami (`cab-mirror-front`). Maksimum sumy szacowanych draws: 848 (`tykocka-into-town`). |
| High, r11 → r14 | Wszystkie 70 kamer o tych samych nazwach: brak wzrostu sumy draws i tris. |
| Low, maksimum r14 | 369 573 tris (`grodzienska-podlaska`) i 489 draws (`goniadzka-jagiellonska`). |

Porównanie before ma 51 kamer, r14 ma 70; literalnie wspólnych jest 50. Dawna `rynek-fountain` nie występuje już pod tą nazwą: była błędnie nazwana i wskazywała plac wschodni. Kamera `plac-wschodni-from-east` została dodana, lecz zgodność pozycji z baseline nie została tu zweryfikowana, więc nie jest uwzględniona jako para. Pozostałe nowe kamery również nie mają baseline; r11 i r14 mają komplet 70 wspólnych nazw.

Stan sceny przed i po nie jest w pełni porównywalny: po scaleniu main ADR 0219 uzupełniono dane far-field właściwych powiatów, a ADR 0262 zmienił start ciężarówki Knyszyna z 12 na 90 m. Na `dk65-inlet-south` r14 widać naczepę, której nie widać tak samo na baseline. Nie zmierzono wkładu poszczególnych przyczyn i nie należy przypisywać im całego wzrostu ani traktować ograniczenia porównania jako spełnienia wymogu Low. High również zmienia się w niektórych kadrach względem r11, choć optymalizacja masztu dotyczy Low; sam wynik statystyk nie dowodzi przyczyny tej różnicy.

## Iteracja r15 — próba wizualna i budżet

Próbę rozjaśnienia koron wycofano po nieudanym przeglądzie: nie usunęła wad wizualnych. Rendery tej próby pozostają lokalnie w `r15/` i `compare/r15/`; nie potwierdzają wyglądu po wycofaniu, który wymaga ponownej przebudowy i oceny. Pary ze zdjęciami właściciela pozostają poza Git.

Szacunki CPU edytora przed SRP batchingiem, suma siatek i instancji; clear i dusk dają te same wartości geometryczne. **High PASS** limitu 2 mln tris na kamerę: maksimum 1 250 401 (`cab-mirror-front`), maksimum 848 draws (`tykocka-into-town`). **Low FAIL** względem pierwotnego before: największy wzrost sumy draws 240 → 303 (+63, `dk65-inlet-south`); 34 z 50 kamer o tej samej nazwie wzrosło. Największy wzrost tris 272 290 → 310 078 (+37 788, `truck-side`); 42 z 50 kamer wzrosło. Maksima Low r15: 369 575 tris (`grodzienska-podlaska`), 489 draws (`goniadzka-jagiellonska`).

R14 → r15: na 70 wspólnych kamerach draws i szacowane shadow draws bez zmian; liczba tris wzrosła na 37 kamerach, maksymalnie o 22 w Low i High (`cab-dash`: Low 245 380 → 245 402, High 542 027 → 542 049). `rynek-owner-08` Low 295 902 → 295 904 (+2), draws 351 → 351. Przyczyny zmian tris nie rozdzielono pomiarem. Ograniczenia porównania z before, nazwa dawnej kamery i zmiany main pozostają takie jak opisano dla r14; nie przypisujemy im całego wzrostu. Dane nie są pomiarem GPU ani telefonu.

## Tykocka — sprawdzenie ortofoto GUGiK

Skorowidz GUGiK wskazuje w punkcie (760671, 612032) arkusz `N-34-106-B-b-1-4` z 27.05.2025, piksel 0,1 m: [źródłowy arkusz](https://opendata.geoportal.gov.pl/ortofotomapa/83186/83186_1484208_N-34-106-B-b-1-4.tif). Sprawdzono lokalnie fragment EPSG:2180 bbox `[760645, 612005, 760705, 612065]`; szare pasy utwardzenia przy Tykockiej są widoczne, ale granice chodnika zlewają się miejscami ze zjazdami i posesjami. Ciągły obrys chodnika i stan po przebudowie ronda pozostają **OPEN**, bez zgadywania geometrii. Arkusz i wycinek są lokalnie w `artifacts/knyszyn-rynek-0227/ortho-tykocka/`, poza Git.

## Iteracja r16 — ocena i budżet

Eksperyment obwodowych koron nie przeszedł oceny i został wycofany. Rendery `r16/` oraz lokalne pary `compare/r16/` pokazują próbę przed wycofaniem, a nie obecny stan; konieczna jest nowa przebudowa i ocena. Poprawiono styk korony pomnika króla, lecz figura pozostaje PROXY_NOT_APPROVED, a łańcuch jest OPEN.

Szacunki CPU edytora przed SRP batchingiem obejmują siatki i instancje; clear i dusk mają identyczne wyniki geometryczne. High **PASS** limitu 2 mln tris na kamerę: maksimum 1 250 401 (`cab-mirror-front`), maksimum 848 draws (`tykocka-into-town`). Low **FAIL** względem pierwotnego before: na 34 z 50 kamer o tych samych nazwach wzrosła suma draws, maksymalnie 240 → 303 (+63, `dk65-inlet-south`); największy wzrost tris 272 290 → 310 078 (+37 788, `truck-side`).

R15 → r16: wszystkie 70 wspólnych kamer mają draws i shadow draws bez zmian; Low ma na jednej kamerze wzrost o 1 tris (`route-s0726`), High na dziewięciu kamerach o maksymalnie 1 tris. `rynek-owner-08` Low pozostaje na 351 draws i 295 904 tris. Przyczyna zmian ±1 tris nie została zmierzona. Warunki porównania z before opisane dla r14 pozostają aktualne; dane nie są pomiarem GPU ani telefonu.

## Iteracja r17 — budżet po wycofaniu próby koron

Rendery i szacunki r17 obejmują 70 kamer na wariant; dane `r17/{Low,High}-{clear,dusk}/stats.txt`. High **PASS** limitu 2 mln tris na kamerę: maksimum 1 250 401 z instancjami (`cab-mirror-front`), maksymalna suma szacowanych draws 848 (`tykocka-into-town`). Low **FAIL** względem pierwotnego before: w 34 z 50 kamer o tej samej nazwie wzrosła suma draws; największy wzrost 240 → 303 (+63, `dk65-inlet-south`). Największy wzrost tris 272 290 → 310 078 (+37 788, `truck-side`), wzrost na 42 z 50 kamer. Maksima Low r17: 369 575 tris (`grodzienska-podlaska`) i 489 draws (`goniadzka-jagiellonska`).

R16 → r17: 70 wspólnych kamer, draws i shadow draws bez zmian; Low na ośmiu kamerach wzrost o 1 tris, High na siedmiu o 1 tris, przyczyna niezmierzona. R14 → r17: 70 wspólnych kamer, draws i shadow draws bez zmian, maksymalny wzrost tris o 22 w Low i High. `rynek-owner-08` Low względem r16 bez zmian: 351 draws i 295 904 tris. Clear i dusk dają identyczne wartości geometryczne.

Before zawiera 51 nazw kamer, r17 70, literalnie wspólnych jest 50; dawna `rynek-fountain` nie ma potwierdzonego odpowiednika do porównania. Dwie dodatkowe kamery diagnostyczne planowane do r18 nie mają baseline before ani r17 i należy je raportować oddzielnie, nie włączać do porównań par. Zastrzeżenia dotyczące zmian main i interpretacji pierwotnego baseline opisane dla r14 pozostają aktualne. Wszystkie liczby to szacunki CPU edytora z instancjami przed SRP batchingiem, nie pomiary GPU ani telefonu.

## R18 — diagnostyka wkładu pojazdu i dalekiego planu

Dodatkowy pomiar jednej kamery `dk65-inlet-south`, Low-clear, w tej samej scenie i pozycji pojazdu; `diag-r18/dk65-inlet-south_diagnostic.txt`. To szacunek CPU edytora przed SRP batchingiem, nie pomiar GPU ani wynik telefonu. Każda wartość draws poniżej zawiera siatki i 39 draws instancji; shadow draws podano osobno.

| Wariant diagnostyczny | Draws | Tris z instancjami | Shadow draws |
|---|---:|---:|---:|
| Pełna scena | 303 | 162 026 | 56 |
| Bez ciągnika i naczepy | 240 | 135 693 | 2 |
| Bez sektorów far-field | 299 | 156 852 | 56 |
| Bez pojazdu i far-field | 236 | 130 519 | 2 |

W tej scenie i tym kadrze pojazd odpowiada za 63 szacowane draws i 26 333 tris, far-field za 4 draws i 5 174 tris. Ukrycie rendererów służyło wyłącznie diagnozie; formalnym wynikiem pozostaje pełna scena: Low względem before **FAIL**. Zbieżność 240 draws bez pojazdu z 240 w historycznym before nie dowodzi przyczyny całej różnicy: brakuje analogicznego rozbicia i jednakowego stanu dawnej sceny. Runner QA przywrócono bajtowo po pomiarze; diagnostyki nie włączono do produktu ani do testu akceptacyjnego.

## Iteracja r18 — pełny budżet

Dane `r18/{Low,High}-{clear,dusk}/stats.txt` obejmują po 72 kamery we wszystkich czterech wariantach; clear i dusk mają identyczne wyniki geometryczne. Dla 70 wspólnych kamer r17 → r18 nie zmieniły się draws, tris, shadow draws ani liczba rendererów. High **PASS**: maksimum 1 250 401 tris z instancjami (`cab-mirror-front`), maksimum 848 draws (`tykocka-into-town`). Maksima Low: 369 575 tris (`grodzienska-podlaska`) i 489 draws (`goniadzka-jagiellonska`).

Dwie nowe kamery bez baseline before ani r17: `rynek-king-back-0227` Low 364 draws / 340 477 tris, High 594 / 847 374; `rynek-king-profile-0227` Low 273 / 270 450, High 372 / 473 360. Suma obejmuje siatki i instancje.

Low względem before nadal **FAIL**: na 34 z 50 kamer o tych samych nazwach wzrosły draws, maksymalnie 240 → 303 (+63, `dk65-inlet-south`); tris wzrosły na 42, maksymalnie 272 290 → 310 078 (+37 788, `truck-side`). Before zawiera 51 nazw, r18 72; dawna `rynek-fountain` nie ma potwierdzonego odpowiednika do porównania. Szacunki CPU edytora przed SRP batchingiem nie są pomiarem GPU ani telefonu; ograniczenia porównania i diagnostykę jednej kamery opisano powyżej.

## Iteracja r19 — budżet i przestawione kamery

R19 obejmuje 72 kamery w każdym z czterech wariantów; clear i dusk mają identyczne wyniki geometryczne. High **PASS**: maksimum 1 250 401 tris z instancjami (`cab-mirror-front`), maksymalnie 848 szacowanych draws (`tykocka-into-town`). Low względem before nadal **FAIL**: 34 z 50 kamer o tych samych nazwach ma wzrost draws, maksymalnie 240 → 303 (+63, `dk65-inlet-south`); tris wzrosły na 42, maksymalnie 272 290 → 310 078 (+37 788, `truck-side`). Maksima Low to 369 575 tris (`grodzienska-podlaska`) i 489 draws (`goniadzka-jagiellonska`).

R18 → r19: 70 z 72 kamer ma identyczną liczbę rendererów, draws, shadow draws i tris. Dwa przestawione kadry pomnika, bez baseline before, mają następujące wyniki (draws / tris z instancjami):

| Kamera | Low r18 → r19 | High r18 → r19 |
|---|---:|---:|
| `rynek-king-back-0227` | 364 / 340 477 → 359 / 292 593 | 594 / 847 374 → 620 / 832 620 |
| `rynek-king-profile-0227` | 273 / 270 450 → 450 / 338 213 | 372 / 473 360 → 641 / 796 017 |

Shadow draws nie zmieniły się na żadnej z 72 kamer. Różnice w przestawionych kadrach nie dowodzą zmiany kosztu geometrii przy niezmiennym widoku. Dane są szacunkami CPU edytora przed SRP batchingiem, nie pomiarami GPU ani telefonu; ograniczenia porównania z before pozostają aktualne.

## R19 — próba georeferencji targowicy

Historyczna próba rejestracji zdjęcia względem błędnego północnego wycinka zakończyła się **FAIL** (nie dotyczy późniejszego poprawnego wycinka): mediana błędu sześciu odłożonych kandydatów wyniosła 79,92 m. Pary są automatyczne i niezweryfikowane terenowo; wartość nie jest metrologiczną dokładnością ani podstawą wyznaczenia położenia wiat. Lokalny raport `artifacts/knyszyn-rynek-0227/market-georef-attempt.md` opisuje metodę i ograniczenia. Zdjęć właściciela nie publikować ani nie dodawać do Git.

## R23 — kontrola szpalerów względem parku

Po ukończonym build_world odczytano wszystkie wygenerowane `instances_*.json`: 10 instancji `src=treerow:*`, zero wewnątrz lub na granicy poligonu BDOT parku `20029180-A4BE-5C99-E053-CC2BA8C01CFC` (Shapely `covers`, po przeliczeniu lokalnego E/N na EPSG:2180). Najbliższy pień szpaleru leży 582,20 m od obrysu parku i 618,03 m od najbliższej z 15 lip kit (13+2 pozycji w overrides). Doliczenie trzech punktów lip wcześniej odrzuconych przez maskę nie zmienia minimum. To odległości pozycji pni, nie koron; w R23 szpalery nie dublują tych lip.

## R23 — budżet i rondo po integracji

R23 obejmuje po 74 kamery w czterech wariantach; clear i dusk mają identyczne wartości geometryczne. High **PASS** limitu 2 mln tris na kamerę: maksimum 1 248 992 z instancjami (`cab-mirror-front`), maksimum 848 szacowanych draws (`tykocka-into-town`). Low względem before **FAIL**: spośród 50 kamer o tych samych nazwach na 36 wzrosły draws, najwięcej 240 → 304 (+64, `dk65-inlet-south`); na 41 wzrosły tris, najwięcej 272 290 → 309 017 (+36 727, `truck-side`). Maksima Low to 369 557 tris (`grodzienska-podlaska`) i 485 draws (`goniadzka-jagiellonska`).

R23 względem r22: 73 wspólne kamery; Low draws wzrosły na 40, spadły na 19, bez zmian na 14; maksimum wzrostu 162 → 168 (+6, `route-s0145`), maksimum wzrostu tris 111 934 → 116 968 (+5 034, ta sama kamera). High: największy wzrost draws 261 → 272 (+11, `plate-trailer`), tris 777 679 → 788 843 (+11 164, `cab-right`). Nowa względem r22 kamera `rondo-dk65-top`: Low 75 draws / 87 197 tris, High 85 / 87 429; bez baseline. Są to szacunki CPU edytora z instancjami przed SRP batchingiem, nie pomiary GPU ani telefonu. Po integracji zmieniły się dane main i scena; same statystyki nie wyjaśniają przyczyn różnic. Before zawiera 51 nazw, z czego 50 jest wspólnych; `rynek-fountain` nie ma potwierdzonego odpowiednika.

Porównania zdjęć właściciela 09–11 z `compare/r23/Low-clear/` pokazują czytelne czterowlotowe rondo z jasną opaską i wysepkami dzielącymi. Podobieństwo nadal **FAIL**: środek wyspy jest pusty, podczas gdy na zdjęciach widoczne są piasek i rośliny; wysepki na renderze wyglądają ostro i trójkątnie, a na zdjęciach są dłuższe i zaokrąglone, zwłaszcza na długim wlocie. Otoczeniu brakuje części zieleni i detali. Orientacja lub perspektywa kamer 09–11 różni się od zdjęć, więc utrudnia porównanie; geometrii i wymiarów z tych kadrów nie uznano za pomierzone.

## Testy końcowe po scaleniu main

Pełny GIS: **1769 passed, 22 skipped, 2 xfailed** po lokalnej regeneracji danych regionu C; zgodność 64/64 plików instancji potwierdzona SHA. EditMode: **955 passed, 2 skipped**. Regeneracja była lokalna dla worktree.


## R24 — korekta położenia targowicy

Wcześniej błędnie utożsamiono targowicę z sąsiednim placem `OSM way/704368699`; `market-ortho-crop.jpg` ucinał właściwy obszar przy północnej wiacie. Poszerzony lokalny wycinek `market-south-ortho-check.jpg` z arkusza GUGiK 2025 `83186_1484206_N-34-106-B-b-1-2.tif` (EPSG:2180, 0,1 m/piksel) ujawnia cztery dachy w układzie 3+1, pasy, pawilon i długi budynek, wizualnie zgodne ze zdjęciami właściciela. Arkusz i zdjęcia są referencjami, nie teksturami.

SOURCED: ortofoto 2025 i obrysy BDOT dwóch budynków. ESTIMATED: ręczny odczyt okapów (tolerancja odczytu około 0,5–1 m plus nieustalone przesunięcie rzutu dachu), obrysy nawierzchni, identyfikacja obiektów i kamera. WORKING_VALUE: szczegóły, wysokości wiat i pawilonu, słupy oraz elementy wyposażenia. Cztery obrysy i ID BDOT są zapisane w `TYPOLOGIA.md`. Historyczny stan R24 wymagał sprawdzenia obrazu, kolizji i budżetu; nowszą ocenę R26 podano poniżej.


## R26–R27 — porównanie targowicy i łata wlotu

Porównania R26 Low-clear zdjęć 12–14: `compare/r26/Low-clear/12-owner-render.jpg`, `13-owner-render.jpg`, `14-owner-render.jpg` (lokalnie; zdjęcia nie są teksturami ani zawartością Git). Targowica jest już we właściwym miejscu, z wiatami 3+1, długim budynkiem i pawilonem. Względem R25 wyspa jest ziemista, a baza placu czystsza. Nadal widoczne są różnice jasności względem zdjęć oraz czarna łata wlotu między wiatami. Dopasowanie, w tym kadr 14 z poziomu oczu i ocena właściciela, pozostaje **OPEN**.

R26 High: maksimum **1 250 321 tris** z instancjami, poniżej limitu 2 mln na kamerę. Low vs before: **FAIL**, `dk65-inlet-south` 240 → 304 draw calls. R25 → R26: na 9 kamerach liczba draw calls spadła maksymalnie o 1, żadna z 75 kamer nie pogorszyła się. Wartości są szacunkami edytora, nie pomiarem GPU/telefonu.

R27: wykonano opt-in wizualny podział łaty wlotu bez zmiany kolizji; cztery warianty renderów zakończone. Lokalne porównania 12 i 14 pokazują zbyt jasny, sztucznie odcięty pasek nawierzchni, odbiegający od zdjęć; **rekomendacja: odrzucić próbę**. High maksimum **1 250 121 tris** z instancjami, poniżej limitu 2 mln; Low względem before nadal **FAIL**, `dk65-inlet-south` 240 → 304 draw calls. To szacunki edytora, nie GPU. Szerszy wielokąt wyznaczony z ortofoto pozostaje wyłącznie propozycją bez renderu i nie potwierdza poprawy; testy po ewentualnej zmianie i akceptacja wizualna **OPEN**.


## R28 — wycofanie próby R27

Wizualna łata wlotu z R27 została wycofana w commicie `96df3b6cf` po ocenie zbyt jasnego, sztucznego pasa; nie oznacza to usunięcia przyczyny ciemnego wlotu. Po tej decyzji uruchomiono R28; wynik renderów i budżetu podano w kolejnej sekcji, a końcowy GIS pozostaje **OPEN**. Pełny GIS R27 zakończył się wynikiem **1801 passed, 22 skipped, 2 xfailed, 1 failed**: `test_road_fidelity.py::test_report_not_stale` wskazał nieaktualny raport fidelity względem `meshing.py`, `pipeline.py` i `standards.py`. Po wycofaniu R27 test kierunkowy nadal zgłaszał niezgodność dla `pipeline.py` i `standards.py`; wymagane przeliczenie raportu na ostatecznym stanie oraz ponowienie testów. Wynik GIS R28 pozostaje **OPEN**. Szerszy wielokąt z ortofoto nadal pozostaje wyłącznie propozycją bez renderu.


## R28 — obraz i budżet po wycofaniu próby

R28: build_world, import i cztery warianty Low/High × clear/dusk zakończone OK. W katalogach `compare/r28/Low-clear/` oraz `compare/r28/High-clear/` znajduje się po 14 lokalnych par zdjęcie–render; fotografie pozostają poza Git. Na porównaniu zdjęcia 12 znikł sztuczny jasny pas wprowadzony w R27, jednak ciemny wjazd i plamy nawierzchni nadal są widoczne. Ocena wyglądu przez właściciela **OPEN**.

Szacunek CPU edytora z instancjami: High maksimum **1 250 321 tris** oraz **848 draw calls**; Low maksimum **485 draw calls** oraz **372 304 tris**. Na `dk65-inlet-south` Low wzrasta z 240 do 304 draw calls względem before — formalny **FAIL** braku pogorszenia. Wspólnych jest 50 nazw kamer; stan sceny po scaleniu main różni się od before. Dane nie stanowią pomiaru GPU ani telefonu.

Fidelity regionu C przeliczono po wycofaniu R27; wyniki lokalne `artifacts/knyszyn-rynek-0227/fidelity-after-r27-revert/`, testy kierunkowe **9 passed, 1 xfailed**. Pełny GIS R28 uruchomiony, a jego końcowy wynik pozostaje **OPEN**.


## R28 — rozbicie kosztu `dk65-inlet-south` Low

Dla wspólnej kamery `dk65-inlet-south` porównanie before → R28 daje **199 → 266** szacowanych draw calls MeshRenderer (+67) oraz **41 → 38** dla instancji (−3), razem **240 → 304** (+64). Są to estymaty CPU edytora przed SRP batchingiem, nie pomiary GPU. Skok obserwowany między R10 a R11 zbiega się w czasie z integracją dalekiego planu i zmianą położenia ciężarówki, lecz brakuje porównywalnego rozbicia według rendererów dla historycznego baseline; nie można przypisać przyczyny wzrostu wyłącznie jednej zmianie. Wymóg Low bez pogorszenia względem before pozostaje formalnie **FAIL**.

Pełny GIS R28 trwa; końcowy wynik pozostaje **OPEN**.


## R28 — przegląd targowicy z wysokości oczu

Lokalne zestawienie `compare/r28/High-clear/14-owner-render.jpg` pokazuje czytelny rząd wiat; w modelu odtworzono cztery wiaty w układzie 3+1. Dach najbliższej wiaty sprawia wrażenie bardziej płaskiego niż na zdjęciu, a wyspa przy pierwszym planie jest zbyt zielona względem widocznej na fotografii ziemi. To ocena przy szacunkowej pozycji kamery i innym oświetleniu, nie pomiar nachylenia ani potwierdzenie akceptacji właściciela.

Pełny GIS R28 trwa; wynik końcowy pozostaje **OPEN**.


## R28 — przegląd Rynku z wysokości oczu, kadry 03 i 08

Lokalne porównania `compare/r28/High-clear/03-owner-render.jpg` i `08-owner-render.jpg` zestawiono ze zdjęciami właściciela. Pozycje kamer i oświetlenie są szacunkowe; obserwacje nie stanowią pomiaru ani akceptacji właściciela.

**Kadr 03:** zdjęcie pokazuje aleję na pierwszym planie i czytelny portyk urzędu między drzewami. Na renderze wejście oraz znaczna część budynku są zasłonięte bryłą i koronami, a położenie ścieżki oraz perspektywa nie odpowiadają zdjęciu: ścieżka jest widoczna głównie po prawej i dalej od kamery. Korony drzew wyglądają zbyt regularnie i sztucznie, z ciemnymi pionowymi powierzchniami; wymagają dalszej pracy i porównania przy lepiej dopasowanej kamerze.

**Kadr 08:** mimo podobnego ustawienia postumentu i bloku przed nim figura jest ciemnym, gładkim i uproszczonym proxy, które nie odwzorowuje sylwetki ani detali rzeczywistej rzeźby. Korony w tle są powtarzalne i sztuczne, a układ widocznych alejek i pierzei różni się od fotografii. Pozycja kamery, widoczność masztu i warunki oświetlenia nie są dokładnie dopasowane. Rozpoznawalność pomnika i odbiór całego miejsca pozostają **OPEN**; model zachowuje status `PROXY_NOT_APPROVED`.

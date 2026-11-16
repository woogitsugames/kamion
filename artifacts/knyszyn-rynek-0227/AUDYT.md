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

Pary są przygotowywane wyłącznie lokalnie przez `compare.py`; nie zamieszczać zdjęć ani wyników par w Git. Zdjęcia targowicy z drona pozostają opisem, bez lokalnego pliku do bezpośredniego SBS.

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
Cztery warianty ukończone; pary 01–11 lokalnie `compare/r5/High-clear/` i `Low-clear/`. Dach portyku widoczny w obu profilach, wcześniej odrzucany przez culling; pozostaje pofalowana kalenica, pudełkowe lukarny i ciemna loggia. Całość FAIL. Low: max suma szacowanych draw calls 500→485, max wzrost wspólnej kamery +6 i trójkątów z instancjami +1825; High max trójkątów z instancjami 1 258 099→1 229 814 (<2 mln), max suma draw calls 838→843. EditMode 626 passed, 2 skipped. Pełny GIS przed poprawką kamery i przeliczeniem fidelity: 1410 passed, 2 failed; oba testy kierunkowe przechodzą, wymagane ponowienie pełnego zestawu. Właściciel potwierdził targowicę po drugiej stronie Jagiellońskiej od nr 50; poligon OSM way 704368699, GUGiK punkt adresowy poza nim. Brak lokalnych zdjęć dronowych oraz pomiarów nowych wiat: niezintegrowany prototyp ma wyłącznie WORKING_VALUE.

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

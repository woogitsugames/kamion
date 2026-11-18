# ADR 0227 — Knyszyn: rozpoznawalność Rynku z wysokości oczu

Status: WIP, 2026-11-15. Wymaga porównania kadrów, budżetu po zmianach i weryfikacji lidera.

## Kontekst
Właściciel nie rozpoznaje Knyszyna z poziomu ulicy. Zdjęcia 1–14 są lokalne, wyłącznie jako referencja (`Data/raw/refs/owner-knyszyn-2026-11-15/`); nie są teksturami. D65: latem, białe LED. Decyzje właściciela i kolejność w `docs/owner/KNYSZYN-OWNER-FEEDBACK-S21.md`.

Orto GUGiK 2025 i fotografie właściciela pokazują skwer z trawnikami i pojedynczymi drzewami liściastymi. Płyta fontanny leży w zachodnim parku, około 93 m od dotychczasowej kamery na wschodnim placu (ESTIMATED przez dopasowanie dwóch wycinków ortofoto; dokładna pozycja i kadry wymagają kontroli). Mechanizm lasu dla BDOT `20029180-A4BE-5C99-E053-CC2BA8C01CFC` generuje również leśną osłonę HLOD, nieadekwatną do parku.

## Decyzja robocza
Lokalny `park_replacement` usuwa las, jego obrzeże i maskę podłoża leśnego wyłącznie dla wskazanego obrysu; osobne authored punkty drzew i `open_ground` zachowują trawnik. Położenia koron, szerokości alejek oraz proporcje fontanny są ESTIMATED/WORKING_VALUE. Płyta jest płaska, bez niecki; nawierzchnia tymczasowo wykorzystuje istniejący materiał. Kamera wschodniego placu została przemianowana, a kamery 03–08 mają wstępne szacowane pozy na wysokości 1,7 m. Widok i umiejscowienie wymagają porównania z referencjami.

Kościół i urząd: osobne generatory wpięte w stage, obrysy BDOT i wysokości GUGiK; dachy i okna dopasowane do obrysów, detale WORKING_VALUE. Mała architektura i sucha fontanna z obwódką/dyszami wpięte; strumienie OPEN, sylwetka króla PROXY_NOT_APPROVED. Rendery r1 i r2 obejrzano: wynik nadal FAIL; r2 usunęła widoczny uskok nawierzchni w porównanych kadrach, ale drzewa, figura, suche dysze oraz pozycje kamer wymagają poprawek.

## Budżet i walidacja
Baseline i r2: `artifacts/knyszyn-rynek-0227/before/` i `r2/`; zestawienia 01–11 pozostają lokalne w `compare/r2/High-clear/`. Low: maksimum sumy szacowanych draw calls siatek i instancji 500 → 486, lecz na wspólnych kamerach wzrost do +6; warunek bez pogorszenia FAIL. High: maksimum trójkątów z instancjami 1 258 099 → 1 256 983, poniżej 2 mln. To szacunek edytora, nie pomiar telefonu. Po scaleniu main potrzebna kolejna przebudowa i powtórne pomiary. Pełne pytest GIS i EditMode OTWARTE.

## Otwarte
- Rozpoznawalność z oczu, pary zdjęcie–render i weryfikacja lidera/właściciela; minimum trzy iteracje.
- Targowica: korekta po ponownej analizie — wcześniejsze przypisanie do `OSM way/704368699` było błędne. Arkusz GUGiK 2025 `83186_1484206_N-34-106-B-b-1-2.tif` pokazuje rzeczywiste cztery wiaty dalej na południe; ich obrysy dachów są ręcznie oszacowane z ortofoto (szczegóły i tolerancje w `artifacts/knyszyn-rynek-0227/TYPOLOGIA.md`).
- Rondo: PR #97 nie w main; ortofoto 2025 sprzed przebudowy, wymiary aktualnej wyspy/opaski niezmierzone. Nie przedstawiać wartości roboczych jako pomiarów.
- Pomnik króla i obelisk to prawdopodobnie osobne obiekty; geolokalizacje ESTIMATED.
- Telefon i niezależny przegląd wizualny: do lidera, bez adb w tym zadaniu.

- Wierzba płacząca z opisu właściciela: brak potwierdzonego prototypu w istniejącej bibliotece drzew; nie jest jeszcze odwzorowana. Wymaga zasobu i oceny na renderze.

## Iteracja r3
Trzecia przebudowa i cztery warianty renderów zakończone; lokalne pary zdjęcie–render w `compare/r3/High-clear/` i `Low-clear/`. Wynik wizualny FAIL: pozycje kamer 02/07 i osadzenie placu pomnika wymagają korekt, drzewa są zbyt rzadkie, brak strumieni. Low bez pogorszenia FAIL (największy wzrost na wspólnej kamerze +6 szacowanych draw calls z instancjami, +1644 tris). High max 1 229 621 tris z instancjami, poniżej 2 mln; max suma draw calls 838→844. Szczegóły `AUDYT.md`. Kolejna iteracja obejmie przygotowane wejścia urzędu i próbę dwóch koron lip; efekty i budżet niezweryfikowane.

## Iteracja r4
R4 z lokalną próbą dwóch koron, wejściami urzędu i placykiem pomnika: cztery warianty ukończone, pary zdjęć lokalnie. Wizualnie FAIL: dach portyku niewidoczny w obu profilach; plac ciągły i kamera na osi, ale park nadal odbiega od zdjęć. Low na wspólnej kamerze +6 szacowanych draw calls i +1704 tris z instancjami; High max 1 229 693 tris. Pełny GIS 1410 passed, 2 failed: test nazwy poprawiony kierunkowo, raport fidelity po zmianach main przeliczany. EditMode otwarty.

## Iteracja r5 i walidacja
Dach skrzydła kultury jest widoczny po poprawce geometrii; jego kształt i lukarny nadal wymagają pracy. Ocena całości FAIL. Low bez pogorszenia FAIL: max wzrost na wspólnych kamerach +6 szacowanych draw calls z instancjami, +1825 tris; High max 1 229 814 tris. EditMode 626 passed, 2 skipped; pełny GIS wymaga ponowienia po usunięciu dwóch błędów wykrytych w poprzednim przebiegu. Targowica: historycznie błędnie przypisano obiekt do `OSM way/704368699`; niepodłączony prototyp usunięto jako niezgodny ze zdjęciami. Aktualna korekta z ortofoto 2025 i inwentarz znajdują się w części „Targowica — korekta R24” poniżej.

## Iteracja r6
R6: lukarny osadzone niżej; cztery warianty i lokalne porównania wykonane. Wizualnie FAIL: kalenica i lukarny nadal odbiegają od zdjęć. Low bez pogorszenia FAIL (max wzrost wspólnej kamery +6 draws z instancjami i +1825 tris), High max 1 229 814 tris.

## Iteracja r7
R7 po scaleniu main: cztery warianty i lokalne porównania wykonane; daszki i szprosy czytelne w kadrze 02, całość nadal FAIL wizualnie. Low bez pogorszenia FAIL (na wspólnych kamerach wzrost do +6 draws z instancjami i +1832 tris), High max 1 229 853 tris. GIS po poprawce far_field w toku.

## GIS po scaleniu main
Pełny `pytest tests/gis -q`: 1472 passed, 33 skipped, 3 xfailed; exit 0. Poprawiono błędny odczyt terenu far field dla niestandardowego out_root oraz fallback R16; testy syntetyczne 10 passed. EditMode: 626 passed, 2 skipped, wykonany przed ostatnim scaleniem main, więc powtórzyć na stanie końcowym.

## Iteracja r8
Trzynaście próbnych koron daje bardziej liściasty park, ale widoczne szwy, powtarzalność oraz częściowe zasłanianie urzędu oznaczają FAIL naturalności. Cztery warianty ukończone, pary zdjęć lokalnie. Low nadal FAIL: max +5 szacowanych draws i +1832 tris z instancjami na wspólnych kamerach; max sumy draws 500→487. High max 1 230 049 tris, max draws 838→844. Wariant pozostaje roboczy do poprawy i pomiaru.

## Iteracja r9 — wariant odrzucony
Równoległe karty koron wyeliminowały część szwów, ale z niektórych kierunków zanikają do wąskich pionowych pasów. FAIL w High i Low; zmiana kodu i danych wycofana, dowody lokalne `compare/r9/` i kamery boczne R9. Low w tej próbie nadal FAIL względem baseline (+5 draws i +1832 tris na wspólnych kamerach); High max 1 229 989 tris. Konieczna kolejna przebudowa po wycofaniu.

## Iteracja r10 — wariant odrzucony
Objętościowa próba małych kart nie zniknęła w badanych kierunkach, ale dawała pasy i ciemne kliny, przypominając bardziej wierzby niż lipy. FAIL w obu profilach, wycofana; dowody lokalne `compare/r10/` i osiem kierunków. Low nadal FAIL: +5 draws i +1832 tris na wspólnych kamerach; High max 1 230 169 tris. Wymagana przebudowa po cofnięciu.

## Iteracja r11 i porównywalność budżetu
Po scaleniu ADR 0219 poprawne dane far-field pokrywają Knyszyn; w kadrach Rynku 03–08 nie widać istotnej zmiany poza małym fragmentem tła. Cztery warianty i pary wykonane. High max 1 250 405 tris; Low max wzrost wspólnej kamery +63 draws i +37788 tris z instancjami względem pierwotnego baseline. Jednak ADR 0262 zmienił start ciężarówki 12→90 m: w problematycznym kadrze pojawiła się pełna naczepa zamiast szarej atrapy. Części kosztu nie rozdzielono pomiarem; nie przypisywać całej różnicy far-field ani uznać budżetu Low za spełniony.

## Iteracja r12
Dwie lokalne lipy 3D mają pełniejsze sylwetki bez centralnego szwu, lecz ciemne grube kępy pozostają FAIL. W porównaniu z tym samym stanem r11 draws bez zmian, ale na wspólnej kamerze +2044 tris Low i High; High max 1 252 449. R13 przywraca poprzednie Low, zachowuje trial High i dodaje przybliżenia pomników; przejście LOD wymaga oceny.

## Iteracja r13
Wskazówka zegara widoczna, ale rzeźba króla i ptak na obelisku nadal nieczytelne; FAIL wizualny, PROXY_NOT_APPROVED. R13 vs r11 przy tym samym stanie sceny: draws bez zmian, max +14 tris Low i High na nowym kadrze; High max 1 250 419 tris. Low względem pierwotnego baseline nie jest potwierdzony z powodu zmiany pozycji pojazdu. GIS trwa; wykryto brak lokalnych instancji regionu C i cache starej wersji, planowane odtworzenie danych.

## Iteracja r14 — budżet edytora

Low względem pierwotnego before: **FAIL** warunku bez pogorszenia. Dla 50 kamer o tych samych nazwach największy wzrost sumy szacowanych draw calls siatek i instancji to 240 → 303 (+63) na `dk65-inlet-south`; 34 kamery mają wzrost. Największy wzrost sumy tris to 272 290 → 310 078 (+37 788) na `truck-side`. Względem r11 wszystkie 70 wspólnych kamer Low ma draws i tris bez wzrostu; `rynek-owner-08`: 351 → 351 draws, 295 908 → 295 902 tris.

High: **PASS** limitu 2 mln tris na kamerę, maksimum 1 250 399 z instancjami na `cab-mirror-front`; maksymalna suma szacowanych draws to 848 na `tykocka-into-town`. Clear i dusk dają identyczne wartości geometryczne. Są to szacunki CPU edytora przed SRP batchingiem, nie pomiary GPU ani telefonu; shadow draws są osobnym wskaźnikiem.

Before zawiera 51 kamer, r14 70; 50 ma te same nazwy. Dawna błędnie nazwana `rynek-fountain` nie występuje już pod tą nazwą; zgodność pozycji `plac-wschodni-from-east` nie została tu zweryfikowana. Porównanie ograniczają także zmiany main: ADR 0219 uzupełnił właściwe dane far-field, a ADR 0262 zmienił pozycję startu ciężarówki. Nie zmierzono osobnego wkładu tych zmian, więc nie przypisujemy im całości wzrostu ani nie uznajemy Low za spełnione. Szczegóły i ścieżki statystyk są w `artifacts/knyszyn-rynek-0227/AUDYT.md`.

## Iteracja r15 — próba koron i budżet

Próba rozjaśnienia koron nie przeszła przeglądu i została wycofana. Rendery r15 dokumentują tę próbę, nie stan po jej wycofaniu; potrzebna kolejna przebudowa i ocena.

W r15 **High PASS** limitu 2 mln tris na kamerę: maksimum 1 250 401 z instancjami (`cab-mirror-front`). **Low FAIL** względem before: największy wzrost sumy szacowanych draws siatek i instancji 240 → 303 (+63, `dk65-inlet-south`), na 34 z 50 kamer o tych samych nazwach wystąpił wzrost. Największy wzrost sumy tris 272 290 → 310 078 (+37 788, `truck-side`).

R14 → r15: 70 wspólnych kamer, draws i szacowane shadow draws bez zmian; tris wzrosły na 37 kamerach, maksymalnie o 22 w Low i High. Przyczyna nie została osobno zmierzona. Clear i dusk mają te same wyniki geometryczne. Jak w r14 są to szacunki CPU edytora, nie pomiary GPU; ograniczenia porównania z before pozostają aktualne. Szczegóły w `artifacts/knyszyn-rynek-0227/AUDYT.md`.

## Iteracja r16 — wynik i ograniczenia

Eksperyment obwodowych koron wycofano po nieudanej ocenie; rendery r16 pokazują stan przed wycofaniem i nie potwierdzają obecnego stanu. Poprawiono styk korony pomnika, ale łańcuch pozostaje OPEN, a sylwetka króla PROXY_NOT_APPROVED. Potrzebna nowa przebudowa i ocena wizualna.

High **PASS** limitu 2 mln tris na kamerę: maksimum 1 250 401 z instancjami (`cab-mirror-front`). Low **FAIL** względem pierwotnego before: maksymalny wzrost sumy szacowanych draw calls 240 → 303 (+63, `dk65-inlet-south`); wzrost na 34 z 50 kamer o tych samych nazwach. Maksymalny wzrost tris 272 290 → 310 078 (+37 788, `truck-side`).

R15 → r16: dla 70 wspólnych kamer draws i szacowane shadow draws bez zmian, a największy wzrost to 1 tris w Low i High; przyczyny różnic nie zmierzono. Clear i dusk mają identyczne dane geometryczne. To szacunki CPU edytora, nie pomiary GPU; ograniczenia porównania z before opisane dla r14 nadal obowiązują.

## Iteracja r17 — budżet edytora

R17 obejmuje 70 kamer w każdym wariancie. High **PASS** limitu 2 mln tris na kamerę: maksimum 1 250 401 z instancjami (`cab-mirror-front`), maksimum 848 draws (`tykocka-into-town`). Low **FAIL** względem pierwotnego before: 34 z 50 kamer o tych samych nazwach ma wzrost sumy szacowanych draws, maksimum 240 → 303 (+63, `dk65-inlet-south`); największy wzrost tris 272 290 → 310 078 (+37 788, `truck-side`).

R16 → r17: na 70 wspólnych kamerach draws i shadow draws bez zmian, wzrost tris maksymalnie o 1; R14 → r17 również bez wzrostu draws, maksymalny wzrost tris +22. Przyczyn różnic tris nie zmierzono. Dwie dodatkowe kamery diagnostyczne planowane do r18 nie mają baseline before ani r17 i wymagają osobnego raportowania. Ograniczenia porównania z before i zmian main opisane dla r14 pozostają aktualne; są to szacunki CPU edytora, nie pomiary GPU.

## R18 — diagnostyka budżetu jednej kamery

Dla `dk65-inlet-south` Low-clear, w tej samej scenie, szacowana suma draws siatek i instancji wynosi 303 w pełnej scenie, 240 bez ciągnika i naczepy, 299 bez far-field oraz 236 bez obu. Odpowiada to 63 draws pojazdu i 4 drawom far-field w tym konkretnym ujęciu. To diagnostyczny szacunek CPU edytora przed SRP batchingiem, nie pomiar GPU; formalny wynik nadal obejmuje pełną scenę.

Zbieżność wyniku 240 bez pojazdu z pierwotnym before nie dowodzi przyczyny całej regresji: dawnej sceny nie rozbito w porównywalny sposób. Low względem before pozostaje **FAIL**. Szczegółowe liczby i ograniczenia w `artifacts/knyszyn-rynek-0227/AUDYT.md`; tymczasowy kod diagnostyki runnera przywrócono po pomiarze.

## Iteracja r18 — pełny budżet

Cztery warianty obejmują po 72 kamery; clear i dusk mają identyczne wartości geometryczne. Na 70 kamerach wspólnych z r17 draws, tris, shadow draws i liczba rendererów są identyczne. High **PASS**: maksimum 1 250 401 tris z instancjami (`cab-mirror-front`), maksymalnie 848 draws (`tykocka-into-town`). Low względem before nadal **FAIL**: 34 z 50 kamer o tych samych nazwach ma wzrost draws, maksymalnie 240 → 303 (+63, `dk65-inlet-south`); maksymalny wzrost tris 272 290 → 310 078 (+37 788, `truck-side`).

Nowe kamery bez baseline before i r17: `rynek-king-back-0227` Low 364 draws / 340 477 tris, High 594 / 847 374; `rynek-king-profile-0227` Low 273 / 270 450, High 372 / 473 360. To szacunki CPU edytora z instancjami przed SRP batchingiem, nie pomiary GPU ani telefonu. Ograniczenia porównania i diagnostyka `dk65-inlet-south` pozostają aktualne.

## Iteracja r19 — budżet edytora

R19 obejmuje 72 kamery w każdym wariancie; clear i dusk mają identyczne wyniki geometryczne. High **PASS**: maksimum 1 250 401 tris z instancjami (`cab-mirror-front`), maksimum 848 draws (`tykocka-into-town`). Low względem before nadal **FAIL**: wzrost draws na 34 z 50 kamer o tych samych nazwach, maksymalnie 240 → 303 (+63, `dk65-inlet-south`); maksymalny wzrost tris 272 290 → 310 078 (+37 788, `truck-side`).

R18 → r19: 70 z 72 kamer bez zmian liczby rendererów, draws, shadow draws i tris; dwa kadry pomnika przestawiono. `rynek-king-back-0227` Low 364 / 340 477 → 359 / 292 593, High 594 / 847 374 → 620 / 832 620; `rynek-king-profile-0227` Low 273 / 270 450 → 450 / 338 213, High 372 / 473 360 → 641 / 796 017 (draws / tris z instancjami). Nie mają baseline before, a zmiana kadru ogranicza porównanie. To szacunki CPU edytora przed SRP batchingiem, nie pomiary GPU ani telefonu. Szczegóły w `artifacts/knyszyn-rynek-0227/AUDYT.md`.

## R19 — próba georeferencji targowicy

Historyczna automatyczna próba rejestracji zdjęcia względem nieprawidłowego północnego wycinka ortofoto: **FAIL**, mediana błędu sześciu odłożonych kandydatów 79,92 m. Nie jest to ocena późniejszego poprawnego wycinka targowicy. Pary są automatyczne i niezweryfikowane; ta liczba nie jest metrologiczną dokładnością ani podstawą wyznaczenia położenia wiat. Metodę i ograniczenia opisuje lokalny `artifacts/knyszyn-rynek-0227/market-georef-attempt.md`. Zdjęć właściciela nie publikować ani nie dodawać do Git.

## R23 — kontrola szpalerów i parku

Wygenerowane `instances_*.json` zawierają 10 instancji `src=treerow:*`; zero jest wewnątrz lub na granicy poligonu BDOT parku. Najbliższy pień szpaleru jest 582,20 m od obrysu i 618,03 m od najbliższej z 15 lip kit w overrides (13+2). To odległości pozycji pni, nie koron; w R23 szpalery nie dublują tych lip. Metoda w `artifacts/knyszyn-rynek-0227/AUDYT.md`.

## R23 — budżet i rondo po integracji

R23 obejmuje 74 kamery w każdym z czterech wariantów; clear i dusk mają identyczne statystyki geometryczne. High **PASS** limitu 2 mln tris na kamerę: maksimum 1 248 992 z instancjami (`cab-mirror-front`), maksymalnie 848 draws (`tykocka-into-town`). Low względem before nadal **FAIL**: 36 z 50 kamer o wspólnych nazwach ma wzrost draws, maksymalnie 240 → 304 (+64, `dk65-inlet-south`); maksymalny wzrost tris 272 290 → 309 017 (+36 727, `truck-side`).

R23 względem r22: 73 wspólne kamery; Low maksymalnie +6 draws i +5 034 tris (`route-s0145`), High maksymalnie +11 draws (`plate-trailer`) i +11 164 tris (`cab-right`). Nowa kamera `rondo-dk65-top` bez baseline r22: Low 75 draws / 87 197 tris, High 85 / 87 429. To szacunki CPU edytora z instancjami przed SRP batchingiem, nie pomiary GPU; po integracji zmienione dane main i scena ograniczają przypisanie przyczyn różnic.

Lokalne porównania 09–11 pokazują czterowlotowe rondo z jasną opaską i wysepkami, ale nadal odbiegają od zdjęć: środek wyspy jest pusty, wysepki zbyt ostre wizualnie, a otoczenie uboższe w zieleń i detale. Perspektywa i orientacja kamer nie odpowiadają dokładnie fotografiom; wymiary pozostają niepotwierdzone. Szczegóły w `artifacts/knyszyn-rynek-0227/AUDYT.md`.

## Testy końcowe po scaleniu main

Pełny GIS: **1769 passed, 22 skipped, 2 xfailed** po lokalnej regeneracji danych regionu C i potwierdzeniu zgodności SHA 64/64 plików instancji. EditMode: **955 passed, 2 skipped**. Regeneracja była lokalna dla worktree.


## Targowica — korekta R24 i pochodzenie geometrii

SOURCED: ortofoto GUGiK 2025, arkusz `83186_1484206_N-34-106-B-b-1-2.tif`, EPSG:2180, piksel 0,1 m, oraz BDOT10k. Wcześniejszy wycinek `market-ortho-crop.jpg` kończył się w rejonie północnej wiaty i pokazywał głównie sąsiedni plac gruntowy; przypisanie go do całej targowicy przez `OSM way/704368699` było błędne. Rozszerzony lokalny wycinek `market-south-ortho-check.jpg` obejmuje całą targowicę i odpowiada zdjęciom 12–14: trzy bliskie dachy, czwarty z większym odstępem, pawilon, długi budynek i pasy nawierzchni.

ESTIMATED: ręcznie odczytane naroża czterech dachów i fragmenty nawierzchni z georeferencyjnego ortofoto; szczegółowe cztery obrysy EPSG:2180 i szacowana tolerancja w `TYPOLOGIA.md`. Identyfikacja długiego obiektu `bdot:2002917F-465A-5C99-E053-CC2BA8C01CFC` i pawilonu `bdot:de62e5a9-3c83-4023-9e77-03b8844df001` względem zdjęć jest ESTIMATED; obrysy BDOT są SOURCED. Środek korony świerka jest ESTIMATED, a pień zasłonięty.

WORKING_VALUE: wysokości i przekroje słupów wiat, sposób ich posadowienia, wysokość pawilonu, detale elewacji i stołów, proporcje modelu drzewa oraz pozycja kamery względem zdjęcia 14. Pomiar dachu nie jest geodezyjną pozycją słupów; należy uwzględnić nieznane przesunięcie rzutu. Historyczny stan R24 wymagał sprawdzenia obrazu, kolizji i budżetu; nowszą ocenę R26 podano poniżej. Zdjęcia wyłącznie lokalna referencja, bez tekstur i bez Git.


## R26–R27 — targowica po korekcie

R26: lokalne zestawienia `compare/r26/Low-clear/12-owner-render.jpg`, `13-owner-render.jpg` i `14-owner-render.jpg` pokazują targowicę we właściwym położeniu: cztery wiaty w układzie 3+1, długi budynek, pawilon i pasy. W porównaniu z R25 wyspa ma ziemistą powierzchnię, a baza placu jest czystsza. Dopasowanie zdjęć pozostaje **OPEN**: nawierzchnia nadal różni się jasnością, a czarna łata wlotu między wiatami jest widoczna. Ujęcia 12–13 z drona są pomocnicze; kryterium rozpoznawalności dotyczy poziomu oczu, zdjęcie 14.

W R26 High spełnia limit 2 mln tris: maksimum **1 250 321** na kamerę, z instancjami. Low względem pierwotnego before nadal **FAIL**: `dk65-inlet-south` 240 → 304 draw calls. W porównaniu R25 → R26 na 9 kamerach draw calls spadły maksymalnie o 1; żadna z 75 kamer nie pogorszyła się. To szacunki edytora, nie pomiary GPU.

R27: wykonano opt-in wizualny podział łaty wlotu bez zmiany kolizji i wyrenderowano cztery warianty. W porównaniu ze zdjęciami, szczególnie z poziomu oczu (14), powstał zbyt jasny, sztucznie odcinający się pasek nawierzchni; **rekomendacja: odrzucić tę próbę**, nie traktować jej jako poprawy ani akceptacji właściciela. High maksimum **1 250 121 tris** z instancjami — poniżej 2 mln; Low względem pierwotnego before nadal **FAIL**, `dk65-inlet-south` 240 → 304 draw calls. Szerszy wielokąt wyznaczony z ortofoto jest wyłącznie propozycją: bez renderu i oceny nie dowodzi poprawy. Wynik testów po ewentualnym wycofaniu lub zmianie pozostaje **OPEN**.


## R28 — wycofanie próby R27

Wizualna łata wlotu z R27 została wycofana w commicie `96df3b6cf` po ocenie zbyt jasnego, sztucznego pasa; nie oznacza to usunięcia przyczyny ciemnego wlotu. Po tej decyzji uruchomiono R28; wynik renderów, budżetu i testów podano w kolejnych sekcjach. Pełny GIS R27 zakończył się wynikiem **1801 passed, 22 skipped, 2 xfailed, 1 failed**: `test_road_fidelity.py::test_report_not_stale` wskazał nieaktualny raport fidelity względem `meshing.py`, `pipeline.py` i `standards.py`. Po wycofaniu R27 test kierunkowy nadal zgłaszał niezgodność dla `pipeline.py` i `standards.py`; następnie przeliczono raport, a GIS R28 zakończył się zielono, jak opisano poniżej. Szerszy wielokąt z ortofoto nadal pozostaje wyłącznie propozycją bez renderu.


## R28 — wynik po wycofaniu łaty

Build świata, import i rendery Low/High × clear/dusk zakończone OK. Lokalne `compare/r28/Low-clear/` i `compare/r28/High-clear/` zawierają po 14 par zdjęcie–render. W kadrze 12 sztuczny jasny pas z R27 znikł; ciemny wjazd i plamy nawierzchni pozostają. Wygląd targowicy oraz rozpoznawalność z wysokości oczu nadal wymagają oceny właściciela.

Szacunek CPU edytora z instancjami: High maksimum **1 250 321 tris** i **848 draw calls**, poniżej limitu 2 mln tris; Low maksimum **485 draw calls** i **372 304 tris**. Dla `dk65-inlet-south` Low 240 → 304 draw calls względem before, co oznacza formalny **FAIL** wymogu braku pogorszenia. Porównanie obejmuje 50 kamer o wspólnych nazwach; zmiany sceny po integracji main ograniczają przypisanie przyczyn. To nie jest pomiar GPU.

Fidelity regionu C rzeczywiście przeliczono po wycofaniu R27; wyniki lokalne w `artifacts/knyszyn-rynek-0227/fidelity-after-r27-revert/`, testy kierunkowe **9 passed, 1 xfailed**. Pełny GIS R28 zakończył się zielono, jak opisano poniżej.


## R28 — rozbicie kosztu `dk65-inlet-south` Low

Dla wspólnej kamery `dk65-inlet-south` porównanie before → R28 daje **199 → 266** szacowanych draw calls MeshRenderer (+67) oraz **41 → 38** dla instancji (−3), razem **240 → 304** (+64). Są to estymaty CPU edytora przed SRP batchingiem, nie pomiary GPU. Skok obserwowany między R10 a R11 zbiega się w czasie z integracją dalekiego planu i zmianą położenia ciężarówki, lecz brakuje porównywalnego rozbicia według rendererów dla historycznego baseline; nie można przypisać przyczyny wzrostu wyłącznie jednej zmianie. Wymóg Low bez pogorszenia względem before pozostaje formalnie **FAIL**.

Pełny GIS R28 zakończył się zielono, jak opisano poniżej.


## R28 — przegląd targowicy z wysokości oczu

Lokalne zestawienie `compare/r28/High-clear/14-owner-render.jpg` pokazuje czytelny rząd wiat; w modelu odtworzono cztery wiaty w układzie 3+1. Dach najbliższej wiaty sprawia wrażenie bardziej płaskiego niż na zdjęciu, a wyspa przy pierwszym planie jest zbyt zielona względem widocznej na fotografii ziemi. To ocena przy szacunkowej pozycji kamery i innym oświetleniu, nie pomiar nachylenia ani potwierdzenie akceptacji właściciela.

Pełny GIS R28 zakończył się zielono, jak opisano poniżej.


## R28 — wynik GIS

Pełny GIS R28 zakończył się wynikiem **1797 passed, 22 skipped, 2 xfailed** w **1098,52 s** (`artifacts/knyszyn-rynek-0227/gis-r28.log`, `.done`: OK). Własne zmiany wygenerowanych danych regionu C pozostawione przez testy zostały przywrócone. Ostatni wykonany EditMode R27, po zmianach targowicy, ale przed wycofaniem wyłącznie łaty Python R27, miał **955 passed, 2 skipped** (`editmode-r27.done`, `artifacts/tests/editmode-20261116-093254.xml`). Świeży EditMode R28 zakończył się wynikiem **955 passed, 0 failed, 2 skipped** (`artifacts/tests/editmode-20261116-102739.xml`; `artifacts/knyszyn-rynek-0227/editmode-r28.done`: OK). Własną zmianę materiału `M_Sky` po teście przywrócono.

Low względem before nadal formalnie **FAIL** (`dk65-inlet-south` 240 → 304 draw calls), a odbiór wizualny, poprawa ciemnego wlotu i weryfikacja właściciela pozostają **OPEN**. Gotowe do scalenia po weryfikacji lidera: **NIE**.


## R29 — plac targowy i diagnostyka Low

Build świata, import i rendery Low/High × clear/dusk zakończone OK. W lokalnych `compare/r29/Low-clear/` i `compare/r29/High-clear/` znajduje się po 14 par zdjęcie–render. W porównaniu kadru 14 korekta wyspy jest tylko kosmetyczna: nadal wygląda zielonkawo względem ziemi na fotografii. Nie zaobserwowano widocznego spływania, ale wygląd wyspy nie jest rozwiązany; ocena uwzględnia szacunkową kamerę i inne światło, bez potwierdzenia właściciela.

Szacunki CPU edytora z instancjami przed SRP: High maksimum **1 250 321 tris** i **848 draw calls**. Low `dk65-inlet-south` względem before **240 → 304 draw calls** przekracza pierwotny wymóg braku pogorszenia; właściciel zaakceptował ten wzrost w **D78**.

W diagnostycznym TSV dla bieżącej sceny `dk65-inlet-south` suma jest zgodna z `stats`: **266 draw calls / 158 591 tris** MeshRenderer oraz **38 draw calls / 6 418 tris** instancji. Rozbicie MeshRenderer: `Region` **203** draws, ciągnik **37**, naczepa **26**. W `Region` warstwy `buildings_lod1` i `buildings` mają odpowiednio **135** i **20** draws. To cel dalszej analizy optymalizacji, a nie gwarancja oszczędności lub pomiar GPU; wynik nie zastępuje oceny całej sceny względem before.

EditMode R29 zakończył się wynikiem **955 passed, 0 failed, 2 skipped** (`artifacts/tests/editmode-20261116-105141.xml`; `editmode-r29.done`: OK). Własną zmianę materiału `M_Sky` po teście przywrócono. Pełny GIS R29 zakończył się wynikiem **1797 passed, 22 skipped, 2 xfailed** (`gis-r29.done`: OK), przed późniejszym scaleniem main; nie jest to walidacja aktualnego stanu po merge.

Analiza materiałów wskazuje na potencjał zmniejszenia liczby szacowanych draw calls o **12**: pięć unikalnych par materiałów Unity `far_office` / `ribbon` ma identyczną zawartość poza nazwą. To hipoteza diagnostyczna, nie potwierdzona oszczędność; konieczny pomiar A/B bez pogorszenia obrazu i funkcji, a wynik nie jest gwarantowany.


## D78 — przekazanie liderowi po scaleniu main

Decyzją właściciela **D78** lider przejmuje lokalnie gałąź `knyszyn-rynek-0227` i PR #139 po zakończeniu pracy Codexa. Wzrost Low na `dk65-inlet-south` z **240 do 304 draw calls** został przyjęty; wartość nadal przekracza pierwotny warunek bez regresji, ale nie należy przedstawiać jej jako niezaakceptowanej przez właściciela. Pozostałe uwagi wizualne, poprawki z recenzji, sprawdzenie obrazu i budżetu nadal wymagają pracy lidera.

Po merge main `a2f62a442` pliki `generated/knyszyn*` pochodzą z main i czekają na przebudowę regionu przez lidera. Wcześniejsze rendery, GIS i EditMode R29 dotyczą stanu **sprzed** tego merge; brak świeżej walidacji scalonego stanu. W overrides starsze ID fontanny i drzew zastąpiono nowszą funkcjonalną reprezentacją, bez dokładania duplikatów. Gotowość do scalenia po weryfikacji lidera: **NIE**.

## rynek-s23 — przejęcie przez lidera (D78): wpływ na inne regiony

- **Ślad w QA innych regionów usunięty.** Sześć generatorów `knyszyn_{church,townhall,market_buildings,park_props,market,fountain}_0227` zapisuje wpis do `streetscape_qa.json` dopiero *po* bramce `region == "knyszyn"`; `vegetation.place` dodaje klucz `park_replacements` tylko wtedy, gdy region ma wpis `kind: park_replacement`. Dla pozostałych kafli raport QA jest bajtowo taki jak przed PR (test `tests/gis/test_knyszyn_qa_gate_0227.py`). Dług (recenzja P2-2): wywołania na sztywno w `stage.py` → docelowo rejestr generatorów sterowany z `overrides.yaml`.
- **`far_field.BorderElevation.from_region` — zmiana zostaje (poprawka błędu).** Ścieżka awaryjna (brak `terrain_conformed.npy`) czytała `heightmap_2049.r16` przez klucze `z_min_m`/`z_max_m`, których nie ma w żadnym z 21 `Data/Regions/*/terrain.json` (format `encoding.offset_m` + `scale_m_per_unit`) — każde jej użycie kończyło się `KeyError`. Teraz dekoduje przez wspólne `roads.profile.load_heightfield` (ten sam dekoder co droga i teren). Dodatkowo `build_far_field` przekazuje swój `out_root`, więc krawędź dalekiego planu czyta teren *bieżącego* buildu zamiast nieaktualnego pliku z domyślnego katalogu. Ścieżka normalna (npy w domyślnym katalogu) bez zmian. Testy: `tests/gis/test_far_field_terrain_source_0227.py`.
- **Kamery diagnostyczne koron** `rynek_crown_side_{0..315}` (8) usunięte z kamer kontrolnych — były tylko do badania lip r9/r10.

## Dopisek D41 (rynek-p1-s23) — poprawki P1 z recenzji wizualnej 2026-11-16

Recenzja: `docs/reports/REVIEW-2026-11-16-s23-visual-rynek.md`. Fakty właściciela: `KNYSZYN-OWNER-FEEDBACK-S21.md`. Google nieużyty. Dane: `docs/reports/rynek-p1/`.
Wszystkie nowe wpisy są na końcu `Data/Regions/knyszyn/overrides.yaml`. Wcześniejszych wpisów nie zmieniano.

- **(a) Wiaty targowicy (SOURCED, pomiar).** Narzędzie `tools/worldgen/qa/market_canopy_ortho.py` mierzy wiaty na GUGiK ORTO WMS 0,1 m:
  profil wzdłuż kalenicy i dwa profile w poprzek.
  - Okapy mają 27,10–27,15 × 7,20–7,28 m. Prześwity: **1,15 m** i **1,17 m** między trzema bliskimi wiatami, 14,2 m do wiaty północnej.
  - Dokładność ±0,2 m na prześwit. Linijkę sprawdza test na syntetycznym rastrze.
  - Przyczyna styku w grze: ręczne obrysy R24 nachodziły na siebie o ok. 1 m, a generator dawał wcięcie 0,25 m. Okapy stały więc 0,3 m od siebie.
  - Wpis `market_canopy_geometry_d41` podmienia obrysy po `id`, bez wcięcia. Generator raportuje `eave_gaps_m`.
- **(b) Pawilon (dane).** `kind: market_pavilion_d41` dla `bdot:de62e5a9` (narożnik płd.-wsch., zdjęcie 13).
  - Dach namiotowy (ortofoto: cztery połacie do jednego wierzchołka) i żółty tynk, bez szyldu i marki.
  - Okap 2,8 m i wierzchołek 4,2 m to WORKING_VALUE. Zły wpis jest stale i zostaje wtedy dotychczasowy dach kopertowy.
  - Mały kiosk z dachem namiotowym przy bramie płn.-zach. nie ma obrysu BDOT i nie jest modelowany.
- **(c) Korony lip (ESTIMATED).** `kind: tree_crown_shape`, `height_to_spread` 1,75.
  - Źródło: Niemiera, *Littleleaf Linden (Tilia cordata)*, VCE 2901-1055 (2018): wysokość 70 ft, rozpiętość 40 ft, „upright oval”.
  - Zastępuje średnice WORKING_VALUE (zakresy AABB z GLB) w obu grupach kit lip Rynku: korony 8,8–11,4 m zamiast 9,3–12,9 m.
  - Liczba kart i trójkątów bez zmian. Wygląd z poziomu oczu OPEN.
- **(d) Średnica ronda DK65 × Tykocka (WORKING_VALUE).** Nowy klucz `compact_roundabout.outer_diameter_m`.
  - Walidacja: zakres 14–40 m i najwyżej max(2 m, 40 %) od promienia osi dopasowanego do OSM. Inaczej wpis jest stale i promień z OSM zostaje.
  - Raport: `r_axis_fit_m`. Wpis `knyszyn-roundabout-outer-diameter-d41` ustawia 26,0 m. Opcje `compact_roundabout` kilku wpisów są scalane w kolejności pliku.
  - Pierścień rośnie, a węzły rozdziału DK65 stoją w miejscu, więc wysepki S i N są ok. 1,85 m krótsze od krawędzi pierścienia.
    Po decyzji OD-046 proponuję przeskalować długości z tego samego zdjęcia (× 26/22,6): `split-s` length_m 27 → ok. 33, `split-n` 32 → ok. 38 (ESTIMATED).
  - Do czasu przeskalowania `test_roundabout_0274` ma dolną granicę wysepki S 27 m.
- **(e) Uskok krawędzi jezdni od południa: przyczyna i poprawka u źródła.**
  - Odtworzenie: moduł dróg (`pipeline.build`, conform, `terrain_walls`) uruchomiony na NMT GUGiK z WCS 1 m, poza gitem.
  - Narożnik S→E łączy wiejskie ramię DK65 z ramieniem z krawężnikiem. `_emit_strip` ujednolica go w krawężnik bez chodnika.
    Pas trawy liczono jednak przed ujednoliceniem, więc wiejska połowa narożnika była gołym krawężnikiem, a teren za nim był dopasowany do NMT z 2022 r. (stary rów DK65).
  - Efekt: spadek 0,51–0,74 m w odległości 1,5 m za krawężnikiem, na odcinku 2–24 m od węzła rozdziału.
  - Poprawka w `meshing.build_corner_strips`, tylko dla narożników mieszanych ronda kompaktowego: ujednolicenie przed pasem trawy, trawa o szerokości jak na ramieniu z krawężnikiem, wierzch trawy jako soft footprint conformu.
  - Wynik odtworzenia: spadek ≤ 0,28 m (tyle co profil wiejski ramienia). Trójkąty dróg w promieniu 90 m: 19 237 → 19 061. Inne skrzyżowania bez zmian.
  - OTWARTE: ten sam wzorzec, czyli goły krawężnik w narożniku mieszanym, występuje w zwykłych skrzyżowaniach. Rozszerzenie wymaga przebudowy i QA wszystkich regionów.

**Budżet (szacunek).** Wiaty: ta sama liczba słupów (2 × 9 na wiatę) i połaci, więc 0 trójkątów. Pawilon: dach namiotowy ma ≤ trójkątów niż kopertowy.
Lipy: bez zmian. Rondo: −176 trójkątów dróg w promieniu 90 m, trawa scalona z terenem, więc 0 draw calls. Kamery Rynku i ronda: budżet neutralny albo ujemny.
Pomiar edytora po przebudowie wykona lider. **Wizualnie OPEN:** brak renderów w chmurze (pętla visual-qa u lidera).

### D41 w integracji world3 (int-world3-s23, 17.11; recenzja `docs/reports/REVIEW-2026-11-16-pr169.md`)
Przebudowa knyszyn na kodzie #147 #154 #158 #153 #150 #164 #165 #169 + main; VQA High
`artifacts/int-world3-s23/vqa/knyszyn/r1/High-clear/`.
- (a) wiaty: w `market-owner-12` (widok z góry) cztery dachy rozdzielone prześwitami — zgodne z pomiarem.
- (b) pawilon `bdot:de62e5a9`: w r1 ściany żółte, dach namiotowy (kadr `market-owner-13`, kadrowanie lotnicze). Kolor
  P1-1 widoczny — „szary budynek” z r2 to nie ten pawilon albo inne światło; zostaje OTWARTY parking z płyt oraz
  jasny trójkąt nawierzchni obok pawilonu (wygląda na osobny wielokąt `paved`, do sprawdzenia).
- (c) lipy: proporcja 1,75 działa, ale płaskie karty i ciemny pionowy szew koron (`rynek-owner-05`) bez zmian —
  **P1-2 ZNANE / OTWARTE** (osobne zadanie: bryła korony / normalne kart).
- (e) uskok DK65 płd.: sonda na GLB `tools/worldgen/qa/knyszyn_s_kerb_step.py` (stacje 2–24 m od węzła rozdziału,
  spadek krawędź twarda → grunt 1,5 m dalej): przed #169 W 0,506 / E 0,652 m, po integracji W 0,499 / E 0,654 m;
  w kadrze `rondo-dk65-from-south` betonowa ściana po prawej nadal widoczna. Poprawka (e) w integracji nie działa
  (próg 0,15 m niespełniony) — OTWARTE, przyczyna UNVERIFIED (DK65 to `primary`, więc #165 nie daje ramieniu S
  chodników). Uwaga do sondy: oś stacji to cięciwa drogi OSM 286990127, stąd krawędź E na 0–4,4 m od osi.
  Test `test_knyszyn_route_graph_…` zielony po wyłączeniu `knyszyn-roundabout-outer-diameter-d41` (sprawdzone na danych z gita).
- P2-7 / #153: luka KRTG 1,73 m na pierścieniu — ADR 0274, test `test_knyszyn_route_graph_…` czerwony.
- **Aktualizacja world3 r3 (17.11, decyzja lidera):** wpis `knyszyn-roundabout-outer-diameter-d41` wyłączony
  (zakomentowany z powodem w `overrides.yaml`; wraca, gdy generator ronda przeniesie węzły pierścienia) — test KRTG
  zielony. Przyczyna uskoku od wschodu ustalona: narożnik S→E jest „mieszany” (ramię S wiejskie, ramię E po #165 ma
  chodnik → jego pas trawy = 0), więc poprawka (e) dawała stacjom przekształconym `max(cv) = 0` m trawy. Poprawka
  w `meshing.py`: przekształcona stacja (zwykły krawężnik bez chodnika) dostaje pas ADR 0110 `VERGE_W`. Dodatkowo
  `knyszyn-dk65-split-s-kerbed-edge-w3` (krawężnik z trawą w strefie rozdziału). Sonda: wschód max 0,652 → 0,191 m
  (mediana 0,505 → 0,058); zachód bez zmian 0,506 m — narożnik S→W ma skok wysokości linii krawężnika 0,51 m/m,
  przy którym bezpiecznik `meshing` celowo nie kładzie trawy (OTWARTE). Kadr r1 vs r3 `rondo-dk65-from-south`:
  ściana po prawej znikła.

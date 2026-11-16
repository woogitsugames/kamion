# R63 — deterministyczna samokontrola przyjętych A

**Ponownie osobiście obejrzano 3/3 wylosowanych fotografii, bez podmian. Treść trzech przyjętych A potwierdzona z dotychczasowymi ograniczeniami. 0 nowych fotografii i 0 nowych B.** To samokontrola z wiedzą o dawnych kwalifikacjach, nie ślepa lub niezależna recenzja i nie audyt całej unii P18+s21.

## Snapshot przed losowaniem

Populacja obejmuje dokładnie 11 źródeł wskazanych przez koordynatora: Knight158, Western182, Premier183, KroneEUR15, RoadTourWW17, AutoReview39, RI49, UR54, UR55, RG57, FR60-003. Użyto kanonicznych ID istniejącego głównego manifestu. Aliasy P18-182=CR6 i P18-183=CR7 to po jednej ekspozycji, podobnie Knight158=02-009. Pełne mapowanie w `population-before-sampling.json` i `population.csv`.

Najpierw zapisano niezmieniany snapshot JSON oraz jego SHA256, a dopiero w osobnym wywołaniu wykonano losowanie. Hash bajtów pliku:

`12f6d1170e1de1a0fa96b27dc4dc3ffb8ec0213d947a09cd56e12f4546299c41`

Algorytm: `random.Random(20261115).sample(sorted(ids),3)`. Kolejność wyniku:

1. `02-FR60-003` — Fototruck 348842.
2. `02-009` — Knight / P18-158.
3. `02-UR54-001` — Lamberet JF52527.

`sample.json` zachowuje pełną uporządkowaną populację, seed i hash. Snapshot po oględzinach nie zmieniony; jego dawnych kwalifikacji nie przepisano na wynik dzisiejszej obserwacji. Nie było losowania rezerwowego.

## Wyniki oglądu

- **FR60-003**: potwierdzony drobny dolny szary nalot na obu polach; rude ubytki przy zamkach i środku oraz resztki grafiki oddzielono od filmu. Typ naczepy źródłowo S.KO/Полуприцепы фургоны i konstrukcja w pełnym kadrze. Obraz **1200 × 800 SOURCED [DOM]**, drzwi **380–420 px ESTIMATED**; B_FAIL_GE1000. Zima 0, europejski podzbiór zachowuje PENDING geograficznego źródła z R60.
- **Knight**: bordowe pola z lekkim jasnym nakrapianiem/filmem, ciemne odręczne wytarcia i łuki w dolnej części; duże cienie rygli oraz nadruki osobno. Typ semi-trailer ze źródłowego opisu autora przechowanego w `data/reused-p18-type-audit.json`, bez nowego żądania Commons. Faktycznie obejrzany lokalny plik ma **1093 × 1365 SOURCED [Pillow]**, a nie historyczną miniaturę 960 × 1199. Drzwi tego pliku **740–800 px ESTIMATED**. B przede wszystkim NOT_NEW_BASELINE; nie awansowano go za dostęp do innej istniejącej wersji. SHA256 pliku w `review.json`, bez kopiowania obrazu.
- **Lamberet**: prawy panel silniej szary z drobnymi pionowymi smugami; lewy wyraźnie jaśniejszy. Rdza przy dolnych uchwytach osobno. Białe zamazania danych i tablicy są redakcyjne, nie wzór brudu. Typ ze źródła oferty i istniejącego oglądu konstrukcji R54; nie z samego logo. **768 × 1024 SOURCED [tytuł standalone]**, drzwi **580–650 px ESTIMATED**, B_FAIL_GE1000, kontekst trasy nadal UNVERIFIED. Bez śniegu.

Ponowny ogląd datowany **2026-11-16, date-only**; nie wymyślano godzin. Dat zdjęć/GPS nie weryfikowano ponownie poza aktualnym odczytem Fototruck — nie zastępowano ich datą recenzji. Szczegółowe własne opisy w `audit.csv`, `manifest.csv` i `review.json`. Zero nowych pobrań Commons/Flickr; Knight wyłącznie istniejący lokalny plik przez view_image, dwa ARR wyłącznie przeglądarka. **0 kopii ARR i 0 zapisanych screenshotów**. Bez zmian parenta, globalnych ledgerów ani gita; cel 20/12/6/6 pozostaje otwarty.

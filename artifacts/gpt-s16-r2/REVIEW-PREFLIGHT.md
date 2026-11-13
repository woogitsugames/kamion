# ADR 0154 — niezależny preflight

Status: **Przegląd źródeł A oraz aktualizacji B zakończony; osobny końcowy werdykt obrazu znajduje się w REVIEW-VISUAL.md.** Nie znalazłem wykazanego błędu P1/P2 w przejrzanym kodzie. Audyt integralności i przejście testów nie są podstawą akceptacji wyglądu.

## Przejrzany zakres

`front_gardens` i jego helpery w plantings.py, `garden_canopies` w vegetation.py, dwa podłączenia w stage.py, `ApplyGardenCanopyWidth` i miejsce jego wywołania w InstanceImporter.cs, draft ADR 0154 oraz sześć arkuszy photo-pairs/High-clear/street-01..06.jpg. Odczytano pomocniczo istniejące kontrakty helpera hedge, selekcji starych żywopłotów i instancji drzew w plots.py. Bez Unity, adb, generatorów, testów i zmian kodu.

## Ustalenia źródłowe

- `ApplyGardenCanopyWidth` jest ograniczony do High, odrzuca niefinitywne liczby oraz szerokość poza [1; 1,5]. Prawostronne mnożenie skali zachowuje lokalną oś pionową, początek i istniejący obrót. Import stosuje helper tylko w gałęzi drzew. Nie znalazłem zmiany macierzy rekordów bez opt-in.
- `garden_canopies` zachowuje rekordy nie-High i gatunki poza jawnie wymienionymi. Kopiuje zmieniany rekord; zachowuje pozycję, prototyp, wariant i yaw. Podnoszenie wysokości nie skraca istniejących drzew w obecnym kontrakcie danych, gdzie wysokości źródłowe mają jeden znak po przecinku.
- `front_gardens` sprawdza istniejący warunek starych żywopłotów, odrzuca nieprzezierne płoty, odejmuje dom, utwardzenia i przejścia przy bramach/furtkach. Geometria pozostaje w obrysie posesji. Nowe części trafiają do istniejącego plot_kit; oba warianty wymagają zachowania dotychczasowych grup i obwiedni. Limit trójkątów jest sprawdzany przed dodaniem każdego odcinka.
- Nie znalazłem statycznie wykazanej regresji grupowania, colliderów, lasu lub pozycji instancji. Raport world-integrity podaje brak błędów dla 2151 chronionych siatek i 125450 rekordów nie-High; to dowód techniczny, nie ocena jakości.

## Ryzyka wymagające obrazu, nie spekulacyjnych poprawek kodu

1. **Poszerzane jest całe drzewo, nie tylko korona.** vegetation.py dodaje mnożnik do instancji, a InstanceImporter skaluje model w obu osiach poziomych. Pień, konary i karty liści także stają się szersze. Przy równoczesnym podnoszeniu wysokości trzeba sprawdzić proporcje pnia i kontakt z dachem. Nie ma podstaw, by samą nazwę garden_canopy_width traktować jako izolowaną edycję korony.
2. **Szerokość nie zwiększa liczby liści.** Istniejąca geometria korony pozostaje taka sama i jest rozciągana. Może to zwiększyć obrys bez poprawy wrażenia gęstej, nieregularnej korony. Potrzebne są widoki zmienionych drzew, szczególnie granicy LOD, a nie wyłącznie dalekie kadry ulic.
3. **Pierwsze arkusze nie dowodzą większej poprawy pierzei.** garden_03_a/b oraz garden_06_a/b nadal pokazują dużo otwartej przestrzeni nad płotami i małe, oddzielone korony. garden_02_b jest zdominowany ślepą ścianą i narożnikiem domu; słabo pokazuje frontowe nasadzenia. To luka doboru kadrów lub ograniczenie efektu, nie dowód błędnych współrzędnych nasadzeń.

Referencje są prawidłowo oznaczone jako typologiczne i z innej lokalizacji/pozy. Nie należy dopasowywać do nich konkretnej liczby drzew ani ogłaszać zgodności ulic z fotografią. Wstępna ocena obrazu i dalsze pary należą do REVIEW-VISUAL.md.

## Uzupełnienie po iteracji B

Ponownie odczytano `garden_canopies` oraz podłączenia w stage.py. B wyznacza maksymalny Z z istniejących części budynków i łączy go z identyfikatorami domów danej posesji; uwzględnia dachy w odległości do 25 m od drzewa. Odejmowanie `tree.z` daje wysokość względem podłoża drzewa. Dodatkowe 4,5 m i limity 22–24 m pozostają WORKING_VALUE, a nie pomiarem konkretnego drzewa. Dotychczas wyższe drzewa nie są skracane. Nadal skalowana jest cała instancja wraz z pniem i konarami; wcześniejsze ryzyka jakościowe pozostają właściwe, ale pasujące obrazy B pokazują teraz rzeczywistą poprawę lokalną.

`KAMION_GARDENS_0154=0` wyłącza oba nowe etapy jako jawny przełącznik odtwarzania baseline. Domyślna ścieżka pozostaje włączona. Nie znalazłem nowego wykazanego błędu integralności w tym rozszerzeniu. Werdykt wizualny B jest zapisany osobno w REVIEW-VISUAL.md; nie należy traktować wstępnej oceny wariantu A jako końcowej oceny B.


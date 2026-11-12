# Runda r3 — odrzucone próby, walidacja w toku

Produkcja została przywrócona do stanu r1. Brak zaakceptowanej zmiany r3. Nie przenosić patchy kandydatów do main jako naprawy B8. Pozostają dowodami prób.

Istotne ograniczenie identyfikacji: propozycja czterech koron dotyczy pasa przed JRG2. Nie udowodniono, że to te same drzewa pasa dzielącego, których brak nazywa B8. Poprawa pozy SBS musi poprzedzić nowe przypisanie źródłowych koron do konkretnego blokera.

Źródłowo potwierdzono rejon brakujących koron na ortofoto, ale środków koron nie można utożsamiać z pomierzonymi pniami. Cztery punkty mają niepewność około 3 m. Wysokości i gatunki zastępcze były robocze. A dodało dwa drzewa oraz cztery wywołania Low; B1 zamieniło jeden samosiew bez wzrostu wywołań, ale nie odtworzyło zespołu koron. Osobna zmiana wysokości istniejącego klonu uwydatniła jego rzadką sylwetkę. Krytyk potwierdził odrzucenie.

Pełny końcowy generator, GIS i Unity są w finish-rejected.ps1. Podczas uruchomienia helpera początkowy checkpoint otrzymał listę ścieżek jako jeden argument z przecinkami; nie dodał plików. Naprawiono wywołanie przez pwsh -Command z jawną tablicą, commit f5f60b64 zachował przywrócenie i helpery. Nie uruchomiono przez to dodatkowego generatora.

verify_restored.py sprawdzi 130 GLB i semantyczną równość 64 plików instancji z baseline oraz osobny probe. Ponieważ finish-rejected.ps1 był już uruchomiony przed dodaniem wywołań weryfikatora, należy dodatkowo uruchomić weryfikator ręcznie po zakończeniu sekwencji. Nie polegać na edycji już działającego skryptu.

Nie wykonano pełnej macierzy after dla odrzuconych kandydatów. Baseline ma 368 obrazów: 268 kontrolnych ponownie użytych po pinach oraz 100 nowych kadrów 25 póz B. Raport końcowy ma jawnie rozróżnić te dowody i pojedyncze próby, bez deklaracji akceptacji budżetu wszystkich kamer dla B1.

Następny krok po walidacji: REPORT, ADR, robocopy do main, kolejna wolna gałąź i merge main. Hipoteza jasności koron Putry jest opisana w FOLLOWUP-SHEEN.md. Pozostałe otwarte tematy: źródłowe pobocza przy krawężniku, Pietrasze i HLOD, listopad jako wariant danych. Nie zmieniać teraz shaderów podczas walidacji przywróconego stanu.

Nowszy feedback lidera na main zmienia kolejność następnej próby. docs/owner/GPT-FEEDBACK-S10.md, dopisek s11 około 01:50, oraz REVIEW-2026-11-12-s11-gpt-r1-batch.md wskazują przede wszystkim berberys wyglądający jak bordowe bale, rytm Putry i drzewa pasa dzielącego. REVIEW-2026-11-12-s11-0125.md dodaje, że pozy G3-B są obecnie głównym blokerem porównań; 297817 wymaga korekty SBS. Nie kalibrować precyzyjnego rozmieszczenia nasadzeń do obecnej pozy B. Po merge main następny kandydat powinien skupić się na berberysie z bliskim zdjęciem i kadrze ronda, a hipotezę sheen zachować jako późniejszą.

Rozpoznanie bez edycji: plantings.py nadal buduje pełny nieprzezroczysty rdzeń 6,5 cm pod powłoką alpha. Sama poprawa ciągłości wysokości z r1 usuwa przebicia, ale rdzeń przesłania otwory liści i utrwala prosty bok. Następna próba może rozdzielić berberys od pozostałych gatunków i porównać bardziej cofnięty rdzeń z rdzeniem liściastym korzystającym z istniejącego materiału powłoki. To hipoteza, nie przyjęte rozwiązanie. Zachować liczbę trójkątów lub ją obniżyć, nie zwiększać liczby wywołań; nie ukrywać kosztu alpha overdraw jako pomiaru GPU. Nie zmieniać overrides.yaml ani wspólnego importera.

W kadrze before/High-overcast/g3a-rondo-bie-approach.png płaski brązowy wierzch szczególnie widać na bliskim lewym pasie żywopłotu. To nie wymaga losowych dużych przerw ani powrotu do profilu kanapy z wcześniejszej odrzuconej iteracji. Rzeczywiste zdjęcie Rakoon pokazuje gęstą niską pokrywę i drobną nieregularność brzegu.

Ważne przy następnym eksperymencie: hedge_shell i hedge_sprig są geometrią chunków. RegionImporter tworzy je w swojej zwykłej gałęzi texture/alpha_cutoff jako URP Lit alpha clip, double sided; nie wolno zakładać, że obejmuje je runtime WorldInstances.simpleFoliage lub Vegetation.shader. Rdzeń ma zestaw PBR hedge_foliage. Zamiana rdzenia na istniejącą powłokę zmieni tę ścieżkę, więc mierzyć rzeczywiste materiały i koszty. Rozważyć tylko berberis_red, z UV liści w skali HEDGE_TILE_M i odrębną fazą warstwy, zachowując pozostałe gatunki. Istniejące testy do selekcji: test_vegetation_0109.py oraz test_streetscape_r6.py (pełny GIS dopiero na końcu).

Kontrakt kolizji sprawdzono tylko do odczytu. plantings.hedge_mass zapisuje rdzeń/powłokę do warstwy furniture. build_world eksportuje ją osobno od road_collision, a RegionImporter.BakeCollision pobiera road_collision oraz terrain_lod2 z wariantu low. Nie używa materiału żywopłotu do wyboru kolizji. W nowej rundzie warto porównać pozycje i indeksy tych dwóch węzłów w GLB, zamiast hashy całych assetów Unity z niestabilnymi identyfikatorami podzasobów. Analiza kontraktu nie zastępuje zmierzonej zgodności po przyszłej zmianie. Nie edytowano tych plików.

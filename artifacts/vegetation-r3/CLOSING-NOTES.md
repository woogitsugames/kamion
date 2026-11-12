# Runda r3 — odrzucone próby, walidacja w toku

Produkcja została przywrócona do stanu r1. Brak zaakceptowanej zmiany r3. Nie przenosić patchy kandydatów do main jako naprawy B8. Pozostają dowodami prób.

Źródłowo potwierdzono rejon brakujących koron na ortofoto, ale środków koron nie można utożsamiać z pomierzonymi pniami. Cztery punkty mają niepewność około 3 m. Wysokości i gatunki zastępcze były robocze. A dodało dwa drzewa oraz cztery wywołania Low; B1 zamieniło jeden samosiew bez wzrostu wywołań, ale nie odtworzyło zespołu koron. Osobna zmiana wysokości istniejącego klonu uwydatniła jego rzadką sylwetkę. Krytyk potwierdził odrzucenie.

Pełny końcowy generator, GIS i Unity są w finish-rejected.ps1. Podczas uruchomienia helpera początkowy checkpoint otrzymał listę ścieżek jako jeden argument z przecinkami; nie dodał plików. Naprawiono wywołanie przez pwsh -Command z jawną tablicą, commit f5f60b64 zachował przywrócenie i helpery. Nie uruchomiono przez to dodatkowego generatora.

verify_restored.py sprawdzi 130 GLB i semantyczną równość 64 plików instancji z baseline oraz osobny probe. Ponieważ finish-rejected.ps1 był już uruchomiony przed dodaniem wywołań weryfikatora, należy dodatkowo uruchomić weryfikator ręcznie po zakończeniu sekwencji. Nie polegać na edycji już działającego skryptu.

Nie wykonano pełnej macierzy after dla odrzuconych kandydatów. Baseline ma 368 obrazów: 268 kontrolnych ponownie użytych po pinach oraz 100 nowych kadrów 25 póz B. Raport końcowy ma jawnie rozróżnić te dowody i pojedyncze próby, bez deklaracji akceptacji budżetu wszystkich kamer dla B1.

Następny krok po walidacji: REPORT, ADR, robocopy do main, kolejna wolna gałąź i merge main. Hipoteza jasności koron Putry jest opisana w FOLLOWUP-SHEEN.md. Pozostałe otwarte tematy: źródłowe pobocza przy krawężniku, Pietrasze i HLOD, listopad jako wariant danych. Nie zmieniać teraz shaderów podczas walidacji przywróconego stanu.

Nowszy feedback lidera na main zmienia kolejność następnej próby. docs/owner/GPT-FEEDBACK-S10.md, dopisek s11 około 01:50, oraz REVIEW-2026-11-12-s11-gpt-r1-batch.md wskazują przede wszystkim berberys wyglądający jak bordowe bale, rytm Putry i drzewa pasa dzielącego. REVIEW-2026-11-12-s11-0125.md dodaje, że pozy G3-B są obecnie głównym blokerem porównań; 297817 wymaga korekty SBS. Nie kalibrować precyzyjnego rozmieszczenia nasadzeń do obecnej pozy B. Po merge main następny kandydat powinien skupić się na berberysie z bliskim zdjęciem i kadrze ronda, a hipotezę sheen zachować jako późniejszą.

Rozpoznanie bez edycji: plantings.py nadal buduje pełny nieprzezroczysty rdzeń 6,5 cm pod powłoką alpha. Sama poprawa ciągłości wysokości z r1 usuwa przebicia, ale rdzeń przesłania otwory liści i utrwala prosty bok. Następna próba może rozdzielić berberys od pozostałych gatunków i porównać bardziej cofnięty rdzeń z rdzeniem liściastym korzystającym z istniejącego materiału powłoki. To hipoteza, nie przyjęte rozwiązanie. Zachować liczbę trójkątów lub ją obniżyć, nie zwiększać liczby wywołań; nie ukrywać kosztu alpha overdraw jako pomiaru GPU. Nie zmieniać overrides.yaml ani wspólnego importera.

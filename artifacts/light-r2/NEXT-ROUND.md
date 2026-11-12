Po zamknięciu r2: r3 — mokra nawierzchnia po deszczu, wizualnie.

Utworzyć gpt-light-r3 od zakończonego r2, scalić aktualny main i odczytać nowe decyzje. Nie zmieniać materiałów/asfaltu należących do sesji asphalt. Dziedzina light ma istniejący KamionAtmosphere.hlsl i dane wetness/puddles w LightingPreset oraz rq_wet. Najpierw baseline mokro/sucho na Low i High, potem ocena zdjęć i wybór największego odstępstwa w świetle/odbiciu.

Przejrzane lokalne referencje Rakoon zawierają mokrą kostkę i ciepłe oprawy w śródmieściu zimą. Nie traktować ich jako kalibracji mokrego asfaltu ani dowodu dla geometrii trasy. Szukać właściwego zdjęcia w istniejącym zbiorze refs/Mapillary, zachować pochodzenie i ograniczenia pozy. Nie korzystać z Google ani telefonów.

R2 pozostawia eksperymentalne reflektory off. Brak occlusion, pomiaru zasięgu, kalibracji kształtu/20kcd oraz GPU A16. Ciemne przejścia g3a-eye-s0262/stretch-03 i odcinki edge-west/fence2/office1/docks są jawnie otwarte. Nie ukrywać ich podnoszeniem globalnej ekspozycji, które niszczyłoby wybrany wygląd Night. Nie zmieniać Cab/TruckLights ani geometrii latarni bez zmiany zakresu przez właściciela.

Każdy własny Python tylko po faktycznym zakończeniu poprzedniego procesu i przez heavy z ownerem bieżącej gałęzi. Powtórne Acquire tego samego ownera jest reentrantne: nie jest wzajemnym wykluczeniem dwóch zadań. Unity owner gpt-light, zwalniać w finally. Pełny GIS tylko na końcu rundy.

Przygotowanie następnej rundy, odczyt bieżącego main c89b3e7d0823e9139bf680de0befa2f4c268a9c7; to analiza, bez zmian produkcji r4.

Backlog r4: spójność tonów Low i High na tych samych kamerach. Dopiero po zamknięciu r3, nowej gałęzi gpt-light-r4 i merge main.

LookGrading dokumentuje różne mapowania: High ma krzywą master w przestrzeni FastTonemap, Low zwykły sRGB clip oraz shaderowy toe. To jawna różnica architektury, nie dowód obecnego błędu konkretnego zdjęcia.

Najpierw kontrolowana plansza szarości i kolorów przy rzeczywistym EnvironmentLighting, tej samej ekspozycji i obu poziomach jakości. Shader planszy musi stosować ten sam KamionTone co świat na Low, aby nie porównywać surowego Unlit ze stopniowaną sceną. High otrzymuje istniejący post bez dodatkowych efektów.

Pomiar planszy ma rozdzielić odpowiedź tonalną od innych siatek, normalnych, albedo, cieni i próbek tekstur. Dopiero potem wybrane rzeczywiste kadry trasy i samochodu; nie przenosić laboratoryjnego wyniku na fotometrię klasy C.

Ewentualne wyrównanie Low wymaga kontroli kosztu istniejącego przebiegu, bez nowego fullscreen pass i bez zmniejszania skali. Rozważenie LUT lub mapowania w shaderze nie oznacza zgody na niezmierzony koszt ani decyzji wdrożeniowej.

Mokra droga z r3 pozostaje FAIL, a nie zamknięty sukces. Niezależny lab wskazuje brak lokalnej informacji o punkcie przecięcia i okluzji jako ograniczenie kierunkowej kostki. Nie przywracać sfery20m, promienia12m ani obniżenia połysku jako zamiennika tego wymagania.

# Możliwa optymalizacja po renderach iteracji 3

Manifesty High obejmują wszystkie chunki, bez selekcji kamer i bez instancji:
przed zmianą warstwa furniture ma 259 970 trójkątów, iteracja 1 ma 292 938,
iteracja 2 ma 272 986, a iteracja 3 ma 296 198. To nie jest budżet klatki.
Wynik wymaga porównania wszystkich kamer; nie można z niego ogłosić ani PASS,
ani przekroczenia limitu +2% dla trasy.

Możliwa przyczyna zbędnego kosztu: każdy krótki stopień deski tworzy teraz
dodatkowy pionowy podział siatki. Jej dolna krawędź jest jednak zasłonięta
betonem i gruntem. Siatka z UV opartym na wysokości świata może mieć dolną
krawędź poziomą, poniżej minimum próbek gruntu całego przęsła. Potrzebne
stacje to wtedy końce przęsła i ewentualny środek wygięcia, a nie każdy
stopień podmurówki. Widoczny wzór drutów i zamknięte końce desek pozostają.

Kandydat wymaga kontroli na nierównym NMT: dolna krawędź musi schodzić pod
wszystkie deski i teren, a UV musi zachować poziom drutów. Sprawdzić również
kolizję, AABB i cienie. Nie zastosowano go do źródeł ani do eksportu iteracji 3;
wyniki tej iteracji pozostają powiązane z zapisanymi hashami źródeł.

## Niezależny przegląd kandydata

Kandydat jest sensowny dla siatki renderowanej, ale minimum musi obejmować
również boczne wygięcie oraz wszystkie dotychczasowe próbki desek. Trzeba
uwzględnić różnicę pomiędzy NMT a uproszczonym terenem Low. Kolizja powinna
zachować dotychczasowe stacje i geometrię niezależnie od optymalizacji obrazu.

Uproszczenie sinusoidy do końców i środka zmienia jej sylwetkę oraz normalne;
kontrola obrazów pozostaje potrzebna mimo małego odchylenia 12–25 mm.
Sprawdzić AABB i cienie: głębszy panel lub odstająca próbka mogą zwiększyć
koszt cullingu/ukrytych fragmentów. Porównać granice siatki z istniejącymi
deskami i słupkami, zamiast zakładać brak zmiany granic całej grupy.
Mniej trójkątów nie jest samodzielnym dowodem mniejszego kosztu GPU.

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

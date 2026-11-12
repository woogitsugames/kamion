# Niezależny odczyt próbki terenu i testu prześwitu

vegetation_critic potwierdził zgodność konwersji GLB (-E,U,N), ekstrakcji pełnego prefiksu siatki 129 × 129, odwrócenia kolejności wierszy do rosnącego N oraz bilinearnego samplera. Łańcuch pochodzenia obejmuje źródłowy hash C, brak transformacji i zgodność wspólnych węzłów. Nie wykonywał ekstrakcji, testów lub Unity.

W pierwszej wersji testu znalazł P1: geometria była przesunięta względem pierwszego punktu rabaty. Wysokości gruntu trafiały w prawidłowe miejsce, lecz _crown zależy od bezwzględnych XY i miał inną fazę reliefu. Poprawiono to przed uruchomieniem testów: zapisany przypadek zachowuje region-local XY, a sampler odejmuje tylko początek patcha. Drugi odczyt recenzenta potwierdził rozwiązanie P1 i zachowanie produkcyjnego położenia próbek capu. Syntetyczne przypadki mogą nadal być względne.

Recenzent potwierdził również, że maksimum liczone po wszystkich przecięciach wspólnego podziału zachowuje sens wcześniejszej asercji i pozwala zapisać margines w JUnit. Ostrzeżenie od 4 mm przy granicy 5 mm wskazuje ograniczenie próbki zaokrąglonej do 1 mm. To nadal rekonstrukcja eksportu, nie surowa siatka float64. Test prześwitu rdzeń–shell nie sprawdza całych podstaw pochylonych kart D. Sam pytest nie sprawdza ponownie wejściowego GLB; pochodzenie zapewnia ekstraktor, a zgodność podłoża D dodatkowa kontrola przed importem.

Werdykt dotyczy poprawności kodu testu i mapowania, bez akceptacji wyniku 45 testów, kolizji lub wyglądu D. Testy pozostają w aktywnej kolejce heavy.

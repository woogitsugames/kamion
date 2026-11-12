# Częściowe oględziny dzienne po zamrożeniu r2

Obejrzano pojedynczo arkusze Low-overcast04,05,06:18 par przed/po,
szerokość960px, po6 kamer na stronę. Nie stwierdzono oczywistej nowej
regresji sylwetek, latarni, ogrodzeń, podmurówki ani tyłów znaków.
Na tarczach i tablicach widocznych z daleka różnica zużycia pozostaje mała;
te arkusze nie dowodzą czytelności legendy ani szczegółów śrub.
Brak deklaracji oceny pozostałych312 wariantów.

Przygotowanie interaktywne: compare_frames.py --review-page Low-overcast:4
(lub5/6) --label after3. Ten tryb wybiera dokładnie jeden arkusz, maksymalnie
12 źródłowych PNG, otwiera je pojedynczo i odrzuca wejście powyżej3MP.
Proces ma priorytet Windows IDLE, a bufory obrazów są jawnie zamykane.
Każde z trzech wywołań trwało poniżej1s według narzędzia powłoki.
Nie jest to generator ani zestaw testów. Pełna partia330 obrazów pozostaje
zaplanowana w heavy po oczekującym procesie geometrii.

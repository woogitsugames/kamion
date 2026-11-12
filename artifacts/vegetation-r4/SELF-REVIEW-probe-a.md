# Próba A — ocena autora

Import i wszystkie cztery grupy prób zakończone kodem 0. Obejrzałem wszystkie osiem arkuszy `berberis-review-probe-a`: oba kadry ronda, Low/High, clear/overcast, z rzeczywistym zdjęciem Rakoon. W 16 wierszach kosztu Low ma maksymalnie zero dodatkowych wywołań i zero zmiany trisK. To ograniczona próba, nie pełna macierz ani pomiar GPU.

Materiał liści na warstwie wewnętrznej zagęszcza drobną strukturę boków i ogranicza wrażenie czarnych dziur. Nie widzę pustej skorupy ani wielkich otworów na przestrzał. Główny problem pozostaje: duży, ciągły, jasnobrązowy wierzch nadal czyta się jak płaszczyzna pełnej bryły. Szczególnie lewy bliski krzew w g3a-rondo-bie-approach ma widoczne duże trójkątne płaszczyzny. Zdjęcie ma drobno nierówną pokrywę i obrys; samo poprawienie materiału wnętrza nie odtwarza tego charakteru. Nie uznaję A za zakończoną poprawę realizmu.

Osiem obrazów kontrolnych r10_fence_2 i fire-station-ref7197 jest bajtowo identycznych z baseline we wszystkich profilach i światłach; dowód w probe-a-control-identity.json. Kontrola danych obejmuje wszystkie 64 pliki instancji i dekodowane wejścia kolizji 64 Low chunków. Żaden z tych dowodów nie potwierdza kosztu alpha overdraw ani migotania w ruchu. Następna decyzja wymaga niezależnego krytyka; nie renderować pełnej macierzy A jako rzekomo zaakceptowanej zmiany.

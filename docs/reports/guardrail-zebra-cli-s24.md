# Guardrail / zebra — s24, gałąź guardrail-zebra-cli

Zmiany dotyczą generatorów; Unity, player i `build_world` nie były uruchamiane. Wszystkie zapisy pozostają w tym worktree, bez push.

**Lokalizacja:** `player.log` przejazdu `20261119-140004`: Kleeberga od linii 251, klatka t=650 w linii 305. Klatka t=2560 jest w linii 1082, a przełączenie na Knyszyn-w dopiero w 1086, po t=2570: należy objąć kontrolą również **knyszyn**, nie tylko knyszyn-w. Obejrzano obie wskazane klatki.

**Bariera — luka przyczynowa w kodzie:** `tools/worldgen/streetscape/furniture.py:2463` i `:2468` wygładzają offset, a `:1837` / `:1918` dociągają końce do innych runów. Odległość od osi własnego łańcucha oraz deduplikacja bariera–bariera nie gwarantują odstępu od nawierzchni innego ramienia; brakowało końcowej kontroli względem trójkątów jezdni. Nie przypisuję konkretnego przesunięcia z klatki jednemu z tych etapów bez danych pośrednich tamtego buildu.

**Zebra — luka w kodzie i granica diagnozy:** `tools/worldgen/roads/markings.py:540` scala przejścia tylko w jednym łańcuchu. Przejścia ronda powstają osobno w `roads/compact_roundabout.py:659` / `:704`. Brakowało wspólnej kontroli wynikowych P-10 między łańcuchami i wobec gotowych wysepek. W odtworzeniu płaskiego modelu aktualnych danych Knyszyn / Knyszyn-w nie ma nakładania P-10 już przed poprawką (0 m²). Sam screenshot nie dowodzi przecięcia wielokątów; przyczyna konkretnego artefaktu t=2560 pozostaje **UNVERIFIED**. Nie deklaruję jego wizualnego usunięcia na podstawie zielonych testów.

**Zmiany:** `roads/surface_safety.py` indeksuje trójkąty nawierzchni road + bridge, z zachowaniem rozdzielenia poziomów. `furniture.py:2057` usuwa całe niebezpieczne odcinki po wszystkich przesunięciach; nie łączy punktów przez wyciętą przerwę. Linia słupków: ≥0,47 m od nawierzchni = 0,25 m bufora + 0,20 m obwiedni osprzętu + 0,02 m tolerancji uproszczenia (WORKING_VALUE). Obejmuje bariery przy podporach; `guardrail_built` zawiera zachowaną geometrię. `markings.py:1122` przycina P-10/P-10J/authored do asfaltu, odejmuje wysepki +0,05 m i wcześniejsze P-10 na tym samym poziomie; triangulacja ograniczona i interpolacja zachowują pole, Z, UV, UV1, COL. Nietknięte siatki pozostają bez zmian. ADR 0308.

**Testy:** `tests/gis/test_drive_s24_surface_safety.py`: 9 jednostkowych (przecięcie wnętrza odcinka, rozcięcie bez ponownego mostkowania, most nad drogą, overlap zebr/wysepka, zachowanie pola i UV, trzy duplikaty, flush po join, ścieżka podpór), po 2 kontrole na każdym z trzech kafli oraz szew Knyszyn/Knyszyn-w. Testy nie wymagają Data/raw; opcjonalnie czytają kopie NMT z katalogu wskazanego przez `KAMION_SURFACE_NMT_DIR`, sprawdzając SHA-256 z `Data/Regions/<id>/terrain.json`.

Wyniki końcowe i lista przebudowy zostaną uzupełnione po zakończeniu testów kafli.

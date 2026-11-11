# Przygotowanie kominów EC

Runda r3 ma nastąpić po wiadukcie, bez zmiany źródeł sesji life.
Własny read-only audit rzeczywistego street_props.glb i instancji jest zapisany
w chimney-preflight.json: oba kominy i oba LOD mają dryf osi 0 m, yaw instancji 0.
To nie zastępuje odczytu macierzy Unity. Nie pochylać ani nie prostować modelu na oko.

Fotografia CC0 20200711_073128 Elektociepłownia Białystok pokazuje szerokie pasy
na dużej części obu trzonów. Obecny builder daje siedem pasów dopiero od 0,66H
(dla 120 m około 5,83 m na pas). To konkretna różnica do pomiaru i poprawy.
Nie zmieniać wysokości 120 m, średnic ani pozycji bez osobnego źródła.
Kominy różnią się detalami zwieńczenia i stanem malowania; zdjęcie nie uzasadnia
identycznej kosmetyki dla obu. Zimowa fotografia pod słońce nie kalibruje albedo.

Własność: `landmarks.py` rejestruje nazwy i wymiary w LP.LANDMARKS. Sam builder
`chimney()` znajduje się w cudzym life_props.py; jego pliku nie edytować.
Mesh.tube zapisuje UV0.y od zera osobno dla każdego odcinka, więc proste użycie
istniejącego _STRIPES nie przeniesie ciągłego malowania na cały trzon.
Nie stosować monkey patchingu funkcji life ani hacków w typach wysokości.

Możliwy wariant zgodny ze wspólnymi plikami: addytywna flaga materiału i wariant
WorldSurface wyznaczający pasy z lokalnej wysokości wierzchołka, na obecnych trzech
materiałach kominów. Osobne pole danych z zakresem/metrami, liczbą pasów i kolorami
liniowymi; domyślnie wyłączone dla wszystkich innych materiałów. Nie zmieniać
kontraktu tint, nie tworzyć dodatkowego przejścia ani zwiększać Low draws.
Wariant trzeba sprawdzić na importerze i rzeczywistym układzie local Y, zanim
zostanie wybrany. To propozycja, nie gotowy ani zweryfikowany projekt.

Po merge main wykonać własny świeży baseline z kamery trasy i kamer detalu
w Low/High, overcast/clear. Dokładnie zmierzyć pasy na pełnych zdjęciach CC0,
nie tylko na tych pomniejszonych kopiach. Oznaczyć rozbieżność kąta/pozy fotografii.
Zachować materiały innych obiektów i wszystkie pliki life bez zmian.

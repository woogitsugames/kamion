# Przygotowanie kominów EC

Runda r3 ma nastąpić po wiadukcie, bez zmiany źródeł sesji life.
Własny read-only audit rzeczywistego street_props.glb i instancji jest zapisany
w chimney-preflight.json: oba kominy i oba LOD mają dryf osi 0 m, yaw instancji 0.
To nie zastępuje odczytu macierzy Unity. Nie pochylać ani nie prostować modelu na oko.

Fotografia CC0 20200711_073128 Elektociepłownia Białystok pokazuje szerokie pasy
na dużej części WIDOCZNYCH trzonów; dół jest zasłonięty. Obecny builder daje siedem pasów dopiero od 0,66H
(dla 120 m około 5,83 m na pas). To konkretna różnica do pomiaru i poprawy.
Nie zmieniać wysokości 120 m, średnic ani pozycji bez osobnego źródła.
Kominy różnią się detalami zwieńczenia i stanem malowania; zdjęcie nie uzasadnia
identycznej kosmetyki dla obu. Zimowa fotografia pod słońce nie kalibruje albedo.

Natywne wycinki 073128 są w chimney-photo-details (172x528 i 204x808,
SHA źródła w source.json). Lewy komin ma trzy osobne wyloty na głowicy;
prawy jeden duży wylot i inny układ galerii/zużycia. Obecny wspólny builder
tego nie odwzorowuje. Nie oceniać detalu z samej miniatury 960x540.
Najpierw jednak potwierdzić tożsamość: overrides podają w628899553 i w628899554
(120 m, średnice przy podstawie z OSM), a ich notatka wspomina inne zdjęcie
CC BY-SA EC_Białystok z szachownicą na jednym zwieńczeniu. Na 073128 szachownicy
nie widać. Odszukano oryginalną referencję Hiuppo (podgląd EC-Bialystok-Hiuppo-reference.jpg,
licencja CC BY-SA 2.5, source JSON z atrybucją). Jej EXIF DateTime (306) podaje
2007:03:06 09:06:38. Zdjęcie pokazuje szachownicę na lewej głowicy i gęstsze pasy
tylko u góry prawego. W CC0 z 2020 obie głowice mają pasy na większym WIDOCZNYM
odcinku, lewa trzy wyloty i prawa jeden. Porównanie sugeruje zmianę malowania
tych samych kominów, lecz wymaga przypisania przestrzennego. Nie przenosić stanu
szachownicy z 2007 bez sprawdzenia aktualniejszych referencji ani nie zgadywać
procentu wysokości na podstawie zasłoniętego dołu.

Własność: `landmarks.py` rejestruje nazwy i wymiary w LP.LANDMARKS. Sam builder
`chimney()` znajduje się w cudzym life_props.py; jego pliku nie edytować.
Mesh.tube zapisuje UV0.y od zera osobno dla każdego odcinka, więc proste użycie
istniejącego _STRIPES nie przeniesie ciągłego malowania na cały trzon.
Nie stosować monkey patchingu funkcji life ani hacków w typach wysokości.

Lepsza możliwość po sprawdzeniu istniejącego przepływu: własne GLB w
art-source/world/landmarks, unikalne nazwy landmark_ec_chimney_*, rejestracja
przez rozszerzenie hero_building.plan za osobną konfiguracją EC. Istniejący
InstanceImporter już automatycznie skanuje te biblioteki; nazwa landmark_ ma
domyślnie te same odległości 650/20000 m jak stare kominy. Generyczne HB.apply
zwraca tris do st.hero_tris i światowego estymatora, więc nie potrzeba zmian
w roads/build_world.py, stage.py, props.py ani life_props.py. Własny rekord musi
mieć buildings=[], ground z pustymi fence/gate/thuja/flagpoles oraz meta/spec SHA.
landmarks.py powinien pomijać stary LP model TYLKO przy zweryfikowanym własnym
zasobie; brak/stale ma zachować poprzedni model i czytelny raport. Zachować
zakotwiczenie z obecnej instancji, wysokość/średnice z niezmienianego override.
To pozwala poprawić pasy i głowice geometrią bez nowego shadera. Sprawdzić
kontrakty wszystkich testów HB/landmarks i zderzenie nazw przed implementacją.

Alternatywny wariant zgodny ze wspólnymi plikami: addytywna flaga materiału i wariant
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

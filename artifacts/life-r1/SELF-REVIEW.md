# Oględziny autora — life r1

Obejrzano 28 plansz before/after: 19 wybranych kamer osobówek w czterech warunkach, w tym zbliżenia kół, biały kombi, czarny hatchback, cztery odziedziczone kontrole rozkładu brudu, tył auta i widoki rzędów. Plansze mają maksymalnie 960×780 px. To ocena autora; nowa niezależna recenzja tej rundy pozostaje po stronie integratora.

Korekta Pearl usuwa niebieskawy odcień czarnego lakieru. Zmiana usuwa dawny równy beżowy pas na progach i zastępuje go miękkim nalotem. W tych porównaniach nie ma oderwanych ciemnych plam w środku drzwi. Kurz jest jednak nadal zbyt subtelny i gładki; nie jest pełnym odwzorowaniem listopadowego brudu ze zdjęć. Czerń w słońcu pozostaje szarawa, felgi płaskie, a białe powierzchnie w clear bardzo jasne.

Tablice na bliskich ujęciach zmieniają się zależnie od instancji. Importer włączył 54 podsiatki tablic LOD0/LOD1, a materiał zachował dokładny SHA po czterech sesjach renderowania. Nie jest to dowód globalnej unikalności tablic: nadal używany jest atlas 27 pól. Nazwy g_dirt_level_* pochodzą z poprzedniego dowodu GPU; w r1 nie wykonano nowego odczytu GPU poziomów całej floty.

r10b_black_45 pokazuje ścianę i nie nadaje się do oceny auta. g_current_black_lod_20/45 częściowo zasłaniają inne pojazdy. Widoki rzędów z 20 m pokazują ogólny wygląd floty, ale nie zastępują zbliżeń. Pełne rozliczenie wszystkich 92 kamer znajduje się w all-camera-budget.json; nie pominięto tych kadrów w liczbach.

Low: łączna delta draws od -24 do 0, delta łącznych trisK od -2 do 0. High: draws od -40 do 0, trisK od -3 do 0. Żadna z 59 kontroli trasy w żadnym warunku nie przekracza limitu. Są to zaokrąglone szacunki CPU SceneStats przed batchingiem, bez pomiaru czasu GPU telefonu.

Pary refs/photo-render-black.jpg i photo-render-white.jpg służą porównaniu materiału i kierunku obserwacji; pokazują inną lokalizację i pogodę, nie geodezyjne dopasowanie kadru 1:1 ani kalibrację albedo. Źródła istniejących zdjęć i SHA wskazuje refs/provenance.json. Arkusz refs/r4-reference-review.jpg zawiera szerszy kontekst.

EditMode: 274/274, 0 błędów i 0 pominiętych. Końcowe pełne GIS jest jeszcze do wykonania pod heavy. Nie wykonano pomiaru A16 ani nowego niezależnego odbioru wizualnego.

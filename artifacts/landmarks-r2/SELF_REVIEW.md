# Samokontrola rundy r2

Źródła i walidacja końcowa zakończone. Nie jest to niezależna akceptacja bramki 3.
Obejrzano wszystkie 32 arkusze po 58 kamer w czterech kombinacjach (232 pary),
oraz natywne wycinki filarów i parę ze zdjęciem 7204. Pary mają szerokość 960 px.

Schody przecinające ekran zniknęły. Boki ścian oporowych pozostały bez zmian.
Szare pionowe fazy i cieplejsza ochra odpowiadają kierunkowi obserwacji zdjęcia.
Pomalowane płaszczyzny mają mniej jednolitą powierzchnię i zabrudzony dół.
Zacieki teksturowe są delikatne, nie odpowiadają jeszcze dokładnie każdej podporze.
Nie podnoszono proceduralnego szumu do sd mieszanego ROI z recenzji.

Pełny Low: 116 porównań, maks. delta mesh draws 0, instance draws 0; szacowana
suma tris od -0,4202% do 0%. To SceneStats przed SRP, nie pomiar GPU A16.
116 spośród 232 PNG ma identyczne piksele. Różnice dotyczą wiaduktu i drobnych
niestabilności renderowania; oględziny nie wykazały regresji remizy ani scen trasy.

ROI ochry Low-overcast: 84/79/47 -> 85/71/41, sd Y 3,377 -> 4,880.
ROI u dołu: Y 63,114 -> 54,746, stosunek dół/góra 0,812 -> 0,762.
W clear dół jest oświetlony inaczej niż środkowa płaszczyzna i pozostaje jaśniejszy;
nie przedstawia się tego jako identycznego kontrastu zabrudzenia w obu światłach.
Pomiary są sRGB z obrazu, nie pomiarem reflektancji materiału.

Poza zdjęcia nadal UNVERIFIED. GPS i ogniskowa oraz wybór kierunku 295 stopni
dają przybliżone porównanie; geometria ekranów przy jezdni różni się od zdjęcia
i należy do Claude. Nie korygowano dróg, ekranów, kapy ani barier dla poprawy kadru.
Wymiary konstrukcyjne, spód i czyste oczepy pozostają WORKING_VALUE / otwarte P2.

Budżet jest spełniony na wszystkich kamerach. Koszt dodatkowych próbek istniejącego
PBR na A16 pozostaje UNVERIFIED bez telefonu. Nie zmieniono shaderów ani QualityProfile.
World Surface i World PBR mają ten sam zestaw LightMode: UniversalForward,
ShadowCaster, DepthOnly. Mapy są istniejące, bez nowego build_all dla filarów.

Testy: pojedynczy plik 14/14, pełny GIS 585 zaliczonych i 1 oczekiwana porażka,
EditMode 295/295. Physics/gate3: 47 zaliczonych i znana porażka odtwarzania
top_speed_flat_comb.json. Jej wejścia są niezmienione względem początku rundy;
nie poprawiano ich w sesji landmarks. Cache 64 High + 64 Low + 64 instancje
zweryfikowano przed i po testach, manifest i własne źródła nie zmieniły się.

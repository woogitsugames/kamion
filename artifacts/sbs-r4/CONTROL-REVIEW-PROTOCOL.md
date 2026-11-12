# Kryteria przeglądu kontrolowanych prób r4

Plan obejmuje 15 prób, ale liczba renderów zależy od znalezienia jednoznacznej widocznej jezdni. Odrzucenia pozostają w planie. Każda kamera jest C. Kontrole przenoszą wcześniejszy przepis XY, yaw i FOV na świeży świat, z ponownym osadzeniem nominalnego oka na widocznej powierzchni. Nie są dokładnym odtworzeniem pikseli r3. Delta przesunięcia w nagłówku jest liczona od tej kontroli, nie od produkcyjnej kamery.

Ocenę zaczynamy od pełnego natywnego zdjęcia porównawczego i renderu. „Natywne” oznacza tu plik porównawczy w jego własnej rozdzielczości, także po wcześniej zapisanej rektyfikacji SfM; nie oznacza nieprzekształconego oryginału aparatu. Oryginał i zdjęcie porównawcze mają odrębne SHA w referencjach. Arkusz 960 px służy orientacji. Przybliżone regiony zapisane poniżej pochodzą z ręcznego przeglądu r3, są WORKING_VALUE i nie stanowią punktów kalibracyjnych ani automatycznego testu. Trzeba porównać stałe elementy świata; ruchome samochody i sam histogram nie kwalifikują pozy.

Sprawdzono optykę zapisaną w migawce r4. Wszystkie sześć źródeł ma intrinsics SfM i rektyfikację; FOV nie jest wspólną dowolną wartością 70°. Poniższe wartości są odczytem istniejących danych, nie nowym pomiarem lub zatwierdzeniem SfM. Roll, GPS i dokładność estymacji nadal pozostają niezweryfikowane. Próby zachowują FOV zgodny z zapisanym obrazem porównawczym.

| Źródła | Model źródła | Focal obrazu po rektyfikacji | Pionowy FOV renderu |
|---|---|---:|---:|
| 275528, 837235 | fisheye | 0,5 | 58,71551° |
| 328135, 297817 | perspective | 0,9388413792 | 43,54635° |
| 180137 | perspective | 0,5 | 58,71551° |
| 494288 | perspective | 1,3087019493 | 31,97862° |

Pełne ID, parametry i SHA źródeł zachowuje six-pose-optics-preflight.json. Zmiana samego renderowego FOV bez zgodnej zmiany rektyfikacji zdjęcia nie jest poprawną kalibracją.

| Zdjęcie | Kontrola i zmienna | Dwie niezależne obserwacje wymagane przed zmianą produkcyjnej pozy |
|---|---|---|
| 275528 | Przepis r3 nr04; następnie +1 m po osi spojrzenia i h=0,55 | Zbieg krawędzi jezdni oraz oba zewnętrzne piony portalu. R3 wariant02 lepiej trafiał w zbieg, wariant04 w skalę portalu; nowa próba musi poprawić zgodność obu, bez dopasowania do zbyt niskich znaków. |
| 837235 | Wyłącznie kontrola przepisu nr12 | Portal oraz rzeczywisty nos wyspy. U-3 może mieć własny błąd geometrii lub osadzenia; nie wolno nim samotnie uzasadniać przesunięcia kamery. |
| 328135 | Przepis nr21, stałe XY; h=0,74 i 0,77 | Zbieg krawędzi jezdni i położenie obu stron portalu. Poprawa pionowa nie zamyka poziomego przesunięcia portalu. |
| 297817 | Przepis nr26, stałe XY; h=0,74 i 0,77 | Zbieg jezdni i rozdzielenie prawej odnogi. Rytm drzew oceniać dopiero po rozstrzygnięciu pozy. |
| 180137 | Produkcyjne XY, h kontrolne oraz 0,54/0,57 | Zbieg jezdni i trwałe elementy ekranu lub słupa. Zdjęcie 1280×720: region zbiegu około x725–785/y375–410, raw r3 x705–775/y435–470. Nie traktować granic regionów jako dokładnych współrzędnych. |
| 494288 | Produkcyjne XY, h kontrolne oraz 0,72/0,75 | Zbieg jezdni i górna krawędź prawego ekranu. Zdjęcie 1280×960: zbieg około x250–335/y690–725, raw r3 x245–325/y625–665. Góra ekranu na zdjęciu około y280–315, raw r3 y400–435. Zmiana pitch może poprawić jedno i pogorszyć drugie; to przesłanka do rozdzielenia błędu pozy i świata, nie do awansu kamery. |

Przed oceną sprawdzić SHA zdjęć, raw, planu, kamery, świata i materiałów oraz kompletność rosteru. Wynik „wygląda bliżej” zapisujemy oddzielnie od decyzji o produkcyjnej pozie. Awans wymaga niezależnego przeglądu dwóch trwałych kotwic, bez jednoczesnej korekty świata. Jeśli żadna próba nie spełni warunku, pozostaje C i jawny opis nierozstrzygniętej przyczyny.

Źródła historycznych obserwacji: artifacts/sbs-r3/275528-ANCHOR-REVIEW.md, ROAD-PROJECTION-NOTES.md, BRIDGE-POSE-NOTES.md i REVIEW-REFINEMENT1.md. Świeże wyniki r4 nie zostały jeszcze ocenione.

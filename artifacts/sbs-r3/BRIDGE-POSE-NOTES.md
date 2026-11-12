# Kamery 494288 i 180137 — ograniczenia następnych prób

494288 ma kurs siatki 309,3705 stopnia, pochodzący ze SfM (computed_compass_angle 312,6955 przed konwersją). Najbliższy właściwy źródłowy odcinek wiaduktu ma oś około 306,99 stopnia, a nie kierunek sąsiedniej kamery 180137. Graf nie dowodzi błędu kursu o kilkadziesiąt stopni. Nie przenosić kierunku 180137 na 494288.

Po poprawieniu projekcji na odcinek: 494288 leży około 1,69 m od najbliższej osi bridge=viaduct i około 6,09 m od najbliższego odcinka naziemnego ronda. To odległość od źródłowej osi, nie od wygenerowanej krawędzi pasa. Obejrzano wcześniejszy r2/pose-topology/putry-camera-topology.png: pokazuje różne poziomy i kierunki, nie powierzchnie jezdni. Sprawdzić położenie wzdłuż pomostu i małe warianty kursu, zachowując kontrolę wysokości nad rzeczywistą nawierzchnią.

Historyczny deck-ray-heights.json z main zapisuje trafienie przy pozy 494288 w U140,1883 m oraz brak trafienia przy oryginalnym GPS około (-516,18;0,48). Nie ma tu związania tego dawnego pomiaru z nowym światem r3: traktować jako wskazówkę do ponownego sprawdzenia, nie aktualny raycast. Produkcyjne U141,888 to nominalne 1,7 m nad dawnym trafieniem. NMT jest gruntem pod mostem i nie zastępuje pokładu.

180137 ma kurs353,0641, a najbliższy naziemny odcinek ma oś około 349,80 stopnia i odległość około 1,07 m. Historyczny ray przy jej pozy miał U135,4138 m. Nie obejmować tej kamery ślepym założeniem stałego poziomu wiaduktu 494288; rozstrzygnąć powierzchnię przy ewentualnym przesunięciu. Dotychczasowa recenzja sugeruje +15–20 m, nadal hipoteza.

bridge-topology.json zawiera SHA źródłowego grafu i najbliższe segmenty. historical-deck-ray-heights.json zachowuje bajty starej wskazówki. Nie zmieniono produkcyjnych kamer, wysokości, FOV ani świata. Pierwsza partia gantry-probes nadal dotyczy wyłącznie czterech kamer naziemnych, bez tych dwóch.

Uwaga do korekty topologii: pierwotne pomocnicze obliczenie PowerShell mogło zaokrąglać parametr projekcji do końca odcinka przez wybór przeciążenia Math.Min. inspect-road-topology.ps1 używa double i jawnego ograniczania zakresu; sanity 0,25/3 m przeszedł. Nowy bridge-topology.json zastępuje dawne odległości. Żadna produkcyjna poza ani 18 renderów nie korzystały z tej pomocniczej projekcji.


## Natywna kontrola dwóch kotwic, około 11:28

Własny i niezależny przegląd czterech natywnych obrazów potwierdził przeciwne kierunki potrzebnej zmiany pionowej. Dla 494288 na zdjęciu dalsza jezdnia mieści się orientacyjnie w x250–335/y690–725 (1280×960), a w raw x245–325/y625–665. Obie drogi skręcają w lewo; nie uzasadnia to dużej zmiany yaw. Góra ekranu przy prawym brzegu jest na zdjęciu około y280–315, w raw y400–435. Pitch przesuwający jezdnię w dół przesunie ekran również w dół, więc nie zamknie obu rozbieżności. Wymiary i boczna odległość ekranu oraz poziom kamery wymagają rozdzielenia od pitch.

Dla 180137 zdjęcie daje pasmo x725–785/y375–410, a raw x705–775/y435–470 (1280×720): droga powinna przesunąć się w górę. Odczyty dotyczą dalszych fragmentów zakrzywionej jezdni, nie ścisłego punktu zbiegu ani pomiaru poziomego horyzontu.

Mała następna seria C w r4, przy stałym XY/yaw/FOV i nominalnym oku: 494288 h=0,72/0,75 oraz kontrolny baseline; 180137 h=0,54/0,57 oraz kontrolny baseline. Niezależny recenzent potwierdził zasadność zakresu diagnostycznego, bez akceptacji pozy. Po odświeżeniu świata zapisać zmianę U i zastosować tę samą nową wysokość do kontroli i wariantów.

Ważne ograniczenie starego próbkowania: baseline 494288 miał trafienie wyłącznie road_collision/collision_asphalt U140,188354; nie było trafienia road/road_asphalt. Dla 180137 trafiono oba: road_asphalt U135,413810 i collision_asphalt U135,413445. Nie należy nazywać pierwszego wyniku pomiarem widocznego asfaltu. Lekki odczyt samego JSON GLB chunk_1_3 wykazał w road materiały road_asphalt, road_gravel, road_paving oraz materiały poboczy/kerbów, ale nie road_asphalt_new. To nie rozstrzyga materiału pod dokładnym XY. Następny raycast powinien sklasyfikować wszystkie powierzchnie widoczne i kolizyjne osobno; przy braku potwierdzonej jezdni nie wybierać ślepo kolizji ani NMT.

SHA obrazów i pełne przedziały są w bridge-native-anchor-regions.json. Nie zmieniono żadnej kamery produkcyjnej, świata ani stanu testowanego r3.

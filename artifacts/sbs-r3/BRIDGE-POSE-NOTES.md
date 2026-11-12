# Kamery 494288 i 180137 — ograniczenia następnych prób

494288 ma kurs siatki 309,3705 stopnia, pochodzący ze SfM (computed_compass_angle 312,6955 przed konwersją). Najbliższe źródłowe odcinki wiaduktu mają osie około 304–307 stopni, a nie kierunek sąsiedniej kamery 180137. Graf nie dowodzi błędu kursu o kilkadziesiąt stopni. Nie przenosić kierunku 180137 na 494288.

494288 leży 15–16 m od osi najbliższych odcinków bridge=viaduct i około 7,4 m od naziemnego grafu ronda. To odległość od źródłowej osi, nie od wygenerowanej krawędzi pasa. Obejrzano wcześniejszy r2/pose-topology/putry-camera-topology.png: pokazuje różne poziomy i kierunki, nie powierzchnie jezdni. Sprawdzić położenie wzdłuż pomostu i małe warianty kursu, zachowując kontrolę wysokości nad rzeczywistą nawierzchnią.

Historyczny deck-ray-heights.json z main zapisuje trafienie przy pozy 494288 w U140,1883 m oraz brak trafienia przy oryginalnym GPS około (-516,18;0,48). Nie ma tu związania tego dawnego pomiaru z nowym światem r3: traktować jako wskazówkę do ponownego sprawdzenia, nie aktualny raycast. Produkcyjne U141,888 to nominalne 1,7 m nad dawnym trafieniem. NMT jest gruntem pod mostem i nie zastępuje pokładu.

180137 ma kurs353,0641, a pobliskie naziemne segmenty osi obejmują około346,85–359,45. Historyczny ray przy jej pozy miał U135,4138 m. Nie obejmować tej kamery ślepym założeniem stałego poziomu wiaduktu 494288; rozstrzygnąć powierzchnię przy ewentualnym przesunięciu. Dotychczasowa recenzja sugeruje +15–20 m, nadal hipoteza.

bridge-topology.json zawiera SHA źródłowego grafu i najbliższe segmenty. historical-deck-ray-heights.json zachowuje bajty starej wskazówki. Nie zmieniono produkcyjnych kamer, wysokości, FOV ani świata. Pierwsza partia gantry-probes nadal dotyczy wyłącznie czterech kamer naziemnych, bez tych dwóch.

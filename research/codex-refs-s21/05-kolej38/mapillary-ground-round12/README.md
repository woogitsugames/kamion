# LK38 — trzy nowe punkty przejazdowe, bez uzyskanych kadrów naziemnych

Odczyt 2026-11-16; dokładnej godziny nie zmierzono. Cel: para realnych widoków nawierzchni przejazdu i urządzeń poza wcześniejszymi trzema punktami Fast i dwoma zdjęciami DW671. Wynik ograniczonego obiegu: **3 sprawdzone nowe punkty mapy, 0 indywidualnie obejrzanych fotografii, 0 pobrań**. Manifest fotografii pozostaje nagłówkiem.

Selekcja pochodzi z istniejącego pliku `Data/raw/osm/podlaskie-261108.osm.pbf`, odczytanego read-only przez pyosmium. Źródło i wcześniejszy hash pliku są zapisane w `../../06-region-ring/data/osm-source.json`: Geofabrik/OpenStreetMap, ODbL 1.0, snapshot 2026-11-08. Nie wykonano nowego zapytania OSM/Overpass ani Mapillary API. Odczyt lokalnego pliku nie aktualizuje stanu źródła.

| Węzeł OSM — dane lokalnego PBF | Literalny tag `ref` | Współrzędne węzła do wyboru mapy | Wynik publicznego UI |
|---|---|---|---|
| 1778182465 | 038 023 994 | 53.2506213, 22.9252354 | Droga i tor przecinają się na podkładzie; brak widocznej sekwencji przez przecięcie w sprawdzonym widoku. |
| 2335163874 | 038 019 441 | 53.2151315, 22.9496047 | Przecięcie drogi i toru obok zabudowy na mapie; brak widocznej sekwencji w sprawdzonym widoku. |
| 1778182447 | 038 017 657 | 53.2043969, 22.9693368 | Przecięcie toru i drogi z etykietą Brzozowa; brak widocznej sekwencji, także po rozszerzeniu widoku. |

**SOURCED [lokalny PBF]:** wszystkie trzy mają `railway=level_crossing` i `source:ref=#ŻółtaNaklejkaPLK`. To atrybucja tagu w OSM, nie osobisty odczyt naklejki, pomiar kilometrażu ani formalny dokument PLK. Nie wyprowadzono z numerów dat, kategorii lub wyposażenia.

Podkład **OpenStreetMap** i **All captures** sprawdzono w otwartym menu warstw pierwszego punktu; dalsze punkty otwarto w tej samej sesji z OSM. Nie użyto Google, API, ukrytego stanu ani tokenów. Ponieważ nie otwarto fotografii, nie zapisano autora, daty obrazu, kierunku ani GPS aparatu. Współrzędne powyżej są lokalizacją węzłów OSM, **nie kamer**.

**UNVERIFIED:** rzeczywista nawierzchnia między szynami, rogatki, sygnalizacja, krzyże G-3/G-4, słupy, elektryfikacja z obrazu, kategoria A–D i stan 2026. Brak widocznej sekwencji w tych widokach nie dowodzi braku fotografii w całym Mapillary ani braku wyposażenia w terenie. Nie utworzono nowej referencji wizualnej i nie zastąpiono nią wcześniejszych kadrów.

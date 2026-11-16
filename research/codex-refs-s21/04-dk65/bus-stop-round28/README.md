# Ełcka — kontrola punktu przystankowego, runda 28

Kontrola źródłowa i wizualna z 2026-11-16. Cel: nowy przystanek lub zatoka w korytarzu K1 Białystok → Knyszyn, poza wcześniej zebranymi punktami. Wynik: **2 indywidualnie obejrzane historyczne fotografie, 0 nowych kwalifikowanych referencji przystanku, 0 pobrań, 0 AUX**. Manifest zawiera wyłącznie wpis dokumentacyjny; obrazy pozostają linkami w dzienniku kontroli.

SOURCED [lokalny `research/dk65-knyszyn-refs/data/osm_corridor.json`]: wybrano OSM node **14067837808**, `public_transport=platform`, 53.2179555, 23.01845; K1 km **15,314**, strona R. To odległość wzdłuż wariantu A lokalnej trasy, nie kilometraż państwowy DK65. Lokalny plik podaje `queried_at=2026-11-15T10:17:47Z`. Węzeł nie zawiera nazwy ani informacji o wiacie. Brak tagu nie dowodzi braku wyposażenia.

W normalnym UI Mapillary wybrano i wizualnie potwierdzono podkład **OpenStreetMap** oraz **All captures**. Otwarto punkt przy Ełckiej, następnie strzałkę zmiany kierunku. Dwa różne pKey mają różne daty i autorów; nie są obrotem tego samego zdjęcia. Współrzędne widoku mapy nie są współrzędnymi kamery. Nie odczytano kierunku geograficznego ani magnetycznego.

- **542797913772543 — szurek for Here, 10.08.2017**: asfaltowa droga, białe linie krawędziowe przerywane, wąskie szare pobocze i trawa; po prawej ogrodzenie, tablica handlowa i słup. W dalszej części zielona tablica miejscowości. W tym kadrze nie potwierdzono wiaty, słupka D-15 ani geometrii zatoki. Panel Time travel zgłosił brak kompatybilnych kadrów.
- **138750054907318 — picturehoover, 27.06.2020**: przeciwne ujęcie prostej drogi z białą linią przerywaną osi i krawędzi, ziarnistym poboczem oraz szpalerem drzew. Po prawej w oddali mała niebieska tablica i lokalna zmiana przebiegu krawędzi. **UNVERIFIED**: symbol tablicy, jej nazwa i funkcja; sama widoczna geometria nie wystarcza do pewnego rozpoznania zatoki autobusowej. Nie przypisano urządzenia do konkretnego węzła OSM z dokładnością terenową.

Daty pochodzą z widocznego UI. To stan z 2017 i 2020, nie potwierdzenie stanu w 2026. Brak pewnej identyfikacji w tych dwóch kadrach nie dowodzi nieistnienia przystanku. Nie otwierano dalszych punktów ani wariantów źródeł. Nie zapisano zdjęć ani screenshotów na dysku.

Dedup obu pKey w K1 i całym `04-dk65` przed zapisem: brak wcześniejszych trafień. Oddzielono je od znanych 214528376891610, 944123099745305, 1452388251821206, 766258954039908 oraz PKS Knyszyn z rundy 22.

Zastosowanie: dziennik granic dowodowych. Nie tworzyć modelu wiaty, nazwy przystanku ani zatoki na podstawie tych kadrów. Następny użyteczny krok to źródłowa fotografia wyposażenia tego punktu, bez wnioskowania z samego tagu OSM.

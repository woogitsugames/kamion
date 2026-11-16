# Typologia Rynku w Knyszynie — WIP

## Zakres i znaczenie oznaczeń

Inwentarz obejmuje wszystkie obrysy budynków, które przecinają bufor 25 m od sześciu odcinków osi drogi o nazwie `Rynek` w `Data/Regions/knyszyn/roads.graph.json` (OSM, EPSG:2180), oraz trzy obrysy landmarków: urząd, ośrodek kultury i kościół. Bufor to WORKING_VALUE stosowany do wyszukania kandydatów, nie urzędowa granica pierzei; obejmuje także obiekty zaplecza i wymaga sprawdzenia z ortofotomapą. Kryterium: przecięcie całego obrysu z buforem; odległość w tabeli mierzona do osi. Nazwa drogi i geometria dróg są SOURCED jako dane OSM, nie potwierdzają tożsamości każdego budynku. Zestaw nie dowodzi, że każdy budynek istotny widokowo poza buforem został zidentyfikowany.

SOURCED oznacza pochodzenie z wymienionego zbioru, nie geodezyjną gwarancję stanu aktualnego. ESTIMATED oznacza interpretację ortofoto lub zdjęcia. WORKING_VALUE oznacza wartość generatora, domyślną albo przybliżenie robocze. OPEN oznacza brak ustalenia. Wysokości LoD1 są względem gruntu; wysokość wyliczona z kondygnacji i wartość domyślna nie są pomiarem. Materiały elewacji i dachu opisują obecny generator, nie potwierdzoną cechę rzeczywistej fasady. Rytm okien nie został ustalony indywidualnie dla standardowych budynków.

Źródła: `buildings.geojson` (obrysy BDOT10k/OSM i atrybuty GUGiK), `roads.graph.json`, `overrides.yaml` (dachy), `tools/worldgen/streetscape/buildings_mesh.py` (typ i paleta), `knyszyn_church_0227.py`, `knyszyn_townhall_0227.py`, lokalne zdjęcia właściciela 1–8 i ortofoto GUGiK. Zdjęcia wyłącznie jako referencja, bez użycia jako tekstur.

Wybrano 53 obrysy według bufora i landmarków oraz zachowano 4 obrysy z poprzedniego inwentarza (do 85 m od fontanny), razem 57; lista kandydatów do zatwierdzenia wizualnego.

| ID obrysu | Oś Rynek m | Geometria / typ | Wysokość | Dach | Fasada | Okna |
|---|---:|---|---|---|---|---|
| `bdot:2002917F-4817-5C99-E053-CC2BA8C01CFC` | 5.6 | SOURCED BDOT10k; typ office WORKING_VALUE | SOURCED 11.94 m (gugik_lod1_2024) | ESTIMATED czerwony z lukarnami; geometria WORKING_VALUE | ESTIMATED jasna, portyk czterokolumnowy; detal WORKING_VALUE | ESTIMATED dwupoziomowa loggia; osie i rytm WORKING_VALUE |
| `bdot:2002917F-3002-5C99-E053-CC2BA8C01CFC` | 5.7 | SOURCED BDOT10k; typ house WORKING_VALUE | SOURCED 7.5 m (gugik_lod1_2024) | ESTIMATED kolor wg override; pokrycie OPEN; generator `roof_metal_graphite` | WORKING_VALUE `plaster_beige`; kolor rzeczywisty OPEN | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-3031-5C99-E053-CC2BA8C01CFC` | 6.4 | SOURCED BDOT10k; typ house WORKING_VALUE | SOURCED 5.98 m (gugik_lod1_2024) | WORKING_VALUE `roof_tiles_brown`; forma OPEN | WORKING_VALUE `plaster_grey`; kolor rzeczywisty OPEN | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:5ef114da-f384-4729-a796-a1dedcde6ca0` | 7.6 | SOURCED BDOT10k; typ house WORKING_VALUE | SOURCED 5.22 m (gugik_lod1_2024) | WORKING_VALUE `roof_tiles_brown`; forma OPEN | WORKING_VALUE `plaster_cream`; kolor rzeczywisty OPEN | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-2FCB-5C99-E053-CC2BA8C01CFC` | 7.8 | SOURCED BDOT10k; typ house WORKING_VALUE | SOURCED 7.69 m (gugik_lod1_2024) | WORKING_VALUE `roof_tiles_brown`; forma OPEN | WORKING_VALUE `plaster_beige`; kolor rzeczywisty OPEN | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-46DC-5C99-E053-CC2BA8C01CFC` | 7.9 | SOURCED BDOT10k; typ office WORKING_VALUE | SOURCED 12.35 m (gugik_lod1_2024) | ESTIMATED czerwony czterospadowy z lukarnami; geometria WORKING_VALUE | ESTIMATED biała, żółte opaski; detal WORKING_VALUE | ESTIMATED dwie kondygnacje; osie i rytm WORKING_VALUE |
| `bdot:2002917F-8DCB-5C99-E053-CC2BA8C01CFC` | 8.4 | SOURCED BDOT10k; typ house WORKING_VALUE | SOURCED 6.77 m (gugik_lod1_2024) | WORKING_VALUE `roof_tiles_red`; forma OPEN | WORKING_VALUE `plaster_cream`; kolor rzeczywisty OPEN | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-3066-5C99-E053-CC2BA8C01CFC` | 8.5 | SOURCED BDOT10k; typ house WORKING_VALUE | SOURCED 6.77 m (gugik_lod1_2024) | ESTIMATED kolor wg override; pokrycie OPEN; generator `roof_tiles_red` | WORKING_VALUE `plaster_cream`; kolor rzeczywisty OPEN | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-2DA9-5C99-E053-CC2BA8C01CFC` | 8.7 | SOURCED BDOT10k; typ house WORKING_VALUE | SOURCED 7.35 m (gugik_lod1_2024) | WORKING_VALUE `roof_tiles_red`; forma OPEN | WORKING_VALUE `plaster_grey`; kolor rzeczywisty OPEN | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-8DCC-5C99-E053-CC2BA8C01CFC` | 8.8 | SOURCED BDOT10k; typ office WORKING_VALUE | SOURCED 8.2 m (gugik_lod1_2024) | OPEN forma i materiał; reguła generatora | OPEN kolor i materiał; reguła generatora | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-AB81-5C99-E053-CC2BA8C01CFC` | 9.0 | SOURCED BDOT10k; typ office WORKING_VALUE | SOURCED 8.85 m (gugik_lod1_2024) | OPEN forma i materiał; reguła generatora | OPEN kolor i materiał; reguła generatora | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-2E0C-5C99-E053-CC2BA8C01CFC` | 9.1 | SOURCED BDOT10k; typ house WORKING_VALUE | SOURCED 6.65 m (gugik_lod1_2024) | WORKING_VALUE `roof_metal_graphite`; forma OPEN | WORKING_VALUE `plaster_beige`; kolor rzeczywisty OPEN | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-2E17-5C99-E053-CC2BA8C01CFC` | 9.3 | SOURCED BDOT10k; typ house WORKING_VALUE | SOURCED 8.17 m (gugik_lod1_2024) | WORKING_VALUE `roof_tiles_brown`; forma OPEN | WORKING_VALUE `plaster_light`; kolor rzeczywisty OPEN | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-2EB9-5C99-E053-CC2BA8C01CFC` | 9.8 | SOURCED BDOT10k; typ house WORKING_VALUE | SOURCED 6.85 m (gugik_lod1_2024) | WORKING_VALUE `roof_tiles_red`; forma OPEN | WORKING_VALUE `plaster_cream`; kolor rzeczywisty OPEN | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-2D30-5C99-E053-CC2BA8C01CFC` | 9.9 | SOURCED BDOT10k; typ house WORKING_VALUE | SOURCED 7.79 m (gugik_lod1_2024) | WORKING_VALUE `roof_tiles_brown`; forma OPEN | WORKING_VALUE `plaster_light`; kolor rzeczywisty OPEN | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-2E85-5C99-E053-CC2BA8C01CFC` | 9.9 | SOURCED BDOT10k; typ house WORKING_VALUE | SOURCED 8.2 m (gugik_lod1_2024) | WORKING_VALUE `roof_metal_graphite`; forma OPEN | WORKING_VALUE `plaster_beige`; kolor rzeczywisty OPEN | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-468F-5C99-E053-CC2BA8C01CFC` | 10.5 | SOURCED BDOT10k; typ office WORKING_VALUE | SOURCED 9.64 m (gugik_lod1_2024) | OPEN forma i materiał; reguła generatora | OPEN kolor i materiał; reguła generatora | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-2EED-5C99-E053-CC2BA8C01CFC` | 10.7 | SOURCED BDOT10k; typ house WORKING_VALUE | SOURCED 6.75 m (gugik_lod1_2024) | WORKING_VALUE `roof_tiles_brown`; forma OPEN | WORKING_VALUE `plaster_grey`; kolor rzeczywisty OPEN | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:1cce6b17-099b-49a7-a57d-182081cd6d92` | 10.8 | SOURCED BDOT10k; typ block WORKING_VALUE | WORKING_VALUE 10.0 m (bdot10k_storeys) | OPEN forma i materiał; reguła generatora | OPEN kolor i materiał; reguła generatora | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-465F-5C99-E053-CC2BA8C01CFC` | 10.8 | SOURCED BDOT10k; typ office WORKING_VALUE | SOURCED 5.66 m (gugik_lod1_2024) | OPEN forma i materiał; reguła generatora | OPEN kolor i materiał; reguła generatora | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-468E-5C99-E053-CC2BA8C01CFC` | 11.1 | SOURCED BDOT10k; typ office WORKING_VALUE | SOURCED 9.85 m (gugik_lod1_2024) | OPEN forma i materiał; reguła generatora | OPEN kolor i materiał; reguła generatora | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-3078-5C99-E053-CC2BA8C01CFC` | 11.6 | SOURCED BDOT10k; typ house WORKING_VALUE | SOURCED 6.18 m (gugik_lod1_2024) | ESTIMATED kolor wg override; pokrycie OPEN; generator `roof_metal_graphite` | WORKING_VALUE `plaster_beige`; kolor rzeczywisty OPEN | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-2EEF-5C99-E053-CC2BA8C01CFC` | 11.7 | SOURCED BDOT10k; typ house WORKING_VALUE | SOURCED 5.73 m (gugik_lod1_2024) | WORKING_VALUE `roof_metal_graphite`; forma OPEN | WORKING_VALUE `plaster_beige`; kolor rzeczywisty OPEN | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-2DE1-5C99-E053-CC2BA8C01CFC` | 11.9 | SOURCED BDOT10k; typ house WORKING_VALUE | SOURCED 8.14 m (gugik_lod1_2024) | WORKING_VALUE `roof_metal_graphite`; forma OPEN | WORKING_VALUE `plaster_cream`; kolor rzeczywisty OPEN | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-2E48-5C99-E053-CC2BA8C01CFC` | 12.3 | SOURCED BDOT10k; typ house WORKING_VALUE | SOURCED 8.13 m (gugik_lod1_2024) | WORKING_VALUE `roof_tiles_red`; forma OPEN | WORKING_VALUE `plaster_beige`; kolor rzeczywisty OPEN | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-2EB8-5C99-E053-CC2BA8C01CFC` | 12.3 | SOURCED BDOT10k; typ house WORKING_VALUE | SOURCED 7.95 m (gugik_lod1_2024) | WORKING_VALUE `roof_tiles_red`; forma OPEN | WORKING_VALUE `plaster_grey`; kolor rzeczywisty OPEN | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-306C-5C99-E053-CC2BA8C01CFC` | 12.4 | SOURCED BDOT10k; typ house WORKING_VALUE | SOURCED 6.48 m (gugik_lod1_2024) | WORKING_VALUE `roof_tiles_red`; forma OPEN | WORKING_VALUE `plaster_beige`; kolor rzeczywisty OPEN | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-2DDD-5C99-E053-CC2BA8C01CFC` | 12.4 | SOURCED BDOT10k; typ house WORKING_VALUE | SOURCED 7.75 m (gugik_lod1_2024) | WORKING_VALUE `roof_tiles_red`; forma OPEN | WORKING_VALUE `plaster_light`; kolor rzeczywisty OPEN | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-2E16-5C99-E053-CC2BA8C01CFC` | 12.5 | SOURCED BDOT10k; typ house WORKING_VALUE | SOURCED 9.3 m (gugik_lod1_2024) | ESTIMATED kolor wg override; pokrycie OPEN; generator `roof_tiles_red` | WORKING_VALUE `plaster_grey`; kolor rzeczywisty OPEN | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-4690-5C99-E053-CC2BA8C01CFC` | 12.6 | SOURCED BDOT10k; typ office WORKING_VALUE | SOURCED 6.57 m (gugik_lod1_2024) | OPEN forma i materiał; reguła generatora | OPEN kolor i materiał; reguła generatora | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-3065-5C99-E053-CC2BA8C01CFC` | 12.6 | SOURCED BDOT10k; typ house WORKING_VALUE | SOURCED 6.7 m (gugik_lod1_2024) | WORKING_VALUE `roof_tiles_brown`; forma OPEN | WORKING_VALUE `plaster_cream`; kolor rzeczywisty OPEN | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-3030-5C99-E053-CC2BA8C01CFC` | 13.3 | SOURCED BDOT10k; typ house WORKING_VALUE | SOURCED 6.11 m (gugik_lod1_2024) | WORKING_VALUE `roof_tiles_red`; forma OPEN | WORKING_VALUE `plaster_beige`; kolor rzeczywisty OPEN | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-2E88-5C99-E053-CC2BA8C01CFC` | 13.4 | SOURCED BDOT10k; typ house WORKING_VALUE | SOURCED 5.84 m (gugik_lod1_2024) | WORKING_VALUE `roof_tiles_brown`; forma OPEN | WORKING_VALUE `plaster_cream`; kolor rzeczywisty OPEN | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-2E80-5C99-E053-CC2BA8C01CFC` | 13.8 | SOURCED BDOT10k; typ house WORKING_VALUE | SOURCED 6.68 m (gugik_lod1_2024) | WORKING_VALUE `roof_metal_graphite`; forma OPEN | WORKING_VALUE `plaster_light`; kolor rzeczywisty OPEN | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-3001-5C99-E053-CC2BA8C01CFC` | 14.1 | SOURCED BDOT10k; typ house WORKING_VALUE | SOURCED 8.09 m (gugik_lod1_2024) | WORKING_VALUE `roof_tiles_brown`; forma OPEN | WORKING_VALUE `plaster_grey`; kolor rzeczywisty OPEN | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-3036-5C99-E053-CC2BA8C01CFC` | 15.4 | SOURCED BDOT10k; typ house WORKING_VALUE | SOURCED 8.93 m (gugik_lod1_2024) | WORKING_VALUE `roof_metal_graphite`; forma OPEN | WORKING_VALUE `plaster_light`; kolor rzeczywisty OPEN | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-46DA-5C99-E053-CC2BA8C01CFC` | 15.5 | SOURCED BDOT10k; typ office WORKING_VALUE | SOURCED 10.24 m (gugik_lod1_2024) | OPEN forma i materiał; reguła generatora | OPEN kolor i materiał; reguła generatora | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-303E-5C99-E053-CC2BA8C01CFC` | 15.7 | SOURCED BDOT10k; typ house WORKING_VALUE | SOURCED 6.56 m (gugik_lod1_2024) | WORKING_VALUE `roof_tiles_red`; forma OPEN | WORKING_VALUE `plaster_grey`; kolor rzeczywisty OPEN | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:6a945c1c-3248-4924-88ab-c0867c125b09` | 17.9 | SOURCED BDOT10k; typ house WORKING_VALUE | WORKING_VALUE 4.0 m (bdot10k_storeys) | WORKING_VALUE `roof_metal_graphite`; forma OPEN | WORKING_VALUE `plaster_grey`; kolor rzeczywisty OPEN | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:278392bd-e12f-4439-a72f-d1d5efb74893` | 18.0 | SOURCED BDOT10k; typ house WORKING_VALUE | WORKING_VALUE 4.0 m (bdot10k_storeys) | WORKING_VALUE `roof_metal_graphite`; forma OPEN | WORKING_VALUE `plaster_light`; kolor rzeczywisty OPEN | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-5EC3-5C99-E053-CC2BA8C01CFC` | 19.3 | SOURCED BDOT10k; typ shed WORKING_VALUE | SOURCED 3.73 m (gugik_lod1_2024) | OPEN forma i materiał; reguła generatora | OPEN kolor i materiał; reguła generatora | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-4692-5C99-E053-CC2BA8C01CFC` | 21.0 | SOURCED BDOT10k; typ shed WORKING_VALUE | SOURCED 3.69 m (gugik_lod1_2024) | OPEN forma i materiał; reguła generatora | OPEN kolor i materiał; reguła generatora | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-4660-5C99-E053-CC2BA8C01CFC` | 21.5 | SOURCED BDOT10k; typ shed WORKING_VALUE | SOURCED 4.94 m (gugik_lod1_2024) | OPEN forma i materiał; reguła generatora | OPEN kolor i materiał; reguła generatora | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2014bb16-f457-47db-b915-e18a12bde931` | 22.2 | SOURCED BDOT10k; typ house WORKING_VALUE | WORKING_VALUE 4.0 m (bdot10k_storeys) | WORKING_VALUE `roof_tiles_red`; forma OPEN | WORKING_VALUE `plaster_grey`; kolor rzeczywisty OPEN | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `osm:way/300663247` | 22.6 | SOURCED OSM; typ office WORKING_VALUE | WORKING_VALUE 6.0 m (default) | OPEN forma i materiał; reguła generatora | OPEN kolor i materiał; reguła generatora | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-5AFE-5C99-E053-CC2BA8C01CFC` | 22.8 | SOURCED BDOT10k; typ shed WORKING_VALUE | SOURCED 3.63 m (gugik_lod1_2024) | OPEN forma i materiał; reguła generatora | OPEN kolor i materiał; reguła generatora | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:99d85abc-b635-46d7-b328-207d0f7a9dfa` | 22.9 | SOURCED BDOT10k; typ shed WORKING_VALUE | WORKING_VALUE 4.0 m (bdot10k_storeys) | OPEN forma i materiał; reguła generatora | OPEN kolor i materiał; reguła generatora | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-5D3D-5C99-E053-CC2BA8C01CFC` | 23.2 | SOURCED BDOT10k; typ shed WORKING_VALUE | SOURCED 4.2 m (gugik_lod1_2024) | OPEN forma i materiał; reguła generatora | OPEN kolor i materiał; reguła generatora | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-5C1B-5C99-E053-CC2BA8C01CFC` | 23.4 | SOURCED BDOT10k; typ shed WORKING_VALUE | SOURCED 4.43 m (gugik_lod1_2024) | OPEN forma i materiał; reguła generatora | OPEN kolor i materiał; reguła generatora | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `osm:way/1427273958` | 23.4 | SOURCED OSM; typ office WORKING_VALUE | WORKING_VALUE 6.0 m (default) | OPEN forma i materiał; reguła generatora | OPEN kolor i materiał; reguła generatora | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `osm:way/300660475` | 23.4 | SOURCED OSM; typ office WORKING_VALUE | WORKING_VALUE 6.0 m (default) | OPEN forma i materiał; reguła generatora | OPEN kolor i materiał; reguła generatora | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-307C-5C99-E053-CC2BA8C01CFC` | 24.0 | SOURCED BDOT10k; typ house WORKING_VALUE | SOURCED 5.39 m (gugik_lod1_2024) | WORKING_VALUE `roof_tiles_brown`; forma OPEN | WORKING_VALUE `plaster_light`; kolor rzeczywisty OPEN | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:2002917F-8DAE-5C99-E053-CC2BA8C01CFC` | 34.2 | SOURCED BDOT10k; typ office WORKING_VALUE | SOURCED 14.24 m (gugik_lod1_2024) | ESTIMATED czerwony dach i hełm; proporcje WORKING_VALUE | ESTIMATED biała elewacja | ESTIMATED wysokie łukowe; liczba i rozstaw WORKING_VALUE |

### Obrysy zachowane z poprzedniego zakresu

Te cztery obrysy są poza buforem, lecz mieściły się w dawnym zasięgu 85 m od fontanny.

| ID obrysu | Oś Rynek m | Geometria / typ | Wysokość | Dach | Fasada | Okna |
|---|---:|---|---|---|---|---|
| `bdot:2002917F-465E-5C99-E053-CC2BA8C01CFC` | 27.7 | SOURCED BDOT10k; typ house WORKING_VALUE | SOURCED 7.44 m (gugik_lod1_2024) | WORKING_VALUE `roof_metal_graphite`; forma OPEN | WORKING_VALUE `plaster_light`; kolor rzeczywisty OPEN | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:b8f87351-8cca-4aa6-91a6-3cac0e635290` | 27.9 | SOURCED BDOT10k; typ shed WORKING_VALUE | WORKING_VALUE 4.0 m (bdot10k_storeys) | OPEN forma i materiał; reguła generatora | OPEN kolor i materiał; reguła generatora | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:c34d1055-19ad-404d-a8a1-9f7aa72a359b` | 26.8 | SOURCED BDOT10k; typ shed WORKING_VALUE | SOURCED 2.99 m (gugik_lod1_2024) | OPEN forma i materiał; reguła generatora | OPEN kolor i materiał; reguła generatora | OPEN liczba, rytm i rozmiar; generator proceduralny |
| `bdot:c883a520-e438-40d4-86fa-d30cf00a4dff` | 28.5 | SOURCED BDOT10k; typ shed WORKING_VALUE | SOURCED 4.04 m (gugik_lod1_2024) | OPEN forma i materiał; reguła generatora | OPEN kolor i materiał; reguła generatora | OPEN liczba, rytm i rozmiar; generator proceduralny |

## Park i obiekty Rynku

| Obiekt | Stan, cechy i pochodzenie |
|---|---|
| Skwer i trawnik | SOURCED: `leisure=park` i zdjęcia 3–7; `rynek-park-not-forest-0227` usuwa leśne traktowanie konkretnego poligonu BDOT. Zasięg trawnika i wykluczenia drzew wg `rynek-mown-open-ground-0227`: ESTIMATED; odbiór wizualny OPEN. |
| Alejki i plac centralny | ESTIMATED obrysy `rynek-path-*`, `rynek-central-plaza-0227` z ortofoto i zdjęć; szerokości WORKING_VALUE, materiał `yard_paving` przybliża szarą kostkę. Ustawienie i docelowa powierzchnia OPEN do porównania. |
| Płyta fontanny | ESTIMATED `rynek-fountain-plate-0227`, prostokąt ok. 6,3 × 5,8 m na podstawie ortofoto K1-124; WORKING_VALUE obrzeże 0,15 m i 9 dysz w `knyszyn_fountain_0227.py`. Strumienie i polityka sezonowa OPEN: obecnie stan suchy. |
| Plac pomnika | ESTIMATED `rynek-king-plaza-0227`, ortofoto i zdjęcia; WORKING_VALUE `yard_paving`; wzór czerwonych pasów OPEN. |
| Obelisk | SOURCED punkt OSM `node/3047587676` (760936,66; 612395,45); tożsamość ESTIMATED, wymiary WORKING_VALUE. Model w `knyszyn_park_props_0227.py`; orzeł OPEN, obecnie pominięty. |
| Pomnik króla i blok przed nim | ESTIMATED punkt (760959, 612427), orientacja wg ortofoto i zdjęć 1, 8; sylwetka PROXY_NOT_APPROVED, proporcje i blok WORKING_VALUE. Detale twarzy, korony i tablicy OPEN. |
| Maszt | ESTIMATED punkt (760963, 612424) i wzór wg zdjęcia 8; wymiary WORKING_VALUE. |
| Ławki | ESTIMATED lokalizacje kandydatów i ustawienie wg zdjęć / ortofoto, wymiary WORKING_VALUE; `knyszyn_park_props_0227.py` odrzuca lokalizacje kolidujące z alejkami lub drzewami. Rzeczywistą liczbę po przebudowie podaje `generated/streetscape_qa.json`. |
| Latarnie parkowe | ESTIMATED pozycje i postać wg zdjęć, wysokość WORKING_VALUE; kandydaci jak dla ławek. Emisja dynamiczna OPEN: obecnie brak. |
| Drzewa liściaste | ESTIMATED rozmieszczenie `rynek-park-broadleaf-0227` i `rynek-near-lindens-kit-0227`; dojrzałe lipy według zdjęć 3–7. Rozmiary/model korony WORKING_VALUE, rozpoznawalność lip i wierzba płacząca OPEN. |
| Kosze na śmieci | SOURCED obecność na zdjęciach wg `docs/owner/KNYSZYN-OWNER-FEEDBACK-S21.md`; indywidualne położenia i realizacja w parku OPEN. |
| Pierzeje, szyldy i oznakowanie | ESTIMATED ogólne typy i barwy ze zdjęć właściciela; powiązanie każdej konkretnej elewacji ze zdjęciem, kształt otworów i indywidualne szyldy OPEN. Szyldy bez marek, nazw firm i godeł. |

Stan inwentarza nie jest akceptacją wizualną ani potwierdzeniem budżetu; `generated/streetscape_qa.json` opisuje tylko ostatnią przebudowę, nie gwarantuje jakości widoku.


## Targowica przy Jagiellońskiej — korekta R24

Źródło planu: **SOURCED** ortofoto GUGiK 2025 `83186_1484206_N-34-106-B-b-1-2.tif`, EPSG:2180, rozdzielczość 0,1 m. Cztery obrysy poniżej to ręczny odczyt **ESTIMATED** naroży okapów, w kolejności północno-zachodni, północno-wschodni, południowo-wschodni, południowo-zachodni. Szacowana tolerancja odczytu 0,5–1 m nie obejmuje nieznanego przesunięcia rzutu dachu; współrzędne nie są pomiarem podstaw słupów.

| Wiata | Obrys dachu EPSG:2180 (E, N) w metrach | Typologia |
|---|---|---|
| Północna, oddzielona | (760787.0, 613341.7), (760794.0, 613342.4), (760800.7, 613316.7), (760794.2, 613315.0) | ESTIMATED 27,1 × 6,9 m; czterospadowy dach, WORKING_VALUE wysokości słupów |
| Północna z trójki | (760796.9, 613301.9), (760803.8, 613302.6), (760810.4, 613276.0), (760803.9, 613274.7) | ESTIMATED 27,7 × 6,8 m; czterospadowy dach, WORKING_VALUE szczegółów |
| Środkowa | (760803.8, 613274.3), (760810.5, 613275.1), (760817.3, 613248.3), (760810.8, 613247.0) | ESTIMATED 27,9 × 6,7 m; czterospadowy dach, WORKING_VALUE szczegółów |
| Południowa z panelami | (760810.7, 613246.8), (760817.4, 613247.7), (760824.2, 613221.4), (760817.7, 613219.9) | ESTIMATED 27,5 × 6,7 m; panele widoczne na zdjęciu i ortofoto, WORKING_VALUE rozmieszczenia i wymiarów |

| Obiekt | Źródło i niepewność |
|---|---|
| Długi parterowy budynek | SOURCED obrys `bdot:2002917F-465A-5C99-E053-CC2BA8C01CFC`, wysokości GUGiK LoD1 4,72 m i okap LoD2 4,47 m; identyfikacja ze zdjęciem ESTIMATED, podział fasady i okien WORKING_VALUE. |
| Żółty pawilon | SOURCED obrys `bdot:de62e5a9-3c83-4023-9e77-03b8844df001`; BDOT określa go jako gospodarczy, a identyfikacja żółtego pawilonu ze zdjęcia jest ESTIMATED. Wysokość i detale WORKING_VALUE. |
| Świerk przed budynkiem | SOURCED obecność na zdjęciach i ortofoto; środek korony / kandydat pnia (760803,5; 613217,0) ESTIMATED ±2 m, pień zasłania korona. Wysokość WORKING_VALUE, maski i widoczność wymagają kontroli. |
| Plac i kamera | SOURCED ortofoto i obecność szarej nawierzchni z czerwonymi pasami; ręczny obrys i kamera `market_jagiellonska_qa` ESTIMATED, kadr zdjęcia 14 i granice nawierzchni wymagają weryfikacji. |

Historyczny `OSM way/704368699` dotyczy sąsiedniego placu na północ, nie należy go utożsamiać z rzędem wiat. R24 — wynik generacji, obraz, kolizje i budżet **OPEN**. Fotografie właściciela są wyłącznie lokalną referencją i nie są teksturami.

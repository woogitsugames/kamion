# Licencja danych i atrybucja

## Baza faktograficzna

Kompilacja danych badawczych w `manifest.csv`, `records.json`, `osm_destination.csv`, plikach metadanych, geometrii i audytów jest udostępniana na **Open Database License 1.0 (ODbL)**: https://opendatacommons.org/licenses/odbl/1-0/ .

Atrybucja źródeł: **© OpenStreetMap contributors; Mapillary i autorzy poszczególnych zdjęć wskazani w rekordach; Wikimedia Commons / Rakoon**. Opracowanie faktograficzne dla projektu Kamion, 12.11.2026. Nazwy autorów, linki i daty są zachowane per pozycja. Pozostałe źródła urzędowe i ich autorzy są wskazani w `sources.md`.

Podstawy:

- OpenStreetMap: https://www.openstreetmap.org/copyright — ODbL 1.0; dostęp 12.11.2026.
- Mapillary: https://help.mapillary.com/hc/en-us/articles/115001777705-OpenStreetMap-compatibility — sekcja warunków dotyczących derived metadata; pozwala publikować dane pochodne dla społeczności, jeśli są publicznie dostępne i objęte ODbL. Dostęp 12.11.2026. Baza jest przeznaczona do publicznego katalogu `research/gptpro/3-s8-signs/` w repozytorium Kamion.
- Commons: metadane poszczególnych fotografii Rakoon wskazują CC0; utrwalone w `files/G3-META002.json`.

Nie zmienia to licencji fotografii ani statusu dokumentów źródłowych. ODbL dotyczy kompilacji danych, a nie wizualnej reprodukcji cudzych zdjęć. Pola `licencja` głównego manifestu opisują źródło danej obserwacji, przede wszystkim fotografię, nie zastępują niniejszej informacji o bazie.

## Obrazy i dokumenty

Każdy plik obrazowy ma własną atrybucję i licencję w `asset_manifest.csv`:

- Wycinki Commons: Rakoon, **CC0**.
- Wycinki Mapillary: wymieniony autor, kanoniczny link z image key, **CC BY-SA 4.0**. Modyfikacje: kadrowanie i ewentualne zmniejszenie; szczegóły w rekordzie. MC003 dodatkowo łączy skraje panoramy prostym przesunięciem.
- Mapa zakresu: opracowanie kartograficzne dla Kamion na podstawie bazy ODbL; atrybucja OSM i źródeł geotagów znajduje się na mapie i w `map_notes.md`. Nie zawiera reprodukcji cudzych fotografii.
- `files/G3-L001.pdf`: akt normatywny, materiał urzędowy — art. 4 pkt 1 polskiej ustawy o prawie autorskim.

Dokumentów z niejasnymi prawami do reprodukcji i fotografii NC/ND nie ma w paczce. Linki referencyjne nie są udzieleniem licencji na ich pobranie i wykorzystanie.

## Zalecany zapis atrybucji zdjęcia

`Mapillary [key] — [autor], CC BY-SA 4.0, [kanoniczny URL]. Zmiany: wycinek i zmniejszenie.`

Dla źródeł i współrzędnych zachowaj również `data_dostępu`, `data_zdjęcia` i oznaczenia niepewności. Nie wolno zastępować autora fotograficznego nazwą autora opracowania.

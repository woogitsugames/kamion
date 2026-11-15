# Źródła — G3 (research/gate3-spots-s21)

Dostęp: 2026-11-15. Pełne URL stron i plików, licencje, autorzy i sha256 każdego pliku są w `manifest.csv`
(kolumny `url_źródła`, `url_pliku`, `licencja`, `autor`, `sha256`). Surowe metadane pobrań: `meta_commons.json`,
`meta_panoramax.json`, `meta_kartaview.json`.

## Zdjęcia (wszystkie: referencja, nie tekstura; CC BY-SA i CC BY wymagają atrybucji)

| Źródło | Licencja | Autor | Wiersze |
|---|---|---|---|
| Wikimedia Commons, seria „… in Białystok” | CC0 1.0 | Rakoon | G3-001, 017, 028, 036 |
| Wikimedia Commons, seria „… July 2020” | CC BY 3.0 | Rakoon | G3-026, 027 |
| Panoramax (instancja panoramax.openstreetmap.fr, kolekcja b3131ba1…, 2019-08-15) | CC BY-SA 4.0 | stanton | G3-002, 003, 031, 032 |
| KartaView sekw. 2769366 (2019-08-25) i 2763230 (2019-08-04) | CC BY-SA 4.0 | gpsmapper999 | G3-004, 006, 009, 011–014, 020–022, 033, 034 |
| KartaView sekw. 3686129 (2021-06-23) | CC BY-SA 4.0 | TMishaaa | G3-005, 010, 015, 016, 023–025 |
| KartaView sekw. 10733 (2016-07-19) | CC BY-SA 4.0 | telenavdrives | G3-035 |

Nazwy użytkowników KartaView z `POST https://api.kartaview.org/1.0/list/nearby-photos/` (pole `username`); lista klatek
sekwencji z `GET https://api.kartaview.org/2.0/sequence/<id>/photos?itemsPerPage=1000`. Licencja KartaView: CC BY-SA 4.0
(jak w `research/mistral/p1-route-photos-2`).

Pliki w `files/`: `G3-NNN.jpg` = kadr pomniejszony do ≤ 1600 px (jakość 82); `G3-NNN_crop_*.jpg` = wycinki
szczegółów z tego samego kadru (tylko do oglądania detalu).

## Ortofotomapa GUGiK (dane otwarte PZGiK)

WMS `https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/HighResolution`, warstwa `Raster`, EPSG:2180, JPEG.
Zapytanie generuje `tools/ortho.py <out> <lat> <lon> <pół-bok_m> <px>`:

| Wiersz | Plik | Środek (WGS84) | Bok | px | m/px |
|---|---|---|---|---|---|
| G3-007 | files/G3-007.jpg | 53.158525, 23.153206 | 40 m | 800 | 0,05 |
| G3-018 | files/G3-018.jpg | 53.157650, 23.154250 | 80 m | 1000 | 0,08 |
| G3-029 | files/G3-029.jpg | 53.152220, 23.166900 | 60 m | 1000 | 0,06 |
| G3-037 | files/G3-037.jpg | 53.159177, 23.151580 | 60 m | 1200 | 0,05 |

Data nalotu i rozdzielczość źródłowa kompozycji HighResolution: **UNVERIFIED** (serwis skorowidzów zwraca
„Unauthorized”, GetFeatureInfo zwraca tylko RGB). Region gry używa ortofoto 2024 0,25 m (`Data/Regions/bialystok-industrial-c/ortho.json`).

## OpenStreetMap (ODbL)

`GET https://api.openstreetmap.org/api/0.6/map?bbox=23.1495,53.1560,23.1560,53.1605` (Putry) i
`…bbox=23.1645,53.1505,23.1700,53.1540` (Bieżeństwa), pobrane `osm/osm_fetch_utc.txt`. Wyciąg użytych way z węzłami
skrajnymi, długością i tagami: `osm/ways_extract.txt` (`tools/osm_ways.py`). Overpass nie był używany.

## Repozytorium (wykorzystane, nie dublowane)

- `Data/Regions/bialystok-industrial-c/gate3_cameras.json` + `region.yaml` (origin EPSG:2180 777995 / 596223) —
  pozycje kamer gry przeliczone pyproj do WGS84.
- `docs/reports/REVIEW-2026-11-14-s20-gate3-phone.md` — opis problemów P1-1, P1-2, P2-7, P2-10, P2-12.
- `docs/adr/0144-junctions-r7.md` pkt 10 — tablica F-10 przy 482392 (Mapillary richlv 2020, tylko referencja).
- `docs/adr/0159-barriers-screens-putry-andersa.md` — bariery i ekrany przy Putry/Andersa.
- gałąź `research/mistral-p13-andersa-viaducts` (P13: kolory gzymsów, słupów, ekrany na estakadach A/B) — tu tylko odsyłacze.
- gałąź `research/cloud2-direction-signs-route-c` (R2: tablice E na trasie C, Panoramax 2019) — tu tylko odsyłacze.

## Przeszukane, bez użytecznego wyniku

- Commons geosearch r = 400 m wokół 4 punktów: 55 plików pobrano do selekcji, 6 przypisano; pozostałe 49 obejrzano
  w arkuszach selekcyjnych (część także w pełnym kadrze) — las, park kieszonkowy, wnętrza, autobus, inne skrzyżowania
  albo cel za daleko; nieprzypisane, nie ma ich w manifeście.
- Panoramax w bbox Bieżeństwa (23.162–23.172, 53.150–53.155): 0 zdjęć.
- KartaView sekw. 14055 (2016, ziozzzzz): pliki 404/500 na storage i CDN — luka.
- Mapillary: bez tokenu — nie pobierano (ramki richlv z ADR 0144/0159 tylko jako odsyłacz).

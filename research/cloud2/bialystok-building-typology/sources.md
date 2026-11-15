# Źródła — R4 bialystok-building-typology (dostęp 2026-11-14)

| Źródło | URL | Licencja / status | Użycie |
|---|---|---|---|
| OpenStreetMap przez Overpass (instancja maps.mail.ru) | https://maps.mail.ru/osm/tools/overpass/api/interpreter | ODbL | statystyka budynków, obrysy próbki |
| GUGiK WCS NMPT (DSM 0,5 m) | https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMPT/GRID1/WCS/DigitalSurfaceModel | dane publiczne; Capabilities: Fees none, AccessConstraints none | wysokości próbki 56 budynków |
| GUGiK WCS NMT (DTM) | https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMT/GRID1/WCS/DigitalTerrainModel | jw. | poziom terenu |
| GUGiK LoD1 2024 / LoD2 (stan 2017), powiat 2061 | https://opendata.geoportal.gov.pl/InneDane/Budynki3D/LOD1/2024/20/2061.zip ; https://opendata.geoportal.gov.pl/InneDane/Budynki3D/LOD2/2061_gml.zip | CC BY 4.0 (wg Data/SourceManifests) | tylko sprawdzenie dostępności (HTTP 200); liczby wzięte z `Data/Regions/*/buildings.geojson` w repo |
| Panoramax | https://api.panoramax.xyz/api/search?bbox=23.1437,53.1455,23.1885,53.1680&limit=1000 | CC BY-SA 4.0 — referencja, nie tekstura | 7 kadrów (trasa C); Dojlidy: 0 wyników |
| KartaView API 2.0 | https://api.kartaview.org/2.0/photo/?lat=…&lng=…&radius=500 | CC BY-SA 4.0 — referencja, nie tekstura | 9 kadrów (trasa C); Dojlidy: 0 wyników |
| Wikimedia Commons (geosearch) | https://commons.wikimedia.org/w/api.php | per plik | tylko lista kandydatów (`data/commons_*.json`); kadry NIE obejrzane |
| Wikipedia PL „Technologia wielkopłytowa” (oldid 79506745), „OWT-67” (oldid 72638965) | https://pl.wikipedia.org/w/index.php?title=Technologia_wielkop%C5%82ytowa&oldid=79506745 | CC BY-SA 4.0 | moduły i wysokości kondygnacji systemów |
| Katalog techniczny płyt warstwowych PIR | https://bp2.eu/wp-content/uploads/2023/12/BP2-katalog-techniczny-CORE-PIR-PL.pdf | dokumentacja producenta | moduł okładziny hal |
| Karta blachy trapezowej T35 | https://www.ruukki.com/roofing/products/roofing-sheets/roofing-sheets-detail/profiled-sheet-t35 | dokumentacja producenta | profil blachy |
| Katalog bram segmentowych przemysłowych | https://m.budujemydom.pl/files/anq/15191-przemyslowe-bramy-segmentowe-doorhan-2016-pol-web.pdf | dokumentacja producenta | zakres wymiarów bram |
| Karta bramy segmentowej | https://www.assaabloyentrance.com/master-blueprint/pl/product-assets/loading-dock-equipment/oh1042p/downloads/product-datasheet/Assa%20Abloy%20OH1042P%20Overhead%20sectional%20door.pdf | dokumentacja producenta | wysokość sekcji, rozmiar maks. |
| Katalog techniki przeładunkowej | https://m.budujemydom.pl/files/ghr/15193-technika-przeladunkowa-doorhan-2016-pol-web.pdf | dokumentacja producenta | śluzy, pomosty |
| Karta prefabrykowanych ramp | https://heidelbergmaterials.pl/sites/default/files/2024-06/7-40C_Rampy_przeladunkowe_A4.pdf | dokumentacja producenta | wysokość doku 1,1 m |

## Zapytania Overpass (pełny tekst w `data/overpass_*.query.txt`, surowe wyniki w `data/overpass_*.json`)
- trasa C, 2026-11-14T17:09:59Z (osm_base 2026-11-14T17:07:50Z): `[out:json][timeout:120];(way["building"](53.1455,23.14371,53.168,23.1885);relation["building"](53.1455,23.14371,53.168,23.1885););out tags geom;`
- Dojlidy, 2026-11-14T17:10:21Z: `[out:json][timeout:120];(way["building"](53.09373,23.164,53.11102,23.211);relation["building"](53.09373,23.164,53.11102,23.211););out tags geom;`

## Próby nieudane (URL, kod)
- `https://overpass-api.de/api/status` — reset połączenia przez proxy; `overpass.kumi.systems`, `overpass.private.coffee` — timeout 20 s.
- `https://opendata.geoportal.gov.pl/InneDane/Budynki3D/LOD2/2024/20/2061.zip` — 404 (LoD2 tylko stan 2017).
- WCS `FORMAT=image/tiff` — 200, ale obraz RGB 8-bit; `image/tiff;application=geotiff`, `text/plain` — 400.
- KartaView: `api.openstreetcam.org` — błąd certyfikatu; `storage7.openstreetcam.org` (sekw. 1155711) — 502; promień > 500 → 400.
- `https://bp2.yoho.pl/…/KARTA-PRODUKTU-T35-PL.pdf` — 502.
- Mapillary — nieużyte (brak tokenu). Google/Bing/Apple/Yandex — nieużyte.

# STATUS — R2 direction-signs-route-c

## Krok 1 (2026-11-14 ~17:12 UTC) — Overpass
- Zapytanie `osm/overpass_query.overpassql`, wynik `osm/overpass_raw.json` (167 kB, 597 node / 179 way), data w `osm/overpass_fetch_utc.txt` (lustro maps.mail.ru; overpass-api.de i private.coffee nie odpowiadały przez proxy).
- Wynik: 0 węzłów `traffic_sign=PL:E-*` (jedyny traffic_sign w bbox to PL:B-1), 0 relacji destination_sign, 0 motorway_junction, 1 `man_made=gantry` (node 11877183092), 33 way z `destination*`.
- Nazwy OSM: „Rondo Krzysztofa Jakuba Putry Wicemarszałka Sejmu RP”, „Rondo Pamięci Bieżeństwa 1915 roku”.
- Kamery kontrolne: układ lokalny E,N,U względem origin EPSG:2180 (777995, 596223) → WGS84 przeliczone pyproj (42 sbs + 23 persp + 1 ortho).
- NASTĘPNY KROK: zebrać kadry Panoramax/KartaView/Commons: `python3 research/cloud2/direction-signs-route-c/tools/harvest.py` (do napisania), obejrzeć.

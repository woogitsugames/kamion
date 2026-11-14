# STATUS — R2 direction-signs-route-c

## Krok 1 (2026-11-14 ~17:12 UTC) — Overpass
- Zapytanie `osm/overpass_query.overpassql`, wynik `osm/overpass_raw.json` (167 kB, 597 node / 179 way), data w `osm/overpass_fetch_utc.txt` (lustro maps.mail.ru; overpass-api.de i private.coffee nie odpowiadały przez proxy).
- Wynik: 0 węzłów `traffic_sign=PL:E-*` (jedyny traffic_sign w bbox to PL:B-1), 0 relacji destination_sign, 0 motorway_junction, 1 `man_made=gantry` (node 11877183092), 33 way z `destination*`.
- Nazwy OSM: „Rondo Krzysztofa Jakuba Putry Wicemarszałka Sejmu RP”, „Rondo Pamięci Bieżeństwa 1915 roku”.
- Kamery kontrolne: układ lokalny E,N,U względem origin EPSG:2180 (777995, 596223) → WGS84 przeliczone pyproj (42 sbs + 23 persp + 1 ortho).
- NASTĘPNY KROK: zebrać kadry Panoramax/KartaView/Commons: `python3 research/cloud2/direction-signs-route-c/tools/harvest.py` (do napisania), obejrzeć.

## Krok 2 (częściowy) + zamknięcie (2026-11-14 ~18:00 UTC) — przerwane na polecenie lidera (limit)
- Panoramax: 68 kadrów w bbox, 12 obejrzanych i opisanych; 8 wierszy tablic; manifest 57 wierszy; fetch.py OK (4,77 MB, 0 błędów); audit 12 wierszy: 11 PASS / 1 FAIL (R2-009 skorygowany).
- NIE zrobione: kadry Andersa (KartaView), Tysiąclecia kier. S, Commons, wymiary, normatyw Dz.U. 2019 poz. 2310, cel ≥ 20 kadrów.
- NASTĘPNY KROK: pobrać i obejrzeć KartaView sekwencję 3686129 (Andersa → Putry): `curl -s "https://api.kartaview.org/2.0/photo/?sequenceId=3686129&itemsPerPage=150&page=1"` (pole `fileurlLTh`, 1280 px; filtr lat 53.150–53.160), dopisać kadry do listy `F` i tablice do `T` w `tools/build_manifest.py`, potem `python3 -I research/cloud2/direction-signs-route-c/tools/build_manifest.py research/cloud2/direction-signs-route-c/osm/panoramax_search_bbox.json research/cloud2/direction-signs-route-c/control_cameras_wgs84.json && python3 -I research/cloud2/direction-signs-route-c/fetch.py`

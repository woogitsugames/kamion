# STATUS — R2 direction-signs-route-c

## Krok 1 (2026-11-14 ~17:12 UTC) — Overpass
- Zapytanie `osm/overpass_query.overpassql`, wynik `osm/overpass_raw.json` (167 kB, 597 node / 179 way), data w `osm/overpass_fetch_utc.txt` (lustro maps.mail.ru; overpass-api.de i private.coffee nie odpowiadały przez proxy).
- Wynik: 0 węzłów `traffic_sign=PL:E-*` (jedyny traffic_sign w bbox to PL:B-1), 0 relacji destination_sign, 0 motorway_junction, 1 `man_made=gantry` (node 11877183092), 33 way z `destination*`.
- Nazwy OSM: „Rondo Krzysztofa Jakuba Putry Wicemarszałka Sejmu RP”, „Rondo Pamięci Bieżeństwa 1915 roku”.
- Kamery kontrolne: układ lokalny E,N,U względem origin EPSG:2180 (777995, 596223) → WGS84 przeliczone pyproj (42 sbs + 23 persp + 1 ortho).
- NASTĘPNY KROK: zebrać kadry Panoramax/KartaView/Commons: `python3 research/cloud2/direction-signs-route-c/tools/harvest.py` (do napisania), obejrzeć.

## Krok 3 (2026-11-15, sesja s21) — Andersa z KartaView, dokończenie
- KartaView sekw. 3686129 (2021-06-23): 148 zdjęć w bbox trasy C (kartaview/seq_3686129_trasaC.json); 15 obejrzanych 960 px + wycinki (R2-058…R2-072), 11 tablic/zespołów (R2-073…R2-083).
- Manifest 83 wiersze; 27 obejrzanych kadrów; audyt uzupełniający seed 20261115: 5 PASS / 1 FIX (R2-058 poprawiony); REVIEW.md: PASS z uwagami P2.
- Zdjęcia w repo: files/kv_*.jpg (1280 px), files/jpg1600/ (Panoramax ≤1600 px + INDEX.csv); oryginały Panoramax 2048 px przez fetch.py (ignorowane).
- NASTĘPNY KROK (opcjonalny): kierunek SE i sekw. 2769366 (2019): `curl -s "https://api.kartaview.org/2.0/photo/?sequenceId=2769366&itemsPerPage=150&page=1"`, potem dopisać do K/KT w tools/build_manifest.py i `python3 -I tools/build_manifest.py osm/panoramax_search_bbox.json control_cameras_wgs84.json`.

## Krok 2 (częściowy) + zamknięcie (2026-11-14 ~18:00 UTC) — przerwane na polecenie lidera (limit)
- Panoramax: 68 kadrów w bbox, 12 obejrzanych i opisanych; 8 wierszy tablic; manifest 57 wierszy; fetch.py OK (4,77 MB, 0 błędów); audit 12 wierszy: 11 PASS / 1 FAIL (R2-009 skorygowany).
- NIE zrobione: kadry Andersa (KartaView), Tysiąclecia kier. S, Commons, wymiary, normatyw Dz.U. 2019 poz. 2310, cel ≥ 20 kadrów.
- NASTĘPNY KROK: pobrać i obejrzeć KartaView sekwencję 3686129 (Andersa → Putry): `curl -s "https://api.kartaview.org/2.0/photo/?sequenceId=3686129&itemsPerPage=150&page=1"` (pole `fileurlLTh`, 1280 px; filtr lat 53.150–53.160), dopisać kadry do listy `F` i tablice do `T` w `tools/build_manifest.py`, potem `python3 -I research/cloud2/direction-signs-route-c/tools/build_manifest.py research/cloud2/direction-signs-route-c/osm/panoramax_search_bbox.json research/cloud2/direction-signs-route-c/control_cameras_wgs84.json && python3 -I research/cloud2/direction-signs-route-c/fetch.py`

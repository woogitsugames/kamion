# Źródła — R9 next-region-ring (dostęp 2026-11-14)

| # | tytuł | URL | licencja / status | użycie |
|---|---|---|---|---|
| S1 | OpenStreetMap przez Overpass API (mirror) | https://maps.mail.ru/osm/tools/overpass/api/interpreter | ODbL 1.0, © OpenStreetMap contributors | węzły, drogi główne, mosty, ekrany, stacje, wyposażenie |
| S2 | GUGiK skorowidze ortofotomapy (WFS) | https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WFS/Skorowidze | dane otwarte GUGiK | roczniki, piksel, rozmiary |
| S3 | GUGiK skorowidze NMT (WFS) | https://mapy.geoportal.gov.pl/wss/service/PZGIK/NumerycznyModelTerenuEVRF2007/WFS/Skorowidze | dane otwarte GUGiK | NMT |
| S4 | GUGiK skorowidze NMPT (WFS) | https://mapy.geoportal.gov.pl/wss/service/PZGIK/NumerycznyModelPokryciaTerenuEVRF2007/WFS/Skorowidze | dane otwarte GUGiK | NMPT |
| S5 | GUGiK BDOT10k — pobieranie (WMS GetFeatureInfo) | https://mapy.geoportal.gov.pl/wss/service/PZGIK/BDOT/WMS/PobieranieBDOT10k | dane otwarte GUGiK | paczki powiatów 2061, 2002 |
| S6 | GUGiK modele 3D budynków (WMS GetFeatureInfo) | https://mapy.geoportal.gov.pl/wss/service/PZGIK/FOTO/WMS/ModeleBudynkow3D | CC BY 4.0 (panel usługi) | LoD1 2022/2024, LoD2 2017 |
| S7 | GUGiK PRG granice (WFS) | https://mapy.geoportal.gov.pl/wss/service/PZGIK/PRG/WFS/AdministrativeBoundaries | dane otwarte GUGiK („Brak opłat” w Capabilities) | gminy, TERYT |
| S8 | opendata.geoportal.gov.pl (HEAD plików) | https://opendata.geoportal.gov.pl/ | dane otwarte GUGiK | rozmiary, Last-Modified |
| S9 | Panoramax meta-katalog | https://api.panoramax.xyz/api/search | CC BY-SA 4.0 | liczba zdjęć, 32 kadry |
| S10 | KartaView API 2.0 | https://api.kartaview.org/2.0/photo/ , /2.0/sequence/{id} | CC BY-SA 4.0 | sekwencje, 6 kadrów |
| S11 | Wikimedia Commons API geosearch | https://commons.wikimedia.org/w/api.php | per plik; nic nie pobrano | liczba plików przy 7 punktach |
| S12 | Repo: Data/Regions/*/region.yaml, tools/worldgen/ingest.py, gugik_index.py | (lokalne) | — | siatka, wzorce URL |

Niedostępne: overpass-api.de (reset połączenia), overpass.kumi.systems i overpass.private.coffee (timeout), overpass.osm.jp / nchc.org.tw (502), overpass.openstreetmap.fr (403 whitelist), download.geofabrik.de (reset), api.openstreetcam.org (błąd certyfikatu; użyto api.kartaview.org), Commons (429 naprzemiennie z 200).

## Zapytania Overpass (pełny tekst)

### junctions_wide — 2026-11-14T17:10:30Z UTC, timestamp_osm_base 2026-11-14T17:08:49Z, 15 elementów, 3252 B, sha256 2c68dd142ef7a9dd…
```
[out:json][timeout:60];
(node(53.00,22.85,53.28,23.40)[highway=motorway_junction];);
out body;
```

### major_wide — 2026-11-14T17:12:44Z UTC, timestamp_osm_base 2026-11-14T17:11:50Z, 1534 elementów, 1166473 B, sha256 68c51acbb422853e…
```
[out:json][timeout:120];
(way(53.00,22.85,53.28,23.40)[highway~"^(motorway|motorway_link|trunk|trunk_link|primary|primary_link|construction|proposed)$"];);
out tags geom;
```

### junctions — 2026-11-14T17:15:23Z UTC, timestamp_osm_base 2026-11-14T17:13:51Z, 11 elementów, 2411 B, sha256 bdda7d82d0292d80…
```
[out:json][timeout:60];
(node(53.052,22.951,53.249,23.306)[highway=motorway_junction];);
out body;
```

### bridges_tunnels — 2026-11-14T17:17:50Z UTC, timestamp_osm_base 2026-11-14T17:15:56Z, 1169 elementów, 571677 B, sha256 ed1b9aeb6229aebc…
```
[out:json][timeout:120];
(way(53.052,22.951,53.249,23.306)[highway][bridge];way(53.052,22.951,53.249,23.306)[highway][tunnel];way(53.052,22.951,53.249,23.306)[railway][bridge];way(53.052,22.951,53.249,23.306)[man_made=bridge];);
out tags geom qt;
```

### barriers — 2026-11-14T17:18:50Z UTC, timestamp_osm_base 2026-11-14T17:16:56Z, 810 elementów, 406671 B, sha256 33bd6b949d45f0b2…
```
[out:json][timeout:120];
(way(53.052,22.951,53.249,23.306)[barrier~"^(noise_barrier|guard_rail|wall|jersey_barrier|cable_barrier)$"];way(53.052,22.951,53.249,23.306)[wall=noise_barrier];way(53.052,22.951,53.249,23.306)[noise_barrier];);
out tags geom qt;
```

### services — 2026-11-14T17:21:58Z UTC, timestamp_osm_base 2026-11-14T17:21:01Z, 76 elementów, 30365 B, sha256 d7286e875fa36707…
```
[out:json][timeout:120];
(nwr(53.052,22.951,53.249,23.306)[highway~"^(rest_area|services)$"];nwr(53.052,22.951,53.249,23.306)[amenity=fuel];nwr(53.052,22.951,53.249,23.306)[amenity=parking][hgv~"^(yes|designated|only)$"];nwr(53.052,22.951,53.249,23.306)[amenity=weighbridge];nwr(53.052,22.951,53.249,23.306)[highway=toll_gantry];nwr(53.052,22.951,53.249,23.306)[man_made=surveillance]["surveillance:type"=ALPR];);
out tags center qt;
```

### signs_furniture — 2026-11-14T17:22:23Z UTC, timestamp_osm_base 2026-11-14T17:21:01Z, 2845 elementów, 423364 B, sha256 c92a2c3d240c35cc…
```
[out:json][timeout:120];
(node(53.052,22.951,53.249,23.306)[highway~"^(traffic_signals|speed_camera|street_lamp|milestone)$"];node(53.052,22.951,53.249,23.306)[traffic_sign];node(53.052,22.951,53.249,23.306)[man_made=gantry];way(53.052,22.951,53.249,23.306)[man_made=gantry];);
out tags qt;
```

Niedokończone: `highways` i `buildings` w kaflach 4×4 (tools/ovp_tiled.py) — 10 kafli dróg zapisanych w overpass/_log.jsonl (nazwy highways_i_j), wyniki nieużyte.

## Zapytania GUGiK
Każdy URL z czasem UTC i kodem HTTP: `gugik/skorowidze_summary.json` (27 zapytań WFS), `gugik/powiat_packages.json` (GetFeatureInfo + HEAD), `gugik/head_sizes_sample.json`. PRG: URL w manifeście (wiersze PRG), HTTP 200, 2026-11-14T17:17:53Z.

## Zapytania o zdjęcia
`panoramax/search_log.json`, `kartaview/search_log.json` (161 URL-i), `kartaview/sequences.json`, `commons/geosearch_landmarks.json`.

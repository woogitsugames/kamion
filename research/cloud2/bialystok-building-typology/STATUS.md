# STATUS — R4 bialystok-building-typology

## Krok 1 (2026-11-14 17:10 UTC) — Overpass
- Przeczytane: brief, mistral/p3-buildings-2, gptpro/p3, p11, p12 (README), ADR 0185, region.yaml obu kafli.
- `tools/overpass.py` → `data/overpass_trasa_c.json` (2734 budynki), `data/overpass_dojlidy.json` (962); zapytania + data UTC w `data/*.query.txt`.
- Wniosek wstępny: OSM ma `building=yes` w ~80 %, `building:levels` w ~10 %, `roof:shape` ~0 % → statystyka typów musi iść z BDOT10k/LoD (buildings.geojson w repo).
- NASTĘPNY KROK: `python3 research/cloud2/bialystok-building-typology/tools/gugik_probe.py` (LoD2/WCS NMPT+NMT).

## Krok 2 (2026-11-14 ~17:35 UTC) — GUGiK, KartaView, Panoramax, statystyki
- GUGiK: LoD2 `…/Budynki3D/LOD2/2061_gml.zip` HTTP 200 (23,45 MB, Last-Modified 2018-11-14), LoD1 2024 HTTP 200, LOD2/2024 → 404. WCS NMPT/NMT GetCapabilities 200; GetCoverage `image/x-aaigrid` działa (`image/tiff` zwraca RGB 8-bit — nieużyteczne).
- `tools/nmpt_heights.py` (próbka 56 budynków, seed 20261114) — w toku.
- KartaView API 2.0: trasa C 39 zdjęć (9 pobranych, sekw. 3686129 z 2021; storage7 → 502), Dojlidy 0. Panoramax: trasa C 53, Dojlidy 0. Obejrzane dotąd: 4 Panoramax + 9 KartaView.
- `tools/stats.py` → `data/stats.json` (OSM + buildings.geojson repo).
- Dokumenty producentów w files/docs (płyta warstwowa, doki, bramy segmentowe).
- NASTĘPNY KROK: `python3 research/cloud2/bialystok-building-typology/tools/commons_scan.py` → wybór i obejrzenie kadrów Commons.

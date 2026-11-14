# STATUS — R4 bialystok-building-typology

## Krok 1 (2026-11-14 17:10 UTC) — Overpass
- Przeczytane: brief, mistral/p3-buildings-2, gptpro/p3, p11, p12 (README), ADR 0185, region.yaml obu kafli.
- `tools/overpass.py` → `data/overpass_trasa_c.json` (2734 budynki), `data/overpass_dojlidy.json` (962); zapytania + data UTC w `data/*.query.txt`.
- Wniosek wstępny: OSM ma `building=yes` w ~80 %, `building:levels` w ~10 %, `roof:shape` ~0 % → statystyka typów musi iść z BDOT10k/LoD (buildings.geojson w repo).
- NASTĘPNY KROK: `python3 research/cloud2/bialystok-building-typology/tools/gugik_probe.py` (LoD2/WCS NMPT+NMT).

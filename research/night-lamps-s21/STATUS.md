# STATUS — K69 nocne latarnie (gałąź research/night-lamps-s21)

## 2026-11-15 ~10:30 UTC — WIP 1
- Overpass niedostępny przez proxy (reset / 502 / 504 na 4 instancjach) → OSM API 0.6 /map w kaflach 0,01° (`tools/osm_tiles.py`), bbox 53.095–53.165 N, 23.120–23.215 E: 1443 węzły `highway=street_lamp`.
- Rozstawy z OSM (`tools/osm_spacing.py`): 16 ulic z ≥ 10 parami (ogólnie Białystok); ulice trasy w OSM prawie bez latarni (Kombatantów 2 pary).
- Dokumenty ZDM (platforma e-zamówień, publiczne): warunki techniczne 2023 (Andersa, 1000-lecia, Maczka) i 2024 (Wysockiego; Kuronia, Mickiewicza, Dywizjonu 303) — CCT 4000 K ulica, 5700 K przejścia.
- Kadry: Panoramax 5 nocnych (obejrzane), Commons w toku (HTTP 429 — powolne pobieranie metadanych).

Następny krok: `python3 -I tools/commons_geo.py "$PWD/tools" titles.json commons_meta.json --geo` (kandydaci nocni), potem oglądanie i manifest.

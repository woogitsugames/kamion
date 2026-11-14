# STATUS — M65 (cloud p22-red-bike-paths)

- [x] Overpass (maps.mail.ru) 2026-11-14T16:49Z, osm_base 2026-11-14T16:48:34Z → `overpass-result.json` (zapytanie: `overpass-query.ql`)
- [x] `tools/inventory.py` → `inventory.json` (C: 71 odcinków, Dojlidy: 22), `tools/crossings.py` → `crossings.json`
- [x] ortofotomapa GUGiK 5 cm (WMS HighResolution): 27 wycinków skrzyżowań (`data/ortho_clusters.json`), 64 przekroje odcinków (`data/ortho_transects.json`, `tools/transect.py`), 32 wycinki przejazdów (`data/ortho_crossings.json`, `tools/crossing_crop.py`) — obejrzane, odczyty w notatkach (do wpisania w `data/observations.json`)
- [x] Panoramax (55 kadrów w kaflu C, 0 w Dojlidach), KartaView (C; 0 w Dojlidach) — wybrane kadry obejrzane
- [ ] Commons (P11-001, P11-056 i kadry Dojlid): upload.wikimedia.org i API zwracają HTTP 429 (retry-after 600) od 16:52Z — ponawiać
- [ ] manifest.csv, README.md, sources.md, fetch.py, audit_20_percent.json, PR

NASTĘPNY KROK: `python3 -I tools/build_manifest.py` (do napisania: inventory + crossings + data/observations.json → manifest.csv), potem ponowić pobranie Commons: `curl -A 'kamion-research/1.0 (open-data reference collection)' https://upload.wikimedia.org/wikipedia/commons/8/88/20240623_142113_June_2024_in_Bia%C5%82ystok.jpg`.

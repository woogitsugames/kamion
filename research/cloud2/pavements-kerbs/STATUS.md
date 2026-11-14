# STATUS — R6 pavements-kerbs

## Krok 1 (2026-11-14 ~17:10 UTC) — worktree, dane OSM
- Worktree `/workspace/wt/pavements-kerbs`, gałąź `research/cloud2-pavements-kerbs`.
- Overpass (overpass-api.de, lz4, z, kumi, private.coffee, mail.ru) niedostępny przez proxy sesji → surowe dane z OSM API 0.6 `/map` (24 kafle, 85 MB, `files/osm/`, poza gitem) — `osm_fetch.py`.
- `osm_analyze.py` → `osm_summary.json`: ulice trasy C i Dojlid (way_id, długości, surface), ciągi boczne ≤30 m, węzły kerb/manhole/tactile_paving. `manhole=*` przy trasie: 0 węzłów.
- NASTĘPNY KROK: `python3 research/cloud2/pavements-kerbs/docs_fetch.py` (Dz.U. 2022 poz. 1518, wytyczne ZDM, OST/KTKNPiP/DSN GDDKiA) i wyciąg cytatów.

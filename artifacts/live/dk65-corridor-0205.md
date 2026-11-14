# dk65-corridor-0205 (ADR 0205) — live
- 11-15: worktree, gałąź od main + cherry-pick 7ce3fe325 (bbox OSM z 0204), pkl OSM skopiowany z knyszyn-0204. Kafel: `dk65-01` (-4,0) 768779,595199–770827,597247, powiat 2002, trasa A km 8,76–9,39 (631 m, Szosa Knyszyńska, 70 km/h). Budowa S19 poza kaflem (km 16,7+).
- W TLE: ingest (log `artifacts/dk65-corridor-0205/logs/ingest.log`, koniec `ingest.done`).
- NASTĘPNY KROK: `uv run --project tools/worldgen tools/worldgen/build_region.py --region dk65-01`
- 11-15 00:2x: ingest OK (462 MB; NMT 2025, orto 2024, BDOT/LoD1/LoD2 powiat 2002), build_region (235 węzłów, 229 krawędzi, 460 budynków), build_world 257 s OK (ściany terenu > 0,15 m: 55, max 1,62 m — do sprawdzenia; spójność 21, 0 na trasie), export-route 632 m. W kaflu: S19/S8 (motorway 4,1 km + łącznice 2,7 km, mosty) poza trasą; brak budów w OSM.
- W TLE: `pwsh artifacts/dk65-corridor-0205/tools/import.ps1` (import → vqa Low → vqa High), status `artifacts/dk65-corridor-0205/logs/chain.status` (koniec `IMPORT DONE r1`).
- NASTĘPNY KROK: obejrzeć `artifacts/dk65-corridor-0205/r1/Low-clear/*.png`, porównać skrzyżowania z ortofoto, kamery authored (control_cameras_place.authored.json).

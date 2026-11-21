# STATUS landmarks-s24 (ADR 0320)

## Krok 1 — most kratownicowy Tykocin (WIP)
- `tools/worldgen/streetscape/truss_bridge.py` (override `kind: truss_bridge`), hak w `roads/build_world.py` po `HB.apply`,
  materiały `truss_steel` / `truss_rail_blue` / `truss_picket`, override `tykocin-narew-truss-0320`.
- build_world tykocin: exit 0, kratownica 26 138 tris LOD0 / 5 302 LOD1, przebieg 194,4 m, przęsła 15+51+39+38+37+15 m.
- NASTĘPNY KROK: obejrzeć `artifacts/landmarks-s24/r1-bridge/*.png` (import + visual-qa w tle), SBS z Commons 05/08.
  `pwsh scripts/visual-qa.ps1 -Scene World_tykocin_High -Tier High -Lighting clear -BuildTarget Win64 -OutputDir artifacts/landmarks-s24/r1-bridge -Cameras tyk_narew_side -Gate3 artifacts/landmarks-s24/bridges-tykocin.json`

## Krok 2 — runda 1 obejrzana (SBS w artifacts/landmarks-s24/sbs/r1-*.jpg), runda 2 w toku
- r1: most czyta się jak na zdjęciach (4 przęsła, portale, balustrada); błąd: `viaduct_concrete` ma czerwoną farbę → `truss_concrete`.
- r1 król: korona za „kolczasta”, szyja za cienka → szersza głowa, niska korona, bez cienkich rurek. Tykocin: bruk nie-flush (teren przebijał).
- NASTĘPNY KROK: po rundzie 2 (`artifacts/landmarks-s24/r2-*`) SBS → ewentualna runda 3 → pytest + EditMode:
  `uv run --project tools/worldgen python -m pytest tests/gis/test_truss_bridge_0320.py tests/gis/test_knyszyn_park_props_0227.py -q`

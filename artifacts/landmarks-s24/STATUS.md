# STATUS landmarks-s24 (ADR 0320)

## Krok 1 — most kratownicowy Tykocin (WIP)
- `tools/worldgen/streetscape/truss_bridge.py` (override `kind: truss_bridge`), hak w `roads/build_world.py` po `HB.apply`,
  materiały `truss_steel` / `truss_rail_blue` / `truss_picket`, override `tykocin-narew-truss-0320`.
- build_world tykocin: exit 0, kratownica 26 138 tris LOD0 / 5 302 LOD1, przebieg 194,4 m, przęsła 15+51+39+38+37+15 m.
- NASTĘPNY KROK: obejrzeć `artifacts/landmarks-s24/r1-bridge/*.png` (import + visual-qa w tle), SBS z Commons 05/08.
  `pwsh scripts/visual-qa.ps1 -Scene World_tykocin_High -Tier High -Lighting clear -BuildTarget Win64 -OutputDir artifacts/landmarks-s24/r1-bridge -Cameras tyk_narew_side -Gate3 artifacts/landmarks-s24/bridges-tykocin.json`

# dk65-tiles-0207 (ADR 0207) — live
- 11-15 01:4x: worktree `.claude/worktrees/dk65-tiles-0207`, regiony dk65-02..05 w regions.py, ingest (NMT 2025, orto 2024-05-27 0,25 m; BDOT/LoD 2002 już były) + build_region OK (02: 99 węzłów/293 bud.; 03: 54/280; 04: 145/788; 05: 139/473). route_endpoints z planu 0203.
- 01:57: build_world r1 dk65-02 (2401 m) i dk65-03 OK; 04/05 w toku (`artifacts/dk65-tiles-0207/logs/chain.status`). Narzędzia ortofoto: tools/ortho_strip.py (pasek), strip_zoom.py, ortho_crop.py, mosaic.py.
- NASTĘPNY KROK: przekrój dk65-02 z ortofoto (strip_zoom), overrides.yaml + kamery authored, potem `pwsh artifacts/dk65-tiles-0207/tools/chain.ps1 -Tiles dk65-02 -Tag r2`

# STATUS — trailer-763-s23 (ADR 0280 §9: model 3D naczepy pod 7,63 m)
- Krok 0: worktree z origin/main @ 64e54592e; generator Blendera czyta osie z dims.json (`trailer_build.py:37`); kamera
  `zbl_kolo` liczona z `T.AXLES[1]`, nowa kamera `gora` (przekrój 1,20 m z góry). Rendery „przed” w `artifacts/trailer-763-s23/before/`.
- Krok 1: eksport (6 min, 1. próba OOM w bake'u, 2. OK): koła/AXLE_n na −6,32/−7,63/−8,94, chlapacze −9,622, lampa boczna 3
  −6,975; `check_export` PASS (LOD 89000/24499/7847), `regs_check` 158/158, pytest dims_sync 9/9, truck_regs 5/5.
- Uwaga (stan sprzed zmiany, nie z tej gałęzi): obręcze kół próbkują czerwone/tekstowe fragmenty atlasu Metal (639/10651
  tekseli identycznie w starym i nowym FBX; UV kół dzielone z kołem zapasowym w CHASSIS) — do osobnego zadania.
- Krok 2: Unity: shader `_CurtainAxles` domyślnie 7,63; wejście `DrivingLabSceneBuilder.RebuildTrailerPrefabBatch`; test
  `TrailerAxleSyncTests` (8 testów); merge origin/main (#171).
- NASTĘPNY KROK: `pwsh <scratch>/unity_method.ps1 -Method Game.Editor.Setup.DrivingLabSceneBuilder.RebuildTrailerPrefabBatch`,
  potem `TrailerAssetBuilder.BuildBatch`, `pwsh scripts/visual-qa.ps1 -Scene Boot -Tier High -Cameras trailer-34,trailer-side`,
  `pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64`.

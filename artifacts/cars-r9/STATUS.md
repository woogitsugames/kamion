# cars-r9 status (REVIEW r8: "auta-mydelniczki")

Worktree `.claude/worktrees/agent-adeef0c396335e1ed`, branch `worktree-agent-adeef0c396335e1ed`.
Junctions: `Data/raw/gugik`, `Data/raw/osm` -> main (remove with `cmd /c rmdir`). Copies from main (untracked):
`Data/raw/derived`, `game/Library`, `game/Assets/_Generated`, `art-source/world/materials/<set>`, `art-source/world/cc0`,
`art-source/truck/interior/export/SM_CabInterior_LOD0.fbx`.
Stray empty dir created by mistake (first Blender run resolved a relative path): `C:\artifacts\cars-r9\it0` - leader may delete.

## Step 1 (done): r9 shell in `tools/worldgen/streetscape/life_cars.py`
- New `_controls` / `_Shell` / `_vehicle2` / `_wheel2`: bonnet arc + tight lip, near-vertical lamp band, bumper face, chin, rear
  bumper ledge, super-elliptic plan corners, section with tuck / shoulder facet / tumblehome, side rows on feature lines,
  arch flares + lip rings, lamp units (dark housing + bright lens, wrap into the wing), tail clusters, bonnet / door /
  bumper seams, black B pillars, belt weatherstrip, cowl panel, wipers, recessed handles, wedge mirrors.
- Van = mid-size panel van 4.90 x 1.93 x 1.97 m (was the 4.5 m car-derived van), unpainted bumpers, sliding-door track.
- Tris: LOD0 3203-3409 (r8 3528-3798), LOD1 860-882, LOD2 54-58. Holes: 0 of 81 (`holes-it5.log`).
- pytest cars subset 15 passed. Blender control renders: `it0` (r8 baseline) .. `it6` (LOD1), `it6-lod2`.
- Tools: `tools/worldgen/qa/car_preview.py`, `tools/blender/world/render_cars.py`, `artifacts/cars-r9/preview.sh <dir>`.

## NEXT
1. `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c`
2. `pwsh scripts/import-region.ps1 -Region bialystok-industrial-c`; InstallBatch; visual-qa WorldC Low+High x overcast+lowsun
   (cams cab-dash, truck-34, stretch_01, car_lod_08/12/15/25 with `-Gate3 artifacts/cars-r9/car_cams.json`).
3. Paint gloss in the engine (materials.py rough 0.20-0.36 now), reference montage, pytest tests/gis, EditMode, ADR 0073 + 0041 r9.

## Step 2 (done, 20:50): world regenerated, Unity pipeline RUNNING
- Final dims tweak (hatch nose 0.86 / belt 1.05 / hood 1.00; sedan, estate nose 0.83 / belt 1.03). Tris all 27 prototypes:
  LOD0 3203-3449, LOD1 844-882, LOD2 54-58. Holes 0 of 81 (`holes-it7.log`). New `tests/gis/test_cars_r9.py` (5 passed).
- build_world EXIT 0 (4 min 11 s): stretch_04 High 1 997 615 -> 1 997 661 (cap 2.0 M), stretch_01 1 661 414 -> 1 635 529,
  stretch_05_docks 1 742 105 -> 1 723 446; Low max 961 666. 962 cars + 123 vans in 1643 bays.
- Importer: `WorldPbrMaterials` scales car_grime smoothness to the manifest `rough` of `car_paint_*` (was ignored).
- ADR draft `docs/adr/0073-cars-r9-silhouettes.md` (placeholders WYNIKI / OTWARTE still to fill), montage `compare/it5_cab_vs_refs.jpg`.

## NEXT (ready commands, from the worktree root)
1. Pipeline (import + install + 4 x QA) was started: `pwsh artifacts/cars-r9/unity_pipeline.ps1 -Stage after -SkipSetup`
   (log `artifacts/logs/cars-r9-pipeline.log`; if it died after "IMPORT DONE": add `-SkipImport`). Output `artifacts/cars-r9/after/<Tier>-<light>/`.
2. Look at the PNGs (cab-dash, truck-34, stretch-01, car_lod_*), montage vs `C:\Users\matma\Documents\Claude\kamion\artifacts\world-fixes\cars-r8\after`.
3. `uv run --project tools/worldgen pytest tests/gis -q`; `pwsh scripts/test.ps1 -Platform EditMode`.
4. Fill ADR 0073 placeholders + ADR 0041 r9 addendum; `git checkout game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings`;
   final commit; `robocopy artifacts\cars-r9 C:\Users\matma\Documents\Claude\kamion\artifacts\cars-r9 /E`.

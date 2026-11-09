# ADR 0015 — Forest HLOD cells and LOD1 far facades (world v3.1)
Status: Proposed (world-builder), 2026-11-09. Extends ADR 0012 (tiers, instancing). Needs the importer / shader
work listed under "Consequences" before it is visible in Unity.
Evidence: `Data/Regions/bialystok-industrial-c/generated/streetscape_qa.json` → `mesh_budget` (frame estimate by
category), `docs/reports/visual/world-c/README.md` (v3.1 renders), `tests/gis/test_world_v31.py`.

## Context
- REVIEW-2026-11-09-r2 §3 #12: the DK8 forest frame was **8.16 M triangles** on High (generator estimate), almost all
  of it individual trees at LOD1 between 80 and 250 m. Target (docs/06 §6): ≤ 2 M High, ≤ 0.6 M Low.
- REVIEW r2 #1: large offices / blocks read as boxes from afar. Low/Medium draws only LOD1 buildings beyond
  100 m of the start route (ADR 0012), and LOD1 was a plain prism.

## Decisions
### 1. Forest HLOD per 64 m cell
- `streetscape/forest_hlod.py` builds, per 64 m cell with ≥ 8 forest trees, one mesh: a canopy surface at the crown
  tops of the real instances + alpha-tested **edge walls** along the stand edge (BDOT10k forest outline minus roads,
  yards, buildings) and lower inner walls on cell borders. Textures are baked from the LOD0 trees
  (`make_trees.py`: `forest_edge_<mix>.png` side view 48 × 24 m, `forest_canopy_<mix>.png` top view 48 × 48 m, mix by
  BDOT forest category: conifer / mixed / broadleaf). ~145 triangles per cell (534 cells, 77.6 k in the tile). The
  roadside row of trees (within 12 m of a road or yard) is never replaced and stays individual (impostors far away).
- GLB contract: node `forest_hlod_<i>_<j>` in `chunk_*.glb` and `chunk_*.low.glb` with extras
  `{layer: forest_hlod, cell, bbox_local_m, trees, switch_m}`; materials `forest_edge_*` (alpha MASK, double sided)
  and `forest_canopy_*` carry `extras.texture_ref` (shared PNG in `art-source/world/vegetation/`, not embedded).
  Forest trees in `instances_*.json` carry `fc: "<i>_<j>"` (their cell) and `fk` (mix).
- Rule (engine and Blender renders): when the distance from the camera to the cell bbox is above
  `lod_policy.<tier>.forest_hlod_m` (High 120 m, Low 70 m; manifest `lod_policy`), draw the cell node and skip every
  tree with that `fc`; Low culls cells beyond `forest_hlod_cull_m` = 1000 m.
- Tree LOD distances tightened at the same time (High LOD0 < 35 m, LOD1 < 80 m, impostor beyond; Low unchanged).
  WORKING_VALUE until measured on the A16.

### 2. LOD1 far facades
- `buildings_mesh.lod1_wall`: every LOD1 wall of an office / block is plinth + window zone + wall + coping ledge
  (≤ 10 triangles per edge instead of 2; edges < 3 m stay plain), blocks and offices of ≥ 5 storeys get lift
  machine rooms; the LOD1 roof stays one flat polygon.
- The window zone uses material `<wall>__far_<block|office|ribbon>`; `TEXCOORD_1` = (window bay, storey) grid —
  one unit is one bay (3.0 m) by one storey (BDOT10k storey count when plausible). `extras.window_grid` gives the
  pane rectangle in those units; the shader draws panes with a per-cell tone (hash of floor(uv1)).

## Consequences
- Unity importer (ADR 0012 §3 drops TEXCOORD_1): keep TEXCOORD_1 (float16 × 2) for `__far_` materials and add the
  far-facade shader; read `forest_hlod_*` nodes into per-cell meshes and make `WorldInstances` skip trees whose `fc`
  cell is drawn as HLOD. Owner: lead / rendering-perf (shared scripts and shaders).
- Estimated Unity Low meshes (ADR 0012 formats, before LZ4HC): 59.3 MiB (v3 55.6): +1.8 HLOD, +0.55 LOD1, plus the
  walled ramps (+0.9) and barriers (+0.4) of the same release.
- Without the importer work Unity shows plain-colour LOD1 window zones and keeps drawing all trees (no regression
  in triangles versus v3, no gain either).

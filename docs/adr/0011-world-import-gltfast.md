# ADR 0011 — World import into Unity: glTFast, generated assets outside git
Status: Accepted (rendering-perf / world import), 2026-11-09. **Import path superseded by ADR 0012** (GLBs are baked directly, not copied into Assets; glTFast stays for future run-time loading).

## Context
`tools/worldgen/roads/build_world.py` writes 64 chunk GLBs (~270 MB, `Data/raw/derived/<id>/world/`, not in git) and
`world_manifest.json` (git). Unity needs the meshes, URP materials per material id, colliders per surface, and a drivable
scene placed relative to the region anchor (ADR 0003).

## Options
| | glTFast (`com.unity.cloud.gltfast`) | UnityGLTF (Khronos/Prefrontal Cortex) | own GLB reader |
|---|---|---|---|
| maintainer | Unity Technologies (Unity's official glTF package) | community (MIT) | us |
| licence | Apache 2.0 | MIT | — |
| editor import | ScriptedImporter, sub-asset meshes, fast (Burst/Jobs) | ScriptedImporter | to write |
| runtime import (future streaming / DLC regions) | yes, async | yes | to write |
| axis convention | negates x → our (−E,U,N) becomes Unity (E,U,N) (documented in the manifest) | same | own |
| risk | another package in the lock file | slower, less maintained for Unity 6 | maintenance, edge cases |

## Decision
- **glTFast 6.20.0** (released 2026-08-27, stable; 7.0.0 is experimental), added to `Packages/manifest.json`.
- `scripts/import-region.ps1 -Region <id>` (→ `Game.World.Import.RegionImporter.ImportBatch`):
  1. copies the chunk GLBs into **`game/Assets/_Generated/World/<id>/Chunks/` (gitignored)**; glTFast imports them;
     sha256 is compared with the manifest (mismatch = warning: the generator's bytes differ between Python environments,
     see below);
  2. creates materials `M_<id>` from `world_manifest.json` (colour = linear mean albedo, roughness, metal, decal flag) on
     `Kamion/World Surface` (URP Lit for metals);
  3. splits `road_collision` (one primitive per surface) into one mesh per surface → `MeshCollider` + `GroundSurface`
     (asphalt → DryAsphalt, concrete/kerb → Concrete, paving/sett → Cobbles, gravel → Gravel, grass → Grass);
     terrain LOD1 as the fallback collider off the road;
  4. builds `WorldC.unity` (also gitignored): region root at y = −anchor height so Unity (0,0,0) is the region anchor;
     `WorldRegionRoot` keeps the EPSG:2180 anchor in double and an `originShift` for the floating origin; LODGroups from the
     manifest switch distances (+0.7 chunk, measured to the chunk centre); chunks within **320 m of the start route** get
     LOD0–3, markings and collision, the rest only LOD2/3 and roads; lighting (ADR 0010), volume, the DrivingLab
     tractor + trailer at the Kwadrat Park gate, the start route (`scripts/export-route.py`), control cameras from
     `control_cameras.json`.
- Generated, large: everything under `Assets/_Generated/` (278 MB) stays out of git; regenerate with the script
  (inputs in git + `build_world.py`). The build list includes WorldC only when the file exists; the Boot menu shows
  "Białystok — Kwadrat Park" only when the scene is in the build.

## Consequences / known issues
- APK: meshes are **220.8 MB uncompressed** of 974 MB build content (APK 159.7 MB): a glTFast asset is included whole, so
  the far chunks' unused LOD0/1 still ship. On a 4 GB A16 this is the first memory risk (PSS unmeasured). Next steps, in
  order: (1) import only the needed nodes per chunk (glTFast import settings or a post-import mesh copy), (2) mesh vertex
  compression (half normals/UVs), (3) chunk streaming with Addressables — also the basis for the floating-origin shift.
- The generator is not byte-reproducible across Python environments (a fresh `uv` venv on this machine gave different
  sha256 for 10 of 64 chunks vs the committed manifest; triangle counts identical). Reported to world-builder; until fixed
  the importer only warns.
- Route-level collision is verified by `WorldCRouteTests` (solo and 40 t, full 2.4 km, no fall-through).

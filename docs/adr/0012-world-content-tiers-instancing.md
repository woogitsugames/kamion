# ADR 0012 — World content tiers, mesh compression, terrain band and GPU instancing
Status: Accepted (rendering-perf / world import), 2026-11-09. Extends ADR 0011 (import path) and ADR 0010 (tiers).
Evidence: `artifacts/world/<region>-import.json` (bake report), `artifacts/apk/*.content.json` (build report),
`docs/reports/visual/unity-look-v2/README.md` (renders), `docs/PERFORMANCE_BUDGETS.md` (numbers).

## Context
World generator v2 (`docs/WORLD_GENERATION.md`) adds paved areas, LOD0/LOD1 buildings, linear furniture, a quantised
`chunk_*.low.glb` per chunk and `instances_*.json` (≈ 2 300 street props + ≈ 109 000 trees) that reference prototype
libraries (`street_props.glb`, `trees.glb`, `trees_lod2.glb` impostors). High GLBs are ~390 MB (217 MB of it 1 m
terrain), Low ~85 MB. The v1 import shipped 220.8 MB of uncompressed meshes in a 160 MB APK (whole glTFast assets).
Targets for the 4 km² tile on the Galaxy A16 (4 GB): Low/Medium world content in the APK ≤ ~60 MB, run-time mesh memory
≤ ~150 MB.

## Decisions

### 1. Two content tiers, two scenes, no Addressables (yet)
- **Low content** (quality Low + Medium) → scene `WorldC` from `*.low.glb`: terrain band 2 m / 4 m, terrain 4 m / 8 m,
  roads, bridges, markings, paved areas, LOD1 buildings, furniture.
- **High content** (quality High + Ultra) → scene `WorldC_High` from `chunk_*.glb`: terrain band 1 m / 2 m, terrain
  2/4/8 m, the same layers plus LOD0 buildings (openings, docks).
- `GameBootstrap.WorldCSceneForTier()` loads `WorldC_High` on High/Ultra when it is in the build, otherwise `WorldC`.
  Collision is identical in both scenes (built from the Low GLB), so physics never depends on the quality tier.
- The default APK carries only `WorldC`; `build-android.ps1 -WorldHigh` adds `WorldC_High`.
- Addressables (one group per tier) would let a single APK download only one tier, but the A16 is the only measured
  device, the High tier has no flagship to tune it on, and Play Asset Delivery needs an AAB pipeline we do not have.
  Revisit when streaming chunks (floating origin, ADR 0003) is implemented — the per-chunk mesh assets are already the
  unit an Addressables group would hold.

### 2. Bake instead of shipping glTF assets
The importer reads the GLBs directly (`GlbReader`, same axis convention as glTFast: x negated, winding flipped) and writes
one mesh asset per chunk and tier (`Meshes/<tier>/chunk_<id>.asset`). Only the meshes a scene references are in the build.
glTFast stays in the project for future run-time loading (DLC regions) but is no longer on the import path.

### 3. Mesh compression = compact vertex formats + LZ4HC
Not Draco/meshopt: glTFast can decode `EXT_meshopt_compression`/`KHR_draco_mesh_compression` only at import or at run
time — it shrinks the GLB, not the Unity mesh that ends in the build or in memory. Unity's own "mesh compression" only
shrinks the serialized file (decoded back to float32 at load) and quantises positions relative to the mesh bounds, which
is too coarse for 256 m chunks. Instead each vertex stream is stored in the format the shader needs:

| attribute | format | where |
|---|---|---|
| position | float32 × 3 (half would be 6–12 cm at 128–256 m) | all |
| normal | SNorm8 × 4 (fallback float16 × 4 if the editor rejects it) | all |
| COLOR_0 ground masks | UNorm8 × 4 | terrain only |
| TEXCOORD_0 | float16 × 2 | only meshes whose material samples a texture (fence mesh, dock digits, props, trees) |
| TEXCOORD_1 | dropped | not read by the surface shader yet |

Meshes are uploaded non-readable (no CPU copy at run time). Collision meshes stay readable, position-only.
Release builds use `BuildOptions.CompressWithLz4HC`.

### 4. Terrain: 1 m (High) / 2 m (Low) only along roads
`WorldMeshBake.TerrainBand` rebuilds LOD0 terrain from the chunk grid: 8 × 8-cell blocks keep the fine spacing when any
vertex is within 15 m of a road or paved edge (COLOR_0.R), dilated by one block; all other blocks use twice the spacing.
Odd vertices on fine/coarse block edges and on the chunk border are moved onto the coarse edge (no cracks, no skirts
inside the chunk); a 1.5 m skirt on the chunk border hides cracks against a neighbour drawn at another LOD.

### 5. Props and trees: `Graphics.RenderMeshInstanced`, not the GPU Resident Drawer
- GRD needs one GameObject + MeshRenderer per instance (≈ 111 000 here), Forward+ and compute; on a 4 GB Mali-G57 phone
  the GameObject memory and per-object CPU culling defeat the purpose, and GLES3 fallback devices have no GRD at all.
- `WorldInstances` (on the region root) keeps instances in flat arrays sorted by 64 m cell and prototype
  (`WorldInstanceSet` asset). Per camera (`beginCameraRendering`, so mirrors get their own shorter cull): frustum test per
  cell, one LOD for a whole run when the cell lies inside one LOD band, else per instance; 1023-matrix batches,
  one `RenderMeshInstanced` per submesh per batch. No GC per frame.
- LOD end distances at LOD bias 1 (`InstanceImporter.Policy`, WORKING_VALUE): trees 20 / 60 m, impostor to 1000 m;
  shrubs 12 / 40 / 300 m; lamps 60 / 400 m; signs and signals 50 / 250 m; pylons 80 / 1500 m; small props 30 / 120 m.
  They scale with the tier's LOD bias (Low 0.5, Medium 0.8, High 1.5). Hard switches, no cross-fade (to do: dithered
  LOD fade once measured on the A16).
- Device-driven limits (A16 / S24+, DK8 forest, `docs/reports/device/DEVICE-RUN-2026-11-09.md`): tree card LODs
  (LOD0/LOD1) use at most LOD bias 0.5 on every tier (10 / 30 m), trees are thinned with distance (every 2nd beyond
  90 m × bias, every 4th beyond 2.5×), impostors end at 600 m × bias. Alpha-tested leaf cards were the GPU bottleneck.
- Shadows: LOD0 props and LOD0 trees cast (LOD1 trees too on High); impostors never.
- Materials: leaves and impostors URP Lit alpha-clip 0.5 with coverage-preserving mips + alpha-to-coverage (MSAA),
  double-sided (glTF `BLEND` would need per-instance sorting); sign faces alpha-clip, back faces culled (the plate back
  hides the face from behind); bark opaque. Textures are the art-source PNGs with ASTC 6×6 (ASTC 4×4 for sign faces and
  dock numbers), max 1024 px on Android.
- Collision of props: box colliders from the `.col` prototype meshes for instances in the start-route corridor
  (lamps, poles, masts, gates). Trees have no collision yet.

### 6. Collision surfaces
`road_collision` primitives are merged per surface: asphalt → DryAsphalt, concrete / kerb → Concrete, paving / sett →
Cobbles, gravel → Gravel, grass → Grass, steel (fences, guard rails, LOD1 building walls are `concrete`) → Concrete.
Terrain fallback: 2 m grid in the 320 m route corridor, 4 m elsewhere (every chunk now has collision).

## Consequences
- The import no longer copies GLBs into `Assets/` (−480 MB in `Assets/_Generated`, faster import).
- A tier switch at run time (diagnostics overlay) changes rendering settings but not the loaded content tier until the
  world scene is reloaded.
- Numbers (memory, APK, frame estimates) are in `docs/PERFORMANCE_BUDGETS.md`; all UNMEASURED on the phone until the A16
  is unlocked.

## Addendum r7 (2026-11-10) — the same buildings on every tier: LOD1 silhouette parity (HANDOVER pkt 7)

**Problem.** Low content draws `buildings_lod1` for every chunk more than `LowBuildingsLod0M` = 60 m from the start
route, and High draws it beyond the LOD switch. The facade kit put docks, dock shelters, gutters, downpipes, canopies
and chimneys only into LOD0 (`buildings`), and the LOD1 hall wall was one band of the base cladding. Result
(`artifacts/world-fixes/halls-parity/before/sheet_docks_far_7_6_eye_*`): the Kwadrat Park hall in chunk 7_6 (90 m from
the route) had 11 docks and a red top band on High and was a plain ivory box on Low.

**Decision.** A tier changes detail density, never the building:
- `facade_kit.gutter / downpipe / canopy / chimney` emit a LOD1 copy as one box without the faces against the wall or
  never facing the street (`Acc.box(skip=...)`): gutter 6, downpipe 6, canopy 10, chimney 10 triangles.
- `buildings_mesh.build_dock_lod1`: shelter frame (two curtains + header) with the yellow guide stripes, leveller block,
  wheel guides; 54 triangles per dock (LOD0 178) + ~10 for the recessed door opening in the LOD1 wall. Number
  plate, hazard stripes, bumpers, signal and flood lights stay LOD0 detail.
- LOD1 hall walls are built by `FK.wall_pieces` with the LOD0 plinth height (dock floor on dock facades), the LOD0
  colour bands (graphite base / accent top) and the dock doors as recessed openings (reveals + door infill), so the LOD1
  colour and the door rhythm match LOD0.
- Draw calls: every material is one submesh per chunk, so the LOD1 pieces reuse materials LOD1 already draws
  (`FK.L1_MAT`: gutter / canopy / leveller -> `downpipe` grey, shelter / dock reveals -> `hall_flashing` graphite).
  Without this merge the Low dock view cost 332 draws instead of 275 (`after-v1`, `after-v2`).
- Tests: `tests/gis/test_world_tiers.py::test_lod1_keeps_the_silhouette_pieces` (no chunk has a LOD0-only dock / gutter
  / downpipe / chimney), `test_low_variant_carries_the_lod1_silhouette`, `tests/gis/test_world_v31.py::
  test_dock_lod1_silhouette_is_cheap_and_complete`.

**Numbers** (bialystok-industrial-c, 64 chunks, 207 docks; editor estimates before SRP batching, 2340x1080):

| | before | after | delta |
|---|---|---|---|
| `buildings_lod1` triangles, region | 32 633 | 73 267 | +40 634 |
| `buildings` (LOD0) triangles, region | 1 044 774 | 1 044 382 | −392 (chimney bottoms) |
| `*.low.glb` bytes, region | 94 562 504 | 96 915 008 | +2.35 MB (+2.5 %) |
| Unity Low world meshes (buildings) / total | 18.4 / 109.8 MB | 20.5 / 111.9 MB | +2.1 MB |
| Unity High world total | 246.5 MB | 248.5 MB | +2.0 MB |
| Low `docks_far_7_6_eye` draws / shadow draws / tris | 94 / 50 / 128 k | 105 / 55 / 132 k | +11 / +5 / +4 k |
| Low `docks_far_7_6_wide` draws / tris | 96 / 124 k | 107 / 128 k | +11 / +4 k |
| Low `stretch_05_docks` draws / tris | 244 / 250 k | 275 / 261 k | +31 / +11 k |
| High `stretch_05_docks` draws / tris | 463 / 1 100 k | 489 / 1 108 k | +26 / +8 k |
| Generator frame estimate `stretch_05_docks` Low tris | 664 754 | 680 981 | +2.4 % |

`stretch_05_docks` on Low now exceeds the static draw budget of 250 (docs/PERFORMANCE_BUDGETS.md, before SRP
batching; it was at 244). All Kamion/World PBR / Surface materials share one shader, so the SRP Batcher keeps the extra
draws cheap on the CPU, but the phone number decides: measure on the A16 (UNMEASURED); if it costs frame time, the next
lever is merging the LOD1 colour-band materials per chunk (vertex-colour tint of one hall-wall material).

**Tyre marks in front of the docks (HANDOVER pkt 7, "not rendered on Low").** Not reproduced in the editor on
0eb8b84 + this change: Low and High draw the `decal_tyre` strips in both lightings (`*/stretch-05-docks.png`,
`*/docks_far_7_6_eye.png`; apron crop p5/p50 luminance Low 63/168 vs High 67/175 overcast, 37/167 vs 42/173 clear).
Checked: the decal is in the `markings` node of both GLB variants with TEXCOORD_0/1 (Low compact GLB keeps UV),
`WorldPbrMaterials.Channels` keeps UV0/UV1 on both tiers, `_DECAL_TYRE` is a `shader_feature_local` set on the shared
material and not stripped (`ShaderVariantStripper` strips only lightmap / deferred / debug), the lighting path has no
tier branch, and the Low LODGroup keeps `markings` in LOD0-1. The earlier impression came from 1000 px thumbnails of
the 0.75-scale Low frame, where the 0.3-0.46 m broken strips average out. Open: confirm on the A16 (offline in adb).

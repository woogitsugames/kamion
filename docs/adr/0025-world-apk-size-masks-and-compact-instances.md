# ADR 0025 — World APK size: half-size PBR MaskMap/Var on Android, compact instance TRS

Status: Accepted (rendering-perf), 2026-11-10. Extends ADR 0012 (content tiers, instancing), ADR 0022 (world PBR).
Gate 3 item E6 (world payload in the Low/Medium APK ≤ 60 MB, WORKING_VALUE). Target **not met** by this ADR.

## Measurement (editor build, LZ4HC, lean APK, same tree; artifacts/e6/ of the worktree)
"World share" = APK − APK built with `-noWorld` (new measurement flag in `BuildCommands`: drops the
`Assets/_Generated/World/` scenes). Caveat: the world-less APK also loses everything only WorldC references (truck +
trailer meshes ≈ 22.6 MB raw, World PBR / Surface / Vegetation shaders ≈ 6.7 MB raw), so the share is an upper bound.

| | APK | world-less APK | world share | world raw (build report) |
|---|---|---|---|---|
| before (119b2c2) | 159.65 MB | 58.07 MB | 101.6 MB | 133.5 MB (Meshes/Low 73.5, PBR 27.4, Instances 14.6, Collision 11.9, Textures 5.8) |
| after | **152.45 MB (−7.2)** | 58.07 MB | **94.4 MB** | **123.2 MB** (PBR 21.1, Instances 10.6; rest unchanged) |

## Decisions
1. **PBR MaskMap and Var at half resolution on Android** (`WorldPbrMaterials.Import`, Android override
   `maxTextureSize = res/2`; editor/other platforms keep full size; `-fullPbrMasks` restores the old import).
   Mask (metallic / occlusion / detail mask / smoothness) and Var (height / element id / joint / convexity) are
   low-frequency; the downscale is mip 1 of the same tier, so the tier's Toksvig smoothness stays as is.
   BaseColor, Normal, crack layer and detail photo keep full size. −6.3 MB raw (ASTC does not shrink under LZ4).
2. **Instances as compact TRS** (`WorldInstanceSet.positions` float32×3, `rotations` SNorm16×4 quaternion, `scales`
   half×3 = 26 B instead of a 64 B matrix). `Pack` verifies the round trip (≤ 1 mm per metre of basis, translation
   exact) and keeps full matrices for the whole set otherwise (mirror / shear); old assets with `matrices` still load.
   `WorldInstances` decodes once at load and only rewrites translations on an origin shift (no per-shift TRS, zero GC
   in the loop; run-time RAM unchanged). −4.0 MB raw.

## Visual evidence
`scripts/visual-qa.ps1 -Scene WorldC -Tier Low`, 21 control cameras before/after: PSNR 47.5–63.2 dB, pixels with
|Δ| > 8/255 ≤ 0.06 % in every view except `dk8-dk19-exit` (0.49 %): single-pixel speckle on alpha-tested foliage edges
(sub-millimetre instance precision flips coverage samples), no structural or tonal change. Road / yard ground: no
visible change (mean |Δ| ≤ 0.18/255).

## Rejected
- PBR `-MaterialTier Low` for everything (−20 MB raw): halves ground BaseColor/Normal texel density (3.9 → 7.8 mm),
  visible in the first metres of road from the cab.
- Unity mesh compression on world meshes: decompresses to float32 channels at load (SNorm8 normals → 12 B), more PSS.

## Remaining levers for E6
- Render-mesh positions UNorm16×4 per mesh AABB: **rejected on precision** (measured on the Low meshes, 2026-11-10):
  worst rounding error = half a step; only 109 of 505 meshes stay ≤ 1 mm, median 1.95 mm, worst 4.57 mm
  (`7_7_buildings_lod1`, 299 m extent). Meeting ≤ 1 mm needs ≤ 131 m renderers (more draw calls) or 24-bit positions.
- Terrain collision (5.9 MB raw of 11.9) is the 65 × 65 4 m grid of `terrain_lod2` + 260 skirt vertices with a fixed
  triangulation: a height grid (16.9 kB/chunk) rebuilt at load before `Physics.BakeMesh` would save ≈ 5 MB raw; not
  done (needs the glb vertex order mapped and a vehicle-physics check of the collider).
- Collision positions UNorm16 storage expanded before `Physics.BakeMesh`: ≈ −3 MB raw of 6.5 MB positions; the same
  1.95 mm median step at chunk scale, and per-chunk grids would open seams between chunk colliders unless snapped to
  one region grid. Not done (needs a vehicle-physics review).
- Impostor albedo atlases (since world v3.4, ADR 0023): 1536 × 384 imported with NPOT "to nearest" → 2048 × 512 ASTC
  6x6, 614 kB each, 18 atlases = 11 MB raw (`world/Textures` 18.2 MB). Tried `npotScale = None`: Unity then stores
  them uncompressed (3.0 MB each), reverted. Lever for world-builder: bake the atlases at 2048 × 512 (6 views × 341 px)
  or 8 views × 256 = 2048 wide, or pack two trees per POT atlas.
- Reproduction (2026-11-10, merged main 3e0f572, real `import-region.ps1 -Tiers Low` from Data/raw): MaskMap 1024²
  341.5 kB → 85.5 kB in the build report, PBR 27.4 → 21.1 MB raw, Instances 10.6 MB raw.
- Terrain as height grids rebuilt at load instead of three mesh LODs (terrain = 29 MB raw of the meshes).
- Truck/trailer meshes (≈ 22.6 MB raw) are inside the measured share; the High tier as a Play Asset Delivery pack.

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

## Remaining levers for E6 (need a full region re-import, i.e. Data/raw glb chunks; not in this worktree)
- Render-mesh positions UNorm16×4 per chunk (chunk offset + per-axis scale in the renderer transform; ≈ 4 mm in xz,
  < 1 mm in y): −4 B/vertex ≈ −10 MB raw of 73.5.
- Collision positions UNorm16 storage expanded before `Physics.BakeMesh` (WorldCollisionCooker): ≈ −4 MB raw.
- Terrain as height grids rebuilt at load instead of three mesh LODs (terrain = 29 MB raw of the meshes).
- Truck/trailer meshes (≈ 22.6 MB raw) are inside the measured share; the High tier as a Play Asset Delivery pack.

# ADR 0013 — Foliage shader for Low/Medium and MSAA 2× on Medium

Status: Accepted (rendering-perf), 2026-11-09. Extends ADR 0010 (tiers) and ADR 0012 (instanced vegetation).
Evidence: `docs/reports/device/DEVICE-RUN-2026-11-09.md` §"Las DK8 — ablacja GPU", `artifacts/device/RFGL34SJYDZ/20261109-17*`.

## Context
The DK8 forest control camera (`dk8-dk19-exit`) was the frame-rate floor of world C on the Galaxy A16 (Mali-G57 MC2):
Medium 15–17 FPS, Low 28 FPS after D23. There is no vendor GPU profiler yet, so the bottleneck was found by on-device
ablation (`RenderOverrides`, one feature at a time, `FrameTimingManager` GPU time, same camera, 30 FPS cap):

| A16, Medium, DK8 forest | GPU p50 |
|---|---|
| baseline (URP Lit leaves, MSAA 4×, HDR + post) | 61.3 ms |
| trees off | 18.4 ms |
| render scale 0.85 → 0.6 | 37.7 ms |
| MSAA 2× / 1× | 50.4 / 50.4 ms |
| shadows off | 56.0 ms |
| post + HDR off | 57.7 ms |
| alpha-to-coverage off | 58.7 ms |
| tree cull 600 → 300 m / card LOD scale 0.25 | 62.4 / 58.9 ms |

The trees cost ~43 ms and scale with pixel count, not with instance count or distance: fragment work on overlapping
alpha-tested leaf cards. URP Lit runs full PBR (GGX, reflection probe, cascade lookup) on every card layer, and `clip`
with depth write stops the tile GPU from killing hidden layers early.

## Decision
1. **`Kamion/Vegetation`** (`Rendering/Shaders/Vegetation.shader`) for leaf cards and impostors on tiers with
   `QualityProfile.simpleFoliage` (Low, Medium). High/Ultra keep URP Lit.
   - Pass 1 (`SRPDefaultUnlit`, runs before `UniversalForward` for the same draw): depth only, alpha test or
     alpha-to-coverage.
   - Pass 2 (`UniversalForward`): `ZWrite Off`, `ZTest LEqual`, `Offset -1,-1`, same clip/coverage. Hidden card layers fail
     the early depth test before shading.
   - Lighting: Lambert with the sun shadow, back-lit transmission 0.25 (WORKING_VALUE), per-vertex L2 SH, fog. No
     specular lobe, no reflection probe. Leaf specular at the old smoothness 0.25 is a few % of the diffuse.
   - `ZTest Equal` was tried first: no leaf passed it on the A16. The two passes are separate programs, and
     bit-identical depth is not guaranteed without an invariant position.
2. **Runtime swap, assets untouched:** `WorldInstances` draws runtime copies of the generated Lit materials (texture,
   colour, cutoff, alpha-to-coverage).
   - The copies are made from `QualityProfile.foliageMaterial` (`Settings/M_VegetationInstanced.mat`, instancing on).
     The template has to be a material asset. With the shader alone, Unity strips the `INSTANCING_ON` variants (no
     instanced material in the build), and `Graphics.RenderMeshInstanced` draws nothing.
3. **Medium MSAA 4× → 2×.** A16 DK8 forest, GPU p50:
   - Kamion/Vegetation: 64.7 ms at 4×, 36.9 ms at 2×.
   - URP Lit: 61.6 ms at 4×, 50.4 ms at 2×.
   - Cause UNVERIFIED (no GPU counters). The likely cause is 4 HDR samples per pixel exceeding the G57 tile buffer.
   - `QualitySettings.antiAliasing` mirrors the URP asset (`ProjectSetup`).
4. A16 default tier stays **Low** (device rule `Mali-G57 → Low`, `QualityProfile.deviceRules`). Medium remains
   selectable.

## Result (A16, DK8 forest, 30 FPS cap)
- **Low:** 30.0 FPS, GPU 26.1 ms (was 28.1 FPS, 35.5 ms).
- **Medium:** 27.0 FPS, GPU 36.9 ms (was 15.4–16.4 FPS, 61–65 ms).
- **Route, 40 t at 50 km/h (s ≤ 900 m), GPU p50:** Low 16.3 ms, Medium 23.2 ms.
- **Look:** the conifer mass is darker than with Lit, whose probe reflection painted a blue-grey sheen on impostors at
  grazing angles. To be judged by visual-critic against the CC0 photos.

## Consequences / open
- **HLOD "forest walls"** (one card strip per forest edge instead of many impostors): not needed for 30 FPS on Low. Keep it
  as the next lever if Medium has to reach 30 in the forest, or if world v3 adds trees.
- **High on the S24+:**
  - MSAA 4× shows the same pattern on the Xclipse 940: 68 ms (Lit) and 72 ms (Kamion/Vegetation) at 4×, against
    43 ms with Kamion/Vegetation at 2×.
  - The phone was at thermal status 2 and 44 °C, so that run is not valid.
  - Re-measure cool, then decide `simpleFoliage` / MSAA for High.
- Alpha-to-coverage edges in pass 2 depend on the same sharpened alpha as pass 1. Check for shimmer in motion on the
  phone (visual QA in motion, not only stills).

## Addendum r4 (S24+ High, measured cool: 32-36 C, thermal 0; DK8 forest, 30 FPS cap)
| High | GPU p50 | FPS |
|---|---|---|
| Lit, MSAA 4x (current) | 38.7 ms | 25.7 |
| Kamion/Vegetation, MSAA 4x | 31.3 ms | 30.0 |
| Kamion/Vegetation, MSAA 2x | 18.0 ms | 30.0 |
| Lit, MSAA 2x | 21.6 ms | 30.0 |

Evidence: `docs/reports/device/DEVICE-RUN-2026-11-09.md` r4. The r3 S24+ numbers (68/72 ms) were taken at 44 C and are superseded.

Proposal (not applied; QualityProfile is rendering-perf's code, High keeps the current 4x until the owner decides):
- High MSAA 4x to 2x. This is the lever (-17 to -18 ms), and High then holds 30 FPS in the forest with 12 ms to spare.
- Keep Lit on High: Vegetation saves another 3.6 ms at 2x, which does not justify the visual change (specular lobe, probe reflection) on the tier meant to look best. Revisit if High must reach 60 FPS.
- Visual check of 2x vs 4x edge quality on the S24+ is still due (visual-critic).

## Addendum r5 — applied on High (rendering-perf, 2026-11-09)
- Review r3 §7 accepted MSAA 2× on High (no visible edge difference on native S24+ crops) on condition of a 10 s motion
  recording on the S24+ (DK8, flicker of poles, rails, power lines). `QualityProfile` High/Ultra: `msaa = 2`
  (`URP_High`, `QualitySettings.antiAliasing` via `ProjectSetup`).
- Review r3 §7 also passed `Kamion/Vegetation` over Lit ("Lit shows blue-ish see-through sheets instead of crowns", −3.6 ms
  at 2×), and G4 found High foliage greyer than Low: `simpleFoliage` is now on for every tier (one foliage look).

# ADR 0131 — Render P1 fixes on main (s12): crack sealant, road covers at night, FurnitureSign variants, retro bridge GC

Status: implemented on branch `render-p1` (base main `587adc32`, 2026-11-12); not merged.
Source: `docs/reports/visual/REVIEW-2026-11-12-s12-gpt-batch-d.md` (asphalt P1 "white chalk sealant", "black ellipse"
on Putry) and `-batch-c.md` §6 (FurnitureSign full `multi_compile`, FurnitureRetroSource allocations).
Evidence: `artifacts/render-p1/` (before = this worktree with main's shaders and main's materials, after = branch).

## 1. White "chalk" crack sealant (WorldPBR `_CRACKS`, ADR 0099/0118)

Finding: not a texture or colour bug. The crack-layer G channel (sealant band, `sets_asphalt.cracks_layer`) set albedo to
0.03 (correct, black bitumen) but smoothness to **0.55** against ~0.10 of the asphalt. The World PBR env term uses
`lerp(F0, grazing = smooth, Pow4(1 - NoV))`; at the driver's grazing NoV ~0.2–0.3 the sealant reflected 3–4x more sky than
the asphalt and the dark albedo could not compensate → bright white loops, also under overcast (diffuse sky).
Decision: sealant smoothness = asphalt + 0.06 (WORKING_VALUE, aged dust-filmed bitumen). 0.24 was tried first: it
cancelled the dark albedo exactly (sealant invisible, `cmp/sealant-before-after.jpg`). +0.06 gives thin dark bands
(`cmp/sealant-iter2.jpg`, Low clear/overcast). The loop/blob shapes of the mask itself (warped Voronoi) are unchanged —
P2 for the asphalt owner (`art-source/world/materials/_src/sets_asphalt.py`, would need `build_all.py` + reimport).
Files: `Environment/Shaders/WorldPBR.shader` (one line in `_CRACKS`).

## 2. "Black ellipse" on Putry = the Fab manhole cover lit by URP Lit

Finding: `M_fab_metal_manhole_cover` (Megascans scan, ADR 0084) is a URP Lit alpha-test decal. By day it is only slightly
darker than the road (sRGB 84 vs 87 at the cover). At dusk/night the asphalt is lit by the analytic lamp pools and the
headlamp cone (`KamionLampPools.hlsl`, only in World PBR / World Surface) while URP Lit gets none of it → a black disc
("hole") in the beam. Same for `fab_round_drain_cover`, `fab_square_rusty_drain`, `fab_drainage`.
Decision: `FabMaterials` creates cover/drain decals with **Kamion/World PBR `_DECAL_ALPHA`** (world GI, far shadow, lamp
pools, headlamps, Kamion fog), photographed albedo unchanged (tint 1), `metallic_gloss` as `_MaskMap` (A = smoothness),
alpha-blended at Geometry+20 like the oil decals. New uniform `_DecalCells` (default 2 = the oil 2x2 atlas, unchanged; 1 =
whole UV) — no new keyword, no new variants. `FabDecalRetrofit.RunBatch` converts already imported materials (4
converted in the worktree); a regular reimport produces the same state.
Result (`cmp/manhole-before-after.jpg`): Low dusk black blob → cover at road tone with its pattern; clear and High dusk
unchanged within noise.
Files: `World/Import/FabMaterials.cs`, `World/Import/FabDecalRetrofit.cs`, `WorldPBR.shader`.

## 3. `Kamion/Furniture Sign` variants (ADR 0120 r2)

Before: URP Lit forward list copied verbatim (shadows incl. screen, additional lights incl. vertex + shadows, SH modes,
probe blending/box/atlas, soft-shadow qualities, SSAO, screen-space irradiance, DBuffer, cookies, light layers, cluster
loop, foveation, rendering layers, all lightmap keywords, LOD cross-fade, debug display, APV, DOTS) + 9 UsePass incl.
GBuffer, Meta, 2D, motion vectors.
After: `_ALPHATEST_ON`, `_FURNITURE_RETRO` (shader_feature, all materials use both), `_MAIN_LIGHT_SHADOWS(_CASCADE)`,
`_ADDITIONAL_LIGHTS` (StreetLamps point lights), SH eval modes (as Lit), soft-shadow set, fog, instancing; passes
ForwardLit + ShadowCaster + DepthOnly + DepthNormals (Ultra SSAO prepass). Like World PBR the face takes no SSAO and no
probe blending / box projection (nearest probe). Variant numbers: see "Measurements".
SRP Batcher: UnityPerMaterial is LitInput's in every pass; globals of the retro term are outside the CBUFFER → compatible
(`ShaderBatcherAudit`, `variants/batcher-*.txt`).
Tests: `ReturnDoesNotCreateAdditionalPasses` now asserts "≤ Lit passes and ShadowCaster/DepthOnly/DepthNormals present";
the GPU parity tests switch the dropped global keywords off for both draws (parity on the supported subset).
Build tooling: `ShaderVariantCounter.Full()` → `artifacts/apk/*.variants.txt` (all shaders; the top-12 hid this one).

## 4. `FurnitureRetroSource` GC

Before: with a TruckLights whose sockets were incomplete, `GetComponentsInChildren<Transform>` (new array + `name`
strings) ran every second; during 2 s after a scene change on every camera render.
After: sockets are rescanned only when the rig hierarchy (root id, `hierarchyCount`) differs from the last scan, into a
reused `List<Transform>`; a missing rig costs `FindAnyObjectByType` once a second. EditMode
`FurnitureRetroSourceAllocTests` (Unity `Is.Not.AllocatingGCMemory` + `GC.GetAllocatedBytesForCurrentThread`):
complete rig 0 B / 200 frames, incomplete rig with the timer forced every frame 0 B / 200, no truck 0 B / 200, no truck
with a lookup forced every frame 0 B / 50 (editor Mono; device UNVERIFIED).

## Measurements
(filled below from the worktree APK builds)

## Conflicts for the leader
- GPT asphalt: only the `_CRACKS` sealant smoothness line and the `_DECAL_ALPHA` UV block in `WorldPBR.shader` + one CBUFFER
  float. `materials.py` untouched.
- GPT furniture: `FurnitureSign.shader` pragma/UsePass block, `FurnitureRetroSource.BeginCamera`, two tests in
  `FurnitureSignTests.cs`. `FurnitureSignForward.hlsl` untouched.
- `Editor/Build/ShaderVariantCounter.cs`, `BuildCommands.cs`: additive `.variants.txt`.
- After merge: reimport (or `-executeMethod Game.World.Import.FabDecalRetrofit.RunBatch`) for the cover materials.

# ADR 0068 - Fixed-pass cost: cheaper mirror renders, pass telemetry and on-device A/B

Status: proposed (rendering-perf), 2026-11-10. Phone verification UNVERIFIED (no adb used by this agent; the A/B is the
lead's). Extends ADR 0042 / 0046 (mirror budget), 0056 (reflection capture), 0062 (S24+ High ≈ 13 ms of
resolution-independent GPU work). Goal: S24+ High steady 60 FPS without visible quality loss.

## Context (measured, editor RTX 5070, CPU-bound, UNVERIFIED for the phone)
- `Game.Editor.VisualQA.MirrorCostProfiler` (new), WorldC_High, High, every real TRAKT mirror camera, 60 renders each:
  one mirror render = 2.6-4.3 ms CPU submit in the editor (more than half a main view); each view submitted
  270-520 instanced draws and 480-630 k triangles. The regular triangles came mostly from one world chunk (131 k) and the
  **own cab interior (81 k triangles in every mirror view, LOD0 because the mirror is 1-2 m away)**, seen at most at a
  grazing angle through the side glass.
- The mirrors rendered at the main view's LOD bias (1.5): a class II texture is 384 px over 35-44° (≈ 9-11 px/deg) vs
  ≈ 25 px/deg in the main view, so its LODs were 2-3× finer than its pixels.
- Shadows (`TierCostProfiler`, gate-3 cameras, `perf/tiercost-High-20261110-195843.tsv`): whole shadow pass
  0.9-1.6 ms wall in the editor; 2 cascades / 80 m / 1024 px / soft off are within the run noise (±0.7 ms). No evidence
  for a shadow change → none made; phone A/B switches added.

## Decision (High only; Low / Medium / Ultra unchanged)
1. **Per-camera LOD bias for extra views** (`Game.Core.ExtraViewLod`, `IExtraViewCamera`): while a mirror renders,
   `QualitySettings.lodBias` = tier × scale (restored at endCameraRendering); `WorldInstances` uses
   `ExtraViewLod.EffectiveLodBias(cam)` (independent of handler order). High: class II 0.5, convex 0.3 (pixel-equivalent
   ≈ 0.35 / 0.2; margin for the HUD inset that shows class II at ≈ 1:1). Capture faces (128 px / 90°): 0.25
   (only LODGroups; the instanced world already skips Reflection cameras). Instanced triangles per mirror −50 %.
2. **Class II and IV mirrors do not draw the own-cab interior** (`forceRenderingOff` between begin/end of that camera).
   Classes V and VI keep it: the class VI image looks down through the windscreen and showed the empty cab without it
   (`montage/crop_front_glass.png`, first try, reverted for VI/V).
3. **Due-based schedule on High** (`MirrorRefreshSchedule.StepDue`): mirrors render when their interval has passed,
   staggered by phase (even load). Driving: II every 2nd frame, IV/V/VI every 4th, spare slots to II/IV — identical cadence
   to ADR 0046 (test). Standing (< 0.5 m/s, < 3°/s for 0.5 s): II unchanged (30 Hz), IV ×2, V/VI ×4, no spare fill →
   1.375 instead of 2 renders/frame. The worst case (driving, six on screen) stays 2 renders/frame.
4. Unchanged by design: camera position, aim, field of view and aspect (UN R46 fields; `MirrorFieldOfVisionTests`
   and the new `MirrorCostTests.MirrorRender_KeepsOptics_RestoresLodBias`), texture size (384 px; the pixel cost of
   171×384 is ≈ 1.5 % of the main view, so a smaller RT + sharpening would buy nothing and blur the HUD inset), far clip,
   cap 2, no shadows / post / MSAA (already so since ADR 0042). Not done: one RT atlas / shared culling - every mirror is
   its own camera with its own view matrix in URP, an atlas saves no culling or submit, only render-pass switches.
5. **Capture interval and shadow settings unchanged** (no measurement justifying a change; see A/B below).

## Result (editor, 3 interleaved runs, `artifacts/mirror-r9/perf/mirrorcost-High-*.tsv`)
| per frame, driving, all six on screen (1 II + 1 convex render) | legacy | ADR 0068 |
|---|---|---|
| CPU submit (editor) | 6.30-7.36 ms | 5.37-5.84 ms (−12 to −21 %) |
| triangles class II view | 621 k | ≈ 476 k (−23 %) |
| triangles convex view | 633 k | ≈ 320 k (−49 %) |
Standing: −31 % renders. Control frames (`before/`, `after/` High overcast, 2340×1080): mean |Δ| 0.00-0.22 / 255,
mirror crops identical to the eye (`montage/`). Phone ms UNVERIFIED.

## Telemetry (works in release players)
- `[DIAG] ... mir=<renders/frame> cpu=<ms> gpu=<ms|-> cap=<faces/frame> cpu=<ms> gpu=<ms|-> shd_gpu=<ms|-> main_cpu=<ms>`
  (`ExtraViewCostMonitor`: main-thread ms between begin/endCameraRendering per view kind; GPU via Recorder only in
  development players). frametimes.csv gains `mirror_n,ab`.
- **On-device A/B** (`rq_ab <key>`, `rq_ab_period 4`): alternates shipping (A) and a variant (B) every period, logs
  `[PASSAB] key state gpu_p50 gpu_p90 cpu_p50 ...` per window and a running `[PASSAB] summary` (A−B). Keys: `mirrors`
  (B = none), `mirrorcfg` (B = pre-0068), `mirrorlod`, `envcap` (B = no faces), `shadows` (B = distance 0),
  `shadowcasc` (B = one cascade fewer). Run with `rq_scale 1.0 rq_pacing 0` (else the adaptive scale reacts).
- Fixed overrides: `rq_mirror_cap|lod|far|res|rate|legacy|off`, `rq_envcap_iv`, `rq_envcap_lod`, `rq_shadowcasc`, `rq_shadowres`.

## Phone runs for the lead (S24+ High, cab view driving, same APK)
`-e rq_scale 1.0 -e rq_pacing 0 -e rq_ab mirrorcfg`, then `rq_ab mirrors`, `envcap`, `shadows`, `shadowcasc`
(≥ 90 s each). Decide from the `[PASSAB] summary` GPU/CPU deltas: if `mirrors` A−B is still > 2 ms GPU, next lever is
the cap (High 2 → 1.5 average) or class IV interval 6; if `shadowcasc` saves > 1 ms with no visible near-shadow loss, take 2
cascades. Also an A16 Low run with `rq_mirror_lod 0.5` (Low keeps 1 here).

## Files
`Core/ExtraViews.cs`, `Vehicle/Runtime/RenderTextureMirror.cs`, `Vehicle/Runtime/MirrorRefreshSchedule.cs`,
`World/Runtime/WorldInstances.cs` (one line, world-builder FYI), `Rendering/Runtime/{ExtraViewTag,ExtraViewCostMonitor,
RenderOverrides,QualityProfileApplier}.cs`, `Rendering/Runtime/Truck/VehicleReflectionCapture.cs`,
`Telemetry/DiagnosticsSampler.cs`, `Editor/VisualQA/MirrorCostProfiler.cs`, `Tests/EditMode/MirrorCostTests.cs`.

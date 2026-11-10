# ADR 0046 - High tier headroom for 60 FPS (gate 3, Galaxy S24+)

Status: proposed (rendering-perf), 2026-11-10. Phone verification UNVERIFIED (no phone used; S24+ is the owner's phone).
Changes only High. Low/Medium unchanged. Extends ADR 0010 (tiers), 0013 (MSAA), 0042 (mirror budget).

## Context
Gate 3, S24+ High, 60 FPS cap: G3-A p50 16.7 / p95 50.0 / p99 50.1 ms, G3-B 16.7 / 33.5 / 50.1 ms, thermal 2 (fefd804).
The earlier cool run (9d46b38, `artifacts/gate3/20261109-232246/RZCX60VE8ZY/drive/frametimes.csv`, 25.9 -> 32.2 C,
thermal 0) already showed the pattern, so it is not only throttling:
- GPU (FrameTimingManager) p50 14.8 / p95 16.2 / p99 16.9 ms, CPU main p50 12.6 / p95 18.4 ms; screen 3120x1440 (QHD+),
  render scale 1.0 = 4.49 Mpx with MSAA 2x + HDR + post.
- 401 of 3682 frames > 20 ms; in those frames GPU median 15.0 ms and CPU 11.9 ms - the same as in good frames.
  Spike spacing is mostly every 2nd/4th frame; per-frame correlation frame_ms vs gpu_ms is |r| < 0.27 at any lag.
  => vsync-quantised misses: GPU work at ~89 % of the 16.7 ms interval leaves no slack for compositor / DVFS jitter, and
  sustained ~90 % GPU load is what heats the phone (thermal headroom 0.44 -> 0.75 in 70 s).
- Target: GPU p50 <= 12 ms on the G3 views (-19 %).

## Editor measurement (and why it cannot rank GPU features)
`Game.Editor.VisualQA.TierCostProfiler.Run` (new): WorldC_High, High, 10 G3 driver-eye cameras, 3120x1440, 10 synced
renders per camera per variant, plus a mirror proxy (3 renders 173x384, far 400 m, no shadows/post/MSAA).
Result: `docs/reports/perf/tiercost-High-20261110-093732.tsv` (RTX 5070, shared with another Unity process).
- Editor is CPU-bound: CPU submit = 70-85 % of wall time; base repeated 5.61 / 5.82 ms, variants scatter +-25 %
  (scale 0.75 measured *slower* than 1.0). Pixel features (scale, MSAA, soft shadows, post) are not resolvable here.
- What it does show: **3 mirror renders cost 6.3 ms vs 5.6 ms for the main view** (CPU culling + submit of the whole
  world 3x). Workload estimate per G3 view: 510-640 draws, 360-540 shadow draws, 1.07-1.30 M tris (before SRP batching).
  Removing all trees: -16 % wall (4.69 vs 5.61), i.e. trees are a visible but not dominant CPU share.

## Top 3 contributors (High vs Medium content; ms are phone estimates, UNVERIFIED)
1. **Resolution**: High renders 4.49 Mpx vs Medium 3.25 Mpx (0.85) - every pixel pays MSAA 2x HDR resolve, world PBR,
   foliage A2C and post. If ~70 % of the 14.8 ms is pixel-bound, 1.0 -> 0.85 saves ~2.9 ms.
2. **Mirrors**: 3 renders/frame on High (Medium 2) at 384 px, far 400 m: in the editor more CPU than the main view; on the
   phone mostly vertex/binning + render-thread cost. 3 -> 2 saves ~1/3 of it; est. 0.8-1.5 ms GPU, more on CPU main.
3. **Shadows**: 100 m, 3 cascades, 2048, soft Medium (9-tap), LOD0+LOD1 tree casters (Medium: 60 m, 2 cascades, hard,
   LOD0). Soft Low (4-tap) and LOD0-only tree casters: est. 0.6-1.2 ms. Distance/cascades kept (visible on the road).

## Decision (High only; revision 2 after the coordinator / owner priority "quality first")
A fixed 0.85 would pay the softer image on every frame, also where the GPU has slack. Instead:
- **Adaptive render scale** (`AdaptiveRenderScaleController`, `AdaptiveFrameDriver`; tier fields `adaptiveScaleMin` 0.80,
  `renderScale` stays 1.00): FrameTimingManager GPU time, tumbling 2 s windows, p90. p90 < 0.78 of the frame interval
  (13 ms at 60 FPS) -> step up 0.05 towards 1.00 if the pixel model (GPU ~ scale^2) keeps the next step under the
  step-down line; p90 > 0.90 of the interval (15 ms) -> from 1.00 straight to 0.85, then 0.80 only if p90 is still
  > 15 ms after the next 2 s window at 0.85 (visual-critic: 0.85 PASS, 0.80 conditional PASS as a short state); in between hold. At most one change per 2 s, multiples of 0.05, floor 0.80. Devices without GPU timings stay at 1.00.
  Disabled with the profiling override `rq_scale`; not active in the editor (it writes the URP asset).
- **Thermal fallback** (`ThermalFpsGovernor`, tier field `thermalFallbackFps` 30): thermal status >= 2 for 30 s -> 30 FPS
  cap; back to the requested cap after status <= 1 for 60 s. Status polled every 5 s (JNI call, a small allocation per
  poll; nothing per frame). 30 rather than 40/45: the CSV shows 60 Hz quantisation, so 40 would judder.
- **Shadows soft Low + LOD0-only tree casters: kept.** A/B frames (below) show no visible difference: mean abs diff vs soft
  Medium + LOD0/1 casters <= 0.25/255 on every crop (0.00 overcast), penumbra identical by eye at 1:1 low sun.
- **Upscaler: FSR 1.0** (`m_UpscalingFilter` FSR, RCAS sharpness 0.75 override) on URP_High; URP runs it only when the
  render scale is < 1 (needs post-processing, on for High). Cost estimate: EASU + RCAS = two full-output-resolution passes
  (4.49 Mpx), est. 0.4-0.8 ms on Xclipse 940 against the ~2.3-3.3 ms saved at 0.85 (UNVERIFIED, not measured). Fallback
  if it is too slow or rings: bilinear upscale + a CAS-only sharpen in the uber post (one pass, est. 0.2-0.3 ms).
- Kept: MSAA 2x, HDR, shadow 100 m / 3 cascades / 2048, HLOD 120 m, LOD bias 1.5, far clip 2500 m, reflection capture.
- Low / Medium: unchanged (fields 0 = off).
Estimate on the S24+ G3 views: at 14.8 ms the controller holds 1.00 (band 13-15 ms); spikes of the hot run (GPU p95
19.3 ms, fefd804) step to 0.85 (~13.9 ms) - UNVERIFIED.

## A/B frames (editor, for visual-critic)
`C:/Users/matma/Documents/Claude/kamion/artifacts/perf-high-ab/` (README.txt, diff.tsv): 4 G3 eye cameras x overcast/lowsun,
scale 1.00 / 0.85 / 0.80 with the new shadows, plus 1.00 with the old shadows, 1024 px crops near/mid/far.
Scale 0.85/0.80 vs 1.00: mean abs diff 1.0-3.5/255, visibly softer thin lines on 1:1 crops (railings, overhead wires,
pylon lattice) - the trade the controller only takes under GPU load. Phone view UNVERIFIED.

## Open items
- **Mirrors 3 -> 2 renders per frame on High** (`Vehicle/Runtime/RenderTextureMirror.cs`, `VehicleCameraBudget.MirrorsPerFrame`,
  owner: vehicle / lead). Editor proxy: 3 mirror renders 6.3 ms vs 5.6 ms main view (CPU culling + submit of the whole
  world 3x). With 2/frame the main mirrors still refresh >= 30 Hz at 60 FPS (weighted round-robin, ADR 0042).
  Est. -0.8..1.5 ms GPU and a larger CPU main saving (S24+ CPU main p95 18.4-20.7 ms is also over 16.7). Needs a
  phone A/B and a check that the wide-angle mirror stays usable (docs/06: mirrors always usable).
- Adaptive thresholds are WORKING_VALUE; tune from the phone log lines `[PERF] adaptive render scale`.

- Open checks (visual-critic): (a) the S24+ native resolution in the build - the gate log says 3120x1440 (QHD+), the
  phone default is FHD+ 2340x1080; at FHD+ the pixel load is -44 % and the controller would likely stay at 1.00;
  (b) motion shimmer on wires / railings at 0.85 / 0.80 with FSR (10 s recording, driving); (c) a control camera with a
  readable direction sign at 0.85 / 0.80 (legibility of the white text on blue).

## Verification needed
S24+ High G3-A/G3-B (`gate3-run.ps1 -Tier High -Fps 60 -WorldHigh`) with logcat `[PERF]` lines; A/B with `-e rq_scale 1.0`
(adaptive off); 30 min thermal run for the fallback. Owner's consent for the phone.

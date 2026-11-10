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

## Decision (High only)
- `renderScale` 1.0 -> **0.85** (2652x1224 on QHD+; ~440 ppi effective, still above FHD+ native 2340x1080).
- `softShadowQuality` Medium -> **Low**; `treeShadowLodMask` 3 -> **1**.
- Kept: MSAA 2x, HDR, shadow 100 m / 3 cascades / 2048, HLOD 120 m, LOD bias 1.5, far clip 2500 m, reflection capture.
- Proposed to the vehicle owner (not in this change, `Vehicle/Runtime/RenderTextureMirror.cs` MirrorsPerFrame):
  High 3 -> 2 mirror renders per frame (main mirrors still refresh >= 30 Hz at 60 FPS).
Estimate: 14.8 ms -> ~11.5-12.0 ms GPU p50 (scale -2.9, shadows -0.6..1.2) before the mirror change. UNVERIFIED.
Trade: slightly softer image on QHD+ (render-scale upscale, no sharpening) and harder shadow penumbra; needs a
visual-critic pass on High G3 renders before merge.

## 60 FPS cap vs adaptive
Recommendation: keep the 60 FPS cap on High and add an **adaptive render scale** (0.75-0.90, from FrameTimingManager GPU
p90 over ~1 s, step 0.05 with hysteresis, only downward when GPU p90 > 14 ms, up when < 11 ms) - URP render scale, not
`ScalableBufferManager` (Vulkan dynamic resolution needs per-camera opt-in and gave no measured benefit yet). If thermal
status >= 2 persists, fall back to 30 FPS rather than an uneven 40-50 FPS (60 Hz quantisation seen in the CSV).
Not implemented here: needs a phone A/B (owner's consent).

## Verification needed
S24+ High G3-A/G3-B with this tier (`gate3-run.ps1 -Tier High -Fps 60 -WorldHigh`), then the same with
`-e rq_scale 1.0` for the A/B; 30 min thermal run.

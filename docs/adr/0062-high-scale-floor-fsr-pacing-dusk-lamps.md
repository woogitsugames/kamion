# ADR 0062 - High render-scale floor 0.70 + FSR 1.0, frame-pacing fallback; dusk = civil twilight with lamp pools

Status: proposed (rendering-perf), 2026-11-10. Owner decision D36 (docs/11). Phone verification UNVERIFIED (no phone used
by this agent; the A/B is the lead's). Extends ADR 0046 (High adaptive scale + thermal fallback), ADR 0010/0016 (sky,
exposure), review r4 L3 (street lamps). Answers review r8 N-24 (S24+ High 43-47 FPS) and N-20 (dusk without lamps).

## Part A - S24+ High does not hold 60 FPS

### Why the phone showed 43-47 FPS with judder instead of scaling down (measured, r8 logcat)
`artifacts/gate3/20261110-172908/RZCX60VE8ZY/logcat-run.txt` and `.../20261110-175241/...`:
- `[PERF] adaptive render scale 0,85 (GPU p90 24,6 ms)` at t≈3 s, `0,80 (GPU p90 21,2 ms)` at t≈5 s. The controller was
  **not lazy**: it reached the ADR 0046 floor 0.80 within 4 s and then stayed clamped there for the rest of the run.
- At 0.80 the GPU (FrameTimingManager) stayed at p50 17.3-22.3 / p90 18.5-24.0 ms (frametimes.csv, 2-102 s windows) and
  CPU main thread p50 14.2-16.2 ms. 25-42 % of frames took > 20 ms: vsync quantisation (16.7 / 33.4 ms alternating).
- From the two logged steps the GPU time is far from proportional to pixels: 25.8 ms at 1.00 vs 22.3 ms at 0.85
  (pixels -28 %, GPU -14 %). A two-point fit GPU = a + b·s² gives a ≈ 13 ms of resolution-independent work
  (shadow maps, 3 mirror renders - ADR 0042/0046 measured them at the main view's cost in the editor -, the vehicle
  reflection capture, MSAA-independent passes) - noisy (boot windows, different views), **UNVERIFIED**.
- Consequence: the floor alone cannot reach 60. By the same fit 0.70 gives ≈ 19.4 ms p90 (from 21.3 at 0.80), i.e.
  -1.5 to -2 ms; the reviewer's 12-15 ms estimate assumed a pixel-bound GPU. The rest needs either fewer fixed passes
  (ADR 0046 options: mirror rate, capture rate, shadow cascades) or a steady 30.

### Decision
1. **High floor 0.70** (D36): `QualityProfile.Defaults()` High `adaptiveScaleMin = 0.70`; existing assets migrate via
   `QualityProfile.revision` 62 in `ProjectSetup.LoadTiers` (a floor tuned away from 0.80 is kept).
2. **Predictive step-down** (`AdaptiveRenderScaleController.Decide`): over the 15 ms line the controller takes the larger
   of the old minimum cut (1.00 → 0.85, then one 0.05 step) and the cut the pixel model needs to land on 14 ms
   (`s·sqrt(14/p90)`, quantised down). The pixel model over-predicts savings (fixed passes), so the jump never
   overshoots the real need; moderate overload (≤ 17.5 ms at 1.0) still stops at 0.85 (visual-critic PASS).
   S24+ r8 case: 25.8 ms → 0.70 in the first 2 s window instead of 0.85 → 0.80 in 4 s.
3. **Frame-pacing fallback** (`FramePacingGovernor`, tier field `pacingFallbackFps`, High = 30): when the scale is at
   its floor and > 10 % of frames miss vsync (> 1.25 × interval) for 3 consecutive 2 s windows, the cap drops to 30 FPS.
   At 30 the scale controller climbs back to 1.0 (thresholds follow the cap), so the fallback is D36 option (b) - full
   sharpness, no judder - and is only reached when option (a) is not enough. Recovery after 20 s of GPU p90 projected to
   the floor (pixel model) and CPU p90 both < 80 % of the 60 FPS interval; each relapse within 2× the wait doubles it
   (max 160 s), so a scene that cannot hold 60 does not ping-pong. Owner ranking: (d) "43-47 FPS with judder" was "not
   recommended"; this governor makes (d) impossible. Off switch: `pacingFallbackFps = 0` or launch arg `rq_pacing 0`.
4. **Upscaler: FSR 1.0** (`upscalingFilter = FSR`, `fsrSharpness = 0.6`) on High (URP asset written by
   `ProjectSetup.CreateUrpTierAssets`; used only while scale < 1). Considered:
   - *Bilinear* (old): free, but at 0.70 (2184×1008 → 3120×1440) markings, kerb edges and the TRAKT lettering go soft.
   - *STP* (URP 17 spatial-temporal): best reconstruction on paper, but it is TAA-based - URP requires render graph,
     compute and **no MSAA**; our High relies on MSAA 2× + alpha-to-coverage leaf cards (ADR 0013), mirrors are separate
     cameras without history, and fast lateral motion of a cab view ghosts. Extra motion-vector + history bandwidth on a
     tiler. Rejected for mobile now.
   - *FSR 1.0* (EASU edge-adaptive upscale + RCAS sharpen): spatial, one full-res pass on top of the final blit, keeps
     MSAA and A2C, no history/ghosting, supported on Vulkan (SM 4.5). Sharpness 0.6 instead of URP's 0.92: RCAS at 0.92
     rings on high-contrast markings and wires (docs/06 "no HDR look / oversharpening"). WORKING_VALUE, phone crop check.
   - Cost of the EASU pass at 3120×1440 on Xclipse 940: UNVERIFIED (expected well under 1 ms; must be < the saving
     between 0.80 and 0.70, otherwise use `rq_upscale linear`).
   Low/Medium keep Auto/bilinear: Low has no post pass (FSR would add the final post pass on the A16), Medium has a fixed
   0.85 and no A16 measurement.
5. **Telemetry**: `[DIAG]` ends with `scale=<s> fallback=<none|thermal|pacing>`; frametimes.csv gets a `render_scale`
   column (headers are parsed by name in `device-metrics.ps1`), summary.json `renderScale` / `capFallback`;
   `[PERF] adaptive render scale ... floor 0.70, upscaler FSR` and `[PERF] pacing fallback ...` lines.
6. **A/B launch args** (RenderOverrides): `rq_scalemin 0.8|0.7`, `rq_upscale linear|fsr|stp`, `rq_fsrsharp`,
   `rq_pacing 0`, `rq_lamppools N`.

### Phone A/B the lead should run (S24+ High, G3-A/G3-B, same build)
`rq_scalemin 0.8 rq_upscale linear rq_pacing 0` (old behaviour) vs default (0.70 + FSR + pacing) vs
`rq_scalemin 0.7 rq_upscale linear rq_pacing 0` (FSR cost). Report p50/p95/p99, GPU p50/p90 from the CSV split by
`render_scale`, share of 30 FPS time (`fallback=pacing`), and a 1:1 crop of markings/TRAKT at 0.70 FSR vs 1.0.

## Part B - Dusk: street lamps do not read (r8 N-20)

### Cause (measured from the r8 phone frames + model numbers)
- Lamp glass emission works: `truck-34_dusk` (S24+) lamp head max 255/255/255, the strip clips white.
- The **pools** are missing because LP_Dusk had the sun at **+1°**: the sky model gives ≈ 2.4 klx horizontal there,
  while a road luminaire (I ≈ 2500 cd down, WORKING_VALUE) gives ≈ 30-40 lx under an 8-9 m head - 1-2 % of the
  background, physically invisible (and real Polish twilight switches would not even be on yet). Exposure (EV100 11.4)
  kept the scene bright, so the frame read as "a darker overcast day".
- Low/Medium had no pools at all (`streetLights = 0`: point lights are High-only).

### Decision
1. **LP_Dusk = civil twilight, sun −4°** (az 300°, hazy as before). `SkyModel` keeps the 0.5° sky shape and colour
   (afterglow toward the sun's azimuth) and dims it by `TwilightFactorAt(el)`: log-linear from 1 at 0.5° to 3.4 lx at
   −6° (end of civil twilight, commonly quoted value, UNVERIFIED from memory of Bond and Henderson-type tables). No
   direct sun below the horizon (the sun light switches off), `TrueSunElevationDeg/TrueSunDirection` drive the sun light
   transform (cab clock, auto dipped beam), the lamp switch and the exposure. At −4°: ≈ 21 lx sky.
2. **Exposure follows the twilight** (a phone lengthens its exposure): `ExposureTable.Ev100(el < 0.5)` =
   EV(0.5°) + log2(twilight) + 0.2 EV by −4°. The ambient-lit scene stays ≈ 2.9 EV under overcast noon (r3 G3 range
   1.9-3.1 kept, test `ExposureTable_HighSunUnchanged_LowSunWalls_DuskDarker`), while emissive lamps (fixed cd/m²) and
   their pools gain ~85× on the background.
3. **Analytic lamp pools on every tier** (`lampPools`: Low 4, Medium 6, High/Ultra 8): `StreetLamps` sends the lamp heads
   nearest a focus 30 m ahead of the camera to `Kamion/World Surface` as a global array (xyz + fade weight; re-chosen
   4×/s; a lamp near the edge of the set fades out over the last 25 % of the distance to the first lamp left out, so
   re-choosing does not pop). The shader adds inverse-square Lambert light with a full-cutoff luminaire shape (constant
   to 60° from nadir, zero at 75°) and URP's smooth 35 m range window; uniform-branch loop, no variants, no lights, no
   shadows. Same photometry as the point lights (`I·k/π`). Cost: dusk only, ≤ 8 × ~20 ALU per world pixel
   (UNVERIFIED on the A16 - switch: `lampPools = 0` / `rq_lamppools 0`).
4. The High point lights stay (4 nearest the camera) but light only vehicles and props; World Surface no longer reads
   URP additional lights, so nothing is lit twice.
5. Expected pool contrast: 39 lx under an 8 m head on 21 lx ambient = 2.9× (test
   `DuskPreset_IsCivilTwilight_LampsOn_PoolsReadOnTheRoad`); r8 acceptance ≥ 1.5×.

### Not covered (other owners)
Car lights and lit windows at dusk (world-builder / gameplay); lamp head position = top of LOD0 bounds over its centre,
so the pool sits ~half an arm length toward the pole (world-builder can export the luminaire point).

## Evidence
See `artifacts/scale-r8/STATUS.md` (worktree) for test results, before/after control cameras and the editor cost table.

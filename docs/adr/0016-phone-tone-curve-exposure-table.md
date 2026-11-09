# ADR 0016 — Phone tone curve and sun-elevation exposure table (D23 v2)

Status: Accepted (rendering-perf), 2026-11-09. Supersedes the tonemapping and exposure parts of ADR 0010 and the D23 v1
grading (contrast −10, linear lift 0.03). Review: `docs/reports/visual/REVIEW-2026-11-09-r3.md` §0, G1–G5, C1, C2.

## Context
- D23 v1 put a 0.03 lift in linear light before the Neutral tonemapper: display black 21 % sRGB, and Neutral (white level
  5.3) never went above ~85 %. Review r3 G1: "milk", tonal range 21–80 %, while the CC0 phone photos have 1–5 % black in a
  cab and clip 2–20 % of an overcast sky.
- Exposure was an incident meter on the horizontal illuminance (+1 EV). At 9° sun the walls facing the sun got 3–6× the
  horizontal illuminance and clipped flat (G2); at dusk the meter compensated the falling light, so dusk was brighter
  than overcast noon (G3).

## Decision
1. **Tone curve instead of Neutral** on every tier with post-processing: URP tonemapping None + a master curve
   (ColorCurves, evaluated in the HDR grading LUT in FastTonemap space), built by `LookGrading.MasterCurveKeys`.
   Scene linear → display sRGB: black floor 1.5 % (lift after the curve), 0.0025 → 3.8 %, 0.01 → 11.5 %, 0.03 → 21 %,
   0.18 → 48.5 % (ADR 0010 mid-grey kept), 0.33 → 62 %, 0.5 → 79 %, hard clip at 0.7. Monotone cubic (Fritsch–Carlson).
   Highlight desaturation (Lum vs Sat) from 0.32 to 0.53 luminance so a clipped sky goes white, not yellow (G5).
   No extra pass: the curve is baked into the existing LUT. Low (no post) is the plain sRGB clip at 1.0, which has the
   same toe and mid-grey, so the tiers stay close (control frames: Low and High medians within 2–7 points).
2. **Exposure table** (`ExposureTable.Ev100`): camera EV100 from sun elevation and cloud, like a phone's scene metering.
   Clear: 0° 11.5, 5° 12.5, 10° 13.3, 20° 13.5, 30° 13.7, 45° 13.9, 90° 14.0. Overcast: 10.0 … 11.6. High sun is
   unchanged (incident meter + 1 EV within 0.15 EV, test). 9° sun: a 0.6-albedo wall facing the sun ≈ 0.6 linear
   (~88 %) instead of 2.8. Dusk (1°, hazy): ~2.4 EV darker on screen than overcast noon (test 1.9–3.1 EV).
3. **Presets are code.** `LookDevAssets.EnsureAll` rewrites `LP_*.asset` from `LightingPreset.Create*` (the clear and
   overcast assets had drifted by hand).
4. Cab: the fill bounce is split into a sun part (sun colour) and a sky part (neutral) with a mild tint (C2).
   Cab displays get `Kamion/Cab Display` (black base, emission in exposed units with a readability floor, hood-occluded
   cover reflection; the cluster cover glass mesh is dropped): contrast 67:1 overcast, 160:1 at low sun (target ≥ 8:1, C1).

## Measured (editor control frames, 2340×1080, luminance percentiles; review r3 targets in brackets)
| Frame | p1 | p50 | p99.9 | > 98 % |
|---|---|---|---|---|
| High overcast cab-dash | 0.8 % [≤ 4 %] (was 12.5 %) | 21.5 % | 95.9 % | 0 % |
| High low-sun cab-dash | 0.4 % (was 20.8 % on the S24+) | 17.9 % | 95.0 % | 0.3 % |
| High overcast truck-34 | 19.2 % | 56.1 % | 100 % [≥ 97 %] (was 80 %) | 24 % (sky) |
| High dusk truck-34 | 8.6 % | 29.2 % (overcast 56 %, was 65 % vs 58 %) | 91 % | 6 % |

## Consequences
- The curve and the table are WORKING_VALUE until compared with owner photos at the same place and time.
- A phone's local tone mapping is not modelled (one global curve): deep shade next to a lit wall stays darker than on a
  phone. A cheap local operator is the next lever if the owner asks for "brighter shadows".
- Visual QA on the phones (`device-r2`) is the acceptance evidence, not the editor frames.

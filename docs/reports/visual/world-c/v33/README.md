# World C v3.3 (ADR 0019) — before / after frames

Unity frames: `pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low` and `-Scene WorldC_High -Tier High`, overcast unless
named, 2340 × 1080 shrunk to 800 px. "before" = main at 88d51c4 (import of 2026-11-09 21:04), "after" = this branch.
Blender: `render_control.py --light overcast --samples 48` (own procedural materials; shows geometry changes only).
`photo_biezenstwa_vs_unity.jpg` contains the CC0 photo `20201102_152339` (Rakoon, Wikimedia Commons, docs/REFERENCES.md).

| File | What to look at |
|---|---|
| `ba_high_truck-34.jpg`, `ba_high_cab-dash.jpg`, `ba_high_stretch-05-docks.jpg` | first frame of the player: textured yard (behaton, concrete apron, tyre scrub alpha, gully), sandwich-panel hall, sectional doors, curtain / box trailers (r4 W-H1) |
| `ba_high_kwadrat-park-gate.jpg`, `ba_high_stretch-01.jpg` | worn asphalt with cracks / wheel paths, kerb units, grass verge, painted truck stands |
| `ba_high_driver-andersa-to-putry.jpg` | sterile asphalt → worn PBR asphalt; grass instead of beige trough (r4 W-H5/W-H6, r3 W3) |
| `tiers_*.jpg` | Low vs High: the block left of Andersa is the same windowed green block on both tiers (r4 W-H4) |
| `photo_biezenstwa_vs_unity.jpg` | asphalt sRGB mean 0.49 vs photo 0.48 (crop of the near carriageway); piers 0.42 albedo, dark soffit |
| `lowsun_stretch-01.jpg` | same materials at low sun, Low and High |
| `blender_*.jpg` | Blender before/after: stall lines, accent window zones on LOD1, supports under the lines |

Known, not fixed here: dotted "arcs" over the DK8 forest on Low are tree crowns (still there with the wire material
switched off, `artifacts/visual-qa/exp_nowire`), not power lines: vegetation LOD1 / impostor alpha on Low (rendering-perf).

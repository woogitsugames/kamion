# World C v3.4 (ADR 0023) — forest impostors / HLOD, understorey, signs: before / after

Unity frames: `pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low` and `-Scene WorldC_High -Tier High`, 2340 × 1080
shrunk to 1000 px. "Before" = v3.3 assets (main at ce667be) rendered in this worktree before the re-import; the shader
change of the forest floor was already compiled for the Low lowsun / High before frames (it only affects the floor).
Blender: `render_control.py --light both --samples 48` (Blender 4.2.9; "before" from the main checkout, read only).
CC0 photos: Wikimedia Commons, licences in `docs/REFERENCES.md`.

| File | What to look at |
|---|---|
| `ba_low_dk8_overcast.jpg`, `ba_high_dk8_overcast.jpg` | DK8 from the cab: lit 6-view impostors (no crossed-quad slivers), understorey (hazel, young pine / birch) instead of a swept beige hall, needle / moss floor |
| `ba_low_dk8_lowsun.jpg` | the beige "camouflage" on the stand edge (r3 W2) is gone: impostors and HLOD walls are lit by the sun and the sky SH like the near trees |
| `crop_dk8_arcs_low.jpg` | the dotted arcs over the forest on Low (v3.3 README "known, not fixed"): HLOD edge walls sampled the wrapped bottom rows at v = 1; V clamped + speck-free bake |
| `photo_tysiaclecia_vs_dk8.jpg` | CC0 photo of Al. Tysiąclecia (pines behind the service road) above the High DK8 frame |
| `signs_putry_entry.jpg` | Andersa approach to Rondo Putry: E-1 diagram, A-7 over C-12 with rim and weathering, exit board; CC0 photo of Rondo Putry |
| `ba_stretch04_signs.jpg` | approach to Rondo Bieżeństwa before / after (C-9 on islands, exit boards facing the ring traffic) |
| `blender_dk8_before_after.jpg` | Blender control render, low sun, before / after |

## Editor GPU cost (RTX 5070, `-TimeFrames 40/60`, forest = frame − frame with `rq_trees=0`)
| Camera | Tier | v3.3 forest | v3.4 forest | v3.3 frame | v3.4 frame |
|---|---|---|---|---|---|
| dk8-dk19-exit | Low (1755 × 810, MSAA 2) | 1.33 ms | 1.23 ms | 2.08 ms | 2.06 ms |
| driver-andersa-to-putry | Low | 0.59 ms | 0.48 ms | 1.88 ms | 2.06 ms |
| dk8-dk19-exit | High (2340 × 1080, MSAA 2) | 1.62 ms | 1.85 ms | 2.72 ms | 3.15 ms |
| driver-andersa-to-putry | High | 0.52 ms | 0.59 ms | 3.08 ms | 3.44 ms |

- Repeat runs of the same frame differ by up to ±0.15 ms (GPU clocks), so Low is "unchanged within noise" (−8 % forest),
  High +14 % forest (two views cross-faded = 4 fetches per impostor texel, understorey). Instances in the DK8 view:
  Low 930 (= v3.3, thinning strides kept), High 2218.
- A16 estimate (UNVERIFIED until a device run): Low DK8 GPU ≈ 26–27 ms (v3.3: 26.1 ms) — budget 33 ms kept. S24+ High
  had 12 ms headroom at 18 ms (ADR 0013 r4); +14 % of the forest share ≈ +1.5 ms.
- Texture memory (ASTC 6×6 + mips): impostors 18 × (1536 × 384 albedo + 768 × 192 normal / visibility) ≈ 7.9 MB
  (v3.3: 1.05 MB); edge normal maps 3 × 512 × 256 ≈ 0.2 MB.

## Visibility strengths (WORKING_VALUE)
Impostor ambient 0.45 / sun 0.25, HLOD edge 1.0 / 0.6 (`InstanceImporter.ImpostorVisibility`, `EdgeVisibility`):
chosen so the impostor crowns at the LOD1 → impostor switch (30 m on Low) have no visible tone step in the frames above.

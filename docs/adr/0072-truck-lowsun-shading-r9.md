# ADR 0072 — TRAKT at low sun r9: D23 toe outside the cab on Low, gloss-trim term debug, glass / roof / mirror status

Status: accepted for the toe change (rendering-perf, 2026-11-10); the "0 dark clusters" criterion is **not met on either
tier** (see Measured). Not reviewed by `visual-critic`. No phone frame: UNVERIFIED on device.
Source: ADR 0061 Open 1, `REVIEW-2026-11-10-r8.md` §2–3 and §8 item 7. Evidence: `artifacts/truckshade-r9/`
(`before/` = main 947749e rebuilt in the worktree, `after/` = this change, `dbg1-3/` = gloss-trim term debug,
`exp-post*/`, `trim1k/`, `noglass/`, `metrics_before_after.txt`, `view/`, `tools/`). Editor frames only, WorldC.

## Diagnosis (measured, gloss-trim pixels in the grille boxes, lowsun, post off on both tiers)
Temporary debug shader (`dbg1-3`, reverted) writing each term of the ADR 0047 r3 gloss-trim path:

| | env·F | diffuse (SH·albedo·AO) | F | hor²·obst | AO | rough |
|---|---|---|---|---|---|---|
| truck-34 Low / High | 0.0054 / 0.0032 | 0.0014 / 0.0018 | 0.072 / 0.044 | 0.29 / 0.30 | 0.93 / 0.94 | 0.16 / 0.10 |
| truck-front Low / High | 0.0018 / 0.0009 | 0.0015 / 0.0018 | 0.042 / 0.040 | 0.50 / 0.42 | 0.95 / 0.96 | 0.12 / 0.11 |

- The linear louvre value is the **same or higher on Low** (0.003–0.007). The tier gap is the display curve: High goes
  through the D23 LUT (black floor, toe 0.0025 → 3.8 %), Low writes plain sRGB (3.2 %). Proof: High with `rq_post=0`
  has 15 clusters / 23 % under 5 % on truck-34 (Low 9 / 13 %), i.e. as dark as Low.
- Why ADR 0061's steep-down change (`obst` 0.3 → 0.5) moved Low only: on truck-34 the louvre reflections sit in the
  near-horizon band (hor²·obst = 0.29–0.30 on both tiers), the steep branch is not reached; on Low the LOD2 louvre faces
  (drawn out 30 %, ADR 0061) are probably steeper than the LOD0 ones (UNVERIFIED). **Low always renders exterior LOD2** (`ExteriorChainFor`),
  which has no louvre lips: the thin sky-lit lip lines that carry the High grille are geometry Low does not have.
  A 1024 Trim atlas on Low (`trim1k/`) sharpened the plate and marks but changed no metric (reverted).
- The values are physically plausible: gloss black (albedo 0.02) facing the truck's own shadowed road at low sun.
  No term was raised: the env ground and SH already assume a sunlit road, which at low sun from behind is in the
  truck's shadow.

## Decision
- `CabInteriorLighting.exteriorToeParity` (new field, default on): on tiers without post-processing the D23 toe
  (`LookGrading.NoPostToeParity`, `KamionToeParity.hlsl`, ADR 0044 r7) is written by the truck shaders in **every** view,
  not only the cab view. The world keeps plain sRGB on Low (a world-wide toe = all world shaders, out of scope).
  Cab-view behaviour unchanged (`toeParity`). No new shader, keyword, pass or texture.
- No change to High (frames bit-identical, `metrics_before_after.txt`).

## Measured (luma Rec.709 %, clusters < 5 % with a full 3 × 3 block; before → after)
| frame | Low clusters / under5 / p50 | High (unchanged) |
|---|---|---|
| truck-34 lowsun | 9 / 13.4 % / 11.3 → **10 / 3.4 % / 12.1** (largest 3344 → 647 px) | 5 / 3.8 % / 12.3 |
| truck-front lowsun | 15 / 58.8 % / 4.3 → **37 / 25.5 % / 5.4** (largest 54 091 → 6 501) | 214 / 13.0 % / 5.8 |
| truck-34 overcast | 0 / 0 / 23.1 → 0 / 0 / 24.7 | 0 / 0.1 % / 24.7 |
| truck-front overcast | 4 / 0.2 % / 11.7 → **0** / 0.03 % / 12.9 | 0 |
| truck-front clear | 2 → **0** | 1 |

Low now matches High on truck-34 (share under 5 % below High) and halves the gap on truck-front; the remaining Low
excess is LOD2 geometry (no lips). The "0 clusters" target is not reached on High either: the dark pixels are the
gaps under each lip (truck-34) and the AO-occluded upper band of each louvre face (truck-front), physically black in
the shade. Closing it needs geometry (LOD2 lips, or LOD0 louvres on Low, truck-artist) or a look
decision (a local shadow lift outside the cab, as `_CabShadowLift` in the cab view).

**Task 2 (state of main + this change; nothing changed for glass / roof / mirrors):**
- Glass from outside (truck-34, ADR 0059 box): σ lowsun Low 5.94 / High 6.48, clear 4.18 / 4.56 → **D44 σ ≥ 8 at sun:
  FAIL**. Overcast σ / σ without glass: Low 3.64 / 4.88 = 0.75, High 3.99 / 5.54 = 0.72 → **D44 ≥ 0.7: PASS** (High by 0.02).
- N-8: the far door pane is still a lighter rectangle at low sun (ADR 0059 ×0.35); unchanged.
- N-3 (cab-left, ADR 0059 method, vs `-NoGlass`): sat 0.99–1.00, σ 0.93–0.97 on Low / High × ov / lowsun: **PASS**.
- N-17 roof crown (truck-34 box 890–1260 × 250–320): pixels ≥ 97 % High ov 8.4 %, lowsun 7.2 %, clear 41.7 %; Low ov 0,
  lowsun 1.0 %, clear 28 % → **FAIL on High**. Cause: the D23 white clip at 0.7 ("lit white paint reaches 100 %",
  D23), not a shader term; lowering it is an owner look decision (D23 vs N-17).
- E7 (mirror housings from the seat): masks show housings / arms are `MI_Ext_Trim` (`mirror_plastic`, albedo 0.025,
  rough ~0.8 after dust). Clear: dark grained plastic, no chrome. Lowsun: the backlit arms show a grazing sheen (rough
  lobe + Fresnel toward the sun), plausible; the light strip at the inner glass edge is the mirror image of the own white
  cab side (ADR 0059). The cab-view shadow lift is **not** the cause (lift off: identical frame). No change.

## Cost (Low; phone NOT measured)
Truck and trailer exterior / interior pixels in exterior views now run `KamionToeParity` instead of its uniform early-out:
per pixel 3 × (2 reciprocals + ~4 FMA) ≈ 6 SFU + 12 FMA, no texture, no varying. At ~25 % of the screen in the chase
view this is a few hundredths of a ms on Mali-G57 class (estimate, UNVERIFIED); 0 on High (no-op branch). A/B on A16:
the field `exteriorToeParity` (component on the truck) – off = previous behaviour.

## Open
1. Grille 0-cluster target: LOD2 louvre lips or LOD0 louvres on Low (truck-artist) / look decision on an exterior
   shadow lift; then re-measure both tiers.
2. D44 σ ≥ 8 at sun (capture without instanced trees/props, no driver; ADR 0059 Open).
3. N-17 vs D23 white clip: owner decision.
4. Phone frames (A16 Low truck-34 / truck-front lowsun), `visual-critic` review.

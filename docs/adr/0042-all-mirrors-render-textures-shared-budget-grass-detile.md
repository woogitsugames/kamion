# ADR 0042 - Every mirror renders a texture under one shared per-frame budget; grass bare-soil de-tiling

Status: accepted (2026-11-10). Answers review r5 C5 (blank wide-angle mirror) and W-N3 ("odra" on grass).

## Context
- r5 C5: the wide-angle mirror (and kerb / front) used `MI_Ext_MirrorProbe`, a metallic lit card that reflects only the
  environment probe: a grey card in every frame. Only the two main mirrors had render textures, alternating by
  `MirrorInterval` (Low: 2 cameras every 4 frames).
- r5 W-N3: the 3 m `grass_verge` tile bakes bare-soil spots (Var.B, 7 % of texels > 0.5; corr. with brown 0.66) at one
  scale and contrast, so the verge repeats an even spot pattern ("odra").

## Decision
1. **All six mirrors get a render texture** (builder `TruckAssetBuilder`, quads use `MI_Ext_MirrorRT`). Camera at the
   mirror image of the design eye point; up = glass Y axis. Convex mirrors: the edge normal turns by s/R, so each
   half field = atan(s/d) + s_full/R (s = half glass size, d = eye-image distance).
2. **UN ECE R46 mirror classes** (radius minima: class II r >= 1200 mm, classes IV-VI r >= 300 mm; fields of vision in
   R46 para 15.2.4 - paragraph numbers UNVERIFIED, verify against the consolidated R46 text before Stage 3 gate):

   | Glass | Class | R (WORKING_VALUE) | d eye-image | H x V field | Required (R46) and check |
   |---|---|---|---|---|---|
   | MainL / MainR | II | 1.8 m | 1.11 / 2.11 m | 24 x 44 / 19 x 35 deg | 5 m wide at 30 m behind the eye: L 8.3 m, R 5.6 m (flat glass gave R 1.9 m: illegal) |
   | WideL / WideR | IV | 0.35 m | 1.15 / 2.14 m | ~80 / ~75 deg | 15 m wide from 10 m behind: outer edge needed 57.5 / 59 deg, got 63 / 60 deg |
   | Kerb | V | 0.30 m | 2.12 m | ~72 deg | ground beside the passenger door (looks 66 deg down) |
   | Front | VI | 0.30 m | 1.97 m | ~97 deg | **art issue:** the glass normal reflects the eye ray 36 deg *up* (sky), not onto the 2 m strip in front of the bumper. Needs re-aim by truck-artist. |

3. **One shared budget, not per-mirror intervals.** `VehicleCameraBudget.MirrorsPerFrame` = 1 / 2 / 3 / 6
   (Low / Medium / High / Ultra) is a hard cap of mirror renders per frame. A weighted round-robin (`MirrorScheduler`,
   execution order 32000, no allocation) picks the largest accrued debts among mirrors whose glass is visible: main
   weight 1, convex 0.5. Low with all six visible: main every 4th frame, convex every 8th; left pair only: every 2nd /
   3rd. Convex mirrors render at 0.43-0.6 of the main RT height and half the far clip (minified image).
   Worst case on Low rises from 0.5 to 1.0 cheap camera render per frame (no shadows, post, MSAA, depth/opaque copy).
   **GPU ms per tier not yet measured on a phone** (rule 2): to do on A16 Low / S24+ High with the cab view.
4. **Grass de-tiling** (`Kamion/World PBR`, local keyword `_GRASS_DETILE`, terrain_grass + verge_grass): bare soil is
   kept only inside a world-space mask from the 64 m macro map (8-64 m damp / worn hollows + 0.5-4 m mottling, ~37 % of
   the area) and along the carriageway edge (terrain COLOR_0.r); elsewhere soil texels are refilled with the
   calibrated grass albedo (`_GrassFill` 0.079/0.109/0.037 linear = mean of texels with Var.B < 0.1, Vector property so
   no sRGB conversion) at their own luminance. Medium+ also blends a second sample rotated 30 deg and scaled 1.37x by
   the 2-16 m / 0.5-4 m macro channels, which removes the 3 m period. Cost: Low +1 texture fetch, Medium+ +4.

## Consequences
- Wide-angle, kerb and front glass show the world; main mirrors are wider (legal class II) and show more of the own
  vehicle side, as real ones do.
- The `MI_Ext_MirrorProbe` material is still generated but unused by the art truck (kept for the graybox fallback).
- Evidence: `docs/reports/visual/r5-c5-wn3/cmp_*.jpg` (editor, overcast, before/after, Low and High). Phone frames and
  GPU timing pending (build-qa / next device run).

## Addendum 2026-11-10 (review r6 C-N8): modern cab mirrors, R46 check, glass adjustment
- **Source of the fields:** UN Regulation No 46, para 15.2.4.2 (class II: 5 m wide from 30 m behind the ocular points
  to the horizon + 1 m wide from 4 m behind), 15.2.4.4 (IV: 15 m wide 10-25 m behind + 4.5 m wide from 1.5 m behind),
  15.2.4.5 (V: 2 m outside the passenger-side cab plane, 1.75 m behind to 1 m ahead of the ocular points or the bumper),
  15.2.4.6 (VI: from the front plane 2 m ahead, driver-side plane to 2 m outside the passenger side). Consolidated text
  OJ EU L 237, 8.8.2014 (CELEX 42014X0808(02)); read via the lexaris.de mirror of that text. This replaces the
  "paragraph numbers UNVERIFIED" note above.
- **Check as code:** `MirrorOptics` (Vehicle/Runtime) is the camera model the builder uses (eye image, convex s/R);
  EditMode `MirrorFieldOfVisionTests` projects an 11x11 road grid of each R46 field (flat road, vehicle side 1.275 m =
  2.55 m trailer, front = `TractorDimensions.FrontFaceZ`) into each mirror view. Own-vehicle occlusion is not in the test.
- **Modern cab, modelled glass (art r4):** II L 100/100 %, II R 100 / **91 %** (1 m strip at 4 m just below the view),
  IV L **93/97 %**, IV R **92/98 %** (glass looked along the own cab side: axis 5 deg out, half the image was the truck),
  V 100 %, **VI 100 %: the front mirror looks at the road (axis 74 deg down), the "front mirror aims at the sky" item is
  closed** (fixed by the art r4 re-aim; upper edge of its view 43 deg below the horizon).
- **Decision: glass adjustment in the builder, not in the geometry.** `TruckAssetBuilder.MirrorAim` gives the reflected
  axis per mirror (vehicle yaw/pitch); `MirrorAdjustment` turns only the glass quad about its centre (what the driver does
  with the electric adjuster), limited to +-10 deg (WORKING_VALUE), warning + clamp beyond. MainR (4.3, -2.7) = 1.0 deg,
  WideL (-17.7, -19.5) = 6.0 deg, WideR (16.6, -10.8) = 6.0 deg; MainL, Kerb, Front keep the modelled glass.
  Result: every class 100 % of its R46 field. If the housing changes (truck-artist), the targets still hold; the test
  fails if the adjuster range is exceeded.
- **Control cameras:** `cab-mirrors-left`, `cab-mirrors-right`, `cab-mirror-front` (eye point, 30 deg, aimed at the glass
  centres) next to `cab-left` / `cab-right`. Frames: `artifacts/owner/mirrors-modern/` (before/after, Low/High, overcast).
- **Open (art, truck-artist):** (1) the class V kerb glass (1.39, 1.95, 4.78) is not visible from the design eye: the
  line of sight (yaw 72 deg right, 15 deg down) runs into the passenger door / A-pillar base below the window sill. Its
  image is right (field 100 %), but the driver cannot see the glass: move it into the lower right windscreen corner or
  give the door a lower window. (2) The class VI glass is half behind the passenger sun visor from the eye; it shows the
  cab nose and the road ahead, no sky. (3) The passenger class II glass is partly behind the A-pillar from the eye.

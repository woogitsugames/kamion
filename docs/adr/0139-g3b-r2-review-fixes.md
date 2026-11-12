# ADR 0139 — G3-B fixes after review s13-0127: clear viaduct screen, portal boards, HV tower, dark screen posts

Status: implemented on branch `g3b-r2` (base main `a6cfe38a`, 2026-11-12); not merged. Gate 3 is NOT re-judged here
(visual-critic). Source: `docs/reports/visual/REVIEW-2026-11-12-s13-0127.md` (P1-1, P2-1..4). Starting point: ADR 0127.
SBS camera poses are not touched (ADR 0140 stream).

## Findings (measured before anything was changed)

| Review item | Evidence | Cause |
|---|---|---|
| P1-1 viaduct screen (494288, 810525) reads as a milky blind | Photo 494288258686575 (`artifacts/g3b-lowread/crops/photo-494288-screen.jpg`): clouds and lamp posts show through the sheet; ~50 thin lines over the 2.75 m sheet of the nearest bay, invisible a few bays on. Material: film 0.06 + lines 0.45 x duty 0.25 = 0.17 mean extra opacity, 27 lines per sheet, film lit as a 0.21 (linear) white surface. | material values |
| P2-3 HV tower seen "from the side of the arms" in 3678296 | GUGiK hi-res orthophoto (WMS ORTO HighResolution, `artifacts/g3b-r2/crops/ortho-pylon-hr.jpg`, 0.04 m): the tower at local (-368.6, -68.6) is a strain tower (horizontal insulator strings, red / white top); the conductors run NE-SW through it, the arm tips lie 8.6 m apart on an axis of bearing ~322 deg (+-3). The generator turns the arms across the BDOT10k line: 321.8 deg. **Orientation in the world = orthophoto.** The camera of 3678296 looks at the tower along bearing 331.5 deg, i.e. ~10 deg off the arm axis. On the photo the near (right) arm tips stand about half an arm level above the far (left) ones - the perspective of arms seen mostly end-on - and still spread ~0.3 of the tower height sideways, which needs a view 20-50 deg off the arm axis: the photo was taken from another position / with a much wider lens than the 58.7 deg of the pose. | **pose / FOV (SBS stream, ADR 0140)**, not the world. Arms were 3.3 m (WORKING_VALUE), orthophoto 4.3 m. |
| P2-1 275528: boards ~15 % too large against the column spacing | Frame 275528677534382 at 2048 px: column axes 797 px apart (= the 14 m beam); left board 214 x 46 px, right board 216 x 67 px, beam chords 30 px apart, board tops ~0.3 m above the top chord, bottoms at the bottom chord. -> boards 3.75 x 0.82 m and 3.8 x 1.2 m, beam 0.55 m deep. The rule drew 4.06 x 1.42 m and 4.03 x 2.04 m on a 1.0 m beam. The left board carries a lane arrow at both ends. | board layout rule (row 0.62 m) + beam depth |
| P2-2 3281350: one board on the photo, two in the render | 3281350541967811 is from 2017-07 and shows one tall board (aspect ~1.7) at 0.50-0.74 of the span seen from behind = the place of today's left board. 275528677534382 (2019), 468708117568850 / 143559297695026 (2020) and 1056932506043672 (2024) show two boards. | older state of the same portal; the world follows the newer frames. **No change.** |
| P2-4 screen posts at al. Tysiaclecia light green | Photo 1801374876712141: posts 55-80 / 66-95 / 66-100 sRGB against the sky (cassette band 33-37); `noise_post` 0.17 / 0.21 / 0.18 was measured on the Andersa link barriers (ADR 0069, 98 / 108 / 100 sRGB in overcast). | one post material for two barrier families |

## Decision

1. **`noise_glass_lined`** (viaduct screens): film 0.06 -> 0.02, lines 22 -> 44 per UV0 v unit (period 0.05 m), strength
   0.45 -> 0.30, duty 0.25 -> 0.12 (line ~6 mm), new `screen.haze_color` (linear, 0.14; default stays 0.21) read by
   `RegionImporter.CarGlassMaterial`. Mean extra opacity 0.17 -> 0.056. Shader unchanged for car panes.
2. **Portal `andersa-putry-approach-gantry`**: `boards[].size_m` (width, height) and `beam_depth_m` in the override;
   `signs.overhead_board(rows, size_m=, arrows=)` fills an authored size (rows centred, a second lane arrow at the right
   end for a board over two lanes); `life_props.sign_gantry(span, H, beam)`; prototype name gets `_b<dm>` when the
   beam depth is authored. With the 5.0 m clearance + 0.2 m the portal top comes to 6.1 m (was 7.0 m; ADR 0127 read
   6.2-6.5 m), board bottoms 5.2 / 5.5 m. Rule-sized boards and portals are unchanged (same hashes).
3. **HV tower**: `PYLON_ARM_L` 3.3 -> 4.3 m (orthophoto); the conductors follow (they hang from the arm tips).
   Orientation unchanged - verified, see above.
4. **Screen posts**: new material `noise_post_dark` (0.055 / 0.080 / 0.066, WORKING_VALUE), selected by the zone key
   `post_mat` on the four al. Tysiaclecia zones of `andersa-ne-noise-barrier-glazed`. Andersa link zones keep
   `noise_post`.

All sizes are WORKING_VALUE read off the cited Mapillary frames (CC BY-SA, reference only) and the GUGiK orthophoto.

## Not done / open

- 3678296 stays PARTIAL until the pose / FOV is re-derived (ADR 0140): evidence above.
- Viaduct screen posts are still square boxes (review P2-4 second half: H-section) - not in this task's list.
- The portal beam is straight; the photo shows a slight camber. Third board row on the photo is a yellow shield +
  white box; ours is the schematic "675 Centrum".
- Phone numbers (A16): next gate measurement.

## Results

(filled in after the final cycle)

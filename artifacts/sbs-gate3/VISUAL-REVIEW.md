# ADR 0103 — self-review of side-by-side evidence

Author: stream J (not an independent visual-critic). Base world: main `9e6e9fde`, copied generated assets.
This review does not certify gate 3 or the accuracy of public GPS/SfM poses.

## Evidence actually viewed

- Original and rectified photo contacts, all 40 photographs; 27 fisheye / 13 perspective.
- r0 Low-overcast: all 40 pairs in four 900-pixel review sheets, selected full pair PNGs.
- Final matrix: all 160 pairs in the eight `review/{Low,High}-{clear,overcast}/G3-{A,B}.jpg` overviews.
- Full pair PNGs across all four states, including close bridge `2818555625124739`, Putry side
  `810525063224609`, deck `454716650857984`, `2948595898752384`, `494288258686575`,
  and the three sunset deck corrections `1406533339711789`, `223210302566110`, `309664504075286`.
- Eight original/computed GPS/heading probes (`probe-sheet-*.jpg`): this prevented replacing oblique
  optical headings with travel bearings. Original GPS improved the close richlv bridge shots.
- All 160 renders and 160 sheets decoded, all render hashes checked against final metrics; original and
  rectified photo hashes checked. Source photo pixels are real Mapillary, not generated substitutes.

## Definite camera errors corrected (no world edits)

| Error | Before | Final |
|---|---|---|
| Seven Bieżeństwa + one Putry deck photos used NMT ground | underside/columns occluded photographs taken from above | authored absolute U = existing deck road level + nominal 1.7 m eye |
| 454716650857984 GPS near barrier | camera on rail/edge rather than photographed right lane | 2.95 m SW lateral correction; before PNGs in `r1-adjustment-before/` |
| 1406533339711789 SfM heading | 187.8°, looked sideways under deck | original 300.8° retained; forward road framing restored |
| Wide-angle lens mismatched to pinhole | curved photographed structure could not align with straight render | radial rectification from cached API intrinsics, cropped valid pinhole view, matching FOV |

27 poses differ from r0; exact subset pose assertions retained 38 unchanged views for r2 and 37 for r3.
The seven Bieżeństwa heights come from existing deck station interpolation; the Putry height comes
from a vertical ray against existing generated bridge-road asphalt (140.188 m + 1.7 m eye).
These are camera estimates tied to the current model, not geodetic ground-truth height measurements.

## What remains visible / uncertain

| Priority | Location | Observation / consequence |
|---|---|---|
| P1 | `sbs-g3-a-2818555625124739`, adjacent close bridge frames | Differences in deck section, pier shape/colour, spacing, gravel/grass and roundabout kerb shape remain. The camera correction improves scale, not photographic realism. Do not move the camera solely to hide geometry differences. |
| P1 | `sbs-g3-b-810525063224609`, `209622370971977`, `4312632558767412`, `494288258686575` | Screen framing, supporting structure and guardrail/edge proportions differ substantially from photos. Generic/white/continuous structure is not the photographed green/red structure. |
| P1 | G3-B long road views (`3281350541967811`, `297817221966185`, others) | Mature street trees and dense crowns in photographs become sparse/small silhouettes; grass/road surfaces are much more uniform. No foliage/material edits in stream J. |
| P1 / pose uncertain | `sbs-g3-b-810896133189484`, `1528935774382039` and GPS-near-junction frames | Foreground occlusion/lane alignment still differs. Public GPS/SfM and model geometry are both uncertain; this evidence alone cannot assign the entire discrepancy to the world. |
| P2 / pose uncertain | `sbs-g3-a-309664504075286` | A generated lamp pole is close to the camera after raising it onto the deck; the reference does not have the same close occlusion. Kept visible, not hidden by an arbitrary camera move. Requires position/asset review. |
| P1 / evidence limitation | G3-A | All 20 shots cluster near the end of the segment (final authored s=343.026–436.716 m); first ~300 m are uncovered. Twenty unique photos do not mean continuous segment coverage. |
| Unverified | all cameras | Nominal eye height, GPS/SfM precision, road-height model, manually estimated horizon and uncorrected roll remain WORKING_VALUE. No pose is labelled survey-verified. |

## Photometric interpretation

Clear/overcast presets do not recreate each source photograph's weather, time, season or camera white balance.
Sunset photographs remain in the set and are explicitly dated; they are framing references, not matched-exposure
ground truth for a midday preset. Car hoods/black borders also affect whole-frame histograms.

32-bin sRGB luma histograms, mean luma, sky/asphalt area ratios and mean-luma ratios are emitted separately.
Default RGB/position masks are WORKING_VALUE heuristics, not semantic masks; author normalized polygons for
strict brightness calibration. Null means no valid mask sample, not a fabricated number. No histogram threshold
produces an automatic PASS. The plots are comparison aids, not physical albedo/radiance measurements.

## Performance and gate conclusion

No tracked runtime/world/shader/material changes. Cameras are created transiently by the editor command;
the runtime scene, Resources cameras and generated world inputs were not changed. Raw regular-renderer
SceneStats and separate instanced estimates are preserved. They are not mobile GPU measurements; a changed
camera pose changes visible-content estimates and is not a runtime-cost regression attributable to this tool.

Tool/evidence pipeline functions and exposes real mismatches. **Gate 3 is not accepted**: photographic
world fidelity, independently reviewed pose confidence, the owner's photos/approval and phone evidence remain
outside this single-stream tooling delivery. The leader should review these artifacts before integration;
do not treat the 160 generated sheets as a quality PASS.

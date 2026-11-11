# Independent review — S10 A / ADR0086

Verdict updated 2026-11-11: **PASS for tint upload contract; calibration FAIL pending leader ADR0101.**
Reviewer: coordinator, separate from implementation author. Reviewed implementation
ab738b01, actual GPU numeric probe, full 59-camera Low/High overcast pairs,
full 59-camera Low/High clear final pairs, and 960px firestation/screen/hall/DK8
and restored-curtain comparisons against the supplied open references.

The original Color-property decode is proven with lighting-free GPU readback;
the helper covers all four importer writes and preserves already corrected
building tints, neutral1 and HDR ratios. Existing tile/weather/macro paths remain.
The hall is more legible, asphalt/pavers remain stable, and the screen was
recalibrated after a measured overshoot. Plaster-only gain places both overcast
profiles within the specified remiza RGB band; roof/trim/glass pixels are protected.

Review caught a real dock3 curtain regression (~55→112 sRGB), which was corrected
in the final palette. Final High-overcast cloth53/55/54 returns to the accepted
baseline, retaining folds and matte appearance. No new blocking tint defect was
observed in the complete four-condition coverage.

Scope limits: this is not119 physical-albedo measurements or a whole-scene
photographic-realism clearance. Existing black crowns, repeated hero cones,
clear highlight clipping, truck glass and geometry simplification remain assigned
to B/C/E/F. Surface weathering remains D. Photo exposure/white-balance differences
are disclosed rather than compensated with a global exposure change.

Validation: GIS359 passed/2 xfailed; EditMode226/226 passed including14 tint
CPU/GPU cases. Same-fixture world matrix has byte-identical stats. The subsequent
canonical truck refresh adds up to7k triangles in High vehicle views only; it has
no draw delta and Low stats remain identical, reported separately from material cost.
No phone/GPU-performance claim, merge or push is authorized by this review.


## Independent critic follow-up ? supersedes calibration approval
The external visual-critic review at docs/reports/visual/REVIEW-2026-11-11-s10-0086.md
(main d80a85a4) identifies missed directional-illumination failures: KP gate
High-clear wall252sRGB/62percent clip, overcast187, versus the shaded-only hall
ROI used above. Screen cassette/plinth ratios .28Low/.30High overcast also miss
the reference .34-.38. The earlier no-new-blocking-defect statement was too broad
and is withdrawn. Contract/GPU proof, stable asphalt/pavers and restored curtains
remain valid. Local appearance cannot be cleared using a single shaded ROI or
absolute photo sRGB across different illumination. Require lit+shaded wall ROIs,
clip fractions and same-frame neutral ratios for calibration closure.
Leader owns active tint-r2/ADR0101 from main99a4f3f8, so no duplicate correction
is made here. D48 retains owner plaster target110/126/145; streamE must preserve it.
Mixed truck-fixture camera pairs are excluded from tint-only proof as already
noted; B/C/F final matched matrices use explicit fixture snapshots.

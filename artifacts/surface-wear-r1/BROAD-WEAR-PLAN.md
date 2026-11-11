# D / ADR0099: separate broader wear probe

Status: INACTIVE. Gate version 2 has completed its canonical import, native audit and 16-frame packet; independent ROOT selection is pending. The current fixture contains 2441 cached Unity files and 192 raw files. The new proof is broadwear-plan-proof-current-r2.json. The earlier dba4855 / 593-file / first-patch proof is explicitly historical and must not justify current activation.

The current patch is candidate-broadwear-r2.patch. Its apply check passes against the actual signed-gate shader, preserving the new gate branch and retained paint calibration: actual wear 0.425 and width 0.085. It remains unapplied. Current production shader, patch and fixture hashes are recorded. All cached and raw hashes were checked again; there are no mutations.

The three proposed changes use existing shader branches:

1. ROADWEAR smoothness increment changes from 0.12 to 0.18 * lerp(0.65, 1.05, macro.b), using the already sampled map. Old/fresh maximum increments are 0.1134/0.04725. Existing albedo darkening, wheel-band width and centres stay unchanged. Measure asphalt display mean instead of assuming that unchanged albedo implies unchanged output brightness.
2. Existing gutter strength is multiplied by lerp(0.6, 1.4, macro.a). Old/fresh maxima are 0.77/0.42. This interrupts uniform edge deposits without a central dirt layer or another texture fetch. Existing damp and drip branches remain unchanged.
3. Longitudinal paint gets 12 percent of the calibrated transverse wheel term, only with real lane data. Preserve transverse wear 0.425 / width 0.085, paint age/dirt, aggregate chip threshold and distance prefilter. This changes longitudinal wear; it is not unchanged relative to the original 0.85 / 0.13 baseline.

All new response constants are working values, not measured BRDF. Existing Mapillary references 469512, 191135, 178375, 102634 and 513486 motivate restrained wheel/edge variation and readable chipped markings. They remain reference photographs, not runtime assets or absolute albedo measurements.

The source sample count remains 20 before and after the inactive patch. No new texture, material, keyword, draw group or geometry is proposed. Extra scalar GPU cost is unverified. Preserve tile selection (set_tile or element scan or atlas), weather/runoff, macro, panel, splash and unrelated material branches. No roads/* or override edits.

After ROOT's gate choice, capture the fresh 14 controls in four conditions before any activation: 56 real frames, including newroad_negative and unknown glyph controls. Keep material, source, cache and runtime pose pins. Then apply only this patch and capture the identical 56 frames. Compare lane polish, gutters, patches, supported/unknown paint, P8 and P10; measure asphalt mean and reject wet-looking ribbons, blanket grime, unreadable paint or a global brightness shift. ROOT independently chooses retain or reject before the full 93-view final matrix and editor tests.

The final Python result is 388 passed and one expected failure. Do not repeat GIS after shader-only changes without a new Python change or test concern. Every Unity launch still requires both shared guards to be absent under the current explicit ROOT release. No render or production source change was performed for this proof refresh.

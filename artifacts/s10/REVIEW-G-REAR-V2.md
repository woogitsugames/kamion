# G R4 rear controls v2: independent review

**Bounded function / blob-fix PASS; dust realism PARTIAL.** Reviewed only the valid `r4-rear-controls-v2`, not the invalid first controls. No production/Unity/test changes.

Opened all20 source PNGs through four size-only full-frame contact sheets and four native1:1 five-level crop strips; also inspected G's Low OFF/3 rear comparison boards. Existing detached mid-body blobs are absent. The rear receives a small, smooth, progressively brighter deposit; there is no new obvious isolated dark island or wet ribbon. In the full scene the effect is subtle. It still reads as a soft film rather than a richly textured physical splash pattern, so this is not a full docs/06 realism PASS.

Independently read all20 saved `control-state.json`: OFF is forceLevel=-1/opacityOff=true, each level0..3 has that exact integer/opacityOff=false; every row identifies target [674.796,-523.807], naturalLevel3. Compared40 begin/end camera/projection/hierarchy/region packets against OFF begin in the same condition: selected fields exact. Saved controller flags alone are not proof of executed GPU state. The rendered target-paint response is separate output evidence; I did not add a GPU command/constant-buffer readback. This is a same-frame target-only ablation, NOT a historical BEFORE/R3 comparison. No image alignment or tonal correction.

Independently recomputed native PNG display-luma means from G's68 ray-selected lower-rear-paint points (5x5 pixels per point):

| Condition | OFF | Level0 | Level1 | Level2 | Level3 |
|---|---:|---:|---:|---:|---:|
| Low clear |49.066|49.365|50.763|52.557|54.402|
| Low overcast |31.942|32.201|33.596|35.338|37.183|
| High clear |54.544|54.894|56.376|58.207|60.086|
| High overcast |36.198|36.520|38.074|39.967|41.888|

All four aggregate series increase strictly. OFF and level0 are deliberately distinct: level0 retains a small nonzero layer. These values describe display RGB, not linear albedo/GPU shader colour; aggregate monotonicity does not prove monotonicity at every pixel or between different cars/lighting conditions.

Point selection is G's actual-native LOD0 CPU-ray/material attribution, not an independent re-raycast by this reviewer. I read its method and recomputed its PNG sampling independently. Target is car_hatch_black, natural GPU level3/nativeIndex8908. Supplied lower-paint samples cover height .315..647m,146 visible rear-paint samples overall/68 lower samples; plastic trim, plate and other cars are excluded by that attribution. No claim that painted geometry exists down to the .19m sill or that this proves dirt on the unpainted bumper.

G's v2 validation records90 canonical fixtures, native Instances asset and shipping source unchanged. Current flags/poses and images support the bounded function result; they do not establish phone timing, internal render dimensions or a photographic dust match. No extra tuning requested. Evidence, exact PNG hashes, saved flags, independent luma and pose checks: `G-rear-v2-independent/independent-check.json`. Low/High, clear/overcast all covered; P2 plates remain a separate next gate.

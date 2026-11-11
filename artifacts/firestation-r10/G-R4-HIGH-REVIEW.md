# G R4 independent High focus review

Reviewed 2026-11-11. Scope: all 20 High pairs, 10 camera IDs in clear and overcast, from G `r4-before` (current-main R4 baseline, 92 cameras/condition) against `r4-focus-r1`. This is not the rejected R3 comparison. No source, cache, Unity or test changes by this reviewer.

**Verdict: PASS for the bounded repair of detached lower-door blobs; PARTIAL for convincing road-dust deposition. Overall docs/06 photographic-realism PASS is not demonstrated by this focus set.** No obvious new bonnet/roof brightening, wet ribbons, or upper-film erasure is visible. This is a visual scope verdict, not the branch's full technical or performance gate.

## Evidence and correction

Read R4-SOURCE-PLAN, STATUS57/58, the actual upper-role shader path and native Tile proof. Mask.R restores the removed legacy film through the forward upper-role multiplier and smoothness subtraction; no claim that Color.GetColor is displayed GPU colour. CPU bonnet residual about 1% is a model, not an image result.

Viewed all 20 full-frame pairs at 960 pixels wide without tonal changes; also viewed four native 1:1 crop boards of white doors and the black bonnet. Files and source SHA256 are in `G-r4-high-pairs-960/view-inputs.json`. Independently verified current source hashes and begin/end camera view, projection, FOV, aspect, clipping, pixel/target dimensions, pixelRect, giRect and cameraParents: all 20 pairs exact. See `independent-input-pose-check.json`.

Correction to my preliminary message: vertical comparison boards initially gave me an impression of framing movement. Native pixel checks and exact matrices disproved that impression; it is withdrawn. G's r4-cross-pose-diff also has zero differing fields for all 40 focus pairs, and ROOT independently checked the wider camera/vehicle/region packet fields. No alignment or altered images were used to obtain parity.

## Findings

| Priority / location | Actual image finding | Assessment |
|---|---|---|
| P0, r10_wheel_02 and r10_front_04, both weather conditions | The isolated grey blotches halfway up the white estate doors are removed. The replacement is a faint, more continuous cream/grey deposit rising from the lower body, rather than islands floating above the sill. Overcast close-up makes the residual layer easiest to see; clear is very pale. | Repair PASS. There is a credible direction from the sill, but a particularly convincing wheel-thrown pattern is not yet obvious at 960. Do not call this photographed dust. |
| P1, same white estate | At ordinary front-quarter size the result is almost clean white. Native close-up still has soft vertical texture, not a completely empty flat mask. Warmth is restrained, not a visibly orange wash. | Deposition quality PARTIAL: the reduction of bad dirt is more legible than the addition of convincing new dirt. Do not compensate merely to make a numeric delta larger. |
| P1, r10b_black_05, both conditions | Lower side becomes cleaner and quieter, while the broad bonnet gradient and highlight remain. I see no material-sized bonnet brightening or lifted roof. | Scoped negative-control PASS, not exact pixel parity. G display-RGB safe-hood mean delta is +0.0252 clear / +0.0112 overcast (0-255 scale); mixed legacy ROI remains separately labelled. These are image means, not linear albedo. |
| P1, g_current_black_wheel_02 | Bright irregular film immediately below the windows/over the front arch remains. Lower door becomes smoother. The upper highlight still reads as a strong streaked band in clear and overcast. | Upper retention PASS; photographic quality of that legacy band is still limited. It was intentionally retained, not newly introduced by this patch. |
| P1, r10_rear_04 | Foreground dark SUV rear and partly visible white rear are distinguishable; estate side is occluded. No new black wet ribbon or obvious upper-body change is visible. | Only the visible SUV/rear portions are assessed. This frame cannot prove the hidden estate's side dirt, nor whole-estate rear deposition. Numerical masks must identify the SUV, not the occluded estate. |
| P2, g_dirt_level_0/1/2/3 and r4_dirt_candidate_3 | All ten High pairs viewed. Lower old grime is reduced. The new predicted level-3 side has subtle low-body deposition; it does not show detached mid-door islands. Existing upper streaks remain. | Four levels are not reliably readable as an ordered set from these different vehicles, views and illumination. Source/GPU instance levels are useful routing proof, not perceptual separation proof. Level-0 frame also includes other dirty vehicles; do not assign their dirt to the target. |

G's fixed black-door ROI changes +1.590 clear / +1.093 overcast display luma while sky/road controls remain within about 0.002. I do not generalise these black-body measurements to the white estate or the occluded rear target. The upper-film band and fine vertical traces still resemble a shared soft texture at close range. This set does not by itself close docs/06 warnings about generic repetition, overly clean areas, or plausible local wear.

## Coverage and limits

The ten IDs viewed in both conditions are r10_wheel_02, r10_front_04, r10_rear_04, r10b_black_05, g_current_black_wheel_02, g_dirt_level_0, g_dirt_level_1, g_dirt_level_2, g_dirt_level_3 and r4_dirt_candidate_3. Full frames preserve surrounding roofs, upper panels, trace details and adjacent cars; no obvious collateral scene change is visible at this review scale.

Actual UV/opacity and 1009-instance level/rebase readbacks are implementation evidence, not subjective quality or GPU timing. Native stride20->24 has a cost even without additional triangles/fetches. Final PNG2340x1080 is not proof of internal render dimensions, executed EASU/RCAS, phone memory, temporal stability or A16 performance. No new phone proof was reviewed. Overall fleet/plate/far-LOD appearance and full route remain outside these 20 High focus pairs; Low is ROOT's independent review.

Recommendation: retain the bounded blob repair only if ROOT's Low/technical gates agree; retain the limited dust/upper-film realism findings explicitly. Do not mark the whole R4 appearance or docs/06 gate PASS on removal of the old blobs alone. No additional source variant is requested by this review.

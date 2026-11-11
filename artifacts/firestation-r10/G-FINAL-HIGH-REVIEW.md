# G R4 final independent High review

**Scoped visual nonregression PASS; detached-blob repair and plate variation PASS; photographic dirt realism remains PARTIAL.** All184 High pairs were inspected (92 camera IDs in clear and overcast). This is pinned `r4-before` versus `r4-final`, not a new merge of current main or a comparison to the earlier invalid controls. No G source/Unity/test changes by this reviewer.

## Exact review scope

Viewed all16 size-only paired contact pages made by ROOT's g-final-review.py. These show every full frame at contact scale; the image tool downsizes the long pages, so this is not184 native-detail inspections. Also viewed six native1:1 pairs (white-door dirt, black bonnet and close wheel, in both conditions) and eight full-frame960 pairs covering all four source cameras of historical sheet_far in both conditions. Original PNGs were neither aligned nor tonally corrected.

`G-final-high-960/inputs.json` pins all184 BEFORE/FINAL PNG SHA256 and92 matching IDs per condition. `keypairs.json` names the extra crop bounds/methods. `independent-final-check.json` records my separate parse of184 begin-packet pairs and184 final end packets: selected camera/vehicle/region/view/projection/pipeline fields exact, actual owned-plate keyword/version enabled and MotionVectors false in every High frame. Both High stats.txt files are byte-exact to their respective BEFORE. These are scoped registration/state/counter checks, not all-pixel or executed-pass equality.

## Visual findings

| Scope | Result |
|---|---|
| White body, r10_wheel_02 / r10_front_04 | Detached grey mid-door islands are removed in clear and overcast. The replacement rises gently from the lower body and retains very subtle grain/vertical variation. This is a clear repair. It also leaves the white body looking quite clean at normal scene scale; the new dust is a soft film, not a strongly convincing tyre-thrown accumulation. |
| Bonnet and upper film, r10b_black_05 / close black-wheel frame | Bonnet shape, gradient and highlight are retained; no obvious new bright bonnet/roof appears. Strong legacy streaking immediately under the windows/above the front arch remains. Upper-role retention is achieved, but the streak still has a generic soft-texture look. |
| Wheels and body silhouettes | Close-wheel native pairs retain the same rim/tyre/body geometry and visible detail. The existing faceted tyre/contact and simplified spokes are not newly solved or worsened. No new wheel/body failure stands out in the parked-car and route views. |
| Plate variation / rear | Different existing strings remain visible on the repeated black cars and adjacent cars, without a new obvious mirrored EU strip, collapsed UV or cross-cell smear. Foreground rear04 SUV remains distinguishable from the partly visible white rear. This is consistent with the separately reviewed High14 native P2 focus; no hidden estate-side or global uniqueness claim. |
| Cab, truck/trailer, route, remiza, buildings, vegetation, ground | All pages retain their visible framing, forms and overall appearance; no obvious collateral colour/geometry regression emerges. The local parked-car improvement does not materially transform the overall driving-scene realism. |
| Fleet / sheet_far sources | r10b_black_20, grey_20 and blue_20 preserve recognizable parked silhouettes and palette, with quieter dirt. At those distances plate text is limited by native footprint; no far-readability PASS. r10b_black_45 remains wall-occluded and invalid fleet evidence. Historical car_lod_08/12/15/25 show a truck or occluded/near geometry, so their names are not car-LOD proof. |

No new severe visual defect found in this final High matrix. Remaining smooth dust, strong retained upper-film band, stylized car/wheel shapes and several unusable inherited controls prevent an overall docs/06 photographic-realism PASS. This review requests no further tuning of the accepted bounded patch.

## Final metadata and practical limits

Read G's r4-final-validation/budget/owner-rois, plate native parity/replay and canonical PBR parity. Final High black05 display-luma ROI results (0-255, not linear albedo): door +1.590 clear /+1.093 overcast; safe bonnet +0.0281 /+0.0126; road and sky sample means unchanged. These support the visible bounded bonnet result; the legacy mixed bonnet ROI is kept separately, not substituted for the safe paint ROI.

Final plate packets have MotionVectors=false. The separate persisted-load replay attributes the earlier true flags to the inherited Lit CustomEditor and removes only that editor association; render programs stayed byte-exact to the numeric GPU/focus source. Earlier High14 captures with true flags remain historical visual evidence, not final pass-state proof. This final matrix supplies fresh false-flag evidence.

The443 PNG/spec byte-parity record from the full467s canonical PBR build proves CPU product reproducibility, not GPU rendering correctness or PBR realism. The texture accounting describes dependency objects/ASTC payload, not measured GPU residency; R4 clean-set dependencies and vertex payload still have costs. Unchanged culling/draw/triangle estimates do not establish actual GPU duration, A16 memory, thermal behaviour, executed upscaling passes or internal render size. The260-sample GPU proof is bounded vertex numeric evidence, not a device-performance claim. GIS/EditMode/source closure remain G/ROOT responsibilities; no test run or blanket technical DoD assertion was made here.

Low184 is ROOT's separate review. Artifacts and input hashes make this High scope reproducible without relying on G's author self-review.

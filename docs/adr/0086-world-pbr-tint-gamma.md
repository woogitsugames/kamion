# ADR 0086: one linear WorldPBR tint contract and measured local recalibration

Status: implemented on gpt-tint-gamma, 2026-11-11; independent root review PASS for this scope.

## Evidence and decision

`Kamion/World PBR` declares `_Tint` as Color. An actual GPU readback probe clones the current shader, preserving its properties/CBUFFER and changing only the fragment return to `_Tint`. With Unity6000.3.28f1, Linear color space, D3D12 and ARGBFloat linear readback, raw0.08 becomes0.007194 and raw0.5 becomes0.214041. Uploading gamma(linear) returns exactly0.08/0.5; HDR1.5 and2.5 also round-trip. Both SetColor and SetVector follow the same conversion. See tint-probe.json and WorldPbrTintProbe.cs; this is measured shader behavior rather than an API assumption.

All four importer writes use SetLinearTint: modulation, calibrated luminance ratios, oil/paint reset and tyre decal. The API accepts a linear multiplier and stores its gamma encoding. Legacy tint_linear metadata remains accepted but no longer selects the conversion. Existing ADR0081 modulation and identity1 are no-ops. No production shader change, extra texture or runtime pass was added.

The119-definition contract audit records56 previously corrected modulation definitions,33 remaining modulation definitions,29 calibrated ratios and1tyre decal. material-contract-audit.json preserves the baseline; material-final-audit.json records the final disposition per definition. This audit does not claim119 independent physical-albedo measurements. Preserve tile(set_tile||elementScan||atlas), weather/runoff, macro, panel_m, splash_h, normal/mask scales and all texture metric sizes. Preserve asphalt linear0.08 (ADR0080/0049). Adjacent StripeA/StripeB/PearlTint Color risks remain outside this change; PearlTint is coordinated with streamG.

## Local working calibration

1. Screen cassette: pure contract made High-overcast28/29/28 become57/59/56, against photographed36-40. noise_panel_dark changes0.068/0.072/0.070 to0.022/0.024/0.023 linear, WORKING_VALUE.
2. Fire station: neutral tint means the contract alone cannot change it. Low remained outside the requested110/126/145 +/-10 target. Apply one common linear gain1.15 only to plaster pigment:0.185/0.260/0.365 to0.21275/0.299/0.41975. This also affects plaster around arch/round windows. Roof, trim, glazing and bars remain pixel-identical in all3tiers; height/roughness unchanged (plaster-atlas-diff.json and pure generator regression). This is a narrow numeric conflict with later streamE, not a building geometry/glass change.
3. Independent review caught the omitted trailer calibration: dock3 ROI960(280,185,305,215) High-overcast53/55/54 became110/112/109. ADR0092 and s9-0092-0093 had accepted matte cloth (overcast48/49/50, clear upper77/80/79). All6trailer_curtain pigments plus trailer_box_white explicitly use the previous GPU-effective linear pigment, srgb_to_linear(oldColor), under the correct global upload. curtain-calibration.json records every value. These are review-supported WORKING_VALUE pigments, not a rollback or special-case conversion in the importer. Preserve roughness0.82/0.72/0.45.

## Matched camera and photo evidence

Each round has59registered cameras xLow/High xovercast/clear =236PNG,2340x1080. Low uses WorldC and High uses WorldC_High, the same Gate3 building camera JSON, and both import MaterialTierMedium (per-spec sizes, Fab mobile512). Baseline is freshly built/imported from captured source4f7da66c, with192raw hashes checked and Fab present without fallback. before, after-contract and after-calibrated share the same copied vehicle fixture; after-final includes canonical vehicle refresh described below. compare-final contains40paged paired sheets plus pivotal960pairs.

ROIs read raw PNG pixels, not JPEG previews. Their coordinates and exact values are reproducible in measure_rois.py and the four *-roi.json files. Fire photo7197 plaster ROI is110.7/126.4/146.6, nominal target110/126/145 +/-10. Hall photos are CC0 Rakoon cm157094809 (overcast, ROI131/146/160) and cm109685822 (sunny,200/209/217, different orientation). Sources/licences are in docs/REFERENCES.md and prior local reference artifacts. Screen references are Mapillaryp38/p40, documented by ADR0069/s9. These comparisons concern screen appearance under different weather/exposure/white balance, not absolute photo-derived physical albedo.

The old hall ROI220,153-245,165 overlapped a trailer roof. Self-audit corrected it to210,83-240,94, entirely on the upper metal facade; hall-roi-grid.jpg proves placement. All four rounds were remeasured. The table below uses the corrected ROI and final images.

| Condition | Asphalt RGB before -> final | Pavers | Fire plaster | Hall metal | Screen cassette | Dock3 curtain |
|---|---|---|---|---|---|---|
| Low-overcast | 70/69/68 -> 70/69/68 | 119/119/116 -> 120/120/117 | 97/112/130 -> 103/120/139 | 80/83/83 -> 122/125/125 | 24/25/25 -> 32/34/32 | 44/46/45 -> 44/46/45 |
| High-overcast | 74/73/72 -> 74/73/71 | 126/125/122 -> 127/126/123 | 105/121/137 -> 111/129/147 | 86/89/89 -> 127/130/130 | 28/29/28 -> 36/38/37 | 53/55/54 -> 53/55/54 |
| Low-clear | 99/97/93 -> 99/97/93 | 145/143/136 -> 146/144/137 | 142/161/176 -> 150/171/187 | 91/95/94 -> 125/128/126 | 49/51/49 -> 66/69/65 | 80/82/79 -> 80/82/79 |
| High-clear | 103/102/98 -> 103/102/98 | 151/149/142 -> 152/150/143 | 154/172/191 -> 165/186/207 | 98/101/100 -> 130/133/131 | 53/56/54 -> 72/74/71 | 88/90/87 -> 88/90/87 |

Both overcast fire-station profiles meet +/-10; clear is not forced to match an overcast photograph. High-overcast screen reaches36/38/37; Low32/34/32 remains approximately4levels below the photo reference, disclosed rather than hidden by global exposure. Sky-control and bridge-soffit ROIs are unchanged. Asphalt changes less than0.2levels, pavers less than1. Hall changes are justified by the lighter metal reference; the colder photographed white balance is not copied as an absolute albedo measurement.

## Validation and limitations

Final GIS:359passed,2expected xfails,553s. Final EditMode after the final world import:226/226passed,0skips, including14actual GPU/CPU tint tests. Import reports0SHA mismatches; world memory111.4MBLow/239.8MBHigh.

Matched before/after-calibrated stats are byte-identical for all59cameras in all4conditions, including instancing (final-budget-proof.json). This is the isolated world-material cost proof, not a phone GPU measurement. After the matched rounds, canonical TruckAssetBuilder/WorldTruckInstaller repaired the copied fixture missing MI_Ext_DoorGlassL. Initial223/226 passed becomes226/226 after fixture repair. No vehicle source code changed; only the missing ignored interior FBX was copied, with its SHA recorded in the artifact log.

Final images use this refreshed canonical fixture. Separate canonical-fixture-budget-diagnostic.json reports Low stats unchanged and High vehicle-camera triangles changing -1k to+7k (cab-dash maximum), with draws/objects/shadow-draws unchanged. Every world-only and instanced row is unchanged. Mixed-fixture full-frame image differences are not attributed solely to tint.

Independent root review PASS is scoped to this contract and material calibration. Remaining inherited issues belong to their owning streams: dark tree silhouettes, conical hero shrubs, sterile wear, High noise, clear white clipping and hall glass artifacts. Low dock trailers still use smooth LOD1 geometry (open s9P2); pigment cannot restore missing folds. No global visual or phone-performance PASS is claimed. Production shader/settings/scenes/packages/asmdefs and geometry code remain unchanged. Independent review: `artifacts/tint-gamma-r1/REVIEW.md` (canonical coordination copy `artifacts/s10/REVIEW-A-0086.md`).

## Correction (ADR 0101, 2026-11-11)

The "approximately 4 levels below the photo" screen statement compared absolute sRGB of a different-weather photo; by
the ADR 0069 ratio method (cassette/plinth on one face, photo 0.34-0.38) the 0086 screens were 0.26-0.31, i.e. too
dark. The hall "matches the photo" claim held only for the shaded dock side; the sunlit gate facade clipped. The single
bridge-soffit ROI lies on the hero viaduct, not on `bridge_soffit`. ADR 0101 recalibrates `kp_wall`,
`noise_panel_dark` and `bridge_concrete` with a two-camera ratio check (`tools/worldgen/qa/tint_ratio.py`); the
`_Tint` contract above is unchanged.

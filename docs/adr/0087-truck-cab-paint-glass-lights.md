# ADR0087: TRAKT cab paint, glazing and finite HDR lamp state

Status: implemented and validated as a bounded result,2026-11-11. PARTIAL OWNER QUALITY: appearance thresholds remain FAIL. Root retained the implementation after independent102-frame review; this is not blanket appearance or Android/GPU-performance clearance.

## Fixed inputs and scope

StreamF began at main232fbada including ADR0095. Before any baseline capture, the authorized merge of committed maindb1432c5 brought ADR0086 into F atf52fabf6. Fresh world339.5s and fullPBR509s were generated from those sources. Canonical TruckAssetBuilder, TrailerAssetBuilder and WorldTruckInstaller ran before baseline. Immutable baseline-fixture/fixture-proof.json pins217source assets and564Generated assets;192world rawSHA were verified. Actual nested Fab QA is15ready sources/320props/954drain replacements, fallbackFalse.

Baseline and final each contain102images:17registered truck/cab cameras xLow/High xovercast/clear/lowsun at2340x1080. Low loadsWorldC, HighWorldC_High; both world MaterialTierMedium. Newer C lighting/post and A0101 calibration are not mixed midmatrix. Their joint integration remains required. No main merge/push, phone action, road/building/far-field geometry or global lighting/settings change was performed.

Three provenanced Commons DAF/Volvo photographs (refs/sources.json and docs/REFERENCES.md) support qualitative appearance, not measured BRDF/albedo/depth/photometry. Owner D30/D35(lacquer), D31/D34/D44(glazing), ADR0059 and ADR0083 remain criteria; no maker-specific design is copied.

## Decision and measured causes

Actual production-shader GPU readback proved RGBAHalf overflow: authored dayDRL160000/high80000 stored and sampledInfinity; nightDRL56000 stayed finite and nightlow50000 quantized50016. Auto day/night/high-off behaviour was correct. The texture remains16x1RGBAHalf, now encoded at1000nits/unit; scale and exposure are multiplied in float before half emission. Final actualGPU returns encoded160/80/56/50/0 and exposed16/8/5.6/5/0 atExposure.0001, allfinite. Authored nits are WORKING_VALUE, not a measured lamp specification. Existing state-hash caching/texture/pass count remains unchanged. Fixed native headlamp-module ROI statistics are retained without claiming every baseline panel was white.

Clearcoat already existed. Pigment/F0.04/coatamount1/nominalcoatroughness.08/base roughness are retained. Legacy stored PaintColor.78/.785/.78 uploads as actualGPU multiplier.5704816/.5787147/.5704816, then_CMap; it is not a physical albedo measurement. DirtColor.15 reaches.01960665GPU. Builder comments/report explicitly preserve this encoding rather than introducing a broad gamma conversion.

OrangePeel.012->.004 is a local WORKING_VALUE reduction in unresolved lobe broadening. The capture has plain box mips, not GGX-prefiltered probe mips. Capture-only mapping now approximates angular alpha=pr^2 against face-centre texel2/N: log2(max(pr^2*N/2,1)), capped by actual mip count. Actual face size occupies existing EnvParams.y; same texture sample/size/rate/LOD and existing analytic/GGX fallback remain. This is an approximation, not GGX convolution or reflectance gain. Focused C2 improved overcast door profiles but did not meet4points.

Capture explicitly uses its physical-radiance/look-off contract and restores actual previous tone/sky/capture globals in finally. Source inspection motivated this protection; probes do not establish a separate visible gain from the tone bypass, so none is claimed.

Near windscreen ExteriorTransmission.42->1 tests actual Fresnel/absorption rather than extra artistic attenuation. Door calibration.42 and far-pane clutter.35 remain. Absorption.16, wiper film and physical Fresnel are retained. Premultiplied glass fog now adds only alpha-scaled in-scatter over the already fogged transmitted scene. The small finite-capture roughness floor.09 is retained; real scene reflections are not replaced with a generic sky.

Actual near shader fields are Tmedian~.745/F~.082/filmmedian0; near/far flags are correct and no extra glazing overlay exists. Overcast near-radianceOFF sigma10.43Low/7.83High versus actual5.92/5.33 and near-paneOFF12.10/10.11 identifies additive body/reflection filling the dark cab. These are postgraded display statistics, not pre-tonemap energy. No further arbitrary transmission/clutter boost or blur of real transmitted geometry is justified.

## Bounded pressed-panel normal

Actual exported DOOR_L/R lower paint panels(sourceheight1.35..1.85m,fore/aft-.35...65m) have211sampled loops per side, lateral-position std0 and geometry-normal std0. Bilinear4096normal PNG samples are constant(up~.00392,std~2e-9:8bitflat-normal bias). Loft.side_pt is flat there; front R10m crown does not extend to doors. SHA-tied evidence is door-panel-normal-analysis.json. This source-map diagnostic is distinct from compressed GPU readback.

Photos show pressed transitions/mild bent reflections and broad nearly planar regions. They do not measure3.6mm or prove a uniform crown. Root accepted one generic bounded experiment: equivalent shading height3.6mm*sin(pi*u)^2*sin(pi*v)^2 over1.3m width/.65m height, analytic maximum tilt.99683degrees. Height and derivative vanish at patch boundaries. The same mapped normal feeds diffuse and coat; geometry/pigment/F0/base roughness remain fixed. No amplitude sweep was made. Root retained the subtle plausible result without inflated waves/seams, while owner gates remain FAIL.

Reserved rendering-layer bit10/0x400 selects exactly DOOR_L/R all3LODs; builder OR preserves lightbit0. Root/current-source searches found no prior consumer; this reserved bit is an integration conflict to disclose. Object-local hinge-relative coordinates, outer skin, paint mask and side-normal gate keep the patch attached through door opening/cab suspension/rebase and exclude body/fender/trim/glass/inner skin. No material/MPB/keyword/texture/interpolator was added. Additional door-pixel scalar/matrix math cost is UNVERIFIED.

## Diagnostic validity

The first no-pane control was invalid because TruckVisualRig.Apply re-enabled Renderer.enabled. Valid controls use forceRenderingOff, verify after rendering and restore finally. All-pane removal is separate because removing far doors exposes empty cab/bright background and confounds a single-pane reference.

Whole-model coatOFF also changes pigment roughness. The valid radiance-only control removes onlyenv*Fc+direct, retaining base roughness, attenuation and mapped normal; transient material assignments are restored from fullJSON and productionSHA checked. Final two overcast controls give door mean display addition+1.28Low/+1.66High; profileON3.32/2.77 versus radianceOFF2.21/1.52. This is separate from coherent crown OFF/ON, which changes diffuse and coat, and separate from the owner roof p99-p50 metric.

Dominant-horizontal non-tie GPU rays prove cube orientation for all+/-X/Z in both tiers. Independent High256 versus128 capture barely changes the precise gate crop; no larger default is justified. The hard house/upper boundary persists with near and all dedicated panes removed: transmitted cab/background geometry, not evidence of blocky near reflection. Exact native registration finds vehicle/background shift0; root independently confirms background translation0 over+/-12pixels. Dither-level RGB differences are not pose/scale changes.

Read-only actual mesh audit finds dedicated panes have only correct reverse-winding inside/outside pairs,0same-winding duplicates and0mixed inside flags. All6residual body/chassis glass submeshes have0triangles in the actual shader glazing-height band and0centroids in paneAABBs. Actual near mask=(outside0,glazing1,frame1), far after near removal=(inside1,glazing1,frame1).

Initial CommandBuffer.DrawRenderer layer tests returned0 because that readback path lacked URP perObjectData.RenderingLayer; this failed XML is retained/classified, not hidden or called production failure. Actual URP mask frames proved the semantic. Repaired isolated realCamera.Render tests use actual canonical mesh/layer data with LIGHT_LAYERS QA define off/on. Production has no such keyword variant; installedURP accessor is unconditional asuint(unity_RenderingLayer.x). All6repaired cases and full238EditMode pass,0skip. A diagnostic-only orphan CMap sampler was corrected when its texture was optimized away; invalid attempts created no accepted frames.

## Final actual outcomes

D30 uses the approved r7door vertical-profile max-min; D35 uses roof p99-p50, not coat-on/off mean. Values below are Rec709/sRGB display percentage points from documented1024ROIs, with native counterparts/placement proof in final-contract-metrics. They are not physical albedo.

| Condition | Door profile | Roof p99-p50 | Glass median | Glass sigma |
|---|---:|---:|---:|---:|
| High-clear | 6.67 | 2.59 | 30.20 | 5.18 |
| High-lowsun | 6.11 | 58.08 | 23.44 | 11.85 |
| High-overcast | 2.77 | 15.63 | 22.61 | 5.33 |
| Low-clear | 5.21 | 10.26 | 28.32 | 4.93 |
| Low-lowsun | 3.23 | 44.74 | 21.76 | 11.28 |
| Low-overcast | 3.32 | 14.17 | 18.80 | 5.92 |

Door requires4-10; overcastLow/High andLow-lowsun stillFAIL. Roof requiresLow>=6/High>=10; lockedC0High-clear stillFAIL(white clipping), separate Cshoulder integration remains open. Glassmedian requires23-45; severalconditions fail. Clear/lowsun sigma requires>=8: clearfails,lowsunpasses. Overcast sigma/reference requires>=.7: bothfail. Thresholds were not redefined or hidden.

Final canonicalTruck/Trailer/Install and actual lampGPU probe succeeded. Final102frames are fresh and complete; render exit was nonzero only AFTER OK102 plus mono cleanup/abort_threads and no crashstack, accepted under the existing explicit ADR0083 proof rule, not described as a normal exit. Final2coat controls exited0. FullEditMode238/238passed,0skip, including6lamp state/actualshader decode and6crown bounds/masks/canonicalrenderer/hinge-suspension-rebase/direction tests. FullGIS370passed/1xfail;4234inputs remained identical. No Python generator/product changes followed, so coordinator explicitly approved no redundant GIS repeat for shader/C#Editor refinements.

Final192rawSHA match,217source assets remain unchanged,0mesh/FBX or semantic hierarchy/local-pose changes across161nodes. All102before-SRP estimate/instanced-counter rows match baseline exactly. Those counters are not actual GPU drawcalls/timing. Additional shader math and Android performance remain UNVERIFIED.

Root independently read238XML and all12final sheets(102frames) plus18focusedOFF/ONpairs: no new scopedcab/glass/lamps/chase/rear regression. REVIEW.md records this independent review with attribution. REPORT remains explicitly PARTIAL OWNER QUALITY/FAIL; newer C/A0101 joint integration and unmet thresholds stay open. No evidence-backed larger normal amplitude or arbitrary T/clutter/F0 gain is justified by the current evidence.

Artifacts: artifacts/truck-paint-r1/{REPORT.md,REVIEW.md,STATUS.md,final-validation.json,candidate3-final-contract-metrics.json,candidate3-final-budget.json,candidate3-final-fixture-proof.json,candidate3-final-coat-contribution.json,final-editmode.xml,candidate3-final-960/}. Immutable baseline/invalid diagnostic history remain retained.

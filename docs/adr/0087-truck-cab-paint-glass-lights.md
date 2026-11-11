# ADR 0087: TRAKT cab lacquer, glazing and finite HDR lamp state

Status: experimental WIP, 2026-11-11. No visual acceptance or phone-performance claim yet.

## Fixed inputs and scope

StreamF starts at main232fbada with ADR0095. Before any baseline capture, authorized merge of maindb1432c5 brought ADR0086 into F atf52fabf6. Fresh world339.5s and complete PBR509s were generated from these sources. Canonical TruckAssetBuilder, TrailerAssetBuilder and WorldTruckInstaller ran before the baseline. Source and binary snapshot: artifacts/truck-paint-r1/baseline-fixture/fixture-proof.json (217source files,564Generated files;192world raw hashes verified; actual nested furniture.megascans QA:15ready sources,320props,954drain replacements).

The102baseline images are17registered truck/cab cameras xLow/High xovercast/clear/lowsun at2340x1080. Low uses WorldC, High uses WorldC_High, both world MaterialTierMedium. The baseline cache remains immutable. Concurrent C lighting/post defaults and later A calibration-r2 are not merged midmatrix; joint integration remains necessary.

Reference photographs are3Commons cab photographs (not generated owner mood sheets), with SHA in artifacts/truck-paint-r1/refs/sources.json and author/licence in docs/REFERENCES.md. They establish appearance, not physical BRDF/albedo/photometry. Project owner decisions D30/D35 (lacquer), D31/D34/D44 (glazing), ADR0059 and ADR0083 remain acceptance criteria. No vehicle branding/design is copied.

## Measured causes

1. Actual production-shader GPU readback proves RGBAHalf overflow: dayDRL160000 and highbeam80000 store/sample Infinity. NightdimDRL56000 remains56000, nightlow50000 quantizes to50016, highOFF is0; automatic day/night state selection works. Baseline GPU output is preserved in baseline-fixture/paint-color-probe.json. The authored nits remain WORKING_VALUE, not a measured lamp specification.
2. Clearcoat already exists. BaselineColor probe confirms legacy material Color upload0.78 becomes about0.5705linear; the candidate preserves that pigment rather than mechanically brightening it. The preserved stored RGB is0.78/0.785/0.78; actual shader multiplier is0.5704816/0.5787147/0.5704816, then multiplied by _CMap. Neither the stored0.78 nor this tint alone is a measured physical linear paint reflectance. DirtColor and DecalColor follow the same legacy serialized Color contract (.15 is directly measured as0.01960665GPU). Their numerical values are deliberately retained; no broad Color conversion is smuggled into F. Source F0 remains0.04 and coat amount1. The unresolved orange-peel slope broadens the nominal0.08coat to roughly0.145perceptual roughness. Candidate slope change is a local WORKING_VALUE experiment.
3. Low capture renders physical sky with its display cap disabled, but ordinary world surfaces still run the Low shader toe. Sampling that cube and then grading the vehicle applies this look twice. Candidate capture bypasses the toe while rendering physical reflection radiance and restores every previous global in finally. It does not change global lighting/post policy, capture size/rate/LOD or scene content.
4. Near-windscreen transmission0.42 is an extra artistic attenuation on top of physical Fresnel/absorption. It suppresses contrast. Candidate tests1.0 for the windscreen only; side-door legacy0.42 and far-pane clutter0.35 remain. ADR0059 rejected a previous high-transmission aquarium; that is an explicit visual rejection criterion, not ignored history.
5. Opaque fog was added to premultiplied glass on top of the already fogged transmitted background. Candidate scales in-scatter by alpha. A small finite-capture reflection-footprint filter is tested without replacing real scene reflections with a generic sky or changing physical Fresnel/direct-sun roughness.

## Candidate implementation

Lamp state keeps the same16x1RGBAHalf texture, encoded at1000nits/unit. Decode combines scale and exposure in float before conversion to half display radiance. Six regression cases cover finite storage across day/night/high on/off and actual source-shader GPU decode. No nits calibration is claimed.

Paint candidate changes OrangePeel0.012 to0.004; pigment, F0, coat amount and base roughness stay unchanged. Glass candidate keeps its original absorption/wiper model and tests the changes above. No geometry, extra draw, texture, runtime shader variant, worldCARPAINT or global preset is added. GPU cost remains UNVERIFIED until appropriate measurement.

## Diagnostic validity and baseline metrics

The first no-pane control was rejected: TruckVisualRig.Apply re-enabled Renderer.enabled. Corrected controls use forceRenderingOff, verify state after rendering, and restore it in finally. All-pane removal is kept separate from near-windscreen-only removal because removing far doors exposes the empty cab and strongly inflates variance. Initial invalid measurements are excluded.

The original coatOFF mode also changes underlying pigment roughness. A separate generated copy of the actual shader removes only env*Fc+direct;3transient paint-material assignments are restored from full serialized JSON, including failure. Production shader SHA is verified unchanged after diagnostics. This radiance-only causal delta is not the owner acceptance metric.

D30/D35 continuity uses the approved r7method: door vertical-profile max-min and roof p99-p50 in the documented1024boxes, plus raw-native counterparts in measure_contract.py. Baseline overcast roof15Low/16High already passes; door1.5Low/1.9High is below4. High-clear roof has83.5percent clipping in the diagnostic roof box, so reflection contrast is compressed; C integration is separate, and this is not addressed by excessive coat gain. Glazing median/sigma and near/all-pane controls are recorded separately.

Baseline102render ended nonzero only after OK102, all102fresh PNGs, mono cleanup/abort_threads and no crash stack; accepted under the same explicit ADR0083 rule as scripts/visual-qa.ps1. Corrected controls exited normally or met the same explicit output proof. Do not describe this as a normal baseline Unity exit.

## Candidate1 actual evidence (not accepted)

After explicit root release, canonical Truck/Trailer/Install completed and102matched frames rendered. Actual GPU storage is now DRL160/high80/night56/50/off0 (scale1000), all finite; exposed production decode at0.0001 gives16/8/5.6/5/0. Root observed thinner DRLs and less windscreen veil. All102camera budget rows are identical, with0mesh/FBX changes and0semantic hierarchy/local-pose changes. GPU timing remains UNVERIFIED.

Owner thresholds still FAIL. Overcast Low/High door profile ranges are1.57/2.01points (minimum4); roof14.17/15.72passes. Glass median18.77/22.61 and sigma5.92/5.32 remain below required median/near-pane-reference gates. Clear sigma4.92/5.18 is below8. Lowsun sigma11.28/11.84passes. Full condition rows are retained in candidate1-contract-metrics artifacts; this is not a visual PASS.

Actual paint-mesh diagnostics show coat1, AO1, median dirt.002, Fc.051, NoV.59 and effective roughness.0976; coat/masks are enabled. Dominant-horizontal non-tie cubemap orientation passes all +/-X/Z in both tiers. An independent High256 capture barely changes the native gate crop (p50 28.908->28.936, sigma11.113->11.074), so capture-size-only changes have no demonstrated value.

Corrected layer diagnosis: the hard house/upper boundary remains in the exact gate crop with only the near windscreen removed and with all dedicated panes removed. It is transmitted cab/background geometry, not evidence of a low-resolution near reflection. Root independently reviewed gate-step-layer-classification.png. Do not blur an actual transmitted silhouette into compliance. Front shader mask is uniformly outside/glazing/hasFrame=(0,1,1).

## Pending evidence

A renewed phone window explicitly holds all Unity launches. Candidate2 is CPU-prepared only: capture mips are box-filtered, so angular footprint alpha=pr^2 versus face-centre texel2/N replaces the GGX-prefiltered-probe mip heuristic in the capture branch. It is an approximation, not a GGX convolution. Both paint/glass consumers change; fallback, F0 and radiance remain unchanged. Numeric plan, focused matched render wrapper, far-pane mask and read-only generated mesh audit are prepared but not yet compiled/rendered/adopted. Full GIS completed during the hold:370passed/1xfailed, exit0 in542.66s. All4234source/generated/cache input hashes stayed identical;0new files and0restorations. The private744file recovery copy was not needed. FullGIS remains relevant after shader-only changes; repeat if Python/products change or a failure emerges. Final candidate images, EditMode, independent root review and final limitations remain required. No main merge/push is performed by this worker.

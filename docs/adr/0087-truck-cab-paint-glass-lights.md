# ADR 0087: TRAKT cab lacquer, glazing and finite HDR lamp state

Status: experimental WIP, 2026-11-11. No visual acceptance or phone-performance claim yet.

## Fixed inputs and scope

StreamF starts at main232fbada with ADR0095. Before any baseline capture, authorized merge of maindb1432c5 brought ADR0086 into F atf52fabf6. Fresh world339.5s and complete PBR509s were generated from these sources. Canonical TruckAssetBuilder, TrailerAssetBuilder and WorldTruckInstaller ran before the baseline. Source and binary snapshot: artifacts/truck-paint-r1/baseline-fixture/fixture-proof.json (217source files,564Generated files;192world raw hashes verified; actual nested furniture.megascans QA:15ready sources,320props,954drain replacements).

The102baseline images are17registered truck/cab cameras xLow/High xovercast/clear/lowsun at2340x1080. Low uses WorldC, High uses WorldC_High, both world MaterialTierMedium. The baseline cache remains immutable. Concurrent C lighting/post defaults and later A calibration-r2 are not merged midmatrix; joint integration remains necessary.

Reference photographs are3Commons cab photographs (not generated owner mood sheets), with SHA in artifacts/truck-paint-r1/refs/sources.json and author/licence in docs/REFERENCES.md. They establish appearance, not physical BRDF/albedo/photometry. Project owner decisions D30/D35 (lacquer), D31/D34/D44 (glazing), ADR0059 and ADR0083 remain acceptance criteria. No vehicle branding/design is copied.

## Measured causes

1. Actual production-shader GPU readback proves RGBAHalf overflow: dayDRL160000 and highbeam80000 store/sample Infinity. NightdimDRL56000 remains56000, nightlow50000 quantizes to50016, highOFF is0; automatic day/night state selection works. Baseline GPU output is preserved in baseline-fixture/paint-color-probe.json. The authored nits remain WORKING_VALUE, not a measured lamp specification.
2. Clearcoat already exists. BaselineColor probe confirms legacy material Color upload0.78 becomes about0.5705linear; the candidate preserves that pigment rather than mechanically brightening it. Source F0 remains0.04 and coat amount1. The unresolved orange-peel slope broadens the nominal0.08coat to roughly0.145perceptual roughness. Candidate slope change is a local WORKING_VALUE experiment.
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

## Pending evidence

Candidate canonical truck build compiled successfully (TRUCK_RESULT OK). Trailer/install/GPUafter/renders are held for ROOT's phone window; PHONE_RUN and GPT_UNITY_HOLD guard every F launch wrapper. Candidate images, final GIS/EditMode, budget comparison, independent root review and final limitations remain required before completion. No main merge/push is performed by this worker.

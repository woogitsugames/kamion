PARTIAL OWNER QUALITY: physical fixes/improvements; owner thresholds still FAIL. Final validation pending PHONE_RUN.
Branch: gpt-truck-paint; source checkpoint370b58cb; locked world/material inputdb1432c5, no newer C/A0101 mix.
ADR0087: finite16x1RGBAHalf lamp encoding1000nits/unit, float scale*exposure decode; authored nits remain WORKING_VALUE.
Actual GPU: DRL160/high80/night56/50/off0 encoded, exposed decode16/8/5.6/5/0 finite; no new texture/pass.
Capture: real scene/physical radiance with actual-global finally restore; box angular mip approximation, GGX fallback/F0 unchanged.
Paint: legacy stored.78/.785/.78 ->GPU.57048/.57871/.57048 times_CMap; preserved, not measured physical albedo.
Fixed generic3.6mm crown (<1deg) onlyactualdoor/all3LOD; coherentdiffuse+coat, geometry/pigment/F0/roughness unchanged.
Door ON: overcastLow3.32/High2.73 FAIL; clear5.21/6.69 PASS; lowsun3.23 FAIL/6.04 PASS (required4-10points).
Glass owner median/sigma remainFAIL in several conditions; real nearT~.745/F~.082, correctnear/far flags, no extra overlay.
Near-radianceOFF OVsd10.43/7.83 vsreal5.92/5.33: additivebody/reflection cutsdisplaycontrast; no arbitraryT/clutter boost.
High-clear roof range2.63 FAIL on lockedC0; C shoulder integration separate. No blanket appearance PASS.
Tests: GIS370passed/1xfail,4234inputsunchanged; realURPcrownGPU6/6. Final fullEditMode/lamp6/full102 pending.
Proof:0mesh/FBX/161pose deltas; selecteddraw/trisestimate rows unchanged. ActualGPUmathcost/Android timing UNVERIFIED.
PNG: candidate3-off-on-960 all6conditions; crown-pipeline-mask-preview.png; native-registration-gate.jpg.
References: provenanced Commons DAF/Volvo via docs/REFERENCES.md; qualitative shape only, no measured BRDF/depth.
Conflicts: reservedrenderingbit10/0x400 DOORsemantic keepslightbit0; TruckExterior/Glass, builder, capture, lights. No main merge/push/phone.
Open: final canonicalTruck/Trailer/Install+102+2OVcoat-radianceOFF+fullEditMode; independent finalrootreview; C/A0101 integrationfollowup.

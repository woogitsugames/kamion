# Read-only hero shell binding audit

Actual generated M_fire_station_thuja_shell and M_hedge_shell_thuja use identical URP/Lit shaderGUID933532a4fcc9baf4fa0491de14d08ed7, ALPHATEST_ON, textureGUIDdc0bd89d5477f364fb1eaa1fe9a0819c, Cull0, cutoff.5, AlphaToMask1, queue2450, smoothness.03, ReceiveShadows1 and instancingON. Hero only changes the A-correct gamma-encoded BaseColor1.2948545/1.2220582/1.5043314; old shell1/1/1. No shader/keyword behavior was lost by the alias.

RegionImporter generic alpha texture branch calls LitMaterial; no hedge-specific transmission applies. High core remains opaque WorldPBR atlas. The existing Kamion/Vegetation shader accepts matchingBaseMap/BaseColor/Cull/cutoff, flipsbackface normals and evaluates SH(n)+tSH(-n) via LeafAmbient. A hero-shell-only opt-in could test physical thin-foliage lighting at unchanged tint/materialslot and unchangedLow.

This is NOT yet a proven color correction. Existing factory VegetationMaterial resets BaseColor towhite, so it must not be used blindly or it loses the calibrated alias. Default CrownShade.5 adds normal-dependent lower-crown occlusion. The shader also has SRPDefaultUnlit depth plus UniversalForward, so unchangedmaterialslot can add High depth/passGPU cost; drawsEst may not include actual multipass calls. Cutoff/AlphaToMask/shadows and old-route material bindings must remain unchanged. No importer/shader/material source was changed in this audit. Any runtime experiment requires ROOTscope and fresh Unityrelease; no blanket tintboost proposed.

## Actual first facade probe and next scoped gate

First facade4PNG completed14:15:20, both exits0; all784source/product pins unchanged after import/capture. Cleanmaterial/UVgable paint remains105/123/141Low and112/131/150High. Glass still FAILED60–75: leftupper/midLow74.72/71.93,High83.36/79.43;right77.72/74.72,84.51/81.00. The G1–G4 overlays were inspected: each lies inside the middle pane, excluding mullions/trim/trees. R1 lies in the upper-leftroundglass quadrant. Wholepaint P1/P2/P3 proposed boxes are not substituted for the exact cleanmaterial masks.

ROOT approved a second hall-only .60factor, now [.0612,.0648,.0702], with the same soft sky gradient. New PBR and fresh328.6s world complete, protectedpixel audit passes;784glass2-ready pins freeze these products. Actual glass2 gate PENDING, no source-only brightness PASS.

Readonly runtime-binding check: WorldInstances.IsFoliage prefix list excludes both old M_hedge_shell_thuja and new M_fire_station_thuja_shell. Thus the alias lost no automatic swap; both remain genericLit. A source material already on the profile Vegetation shader is copied as-is, preservingtint/CrownShade and profileAlphaToMask. Prepared QA tests exactly thatHigh-only path, never shared fire_station_alpha (which also contains text/fence).

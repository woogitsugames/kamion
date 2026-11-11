# D / ADR0099 separate broad-wear probe

Current status: INACTIVE. Rebased candidate-broadwear-r2.patch applies to retained production paint candidate9ba7b0fe, preserving its calibrated transverse wheel response (.425 actual uniform, .085 width). It is NOT unchanged relative the original.85/.13 baseline. Originalr1 patch remains historical only.

Completed foundation: fresh372before images; explicit missing-asphaltUV sentinel; conservative whole-component lane transfer; one verified busstop oil rule; two actual gate approach pairs; source/raw strict invariants and386GISpass/1expectedfailure. These are distinct changes, not proof that three scalar blocks complete all wear quality.

Probe only these existing shader branches:
1. ROADWEAR smoothness increment.12 ->.18*lerp(.65,1.05,macro.b), using the existing sampled map. Old/fresh maximum increment.1134/.04725. Existing albedo darkening, strip width/centres and asphalt mean remain unchanged.
2. Existing gutter g *=lerp(.6,1.4,macro.a). Old/fresh maximum.77/.42; disrupt uniform deposits without a new central dirt layer. Existing damp/drip branches unchanged.
3. Existing longitudinal paint wheel term receives12percent of calibrated transverse term, only with real lane data. Keep .425/.085 calibrated transverse response, age/dirt, aggregate chip threshold and distance prefilter.

All numbers are WORKING_VALUE response calibration, not measured BRDF. Local Mapillary469512/191135/178375/102634/513486 refs motivate restrained wheel/edge variation and readable chipped markings. Photos remain reference only; no absolute albedo claim.

Same20SAMPLE_TEXTURE2D tokens; no new texture/material/keyword/draw or geometry, no roads/*/overrides edits. Extra scalar GPUcost UNVERIFIED. Preserve Tile=set_tile||elementScan||atlas, weather||runoff, macro/panel/splash, all car/vegetation branches.

Sequence after gate AFTER: preserve current actual field images/material+pose pins, gitapply-check and activate r2 only, render matching Low/High clear/OV lane/edge/patch/P8/P10 controls. Reject wet-looking ribbons, blanket grime, newly unreadable paint or globalroad brightness change. Root independent review chooses keep/reject, then full93x4 final matrix+EditMode/counters. CurrentPHONEhold requires a new explicitROOTrelease before any Unity; narrow8 andgateBEFORE8 already complete and must not be repeated.

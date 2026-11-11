# Light / post r12 - stream C, ADR0098

- Step1: read task02 streamC and owning rules; branch gpt-light-r12 from main4f7da66c. No black-car work, no main source edits, no phone/adb. Bootstrap local source/product copies and read-only data junctions next.
- NEXT COMMAND: `pwsh artifacts/light-r12/bootstrap.ps1`

- Step2: bootstrap complete: copied private Fab products, derived/CC0 data, generatedUnity assets, material cache/photos/Library; five source junctions are read-only by policy. git-lfs checkout done. 15 approved Fab ready via actual loader. Removed one source-code drift introduced by copying main material cache; own source baseline remains4f7da66c. Reviewed allsixS9reviews and visual-qa skill.
- NEXT COMMAND: `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c` (fresh baseline before any renderer edit).

- Step3: fresh baseline world build completed330s;128 High/Low chunk SHA verified against current manifest. Fab15ready and fallbackFalse. Geometry source unchanged; two GLB serialization hashes refreshed by rebuild. Fixed-camera capture wrapper checks MAIN PHONE_RUN before every Unity launch.
- NEXT COMMAND: powershell -File scripts/import-region.ps1 -Region bialystok-industrial-c (then capture.ps1 -Phase before).

- Step4: prepared PNG-native fixed-ROI metric script and documented primary installed URP evidence: camera dithering +/-1LSB plus sky +/-0.5LSB; FSR RCAS may also run at100pct. No renderer policy changed before baseline. Import rebuilding143stale material maps from exact source, healthy.
- NEXT COMMAND: powershell -File artifacts/light-r12/capture.ps1 -Phase before (after baseline import).

- Step5: widened standard comparisons to ALL registered scene cameras plus19 building cameras per root; targeted/lowsun isolation remains selectable. Added <=960px contact-sheet generator. FilmGrain volume intensity confirmed0; pepper diagnosis remains dither/RCAS until actual A/B evidence.
- NEXT COMMAND: powershell -File artifacts/light-r12/capture.ps1 -Phase before; then measure.py on each output condition.

- Step6: baseline import OK64chunks Low+High; fresh sky visibility bake1m2048, vis_road0.926, solid_inst82. Material cache rebuilt495s from unchanged4f7 source. Reverted Unity-only settings/sky side effects; no visual policy edit yet.
- NEXT COMMAND: powershell -File artifacts/light-r12/capture.ps1 -Phase before (full registry4conditions).

- Step6a: initial capture launch stopped before Unity because PS5 lacks Path.GetFullPath(path,basePath). Changed artifact wrapper child shell to pwsh7, required by existing visual-qa.ps1; restarted baseline capture successfully. No output accepted from failed launch.
- NEXT COMMAND: pwsh -File artifacts/light-r12/capture.ps1 -Phase before (running; inspect before-capture.log).

- Step7: untouched full baseline236PNGs(59x4), plus22selectedlowsun; all20standard sheets viewed. Route19 overcast gap Low116/High119 already matches photo116-121; keep exposure/toe. Clear High gable254.7/243.8/212.3 confirms clip. Added diagnostic-only rq_dither/rq_skydither; default oldpolicy preserved. QA explicit pipeline override hook centralized/static and logs actual URP fields. Root review requested before ablations.
- NEXT COMMAND: pwsh scripts/visual-qa.ps1 -Scene WorldC_High -Tier High -Lighting clear -Cameras r10_block_3,r10_block_4,r10_house_2 -Gate3 Data/Regions/bialystok-industrial-c/buildings_r10_cameras.json -OutputDir artifacts/light-r12/harness-parity/High-clear

- Step8: diagnostic emptyRq parity meanabs0.34LSB/max2 (only stochastic dither); root reviewed hook/noop. Six controlled noise variants: sky hf3px1.831 -> skyOff0.518 -> skyOff+sharp0withcameraDither0.482. Both-dithers-off0.222 visibly bands; rejected. Installed URP1767 skips RCAS keyword at exact0, actual0/overrideTrue logged. Keep final dither; measure edge/cab legibility before policy decision. All standard236 and selected22beforeframes viewed via22sheets. FullGIS running.
- NEXT COMMAND: inspect noise/legibility-zero road/window/cab edge crops; then implement clear-only shoulder and bounded shadow ablations.

- Step9: fullGIS355pass/2xfail; verified192canonical rawSHA after tests, saved manifest snapshot. High shadow2x2factor capture: same2048px/3cascades, combined .4/.3 bias +.2/.55 splits reduces broad trailer stairs with contacts kept (root viewed). Medium bias-only cleaner than .55split: reject Medium split change. Glass triangles persist in candidate; rendering shadow-off diagnostic before assigning cause. RCAS0 legibility: paintcontrast81->78, edge1.673->1.658px; cabnumeral149->148, gradient-4.6pct, windowcontrast29 preserved butmicrogradient-22pct. No no-loss claim.
- NEXT COMMAND: inspect Medium-no-shadow glass crop, implement actual default pipeline/sky/clear shoulder policy, verify emptyRq.

- Step10: actual glass primitive is hero kp_glass_block (GLB POSITION height6.82-8.38m), not generic M_glass; earlier roughness/SkyOcc heuristic excluded it, so discarded. Added explicit shader/importer flag ONLYkp_glass_block (root authorized). Temporary ignored material flag and GPU magenta probe confirmed exact visiblepane scope, probe restored. Toward-light4cm did not cure triangles; test actual-pane normal2cm next. Default remains0, no final glass fix claim. Existing WorldPBR panel offset untouched.
- NEXT COMMAND: inspect shadow/glass-kp-normal-02; choose bounded actual-material offset only if frame/contact proof passes; bake canonical source policies with Unity.

- Step11: source default candidate now HighFSRsharp0withEXPLICIToverride(mustnotfallbackURPdefault), Highsplits.2/.55 and Med/Highbias.4/.3, map sizes/counts andLowunchanged. PreLUTsky dither off onlypost tiers; finalURPdither retained. Clear-onlywhiteClip.9 shoulder preserves fixed low/midanchors, noEV/toe/Lowchange. Revision98 migrates shippedprofile; bake next to prove actual emptyRq (notonlyoverride). Glasssmalloffset remains diagnostic0default; paneShadowCaster omission rejected+removed.
- NEXT COMMAND: pwsh -File artifacts/light-r12/bake-policy.ps1; then emptyRq clear ROI proof before fullaftermatrix.

- Step12: Unitybaked revision98 profile +High/MediumURPassets from code; LowURP unchanged, actualHighFSRoverrideTrue/0. Restored only unintendedDusk/LowSunserialization side effects. Fullafter wrapper now restoresonlyM_Sky/ProjectSettings, preserving intended bakedpolicies. Three-wayglassdiagnostic realtimeOff alone fixes triangles, bakedOff alone doesnot; root authorized8/12cm sweep after rejection2/4cm. Canonicalimportflag assignedONLYkp_glass_block, receiverShadowCasterunchanged.
- NEXT COMMAND: inspect actual8cmnormal result; emptyRq High clear ROIs after bakeddefaults, then canonicalimport and finalmatrix.

- Step13: root chose8cm smallesttestedacceptable glazingoffset. Actualreceived frame shadow remains6.59LSB versus realtimeOff; broadtriangleerror13.62->1.00LSB; trailer/contactROI MAXdiff0 vscontrol, castersunchanged. Default8cm ONLYMed/High+explicitkp; Low/Ultra0, productioncap8cm. Added9meaningful EditModecases: shoulderanchors, Low/bakedpipeline consistency, semanticimport scope, bound/tier isolation. ClearwhiteClip.9 failedgable249R; factory1.1 now baked, verify actual beforefullmatrix. Canonicalimport resets ignoredtestmaterial tosource-generated semantic next.
- NEXT COMMAND: pwsh scripts/import-region.ps1 -Region bialystok-industrial-c; then emptyRq defaultROI proof/fullafter captures (no truckfixture refresh before matchedmatrix).

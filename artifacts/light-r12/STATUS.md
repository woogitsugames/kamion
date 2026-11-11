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

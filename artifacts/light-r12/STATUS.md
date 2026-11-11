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

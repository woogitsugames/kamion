# Light / post r12 - stream C, ADR0098

- Step1: read task02 streamC and owning rules; branch gpt-light-r12 from main4f7da66c. No black-car work, no main source edits, no phone/adb. Bootstrap local source/product copies and read-only data junctions next.
- NEXT COMMAND: `pwsh artifacts/light-r12/bootstrap.ps1`

- Step2: bootstrap complete: copied private Fab products, derived/CC0 data, generatedUnity assets, material cache/photos/Library; five source junctions are read-only by policy. git-lfs checkout done. 15 approved Fab ready via actual loader. Removed one source-code drift introduced by copying main material cache; own source baseline remains4f7da66c. Reviewed allsixS9reviews and visual-qa skill.
- NEXT COMMAND: `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c` (fresh baseline before any renderer edit).

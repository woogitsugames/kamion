# STATUS — ADR 0101 tint calibration r2 (branch tint-r2, base main 99b96327)

## Step 1 (done) — tooling
- WorldPbrTintRound: optional `-tintOutDir` (rounds go to artifacts/tint-r2/<round>/<Tier>-<lighting>).
- artifacts/tint-r2/run-round.ps1 (one Unity, Low WorldC / High WorldC_High x overcast/clear, Gate3 r10 cameras).
- tools/worldgen/qa/tint_ratio.py + tests/gis/test_tint_ratio.py: ratio-to-neutral method (>=2 cameras, lit+shaded). Spec pending baseline ROIs.
- build_world at HEAD done (manifest hashes only drift: chunk glb sha, props glb).
## Next
pwsh scripts/import-region.ps1 -Region bialystok-industrial-c ; pwsh artifacts/tint-r2/run-round.ps1 -Round baseline

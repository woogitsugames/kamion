# STATUS — ADR 0101 tint calibration r2 (branch tint-r2, base main 99b96327)

## Step 1 (done) — tooling
- WorldPbrTintRound: optional `-tintOutDir` (rounds go to artifacts/tint-r2/<round>/<Tier>-<lighting>).
- artifacts/tint-r2/run-round.ps1 (one Unity, Low WorldC / High WorldC_High x overcast/clear, Gate3 r10 cameras).
- tools/worldgen/qa/tint_ratio.py + tests/gis/test_tint_ratio.py: ratio-to-neutral method (>=2 cameras, lit+shaded). Spec pending baseline ROIs.
- build_world at HEAD done (manifest hashes only drift: chunk glb sha, props glb).
## Next
pwsh scripts/import-region.ps1 -Region bialystok-industrial-c ; pwsh artifacts/tint-r2/run-round.ps1 -Round baseline
## Step 2 (in progress) — baseline + r1 values
- Baseline import OK (111.3 MB Low / 239.7 MB High). Baseline round rendering (waited for PHONE_RUN lock).
- Tool on 0086 evidence (after-final vs before): gate hall/sky overcast 0.935 (High) / 0.965 (Low), High-clear clip 0.815; screen/plinth 0.304/0.282 — reproduces critic.
- r1 values in materials.py: kp_wall 0.37/0.38/0.38, noise_panel_dark 0.039/0.041/0.040; build_world done (derived glbs = r1).
## Next
(after baseline) pwsh artifacts/tint-r2/run-masks.ps1 -Materials 'kp_wall,noise_panel_dark,bridge_concrete,bridge_soffit,bed_soil,container_rust,hedge_thuja,booth_panel,car_paint_white' ; pwsh scripts/import-region.ps1 -Region bialystok-industrial-c ; pwsh artifacts/tint-r2/run-round.ps1 -Round r1

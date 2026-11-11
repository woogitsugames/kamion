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
## Step 3 (done) — baseline round (62 cams x 4 = 248 PNG, artifacts/tint-r2/baseline, not committed: PNGs)
- Baseline == 0086 after-final in all world ROIs (tool ratio identical to 3 decimals): gate hall/sky 0.935 High-ov, 0.966 Low-ov, High-clear clip 0.815; screen/plinth 0.304 / 0.282.
- Waited ~70 min on PHONE_RUN + GPT_UNITY_HOLD (respected both).
## Next
masks -> import r1 -> round r1 running (chain in background): see artifacts/tint-r2/masks.log, import-r1.log, round-r1.log
## Step 4 (done) — r1 measured; masks
- r1 (kp_wall .37/.38/.38, noise .039/.041/.040): gate hall/sky ov 0.72 High / 0.78 Low (was 0.94/0.97), High-clear 217 sRGB clip 0.001 (was 250, 0.815); docks 0.45/0.47; hall4 0.47/0.52.
- screens cassette/plinth ov on 3 lit cams 0.32-0.37 (was 0.26-0.31). Shaded under-deck band 0.42-0.44 (sanity).
- Masks: kp_wall/container/thuja/bed_soil have no renderer slot (instanced/hero) -> change mask. bed_soil unused in the world (no chunk lists it).
- bridge: Low biezenstwa-above draws HLOD; High mask: bridge_concrete = cornices 110->205 sRGB under 0086. Girder/asphalt 1.26-1.36 vs photo pier/road 0.95-1.02.
## Step 5 (running) — r2 adds bridge_concrete .26/.26/.25 (build_world.py)
Next: wait round-r2; uv run --project tools/worldgen python tools/worldgen/qa/tint_ratio.py --round artifacts/tint-r2/r2 --before artifacts/tint-r2/baseline --masks artifacts/tint-r2/masks

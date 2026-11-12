# STATUS — sbs-poses-r2 (ADR 0140, s13)

- 2026-11-12: worktree from main 76c88d4f; copied rectified photos (artifacts/sbs-gate3/rectified, 40) and g3b-lowread final renders (Low overcast/clear, post-0127 world, current poses) as "before"; tools copied from artifacts/sbs-poses/tools.
- NEXT: `uv run --project tools/refs python artifacts/sbs-poses-r2/tools/poselib.py` (formula check), then portal leg resection.
- Found: worktree Data/raw/derived + Unity import were pre-0127 (16 m portal, sign_gantry_16_74); copied g3b-lowread derived world + _Generated/World + Library (= main a6cfe38 world, 14 m).
- Resection (tools/resect.py): legs of the 14 m portal + prior (lane for grobin, EC chimney x for zsolt): 275528 20.1->15.2 m, 837235 68.2->58.9 m (heading -1.75), 3281350 49.4->44.4 m, 297817 119.1->110.8 m (heading -0.54). Residuals < 0.1 px legs.
- PARTIAL diagnosis started; probes for 150280 (horizon 0.50, heading -2.2), 3678296 (horizon 0.559), 1801374 (lateral/eye) added to r1.
- Tool: scripts/sbs-low-pairs.ps1 + tools/refs/sbs_pairs.py (preflight + pairs <= 960), test tests/gis/test_sbs_pairs.py (not yet run, heavy).
- NEXT: wait r1 render (PHONE_RUN): `pwsh artifacts/sbs-poses-r2/tools/render.ps1 -Round r1` (running in background), then sheets.
- r1 (29 probes) + r2 (837235 chevron) rendered; choices in tools/choice.json; finalize.py r1 r2 --write -> overrides/cameras/references for 275528, 837235, 3281350, 297817, 150280, 3678296 (formula mismatches: none). 1801374/494288 unchanged (world).
- NEXT: full tool run `pwsh scripts/sbs-low-pairs.ps1 -OutputRoot artifacts/sbs-poses-r2/after -Before artifacts/sbs-poses-r2/before -SlotOwner claude-sbs-poses-r2` (background), then pytest heavy, merge main.
- Full tool run OK (after/ overcast+clear, pairs with before); tool fix for array flattening. merge main b596efe9; pytest 113 passed (heavy). Preflight now FAILs on main (overrides.yaml changed without world regen) - expected, lead regenerates.
- NEXT (lead): review + merge branch sbs-poses-r2; integration: regenerate world, import, `pwsh scripts/sbs-low-pairs.ps1 -Before artifacts/sbs-poses-r2/after`.

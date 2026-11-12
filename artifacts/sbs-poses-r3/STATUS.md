# sbs-poses-r3 (ADR 0143) STATUS
2026-11-12 18:32
- Worktree created; preflight STALE (derived chunks + overrides.yaml) -> regen running (artifacts/sbs-poses-r3/regen.log; build_world heavy slot then import-region unity slot).
- 494288 photo measured: road VP (441,687) = horizon 0.716; lane dash X=-0.83H, edge X=+2.66H -> camera ~1 m right of the lane dash (left half of the right lane). Production camera stands ~0.3 m left of the right edge line (ADR 0130 moved it 3 m right): main cause of the "curve right" + wide light strip.
- Lead added frames: 320326319617139 (promote probe from artifacts/biezenstwa-island/cams_sbs.json; island D-3/D-6 not on main), 482392746429891 (blue board right under viaduct end: pose vs world).
NEXT: wait for regen; then build probes r1 (tools/probes.py) and render: pwsh artifacts/sbs-poses-r3/tools/render.ps1 -Round r1
18:38 sha 787061126
- 810896: camera stands in the median between the carriageways (5.0 m left of SE-bound Andersa centreline, layer 1) beside the generated ramp wall; photo = car on SE-bound Andersa (guardrail+median+NW-bound+screens to the left). Probes: 3/7 m SW, +-10 m along.
- 837235: ADR 0128 (biezenstwa-island branch) puts U-4a on the 2024 island nose (decision 6); 0140 pose anchored on the 2019 nose (worn paint at -217.3,-240.3, 6.9 m from camera = photo ~6.5 m): pose consistent, difference = world epoch.
- 482392: blue lane-direction board (straight / right arrows, 2 posts) behind the right guardrail under the viaduct end; no such sign in overrides/instances -> world missing; pose also shifted (piers ~ 12-20 deg off). Probes sa-sd (0128 shift of the same richlv sequence).
- 320326: promotion overrides computed (E 541.5 N -690.4 U 140.52 eye 0.9 heading 244.0 rect horizon 0.7205).
NEXT: after regen: cd worktree; uv run --project tools/refs python artifacts/sbs-poses-r3/tools/probes.py r1; pwsh artifacts/sbs-poses-r3/tools/render.ps1 -Round r1

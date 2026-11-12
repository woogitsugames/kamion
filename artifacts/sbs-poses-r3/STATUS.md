# sbs-poses-r3 (ADR 0143) STATUS
2026-11-12 18:32
- Worktree created; preflight STALE (derived chunks + overrides.yaml) -> regen running (artifacts/sbs-poses-r3/regen.log; build_world heavy slot then import-region unity slot).
- 494288 photo measured: road VP (441,687) = horizon 0.716; lane dash X=-0.83H, edge X=+2.66H -> camera ~1 m right of the lane dash (left half of the right lane). Production camera stands ~0.3 m left of the right edge line (ADR 0130 moved it 3 m right): main cause of the "curve right" + wide light strip.
- Lead added frames: 320326319617139 (promote probe from artifacts/biezenstwa-island/cams_sbs.json; island D-3/D-6 not on main), 482392746429891 (blue board right under viaduct end: pose vs world).
NEXT: wait for regen; then build probes r1 (tools/probes.py) and render: pwsh artifacts/sbs-poses-r3/tools/render.ps1 -Round r1

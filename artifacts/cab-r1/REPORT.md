# K / ADR 0104 — IN PROGRESS, not ready to merge
Branch: gpt-cab-r1; base main 9e6e9fde; current SHA: see git rev-parse HEAD.
Scope: stream K only, isolated .claude/worktrees/gpt-cab-r1; no push/merge, no adb.
Prepared: copied local products, source LOD0, Library; source checks and lock-aware Unity evidence matrix.
GIS baseline: 370 passed / 1 xfailed (643.87 s), gis-baseline.log.
Blender export: PASS 103285 / 44190 / 21479 tris; instrument/head-box sightlines PASS.
Added inactive cab-seat / cab-materials QA cameras; native mirror RT/config audit and image-pair metrics.
Full adjusted source rays (315/glass), High: MainL100%, MainR99.0%, WideL84.1%, WideR74.9%, Kerb/Front100%.
Low exterior LOD2, interior/glass LOD0: WideL97.5%, WideR89.5%; other glasses100%.
Prepared but NOT enabled: LOD0-only 30mm housing-backing recess, no added topology, UV/slot/optics changes.
Source study: WideL97.5%, WideR88.3% after recess; right door/channel still obstruct. Not a Unity result.
Blender geometry PNGs inspected: clay-before/, clay-recess/, clay-pair-L.jpg, clay-pair-R.jpg.
Auxiliary A16 frames from leader: phone-lead-*; dirty APK, not candidate evidence; no phone actions by this stream.
OPEN: PHONE_RUN + GPT_UNITY_HOLD; no Unity process started by K. Fresh before/after matrix/EditMode/budgets pending.
OPEN: assess plastic grain, seams, seat/wheel wear in game-material detail frames; independent review and phone by leader.
Expected conflicts: TruckAssetBuilder.cs (additive QA views and future scoped mirror import), generated truck/scenes must rebuild.
No changes to TruckExterior.shader, glazing, TruckLights.cs, world materials, ProjectSettings or Packages.
Resume command after holds: pwsh -NoProfile -File artifacts/cab-r1/render-matrix.ps1 -Stage before

# K / ADR 0104 — STATUS
Branch gpt-cab-r1; base main 9e6e9fde. Worktree isolated; required copies and read-only source junctions prepared.
PHONE_RUN present: Unity not started. No adb.
NEXT: Get-Content docs/adr/0020-*.md,docs/adr/0042-*.md,docs/adr/0044-*.md,docs/adr/0045-*.md,docs/adr/0068-*.md; uv run --project tools/worldgen python -m pytest tests/gis -q
Library copied for independent import. NEXT: wait for PHONE_RUN removal, then pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting overcast -Cameras cab-driver,cab-dash,cab-left,cab-right,cab-mirrors-left,cab-mirrors-right,cab-mirror-front -OutputDir artifacts/cab-r1/before/Low-overcast
Cab export round-trip baseline recorded in export-baseline.log. PHONE_RUN still respected; baseline renders pending. NEXT: pwsh artifacts/cab-r1/render-matrix.ps1 -Stage before
Initial Blender check found ignored LOD0 FBX missing; copied local truck source directories from main and repeated check (see export-baseline.log). NEXT: finish Library copy, then wait PHONE_RUN and render baseline.
Added editor-only native mirror RT/configuration audit; no runtime settings changed. NEXT: after baseline matrix run CabMirrorAudit.Run with -cabTier Low/High -cabLighting overcast/clear.
Instrument/head-box source sightlines PASS. Interior-only 315-ray grid: four mirror glasses 100% clear, WideR 314/315 clear; front and kerb 315/315. Exterior housings/glass adjustment excluded, so full visibility UNVERIFIED until renders. NEXT: wait PHONE_RUN, render baseline, inspect native mirror images.
Found coordinator GPT_UNITY_HOLD after phone/Unity launch race; render launcher now respects both shared holds. No Unity has been started. NEXT: stable release of both holds, then render baseline.
GIS baseline: 370 passed, 1 xfailed, 643.87 s. Leader A16 frame (dirty APK 43bc53a769, auxiliary only): speed/stitches readable; dash smooth; front mirror visible, so historic visor issue not reproduced in that frame. No device touched. NEXT: fresh editor matrix after both holds clear.
Added inactive cab-seat (H-point-relative) and cab-materials QA cameras to builder; acceptance remains original driver-eye frames. No art/lighting/budget changes yet. NEXT: after holds clear BuildBatch + InstallBatch, then baseline matrix with 9 cameras.
Added reproducible image metrics and <=960px paired review sheets (measure.py). NEXT: complete before matrix then run tools/worldgen/.venv/Scripts/python.exe artifacts/cab-r1/measure.py.
ADR 0104 records audit contracts, baseline numbers and explicit evidence limits. PowerShell parser: 0 errors; Python AST checks pass. NEXT: execute queued baseline after stable phone/coordinator release; inspect PNGs before art changes.

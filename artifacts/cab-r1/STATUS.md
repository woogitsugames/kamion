# K / ADR 0104 — STATUS
Branch gpt-cab-r1; base main 9e6e9fde. Worktree isolated; required copies and read-only source junctions prepared.
PHONE_RUN present: Unity not started. No adb.
NEXT: Get-Content docs/adr/0020-*.md,docs/adr/0042-*.md,docs/adr/0044-*.md,docs/adr/0045-*.md,docs/adr/0068-*.md; uv run --project tools/worldgen python -m pytest tests/gis -q
Library copied for independent import. NEXT: wait for PHONE_RUN removal, then pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting overcast -Cameras cab-driver,cab-dash,cab-left,cab-right,cab-mirrors-left,cab-mirrors-right,cab-mirror-front -OutputDir artifacts/cab-r1/before/Low-overcast
Cab export round-trip baseline recorded in export-baseline.log. PHONE_RUN still respected; baseline renders pending. NEXT: pwsh artifacts/cab-r1/render-matrix.ps1 -Stage before
Initial Blender check found ignored LOD0 FBX missing; copied local truck source directories from main and repeated check (see export-baseline.log). NEXT: finish Library copy, then wait PHONE_RUN and render baseline.
Added editor-only native mirror RT/configuration audit; no runtime settings changed. NEXT: after baseline matrix run CabMirrorAudit.Run with -cabTier Low/High -cabLighting overcast/clear.

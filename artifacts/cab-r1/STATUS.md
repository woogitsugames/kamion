# K / ADR 0104 — STATUS
Branch gpt-cab-r1; base main 9e6e9fde. Worktree isolated; required copies and read-only source junctions prepared.
PHONE_RUN present: Unity not started. No adb.
NEXT: Get-Content docs/adr/0020-*.md,docs/adr/0042-*.md,docs/adr/0044-*.md,docs/adr/0045-*.md,docs/adr/0068-*.md; uv run --project tools/worldgen python -m pytest tests/gis -q

# ADR 0103 — stream J
Base main: 9e6e9fde. Dedicated branch/worktree gpt-sbs-gate3; required local copies and read-only-use junctions prepared. PHONE_RUN exists: Unity must wait.
NEXT: uv run --project tools/worldgen python -m pytest tests/gis -q

Step 2: offline tool generates 40 unique GPS/heading cameras (20 per segment), source hashes verified. Contact sheets inspected: night images need exclusion before final selection. Wrapper preserves aspect and honors main PHONE_RUN before every Unity start.
NEXT: uv run --project tools/refs python tools/refs/sbs_gate3.py prepare

Step 3: 40 day/twilight photos (night excluded), per-photo attribution and hashes; manual horizon estimates authored for all 40. True-north to grid-north heading correction added. Focused geometry/evidence integrity tests 6/6 pass. Full GIS baseline still running. PHONE_RUN remains active.
NEXT: pwsh scripts/sbs-gate3.ps1 -EditMode

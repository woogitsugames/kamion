# ADR 0103 — stream J
Base main: 9e6e9fde. Dedicated branch/worktree gpt-sbs-gate3; required local copies and read-only-use junctions prepared. PHONE_RUN exists: Unity must wait.
NEXT: uv run --project tools/worldgen python -m pytest tests/gis -q

Step 2: offline tool generates 40 unique GPS/heading cameras (20 per segment), source hashes verified. Contact sheets inspected: night images need exclusion before final selection. Wrapper preserves aspect and honors main PHONE_RUN before every Unity start.
NEXT: uv run --project tools/refs python tools/refs/sbs_gate3.py prepare

Step 3: 40 day/twilight photos (night excluded), per-photo attribution and hashes; manual horizon estimates authored for all 40. True-north to grid-north heading correction added. Focused geometry/evidence integrity tests 6/6 pass. Full GIS baseline still running. PHONE_RUN remains active.
NEXT: pwsh scripts/sbs-gate3.ps1 -EditMode

Step 4: ADR 0103 documents commands, coordinate/FOV contract, calibration, licence and coverage limits. Composer now draws histograms, checks photo hashes and supports authored sky/asphalt polygons. 6 focused tests pass. Main Library copied (robocopy exit 1 = success). Guarded render/EditMode runner started and is waiting for PHONE_RUN; no Unity launched.
NEXT: Get-Content artifacts/sbs-gate3/render-run.log -Tail 10

Step 5: PowerShell syntax and Python compilation pass; 7 focused tests (including mask overlap/area) pass. NumPy declared directly in refs dependencies. Coverage measured: G3-A stations 340.426–436.716 m (20 photos, max offset 28.235 m), G3-B 0–485.862 m (20 photos, max offset 33.732 m). Owner confirms phone test still active; continue waiting without touching lock.
NEXT: Get-Content artifacts/sbs-gate3/render-run.log -Tail 10

Step 6: full GIS baseline complete: 370 passed, 1 xfailed, 643.04 s. Report saved, honest PARTIAL pending 40 photo/render pairs, EditMode and pose review. No runtime/world code changed. Artifacts will be copied to main for leader visibility.
NEXT: Get-Content artifacts/sbs-gate3/render-run.log -Tail 10

Step 7: existing refs tool tests also pass after declaring NumPy directly (see pytest-refs.log). Unity remains queued under the owner-confirmed PHONE_RUN lock.
NEXT: Get-Content artifacts/sbs-gate3/render-run.log -Tail 10

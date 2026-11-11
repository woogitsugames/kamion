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

Step 8: fetched safe public intrinsics for all 40 references using existing header-only token loader (no credentials saved). 27 fisheye / 13 perspective. Added photographic radial rectification + matched FOV, preserved originals, hashed derivatives and preferred SfM compass. Rectified contacts inspected: bridge/poles now straight, no blank borders observed. 9 focused tests pass. No Unity start: PHONE_RUN still active.
NEXT: Get-Content artifacts/sbs-gate3/render-run.log -Tail 10

Step 9: exposed rectified_horizon_y_fraction for direct calibration on rectified sheets, avoiding double application of the lens transform. Original horizon field remains reproducible. Focused tests 9/9 still pass; worktree otherwise clean, Unity still waits for PHONE_RUN.
NEXT: Get-Content artifacts/sbs-gate3/render-run.log -Tail 10

Step 10: PHONE_RUN removed; guarded runner started EditMode at 11:55 local (log artifacts/logs/test-editmode-20261111-115503.log), then queued the 4-state camera matrix. No second Unity process for this project.
NEXT: Get-Content artifacts/sbs-gate3/render-run.log -Tail 15

Step 11: EditMode 226/226; first matrix 160 renders/sheets completed and archived under r0 (40 per state). Inspected initial pairs: definite below-deck camera error on 4 G3-A photos. Eight original/SfM position/heading probes rendered and inspected; original GPS better for richlv close viaduct and elevated sequences, SfM optical heading retained. Authored 4 deck heights from existing deck stations + 1.7m eye (world untouched), original-GPS deltas for richlv/4 elevated frames. R1 camera JSON generated; 9 focused tests pass.
NEXT: pwsh scripts/sbs-gate3.ps1

Step 12: R1 matrix complete (160/160); inspected representative corrected sheets. Two remaining fixes authored: source 454716650857984 moved 2.95m laterally from rail into lane; source 494288258686575 raised to measured road asphalt U 140.188 + eye 1.7. Exact pose diff asserts only these 2 of 40 changed, so 38 per state are retained; R1 originals for the 2 preserved. R2 rerenders 2 cameras x 4 states, no world changes.
NEXT: pwsh artifacts/sbs-gate3/rerender-r2.ps1

Step 13: R2 complete, all 160 PNGs loaded/hashed and metrics consistent; stats Low regular drawsEst 188–486 / trisK 155–556 (CPU estimates, no world changes). Full contact review found 3 more sunset deck photos with NMT-level cameras, plus one wrong SfM heading; R3 authoring raises them to existing deck + eye and selects original compass for 1406533339711789. Exact pose diff limited to these 3; default metrics now include separate sky/asphalt area AND brightness ratios. PNG/JSON writes atomic to avoid reading partial outputs. Focused tests 10/10.
NEXT: pwsh artifacts/sbs-gate3/rerender-r3.ps1

Step 14: final R3 complete, all 160 frames/sheets decode and source/comparison/render/camera hashes match; 40 distinct original hashes. Final authored coverage and complete per-state stats in SUMMARY.json; 27 poses changed from r0. Updated ADR/licenses/references and honest self-review (gate NOT accepted). Full GIS final sweep running; no Unity remains for this worktree, settings restored.
NEXT: Get-Content artifacts/sbs-gate3/pytest-final.log -Tail 10

Step 15 COMPLETE: final full GIS 380 passed, 1 existing xfailed (601.07 s); refs 51/51 and EditMode 226/226. Final audit validates 40 distinct real photos, 40 rectified sources, 160 renders/sheets with matching hashes and all 160 stats entries; all 4-state overviews and key full before/after PNGs viewed. Final camera inputs + Unity logs + EditMode XML included in artifact bundle. No runtime/world changes, no merge/push/adb. Independent leader review and owner gate acceptance remain explicitly open.
NEXT (leader, after review): git merge gpt-sbs-gate3

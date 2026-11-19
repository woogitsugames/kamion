& "C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\dk19-tiles-s23\artifacts\dk19-tiles-s23/run-steps.ps1" -Log "C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\dk19-tiles-s23/artifacts/logs/dk19-world-wygoda2.log" -Steps @(
  'uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-wygoda --context',
  'pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner dk19-tiles-s23')


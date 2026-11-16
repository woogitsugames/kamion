& "C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\dk19-tiles-s23\artifacts\dk19-tiles-s23/run-steps.ps1" -Log "C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\dk19-tiles-s23/artifacts/logs/dk19-world-mickiewicza-r3.log" -Steps @(
  'pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner dk19-tiles-s23-mickiewicza',
  'uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-mickiewicza --context',
  'pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner dk19-tiles-s23-mickiewicza')


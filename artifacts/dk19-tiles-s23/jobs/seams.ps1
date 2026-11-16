& "C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\dk19-tiles-s23\artifacts\dk19-tiles-s23/run-steps.ps1" -Log "C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\dk19-tiles-s23/artifacts/logs/dk19-seams.log" -Steps @(
  'uv run --project tools/worldgen python -m tools.worldgen.qa.seams --tiles bialystok-industrial-c,bialystok-wygoda,bialystok-bojary,bialystok-mickiewicza,bialystok-dojlidy --json artifacts/dk19-tiles-s23/seams/seams.json --md artifacts/dk19-tiles-s23/seams/seams.md')


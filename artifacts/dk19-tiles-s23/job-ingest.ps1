$wt = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
& "$PSScriptRoot/run-steps.ps1" -Log "$wt/artifacts/logs/dk19-ingest.log" -Steps @(
  'uv run --project tools/worldgen tools/worldgen/ingest.py --region bialystok-wygoda',
  'uv run --project tools/worldgen tools/worldgen/ingest.py --region bialystok-bojary',
  'uv run --project tools/worldgen tools/worldgen/ingest.py --region bialystok-mickiewicza')

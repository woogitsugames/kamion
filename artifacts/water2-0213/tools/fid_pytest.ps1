Set-Location (Resolve-Path "$PSScriptRoot/../../..")
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner water2-0213-pytest | Out-Null
uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region bialystok-industrial-c *> artifacts/water2-0213/logs/fidelity.log
"FIDELITY exit=$LASTEXITCODE" | Add-Content artifacts/water2-0213/logs/fidelity.log
uv run --project tools/worldgen python -m pytest tests/gis -q --deselect tests/gis/test_determinism.py::test_road_stage_independent_of_hash_seed -p no:cacheprovider *> artifacts/water2-0213/logs/pytest-gis.log
"PYTEST exit=$LASTEXITCODE" | Add-Content artifacts/water2-0213/logs/pytest-gis.log
pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner water2-0213-pytest | Out-Null

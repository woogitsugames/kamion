Set-Location $PSScriptRoot\..\..
$A = "artifacts/knyszyn-0204"; "start $(Get-Date -Format s)" | Set-Content "$A/pytest.status"
pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner knyszyn-0204-pytest | Out-Null
uv run --project tools/worldgen python -m pytest tests/gis -q --no-header -p no:cacheprovider --deselect tests/gis/test_road_fidelity.py::test_report_not_stale *> "$A/pytest_gis.log"
"exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content "$A/pytest.status"
pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner knyszyn-0204-pytest | Out-Null

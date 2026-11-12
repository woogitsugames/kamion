$ErrorActionPreference='Stop'
Set-Location (Split-Path (Split-Path $PSScriptRoot))
& pwsh artifacts/landmarks-r2/heavy-step.ps1 -Step WorldWithFocusedGIS -Log artifacts/landmarks-r2/candidate-weather-world.log
if($LASTEXITCODE -ne 0){throw 'Weather tests/world failed'}
$world=Get-Content "$PSScriptRoot/candidate-weather-world.log" -Raw
if($world.Contains('fallback=True') -or -not $world.Contains('done')){throw 'Weather world incomplete or using fallback'}
& uv run --project tools/worldgen python artifacts/landmarks-r2/audit_geometry.py *> artifacts/landmarks-r2/geometry-audit-weather.log
if($LASTEXITCODE -ne 0){throw 'Geometry invariants failed'}
Add-Content -Encoding utf8 "$PSScriptRoot/STATUS.md" "`nKrok 8: świat weather zakończony bez fallback=True. Audyt porównał pomosty i roads_qa z baseline oraz sprawdził zakres payload runoff. NASTĘPNY KROK: import Low+High i wszystkie 58 kamer w czterech kombinacjach do after-weather."
& git add -f artifacts/landmarks-r2/STATUS.md artifacts/landmarks-r2/geometry-audit.json
& git commit -m 'wip(landmarks): świat weather i audyt niezmienionych pomostów'
if($LASTEXITCODE -ne 0){throw 'Weather checkpoint failed'}
& pwsh artifacts/landmarks-r2/unity-step.ps1 -Step Import
if($LASTEXITCODE -ne 0){throw 'Weather import failed'}
& pwsh artifacts/landmarks-r2/unity-step.ps1 -Step Capture -Phase after-weather -Cameras all
if($LASTEXITCODE -ne 0){throw 'Weather capture failed'}
@{complete=$true;focused_exit=0;world_exit=0;audit_exit=0;import_exit=0;capture_exit=0} | ConvertTo-Json | Set-Content -Encoding utf8 "$PSScriptRoot/candidate-weather-result.json"
exit 0

$ErrorActionPreference = 'Stop'
Set-Location (Split-Path (Split-Path $PSScriptRoot))
& pwsh artifacts/landmarks-r1/heavy-step.ps1 -Step Materials -Tiers 'High,Medium,Low' -Log artifacts/landmarks-r1/glass-final-materials.log
if ($LASTEXITCODE -ne 0) { throw 'Final glass material failed' }
& uv run --project tools/worldgen python artifacts/landmarks-r1/scope_material_spec.py
if ($LASTEXITCODE -ne 0) { throw 'Material spec scoping failed' }
Add-Content -Encoding utf8 "$PSScriptRoot/STATUS.md" "`nKrok 29: końcowy materiał szkła wygenerowany w High/Medium/Low pod heavy i ograniczony do własnego wpisu spec. Następnie pojedynczy test remizy."
& git add art-source/world/materials/materials_spec.json art-source/world/landmarks/fire_station_jrg2/atlas_layout.json art-source/world/landmarks/fire_station_jrg2/conifer_foliage_meta.json
& git add -f artifacts/landmarks-r1/STATUS.md artifacts/landmarks-r1/scoped-material-spec.json
& git commit -m 'wip(landmarks): końcowy materiał wnętrza tafli'
if ($LASTEXITCODE -ne 0) { throw 'Material checkpoint failed' }
& pwsh artifacts/landmarks-r1/heavy-step.ps1 -Step FocusedGIS -Log artifacts/landmarks-r1/glass-final-focusedgis.log
if ($LASTEXITCODE -ne 0) { throw 'Final glass focused tests failed' }
Add-Content -Encoding utf8 "$PSScriptRoot/STATUS.md" "`nKrok 30: pojedynczy test remizy po końcowej korekcie zakończony exit 0 pod heavy. Import i szybkie cztery rendery łuków przed walidacją całej trasy."
& git add -f artifacts/landmarks-r1/STATUS.md artifacts/landmarks-r1/glass-final-focusedgis.log
& git commit -m 'wip(landmarks): walidacja końcowej maski szkła'
if ($LASTEXITCODE -ne 0) { throw 'Test checkpoint failed' }
& pwsh artifacts/landmarks-r1/unity-step.ps1 -Step Import
if ($LASTEXITCODE -ne 0) { throw 'Final material import failed' }
& pwsh artifacts/landmarks-r1/unity-step.ps1 -Step Capture -Phase glass-final -Cameras fire-station-ref7197
if ($LASTEXITCODE -ne 0) { throw 'Final glass capture failed' }
@{complete=$true;materials_exit=0;focused_exit=0;import_exit=0;capture_exit=0} | ConvertTo-Json | Set-Content -Encoding utf8 "$PSScriptRoot/glass-final-result.json"
exit 0

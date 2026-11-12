$ErrorActionPreference = 'Stop'
Set-Location (Split-Path (Split-Path $PSScriptRoot))
function Checkpoint([string]$Message,[string[]]$Paths) {
    Add-Content -Encoding utf8 "$PSScriptRoot/STATUS.md" "`n$Message"
    & git add -f artifacts/landmarks-r1/STATUS.md @Paths
    if ($LASTEXITCODE -ne 0) { throw 'WIP staging failed' }
    & git commit -m 'wip(landmarks): checkpoint materiału i walidacji wariantu 2'
    if ($LASTEXITCODE -ne 0) { throw 'WIP commit failed' }
}
& pwsh artifacts/landmarks-r1/heavy-step.ps1 -Step Materials -Tiers High,Medium,Low -Log artifacts/landmarks-r1/round2-materials-fixed.log
if ($LASTEXITCODE -ne 0) { throw 'Fixed material generation failed' }
& uv run --project tools/worldgen python artifacts/landmarks-r1/scope_material_spec.py
if ($LASTEXITCODE -ne 0) { throw 'Shared spec scoping failed' }
Checkpoint 'Krok 25: materiał z poprawką białych detali wygenerowany we wszystkich trzech rozdzielczościach pod heavy. Wspólny spec zachowuje wszystkie pozostałe wpisy z HEAD. Następnie pojedynczy test remizy; bez pełnego GIS.' @(
    'art-source/world/materials/materials_spec.json',
    'art-source/world/landmarks/fire_station_jrg2/atlas_layout.json',
    'art-source/world/landmarks/fire_station_jrg2/conifer_foliage_meta.json',
    'art-source/world/textures/fire_station_alpha.png',
    'artifacts/landmarks-r1/scoped-material-spec.json')
& pwsh artifacts/landmarks-r1/heavy-step.ps1 -Step FocusedGIS -Log artifacts/landmarks-r1/round2-focusedgis-fixed.log
if ($LASTEXITCODE -ne 0) { throw 'Focused tests still failing; no import' }
Checkpoint 'Krok 26: pojedynczy plik testów remizy po poprawce zakończony exit 0 pod heavy. Pipeline przechodzi do importu i 16 renderów fokusowych wariantu 2 przez oddzielne sloty Unity. NASTĘPNA KOMENDA: Get-Content artifacts/landmarks-r1/round2-resume-wrapper.log -Tail 10' @(
    'artifacts/landmarks-r1/round2-focusedgis-fixed.log')
& pwsh artifacts/landmarks-r1/unity-step.ps1 -Step Import
if ($LASTEXITCODE -ne 0) { throw 'Fixed variant import failed' }
& pwsh artifacts/landmarks-r1/unity-step.ps1 -Step Capture -Phase round2
exit $LASTEXITCODE

$ErrorActionPreference='Stop'
Set-Location (Split-Path (Split-Path $PSScriptRoot))
& pwsh artifacts/landmarks-r4/heavy-step.ps1 -Step World -Log artifacts/landmarks-r4/baseline-world.log
if($LASTEXITCODE -ne 0){throw 'R4 baseline generation failed'}
$world=Get-Content "$PSScriptRoot/baseline-world.log" -Raw
if($world.Contains('fallback=True') -or -not $world.Contains('done')){throw 'Baseline incomplete or using fallback'}
New-Item -ItemType Directory -Force "$PSScriptRoot/baseline-generated" | Out-Null
foreach($name in @('world_manifest.json','streetscape_qa.json','roads_qa.json')) {
    Copy-Item -LiteralPath "Data/Regions/bialystok-industrial-c/generated/$name" -Destination "$PSScriptRoot/baseline-generated/$name"
}
Copy-Item -LiteralPath Data/Regions/bialystok-industrial-c/generated/landmarks/viaduct_putry_underdeck.spec.json -Destination "$PSScriptRoot/baseline-generated/underdeck.spec.json"
Add-Content -Encoding utf8 "$PSScriptRoot/STATUS.md" "`nKrok 3: świeży baseline świata po merge main wygenerowany pod heavy, bez fallback=True. Agregaty i spec podmostowy zachowane. NASTĘPNY KROK: import i wszystkie kamery trasy wraz z odziedziczonymi kadrami landmarks pod slotem Unity."
& git add -f artifacts/landmarks-r4/STATUS.md
& git commit -m 'wip(landmarks): świeży świat bazowy remizy po integracji main'
if($LASTEXITCODE -ne 0){throw 'Baseline checkpoint failed'}
& pwsh artifacts/landmarks-r4/unity-step.ps1 -Step Import
if($LASTEXITCODE -ne 0){throw 'R4 baseline import failed'}
& pwsh artifacts/landmarks-r4/unity-step.ps1 -Step Capture -Phase before -Cameras all
if($LASTEXITCODE -ne 0){throw 'R4 baseline capture failed'}
$counts=@{}
foreach($condition in @('Low-overcast','Low-clear','High-overcast','High-clear')) {
    $count=@(Get-ChildItem "$PSScriptRoot/before/$condition" -Filter *.png).Count
    if($count -lt 48){throw "Incomplete baseline inventory: $condition $count"}
    $counts[$condition]=$count
}
@{complete=$true;world_exit=0;import_exit=0;capture_exit=0;camera_counts=$counts} | ConvertTo-Json | Set-Content -Encoding utf8 "$PSScriptRoot/baseline-result.json"
exit 0



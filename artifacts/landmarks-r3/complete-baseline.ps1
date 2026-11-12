param([int]$WorldPid=49724)
$ErrorActionPreference='Stop'
Set-Location (Split-Path (Split-Path $PSScriptRoot))
# This is a dependent continuation of the confirmed live baseline process.
# No second world generator is started here.
while (Get-Process -Id $WorldPid -ErrorAction SilentlyContinue) { Start-Sleep -Seconds 5 }
while (Test-Path 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\heavy-slots\gpt-landmarks-r3.slot') { Start-Sleep -Seconds 2 }
$world=Get-Content "$PSScriptRoot/baseline-world.log" -Raw
if($world.Contains('fallback=True') -or -not $world.Contains('done')){throw 'Baseline incomplete or using fallback'}
New-Item -ItemType Directory -Force "$PSScriptRoot/baseline-generated" | Out-Null
foreach($name in @('world_manifest.json','streetscape_qa.json','roads_qa.json')) {
    Copy-Item -LiteralPath "Data/Regions/bialystok-industrial-c/generated/$name" -Destination "$PSScriptRoot/baseline-generated/$name"
}
Copy-Item art-source/world/props/props_meta.json "$PSScriptRoot/baseline-generated/props_meta.json"
Copy-Item art-source/world/props/street_props.glb "$PSScriptRoot/baseline-generated/street_props.glb"
Add-Content -Encoding utf8 "$PSScriptRoot/STATUS.md" "`nKrok 7: świeży baseline świata po merge main ukończony bez fallback=True. Zachowano manifest, QA i własną bibliotekę proceduralną do porównań kominów. NASTĘPNY KROK: import przygotowanych danych i pełne cztery zestawy QA, pod Unity."
git add -f artifacts/landmarks-r3/STATUS.md
git commit -m 'wip(landmarks): świeży baseline r3 po restarcie maszyny'
if($LASTEXITCODE -ne 0){throw 'Baseline checkpoint failed'}
& pwsh artifacts/landmarks-r3/unity-step.ps1 -Step Import
if($LASTEXITCODE -ne 0){throw 'R3 baseline import failed'}
& pwsh artifacts/landmarks-r3/unity-step.ps1 -Step Capture -Phase before -Cameras all
if($LASTEXITCODE -ne 0){throw 'R3 baseline capture failed'}
$inventories=@{}
foreach($condition in @('Low-overcast','Low-clear','High-overcast','High-clear')) {
    $frames=@(Get-ChildItem "$PSScriptRoot/before/$condition" -Filter *.png -File | Sort-Object Name | ForEach-Object Name)
    if($frames.Count -lt 13){throw "Incomplete inventory: $condition"}
    $inventories[$condition]=$frames
}
$first=$inventories['Low-overcast'] -join '|'
foreach($condition in $inventories.Keys) { if(($inventories[$condition] -join '|') -ne $first) {throw "Different baseline camera inventory: $condition"} }
@{complete=$true;world_exit=0;import_exit=0;capture_exit=0;camera_inventories=$inventories;count_per_condition=$inventories['Low-overcast'].Count;utc=(Get-Date).ToUniversalTime().ToString('o')} | ConvertTo-Json -Depth 6 | Set-Content -Encoding utf8 "$PSScriptRoot/baseline-result.json"
Add-Content -Encoding utf8 "$PSScriptRoot/STATUS.md" "`nKrok 8: import i baseline QA zakończone; faktyczny spis kamer w baseline-result.json. Następnie obejrzenie pełnych zestawów i pary zdjęcia EC przed wdrożeniem."
git add -f artifacts/landmarks-r3/STATUS.md artifacts/landmarks-r3/baseline-result.json
git commit -m 'wip(landmarks): pełny baseline fotograficzny EC i trasy'
exit 0

# Import the region and render the fire-station QA cameras (Low + High x overcast + lowsun). Run from the repo root.
param([string]$Tag = 'r1', [switch]$SkipImport)
$ErrorActionPreference = 'Continue'
$lock = 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN'
$logs = "artifacts/firestation-r9/logs"
function Wait-Lock { while (Test-Path $lock) { Start-Sleep -Seconds 60 } }
if (-not $SkipImport) {
    Wait-Lock
    pwsh scripts/import-region.ps1 -Region bialystok-industrial-c *> "$logs/import_region_$Tag.log"
    "IMPORT_EXIT $LASTEXITCODE" | Add-Content "$logs/unity_round_$Tag.log"
}
foreach ($tier in 'High', 'Low') {
    foreach ($light in 'overcast', 'lowsun') {
        Wait-Lock
        pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $tier -Lighting $light -Cameras fire_station_route,fire_station_abeam,fire_station_ref7197,fire_station_above,driver_andersa_to_putry -OutputDir "artifacts/firestation-r9/unity/$Tag/$tier-$light" *> "$logs/vqa_${Tag}_${tier}_$light.log"
        "VQA $tier $light EXIT $LASTEXITCODE" | Add-Content "$logs/unity_round_$Tag.log"
    }
}
"ROUND_DONE" | Add-Content "$logs/unity_round_$Tag.log"

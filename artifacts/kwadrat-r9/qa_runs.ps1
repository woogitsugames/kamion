# Control renders of the Kwadrat Park yard (ADR 0071): WorldC, Low + High x overcast + lowsun, start cameras of G3-A.
# pwsh artifacts/kwadrat-r9/qa_runs.ps1 -Phase after1 [-Combos 'High-overcast,Low-overcast']
param([string]$Phase = 'after', [string]$Combos = 'High-overcast,Low-overcast,High-lowsun,Low-lowsun')
$root = Resolve-Path "$PSScriptRoot/../.."
Set-Location $root
$cams = 'g3a_eye_s0012,g3a_eye_s0062,g3a_eye_s0112,g3a_ext34_s0040,kwadrat_park_gate,stretch_05_docks,g3a_eye_s0162,g3a_eye_s0212'
foreach ($c in $Combos.Split(',')) {
    $tier, $light = $c.Split('-')
    while (Test-Path 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN') { Start-Sleep 60 }
    $out = "artifacts/kwadrat-r9/$Phase/$c"
    pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $tier -Lighting $light -Gate3 Data/Regions/bialystok-industrial-c/gate3_cameras.json -Cameras $cams -OutputDir $out *> "artifacts/kwadrat-r9/logs/vqa_${Phase}_$c.log"
    "VQA $c EXIT $LASTEXITCODE"
    Get-ChildItem $out -Filter *.png -ErrorAction SilentlyContinue | ForEach-Object { magick $_.FullName -resize 960x ($_.FullName -replace '\.png$', '.jpg') 2>$null }
}
git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset game/ProjectSettings/ProjectSettings.asset 2>$null
"QA RUNS DONE"

param([string]$Round, [string]$Tier = 'High', [string]$Light = 'overcast')
# review cameras cams_r13.json on the current import -> <round>/extra (+ 960 px JPGs)
$wt = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $wt
$lock = 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN'
$lock2 = $lock -replace 'PHONE_RUN','GPT_UNITY_HOLD'
while ((Test-Path $lock) -or (Test-Path $lock2)) { Start-Sleep 60 }
$dir = "artifacts/buildings-r15/$Round/extra"
$ids = ((Get-Content artifacts/buildings-r15/cams_r13.json -Raw | ConvertFrom-Json).cameras | ForEach-Object id) -join ','
pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $Tier -Lighting $Light -Gate3 artifacts/buildings-r15/cams_r13.json -Cameras $ids -OutputDir $dir *> "artifacts/buildings-r15/$Round/qa-extra.log"
New-Item -ItemType Directory -Force "$dir/960" | Out-Null
Get-ChildItem "$dir/*.png" | ForEach-Object { magick $_.FullName -resize 960x "$dir/960/$($_.BaseName).jpg" }
git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset game/ProjectSettings/ProjectSettings.asset 2>$null
"extra done" | Tee-Object -Append "artifacts/buildings-r15/$Round/round.log"

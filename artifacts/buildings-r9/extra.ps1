param([string]$Round, [string]$Scene = 'WorldC', [string]$Tier = 'High', [string]$Light = 'overcast', [string]$Sub = 'extra', [string]$Only = '', [string]$Runoff = 'on')
# review cameras cams_r16.json on the current import -> <round>/extra (+ 960 px JPGs)
$wt = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $wt
$lock = 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN'
$lock2 = $lock -replace 'PHONE_RUN','GPT_UNITY_HOLD'
while (Test-Path $lock2) { Start-Sleep 60 }
pwsh C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1 -Acquire -Owner claude-buildings-r9 | Out-Host      # machine-wide Unity limit, waits for PHONE_RUN too
$dir = "artifacts/buildings-r9/$Round/$Sub"
$ids = if ($Only) { $Only } else { ((Get-Content artifacts/buildings-r9/cams_r16.json -Raw | ConvertFrom-Json).cameras | ForEach-Object id) -join ',' }
pwsh scripts/visual-qa.ps1 -Scene $Scene -Tier $Tier -Lighting $Light -Gate3 artifacts/buildings-r9/cams_r16.json -Cameras $ids -Runoff $Runoff -OutputDir $dir *> "artifacts/buildings-r9/$Round/qa-$Sub.log"
pwsh C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1 -Release -Owner claude-buildings-r9 | Out-Host
New-Item -ItemType Directory -Force "$dir/960" | Out-Null
Get-ChildItem "$dir/*.png" | ForEach-Object { magick $_.FullName -resize 960x "$dir/960/$($_.BaseName).jpg" }
git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset game/ProjectSettings/ProjectSettings.asset 2>$null
"extra done" | Tee-Object -Append "artifacts/buildings-r9/$Round/round.log"

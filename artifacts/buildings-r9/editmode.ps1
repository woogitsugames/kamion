param([string]$Round = 'r3')
# EditMode tests after the round's renders (one Unity per project; waits for the phone / GPT locks)
$wt = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $wt
while (-not (Select-String -Path "artifacts/buildings-r9/$Round/round.log" -Pattern "ROUND DONE" -Quiet)) { Start-Sleep 20 }
$lock = 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN'
$lock2 = $lock -replace 'PHONE_RUN','GPT_UNITY_HOLD'
while (Test-Path $lock2) { Start-Sleep 60 }
pwsh C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1 -Acquire -Owner claude-buildings-r9 | Out-Host
pwsh scripts/test.ps1 -Platform EditMode *> "artifacts/buildings-r9/$Round/editmode.log"
$code = $LASTEXITCODE
pwsh C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1 -Release -Owner claude-buildings-r9 | Out-Host
"editmode exit $code" | Tee-Object -Append "artifacts/buildings-r9/$Round/round.log"
git checkout -- game/Assets/_Project/Rendering/Settings/Lighting game/ProjectSettings 2>$null

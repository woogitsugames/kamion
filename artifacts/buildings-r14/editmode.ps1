param([string]$Round = 'r3')
# EditMode tests after the round's renders (one Unity per project; waits for the phone / GPT locks)
$wt = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $wt
while (-not (Select-String -Path "artifacts/buildings-r14/$Round/round.log" -Pattern 'extra done' -Quiet)) { Start-Sleep 20 }
$lock = 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN'
$lock2 = $lock -replace 'PHONE_RUN','GPT_UNITY_HOLD'
while ((Test-Path $lock) -or (Test-Path $lock2)) { Start-Sleep 60 }
pwsh scripts/test.ps1 -Platform EditMode *> "artifacts/buildings-r14/$Round/editmode.log"
"editmode exit $LASTEXITCODE" | Tee-Object -Append "artifacts/buildings-r14/$Round/round.log"
git checkout -- game/Assets/_Project/Rendering/Settings/Lighting game/ProjectSettings 2>$null

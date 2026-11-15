Set-Location (Resolve-Path "$PSScriptRoot/../../..")
while (-not (Select-String -Path artifacts/water2-0213/logs/chain.status -Pattern "CHAIN DONE r4" -Quiet)) { Start-Sleep 20 }
while (Test-Path 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN') { Start-Sleep 60 }
pwsh scripts/unity-slot.ps1 -Acquire -Pool unity -Owner water2-0213 | Out-Null
pwsh scripts/test.ps1 -Platform EditMode *> artifacts/water2-0213/logs/editmode.log
"EDITMODE exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content artifacts/water2-0213/logs/chain.status
pwsh scripts/unity-slot.ps1 -Release -Pool unity -Owner water2-0213 | Out-Null
git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null

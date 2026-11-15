# EditMode tests under the unity slot (ADR 0210)
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$L='artifacts/water-0210/logs'; $o='water-0210'
while (Test-Path 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN') { Start-Sleep 60 }
pwsh scripts/unity-slot.ps1 -Acquire -Pool unity -Owner $o | Out-Null
"editmode start $(Get-Date -Format s)" | Add-Content "$L/chain.status"
pwsh scripts/test.ps1 -Platform EditMode *> "$L/editmode.log"
"editmode exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content "$L/chain.status"
pwsh scripts/unity-slot.ps1 -Release -Pool unity -Owner $o | Out-Null
git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null

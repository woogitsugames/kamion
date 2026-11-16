$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\c-regen-s22'; Set-Location $wt
$o = 'artifacts/c-regen-s22/unity'; New-Item -ItemType Directory -Force $o | Out-Null; $st = "$o/editmode-pre.status"
"start $(Get-Date -Format s)" | Set-Content $st
while (Test-Path 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN') { Start-Sleep 60 }
pwsh scripts/unity-slot.ps1 -Acquire -Pool unity -Owner c-regen-s22 | Out-Null
try { pwsh scripts/test.ps1 -Platform EditMode *> "$o/editmode-pre.log"; "editmode exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st }
finally { pwsh scripts/unity-slot.ps1 -Release -Pool unity -Owner c-regen-s22 | Out-Null }
git checkout -q -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null
"DONE" | Add-Content $st

$env:Path=[Environment]::GetEnvironmentVariable('Path','Machine')+';'+[Environment]::GetEnvironmentVariable('Path','User')
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\dk19-tiles-s24'; Set-Location $wt
$st = "$wt\artifacts\dk19-tiles-s24\jobs\editmode.status"; "start $(Get-Date -Format s)" | Set-Content $st
while (Test-Path 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN') { Start-Sleep 60 }
pwsh scripts/unity-slot.ps1 -Acquire -MaxSlots 2 -Owner dk19-s24-em | Out-Null
pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64 *> "$wt\artifacts\logs\dk19-s24-editmode.log"
"editmode exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
pwsh scripts/unity-slot.ps1 -Release -Owner dk19-s24-em | Out-Null
git checkout -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat 2>$null
"DONE exit=0" | Add-Content $st

# ADR 0206 round 2: rebuild with overrides -> import -> visual-qa Low+High -> EditMode
$ErrorActionPreference = 'Continue'
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\bialystok-dk65-t2-0206'
$n = 'bialystok-dk65-t2-0206'; $st = "artifacts/$n/all2.status"
"all2 start $(Get-Date -Format s)" | Add-Content $st
pwsh "artifacts/$n/chain.ps1" *> "artifacts/$n/chain2.out"
Get-Content "artifacts/$n/chain.status" -Tail 1 | Add-Content $st
if ((Get-Content "artifacts/$n/chain.status" -Tail 1) -like 'CHAIN DONE*') {
    pwsh "artifacts/$n/vqa.ps1" -Tag r2 -Tiers Low,High *> "artifacts/$n/vqa-r2.out"
    "vqa r2 done $(Get-Date -Format s)" | Add-Content $st
    while (Test-Path C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN) { Start-Sleep 60 }
    pwsh scripts/unity-slot.ps1 -Acquire -Owner $n | Out-Null
    pwsh scripts/test.ps1 -Platform EditMode *> "artifacts/$n/editmode.log"
    "editmode exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
    pwsh scripts/unity-slot.ps1 -Release -Owner $n | Out-Null
    git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
}
"ALL2 DONE $(Get-Date -Format s)" | Add-Content $st

# ADR 0206: visual-qa of World_bialystok-kleeberga; usage: vqa.ps1 -Tag r1 -Tiers Low,High
param([string]$Tag = 'r1', [string[]]$Tiers = @('Low'), [string]$Lighting = 'overcast')
$ErrorActionPreference = 'Continue'
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\bialystok-dk65-t2-0206'
$n = 'bialystok-dk65-t2-0206'; $st = "artifacts/$n/vqa-$Tag.status"
while (Test-Path C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN) { Start-Sleep 60 }
pwsh scripts/unity-slot.ps1 -Acquire -Owner $n | Out-Null
foreach ($t in $Tiers) {
    "vqa $t start $(Get-Date -Format s)" | Add-Content $st
    pwsh scripts/visual-qa.ps1 -Scene World_bialystok-kleeberga -Tier $t -Lighting $Lighting -Width 1920 -Height 1080 -OutputDir "artifacts/$n/vqa-$Tag/$t-$Lighting" *>> "artifacts/$n/vqa-$Tag.log"
    "vqa $t exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
}
pwsh scripts/unity-slot.ps1 -Release -Owner $n | Out-Null
git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
"VQA DONE $(Get-Date -Format s)" | Add-Content $st

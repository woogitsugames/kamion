param([string]$Stage = 'before', [string[]]$Tiers = @('Low','High'), [string]$Light = 'clear')
$ErrorActionPreference = 'Stop'
$root = 'C:\Users\matma\Documents\Claude\kamion'
$wt = Join-Path $root '.claude\worktrees\review-0153'
Set-Location $wt
$slot = Join-Path $root 'scripts/unity-slot.ps1'
foreach ($tier in $Tiers) {
    & pwsh $slot -Acquire -Owner review-0153
    try {
        if (Test-Path "$root/artifacts/locks/PHONE_RUN") { throw 'PHONE_RUN present' }
        & pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $tier -Lighting $Light -Gate3 Data/Regions/bialystok-industrial-c/gate3_cameras.json -OutputDir "artifacts/review-0153/$Stage/$tier-$Light" *> "artifacts/review-0153/$Stage-$tier-$Light.log"
        "exit $LASTEXITCODE $Stage $tier" | Add-Content artifacts/review-0153/render-exit.txt
    } finally {
        git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
        & pwsh $slot -Release -Owner review-0153
    }
}
"DONE $Stage" | Add-Content artifacts/review-0153/render-exit.txt

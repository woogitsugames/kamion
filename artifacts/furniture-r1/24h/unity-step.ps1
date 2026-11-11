param(
    [ValidateSet('import','render','editmode')] [string]$Step,
    [string]$Phase='before',
    [ValidateSet('Low','High')] [string]$Tier='Low',
    [ValidateSet('clear','overcast','dusk')] [string]$Lighting='overcast'
)
$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../../..").Path
Set-Location $root
$ev='artifacts/furniture-r1/24h'
# Never clean another owner's slot, including an old slot. The protocol owns release.
& pwsh scripts/unity-slot.ps1 -Acquire -Owner gpt-furniture -StaleHours 876000
if ($LASTEXITCODE -ne 0) { throw 'Could not acquire Unity slot' }
$ok=$false
try {
    switch ($Step) {
        'import' {
            & pwsh scripts/import-region.ps1 -Region bialystok-industrial-c *> "$ev/import-$Phase.log"
        }
        'render' {
            $scene=if ($Tier -eq 'High') { 'WorldC_High' } else { 'WorldC' }
            & pwsh scripts/visual-qa.ps1 -Scene $scene -Tier $Tier -Lighting $Lighting -Gate3 "$ev/cameras.json" -OutputDir "$ev/$Phase/$Tier-$Lighting" *> "$ev/render-$Phase-$Tier-$Lighting.log"
        }
        'editmode' {
            & pwsh scripts/test.ps1 -Platform EditMode *> "$ev/editmode.log"
        }
    }
    if ($LASTEXITCODE -ne 0) { throw "Unity $Step failed: $LASTEXITCODE" }
    $ok=$true
} finally {
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh scripts/unity-slot.ps1 -Release -Owner gpt-furniture
    Add-Content "$ev/STATUS.md" "`n$(Get-Date -Format o): Unity $Step $Phase $Tier $Lighting; sukces=$ok. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG."
    git add -f "$ev/STATUS.md" "$ev/unity-step.ps1"
    git commit -m "wip(furniture): checkpoint Unity $Step $Phase $Tier $Lighting"
}

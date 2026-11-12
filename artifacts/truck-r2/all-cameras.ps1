param([ValidateSet('before-all', 'after-all')] [string]$Stage = 'before-all')
$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$slotScript = 'C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
foreach ($tier in @('Low', 'High')) {
    $scene = if ($tier -eq 'High') { 'WorldC_High' } else { 'WorldC' }
    pwsh $slotScript -Acquire -Owner gpt-truck -StaleHours 100000 -PollSeconds 5
    if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu Unity.' }
    try {
        pwsh scripts/visual-qa.ps1 -Scene $scene -Tier $tier -Lighting overcast -OutputDir "artifacts/truck-r2/$Stage/$tier-overcast"
        if ($LASTEXITCODE -ne 0) { throw "Nieudany pełny zestaw $Stage $tier." }
    }
    finally {
        pwsh $slotScript -Release -Owner gpt-truck
        git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    }
    Add-Content -Encoding utf8 artifacts/truck-r2/STATUS.md "Zapisano wszystkie kamery: $Stage $tier overcast. Następny krok: zestawić liczniki rendererów i instancji osobno dla każdej kamery."
    git add -f artifacts/truck-r2/STATUS.md
    git commit --only artifacts/truck-r2/STATUS.md -m "wip(truck): wszystkie kamery $Stage $tier"
}

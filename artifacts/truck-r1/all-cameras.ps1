param([ValidateSet('before-all', 'after-all')] [string]$Stage = 'before-all')
$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
foreach ($tier in @('Low', 'High')) {
    $scene = if ($tier -eq 'High') { 'WorldC_High' } else { 'WorldC' }
    pwsh scripts/unity-slot.ps1 -Acquire -Owner gpt-truck -StaleHours 100000 -PollSeconds 5
    if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu Unity.' }
    try {
        pwsh scripts/visual-qa.ps1 -Scene $scene -Tier $tier -Lighting overcast -OutputDir "artifacts/truck-r1/$Stage/$tier-overcast"
        if ($LASTEXITCODE -ne 0) { throw "Nieudany pełny zestaw $Stage $tier." }
    }
    finally {
        pwsh scripts/unity-slot.ps1 -Release -Owner gpt-truck
        git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    }
    Add-Content -Encoding utf8 artifacts/truck-r1/STATUS.md "Zapisano wszystkie kamery: $Stage $tier overcast. Następny krok: zestawić liczniki rendererów i instancji osobno dla każdej kamery."
    git add -f artifacts/truck-r1/STATUS.md
    git commit -m "wip(truck): wszystkie kamery $Stage $tier"
}

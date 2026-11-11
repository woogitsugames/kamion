$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
foreach ($tier in @('Low', 'High')) {
    foreach ($lighting in @('overcast', 'clear')) {
        pwsh scripts/unity-slot.ps1 -Acquire -Owner gpt-truck -StaleHours 100000
        if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu Unity.' }
        try {
            $scene = if ($tier -eq 'High') { 'WorldC_High' } else { 'WorldC' }
            pwsh scripts/visual-qa.ps1 -Scene $scene -Tier $tier -Lighting $lighting -Cameras 'truck-34,truck-34r,truck-front,truck-side,truck-rear34,cab-driver,chase' -EnvDump -OutputDir "artifacts/truck-r1/before/$tier-$lighting"
            if ($LASTEXITCODE -ne 0) { throw "Baseline nieudany: $tier $lighting" }
        }
        finally {
            pwsh scripts/unity-slot.ps1 -Release -Owner gpt-truck
            git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
        }
        Add-Content -Encoding utf8 artifacts/truck-r1/STATUS.md "Baseline $tier $lighting zapisany. Następny krok: obejrzeć PNG i zmierzyć lakier, szybę oraz DRL."
        git add -f artifacts/truck-r1/STATUS.md
        git commit -m "wip(truck): baseline $tier $lighting"
    }
}

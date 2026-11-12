param(
    [ValidatePattern('^[a-z0-9-]+$')] [string]$Stage = 'fog-only',
    [string[]]$Tiers = @('Low','High'),
    [string[]]$Lighting = @('overcast'),
    [string]$Cameras = 'truck-34,truck-34r,truck-front,truck-side,truck-rear34,cab-driver,chase'
)
$ErrorActionPreference = 'Stop'
$Tiers = @($Tiers | ForEach-Object { $_.Split(',') } | ForEach-Object { $_.Trim() })
$Lighting = @($Lighting | ForEach-Object { $_.Split(',') } | ForEach-Object { $_.Trim() })
if (!$Tiers.Count -or @($Tiers | Where-Object { $_ -notin @('Low','Medium','High') }).Count) { throw 'Nieprawidłowy profil.' }
if (!$Lighting.Count -or @($Lighting | Where-Object { $_ -notin @('overcast','clear','lowsun','dusk') }).Count) { throw 'Nieprawidłowe światło.' }
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$slotScript = 'C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
$sources = @('game/Assets/_Project/Rendering/Shaders/TruckExterior.shader','game/Assets/_Project/Rendering/Shaders/TruckGlass.shader','game/Assets/_Project/Vehicle/Runtime/TruckLights.cs')
foreach ($tier in $Tiers) {
    foreach ($light in $Lighting) {
        $output = "artifacts/truck-r2/$Stage/$tier-$light"
        $fingerprint = ((Get-FileHash -LiteralPath $sources -Algorithm SHA256).Hash -join "`n")
        if (Test-Path "$output/complete.ok") {
            if ((Get-Content "$output/complete.ok" -Raw).Trim() -ne $fingerprint.Trim()) { throw 'Kod zmieniony: wybierz nową nazwę Stage.' }
            foreach ($camera in $Cameras.Split(',')) {
                if (!(Test-Path "$output/$camera.png")) { throw 'Brakuje kamery w istniejącym etapie; wybierz nową nazwę Stage.' }
            }
            continue
        }
        pwsh $slotScript -Acquire -Owner gpt-truck -StaleHours 100000 -PollSeconds 5
        if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu Unity.' }
        try {
            $scene = if ($tier -eq 'High') { 'WorldC_High' } else { 'WorldC' }
            pwsh scripts/visual-qa.ps1 -Scene $scene -Tier $tier -Lighting $light -Cameras $Cameras -OutputDir $output
            if ($LASTEXITCODE -ne 0) { throw "Nieudany render $Stage $tier $light." }
            $after = ((Get-FileHash -LiteralPath $sources -Algorithm SHA256).Hash -join "`n")
            if ($after -ne $fingerprint) { throw 'Kod zmienił się podczas renderu.' }
        }
        finally {
            pwsh $slotScript -Release -Owner gpt-truck
            git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
        }
        $fingerprint | Set-Content -Encoding utf8 "$output/complete.ok"
        Add-Content -Encoding utf8 artifacts/truck-r2/STATUS.md "Zapisano $Stage $tier $light, kod wejściowy zgodny z fingerprintem. Następny krok: pomiary i oględziny par przed/po."
        git add -f artifacts/truck-r2/STATUS.md
        git commit --only artifacts/truck-r2/STATUS.md -m "wip(truck): render $Stage $tier $light"
        if ($LASTEXITCODE -ne 0) { throw 'Nie zapisano WIP po renderze.' }
    }
}

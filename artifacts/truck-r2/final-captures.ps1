$ErrorActionPreference = 'Stop'
[System.Diagnostics.Process]::GetCurrentProcess().PriorityClass = 'BelowNormal'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
. scripts/env.ps1
$slotScript = 'C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
pwsh $slotScript -Acquire -Owner gpt-truck -StaleHours 100000 -PollSeconds 5
if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu Unity.' }
try {
    $log = "artifacts/truck-r2/final-truck-$(Get-Timestamp).log"
    $code = Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.World.Import.WorldTruckInstaller.InstallBatch')
    if ($code -ne 0 -or !(Select-String -LiteralPath $log -SimpleMatch 'TRUCK_RESULT: OK' -Quiet)) { throw 'Nieudane końcowe odświeżenie prefabów.' }
}
finally {
    pwsh $slotScript -Release -Owner gpt-truck
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
}
Add-Content -Encoding utf8 artifacts/truck-r2/STATUS.md 'Końcowy rebuild obu prefabów i instalacja scen zakończone poprawnie. Następny krok: końcowe kadry i wszystkie kamery.'
git add -f artifacts/truck-r2/STATUS.md
git commit --only artifacts/truck-r2/STATUS.md -m 'wip(truck): koncowe prefaby rundy 2'
foreach ($job in @(
    @{script='render-phase.ps1';args=@('-Stage','final','-Lighting','overcast,clear')},
    @{script='detail-controls.ps1';args=@('-Prefix','detail-final','-Cases','fleet')},
    @{script='all-cameras.ps1';args=@('-Stage','after-all')}
)) {
    $arguments = $job.args
    pwsh -NoProfile -ExecutionPolicy Bypass -File "artifacts/truck-r2/$($job.script)" @arguments
    if ($LASTEXITCODE -ne 0) { throw "Nieudany końcowy krok $($job.script)." }
}
uv run --project tools/worldgen python artifacts/truck-r2/compare_counters.py
if ($LASTEXITCODE -ne 0) { throw 'Nieudane zestawienie liczników.' }

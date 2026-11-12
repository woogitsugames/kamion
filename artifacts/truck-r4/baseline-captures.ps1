$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
. scripts/env.ps1
$slotScript = 'C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
pwsh $slotScript -Acquire -Owner gpt-truck -StaleHours 100000 -PollSeconds 1
if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu Unity.' }
try {
    # WorldSceneBuilder loads existing truck prefabs; refresh them to include the new main's cab work.
    $log = "artifacts/truck-r4/baseline-truck-$(Get-Timestamp).log"
    $code = Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.World.Import.WorldTruckInstaller.InstallBatch')
    if ($code -ne 0 -or !(Select-String -LiteralPath $log -SimpleMatch 'TRUCK_RESULT: OK' -Quiet)) { throw 'Nieudane odświeżenie prefabów z bieżącego main.' }
}
finally {
    pwsh $slotScript -Release -Owner gpt-truck
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
}
Add-Content -Encoding utf8 artifacts/truck-r4/STATUS.md 'Odświeżono oba prefaby i instalację po zmianach main; sam import regionu używałby starych prefabów. Następny krok: baseline r4, wszystkie kamery i kontrole brudu.'
git add -f artifacts/truck-r4/STATUS.md
git commit --only artifacts/truck-r4/STATUS.md -m 'wip(truck): aktualne prefaby main przed baseline r4'
uv run --project tools/worldgen python artifacts/truck-r4/fixture_state.py before
if ($LASTEXITCODE -ne 0) { throw 'Nie zapisano stanu bazowych siatek i prefabów.' }
foreach ($job in @(
    @{script='render-phase.ps1';args=@('-Stage','before','-Lighting','overcast,clear')},
    @{script='all-cameras.ps1';args=@('-Stage','before-all')},
    @{script='detail-controls.ps1';args=@('-Prefix','detail-before','-Cases','fleet')}
)) {
    $arguments = $job.args
    pwsh -NoProfile -ExecutionPolicy Bypass -File "artifacts/truck-r4/$($job.script)" @arguments
    if ($LASTEXITCODE -ne 0) { throw "Nieudany krok $($job.script)." }
}


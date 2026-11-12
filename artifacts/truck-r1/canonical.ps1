$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$slotScript = 'C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
. scripts/env.ps1
function Snapshot([string]$Label, [string]$Compare = '') {
    pwsh $slotScript -Acquire -Pool heavy -Owner gpt-truck-r1 -StaleHours 100000 -PollSeconds 5
    if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu heavy.' }
    try {
        $arguments = @('run','--project','tools/worldgen','python','artifacts/truck-r1/fixture_state.py',$Label)
        if ($Compare) { $arguments += $Compare }
        uv @arguments
        if ($LASTEXITCODE -ne 0) { throw 'Nie zapisano migawki truck.' }
    }
    finally { pwsh $slotScript -Release -Pool heavy -Owner gpt-truck-r1 }
}
Snapshot 'before-canonical'
foreach ($step in @(
    @{id='truck';method='Game.Editor.Setup.TruckAssetBuilder.BuildBatch';result='TRUCK_RESULT: OK'},
    @{id='trailer';method='Game.Editor.Setup.TrailerAssetBuilder.BuildBatch';result='TRAILER_RESULT: OK'},
    @{id='install';method='Game.World.Import.WorldTruckInstaller.InstallBatch';result='TRUCK_RESULT: OK'}
)) {
    pwsh $slotScript -Acquire -Owner gpt-truck -StaleHours 100000 -PollSeconds 5
    if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu Unity.' }
    try {
        $log = "artifacts/truck-r1/canonical-$($step.id)-$(Get-Timestamp).log"
        $code = Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod',$step.method)
        if ($code -ne 0 -or !(Select-String -LiteralPath $log -Pattern $step.result -SimpleMatch -Quiet)) { throw "Nieudany kanoniczny krok $($step.id), exit $code." }
    }
    finally {
        pwsh $slotScript -Release -Owner gpt-truck
        git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    }
    Add-Content -Encoding utf8 artifacts/truck-r1/STATUS.md "Kanoniczny $($step.id) zakończony poprawnie. Następny krok: dokończyć instalację i porównać migawkę wygenerowanych zasobów."
    git add -f artifacts/truck-r1/STATUS.md
    git commit --only artifacts/truck-r1/STATUS.md -m "wip(truck): kanoniczny $($step.id)"
}
Snapshot 'after-canonical' 'before-canonical'

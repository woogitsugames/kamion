$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$slotScript = 'C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
uv run --project tools/worldgen python art-source/truck/exterior/qa/prepare_round_0115.py
if ($LASTEXITCODE -ne 0) { throw 'Nie przygotowano diagnostyki.' }
. scripts/env.ps1
foreach ($case in @('white-on', 'white-off', 'dark-on', 'dark-off', 'no-pane')) {
    $lighting = if ($case -eq 'no-pane') { 'overcast' } else { 'overcast,clear' }
    $argsForUnity = @('-executeMethod', 'Game.Editor.VisualQA.TruckRound0115.RunBatch', '-truckRound', "control-$case", '-truckOutputRoot', 'artifacts/truck-r1', '-truckCameras', 'truck-34,truck-side,truck-front', '-truckTiers', 'Low,High', '-truckLights', $lighting)
    if ($case.StartsWith('dark')) { $argsForUnity += @('-truckPigment', '0.08') }
    if ($case.EndsWith('off')) { $argsForUnity += @('-truckCoatRadianceOff', '1') }
    if ($case -eq 'no-pane') { $argsForUnity += @('-truckNoPane', 'windscreen') }
    pwsh $slotScript -Acquire -Owner gpt-truck -StaleHours 100000 -PollSeconds 5
    if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu Unity.' }
    try {
        $log = "artifacts/truck-r1/control-$case.log"
        $code = Invoke-UnityBatch -LogFile $log -Arguments $argsForUnity
        if ($code -ne 0 -or !(Select-String -LiteralPath $log -SimpleMatch 'TRUCK_ROUND_RESULT: OK' -Quiet)) {
            throw "Nieudana kontrola $case; exit $code. Zachowano log."
        }
    }
    finally {
        pwsh $slotScript -Release -Owner gpt-truck
        git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    }
    Add-Content -Encoding utf8 artifacts/truck-r1/STATUS.md "Zapisano kontrolę pigmentu $case. Następny krok: porównać amplitudę odbicia ON/OFF i wybrać poprawkę lakieru na podstawie wyniku."
    git add -f artifacts/truck-r1/STATUS.md
    git commit -m "wip(truck): kontrola pigmentu $case"
}

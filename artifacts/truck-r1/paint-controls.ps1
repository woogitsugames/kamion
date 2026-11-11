$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
uv run --project tools/worldgen python art-source/truck/exterior/qa/prepare_round_0115.py
if ($LASTEXITCODE -ne 0) { throw 'Nie przygotowano diagnostyki.' }
. scripts/env.ps1
foreach ($case in @('white-on', 'white-off', 'dark-on', 'dark-off')) {
    $argsForUnity = @('-executeMethod', 'Game.Editor.VisualQA.TruckRound0115.RunBatch', '-truckRound', "control-$case", '-truckOutputRoot', 'artifacts/truck-r1', '-truckCameras', 'truck-34,truck-side', '-truckTiers', 'Low,High', '-truckLights', 'overcast,clear')
    if ($case.StartsWith('dark')) { $argsForUnity += @('-truckPigment', '0.08') }
    if ($case.EndsWith('off')) { $argsForUnity += @('-truckCoatRadianceOff', '1') }
    pwsh scripts/unity-slot.ps1 -Acquire -Owner gpt-truck -StaleHours 100000 -PollSeconds 5
    if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu Unity.' }
    try {
        $log = "artifacts/truck-r1/control-$case.log"
        $code = Invoke-UnityBatch -LogFile $log -Arguments $argsForUnity
        if ($code -ne 0 -or !(Select-String -LiteralPath $log -SimpleMatch 'TRUCK_ROUND_RESULT: OK' -Quiet)) {
            throw "Nieudana kontrola $case; exit $code. Zachowano log."
        }
    }
    finally {
        pwsh scripts/unity-slot.ps1 -Release -Owner gpt-truck
        git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    }
    Add-Content -Encoding utf8 artifacts/truck-r1/STATUS.md "Zapisano kontrolę pigmentu $case. Następny krok: porównać amplitudę odbicia ON/OFF i wybrać poprawkę lakieru na podstawie wyniku."
    git add -f artifacts/truck-r1/STATUS.md
    git commit -m "wip(truck): kontrola pigmentu $case"
}

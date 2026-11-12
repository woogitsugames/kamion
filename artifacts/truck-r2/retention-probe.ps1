$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
uv run --project tools/worldgen python art-source/truck/exterior/qa/prepare_retention_0115.py
if ($LASTEXITCODE -ne 0) { throw 'Nie przygotowano podglądu.' }
. scripts/env.ps1
$slotScript = 'C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
foreach ($mode in @('retention','surface')) {
    pwsh $slotScript -Acquire -Owner gpt-truck -StaleHours 100000 -PollSeconds 1
    if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu Unity.' }
    try {
        $log = "artifacts/truck-r2/probe-$mode.log"
        $code = Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.Editor.VisualQA.TruckRetention0115.RunBatch','-truckRound',"probe-$mode",'-truckOutputRoot','artifacts/truck-r2','-truckCameras','truck-step-detail,truck-mudguard-detail','-truckTiers','Low,High','-truckLights','overcast','-truckMeshProbe',$mode)
        if ($code -ne 0 -or !(Select-String -LiteralPath $log -SimpleMatch "TRUCK_ROUND_RESULT: OK probe-$mode count=4" -Quiet)) { throw "Nieudany podgląd $mode, exit $code." }
    }
    finally {
        pwsh $slotScript -Release -Owner gpt-truck
        git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    }
    Add-Content -Encoding utf8 artifacts/truck-r2/STATUS.md "Zapisano cztery kadry diagnostyczne $mode. Materiały przywrócono; kanały PNG nie są surowym HDR. Następny krok: wskazać dominującą składową na rzeczywistym stopniu."
    git add -f artifacts/truck-r2/STATUS.md
    git commit --only artifacts/truck-r2/STATUS.md -m "wip(truck): rzeczywiste kanaly materialu $mode"
}

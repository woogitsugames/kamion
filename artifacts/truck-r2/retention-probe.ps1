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
        $result = Select-String -LiteralPath $log -SimpleMatch "TRUCK_ROUND_RESULT: OK probe-$mode count=4" | Select-Object -Last 1
        $sha = (Get-FileHash game/Assets/_Project/Rendering/Shaders/TruckExterior.shader).Hash.ToLowerInvariant()
        $cleanup = Select-String -LiteralPath $log -SimpleMatch "TRUCK_ABLATION_CLEANUP: productionSHA=$sha" -Quiet
        $fresh = @(Get-ChildItem "artifacts/truck-r2/probe-$mode" -Recurse -Filter '*.png' | Where-Object LastWriteTime -ge (Get-Item $log).CreationTime).Count
        if ($code -ne 0 -and $result -and $cleanup -and $fresh -eq 4) {
            $mono = Select-String -LiteralPath $log -SimpleMatch 'Cleanup mono' | Where-Object LineNumber -gt $result.LineNumber | Select-Object -First 1
            $abort = Select-String -LiteralPath $log -SimpleMatch 'abort_threads: Failed aborting' | Where-Object LineNumber -gt $result.LineNumber | Select-Object -First 1
            $crash = Select-String -LiteralPath $log -Pattern 'Crash!!!|Obtained \d+ stack frames|Fatal Error|error CS\d+|Shader error' -Quiet
            if ($mono -and $abort -and !$crash) { $code = 0 } # narrowly documented ADR 0083 post-success shutdown
        }
        if ($code -ne 0 -or !$result -or !$cleanup -or $fresh -ne 4) { throw "Nieudany podgląd $mode, exit $code." }
    }
    finally {
        pwsh $slotScript -Release -Owner gpt-truck
        git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    }
    Add-Content -Encoding utf8 artifacts/truck-r2/STATUS.md "Zapisano cztery kadry diagnostyczne $mode. Materiały przywrócono; kanały PNG nie są surowym HDR. Następny krok: wskazać dominującą składową na rzeczywistym stopniu."
    git add -f artifacts/truck-r2/STATUS.md
    git commit --only artifacts/truck-r2/STATUS.md -m "wip(truck): rzeczywiste kanaly materialu $mode"
}

$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
. scripts/env.ps1
$slotScript = 'C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
pwsh $slotScript -Acquire -Owner gpt-truck -StaleHours 100000 -PollSeconds 1
if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu Unity.' }
try {
    $code = Invoke-UnityBatch -LogFile 'artifacts/truck-r2/curtain-audit.log' -Arguments @('-executeMethod','Game.Editor.VisualQA.TruckCurtainAudit0115.RunBatch','-truckRound','curtain-audit','-truckOutputRoot','artifacts/truck-r2','-truckCameras','truck-side','-truckTiers','Low,High','-truckLights','overcast')
    if ($code -ne 0 -or !(Select-String -LiteralPath artifacts/truck-r2/curtain-audit.log -SimpleMatch 'TRUCK_ROUND_RESULT: OK curtain-audit count=2' -Quiet)) { throw "Nieudany audyt, exit $code." }
}
finally {
    pwsh $slotScript -Release -Owner gpt-truck
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
}
Add-Content -Encoding utf8 artifacts/truck-r2/STATUS.md 'Audyt plandeki po dwóch rzeczywistych renderach zakończony. JSON w curtain-audit/Low-overcast i High-overcast. Następny krok: odczytać macierze, bounds i parametry przed dalszą zmianą siły.'
git add -f artifacts/truck-r2/STATUS.md
git commit --only artifacts/truck-r2/STATUS.md -m 'wip(truck): odczytowy audyt transformacji plandeki'

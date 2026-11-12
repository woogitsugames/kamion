param([ValidatePattern('^[a-z0-9-]+$')][string]$Stage='detail-wheels-v2')
$ErrorActionPreference='Stop'
[Diagnostics.Process]::GetCurrentProcess().PriorityClass='BelowNormal'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
foreach($domain in @('exterior','trailer')) {
    $record=Get-Content "artifacts/truck-r3/generate-$domain-result.json" -Raw | ConvertFrom-Json
    if($record.result -ne 'Passed' -or !$record.validated){throw "Brak walidacji FBX: $domain"}
}
if(Test-Path "artifacts/truck-r3/$Stage-fleet"){throw 'Etap już istnieje; wybierz nowy Stage, aby nie nadpisać dowodów.'}
. scripts/env.ps1
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
pwsh $slot -Acquire -Owner gpt-truck -StaleHours 100000 -PollSeconds 1
if($LASTEXITCODE -ne 0){throw 'Nie uzyskano slotu Unity.'}
try {
    $log="artifacts/truck-r3/install-$Stage-$(Get-Timestamp).log"
    $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.World.Import.WorldTruckInstaller.InstallBatch')
    if($code -ne 0 -or !(Select-String -LiteralPath $log -SimpleMatch 'TRUCK_RESULT: OK' -Quiet)){throw 'Nieudana instalacja kandydata.'}
} finally {
    pwsh $slot -Release -Owner gpt-truck
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
}
Add-Content -Encoding utf8 artifacts/truck-r3/STATUS.md "Instalacja kandydata $Stage zakończona. Następny krok: test rzeczywistego eksportu, 12 zbliżeń na tej samej bazie oraz porównanie z baseline."
git add -f artifacts/truck-r3/STATUS.md
git commit --only artifacts/truck-r3/STATUS.md -m "wip(truck): instalacja kandydata $Stage"
pwsh -NoProfile -ExecutionPolicy Bypass -File artifacts/truck-r3/validate-editmode.ps1 -Filter TruckWheelLodGeometryTests -Label $Stage
if($LASTEXITCODE -ne 0){throw 'Geometria kół nie przeszła testów.'}
pwsh -NoProfile -ExecutionPolicy Bypass -File artifacts/truck-r3/detail-controls.ps1 -Prefix $Stage -Cases fleet
if($LASTEXITCODE -ne 0){throw 'Nieudane kadry kandydata.'}
uv run --project tools/worldgen python artifacts/truck-r3/wheel-candidate-pairs.py "$Stage-fleet"
if($LASTEXITCODE -ne 0){throw 'Nieudane arkusze kół.'}

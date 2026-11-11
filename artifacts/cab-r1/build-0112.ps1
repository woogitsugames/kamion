param([ValidatePattern('^[A-Za-z0-9-]+$')][string]$Label='result-0112')
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if ((git branch --show-current) -ne 'gpt-cab-r1') { throw 'Tylko runda cab r1.' }
. ./scripts/env.ps1
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
foreach($method in @('Game.Editor.Setup.TruckAssetBuilder.BuildBatch','Game.World.Import.WorldTruckInstaller.InstallBatch')) {
    $log="$PWD/artifacts/cab-r1/$Label-$($method.Split('.')[-2]).log"
    pwsh $slot -Acquire -Owner gpt-cab -PollSeconds 5 -StaleHours 1000000
    if ($LASTEXITCODE -ne 0) { throw 'Brak slotu Unity.' }
    try { $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod',$method) }
    finally { pwsh $slot -Release -Owner gpt-cab; git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings }
    if ($code -ne 0 -or -not (Select-String -Path $log -SimpleMatch 'TRUCK_RESULT: OK' -Quiet)) { Show-UnityLogErrors $log; throw "Nieudana przebudowa $method, exit $code" }
    Add-Content artifacts/cab-r1/STATUS.md "Zakończono $method, exit 0. Następny krok: kolejny etap prefab/sceny lub capture-0112 -Stage result-0112."
    git add -f artifacts/cab-r1/STATUS.md
    git commit -m "wip(cab): rebuild $($method.Split('.')[-2]) for ADR 0112"
}

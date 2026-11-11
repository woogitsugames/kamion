$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../../scripts/env.ps1"
foreach ($step in @(@{id='build';method='Game.Editor.Setup.TruckAssetBuilder.BuildBatch'},@{id='install';method='Game.World.Import.WorldTruckInstaller.InstallBatch'})) {
 if (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') { throw 'PHONE_RUN present; waiting for owner phone window to finish' }
 $log=Join-Path $LogsDir ("tint-canonical-truck-"+$step.id+'.log')
 $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod',$step.method)
 Show-UnityLogErrors $log
 if ($code -ne 0 -or -not (Select-String -Path $log -Pattern 'TRUCK_RESULT: OK' -Quiet)) { throw "Canonical fixture $($step.id) failed exit=$code" }
 Write-Output "CANONICAL_TRUCK_$($step.id): OK"
}

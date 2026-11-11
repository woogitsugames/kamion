$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
. "$PWD/scripts/env.ps1"
foreach($method in @('Game.Editor.Setup.TruckAssetBuilder.BuildBatch','Game.World.Import.WorldTruckInstaller.InstallBatch')) {
 while((Test-Path 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN') -or (Test-Path 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\GPT_UNITY_HOLD')) { Start-Sleep 60 }
 $log=Join-Path $PWD "artifacts/cab-r1/final-$($method.Split('.')[-2]).log"
 $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod',$method)
 git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
 if($code -ne 0 -or !(Select-String $log -SimpleMatch 'TRUCK_RESULT: OK' -Quiet)) { throw "Build failed $code" }
}
& pwsh -NoProfile -File artifacts/cab-r1/validate.ps1
exit $LASTEXITCODE

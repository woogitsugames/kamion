param([ValidateSet('before','after')] [string]$Stage='before')
$ErrorActionPreference='Stop'
$repo=(Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $repo
. scripts/env.ps1
$phoneLock='C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN'
$coordinatorHold=Join-Path (Split-Path $phoneLock) 'GPT_UNITY_HOLD'
function Wait-UnityAllowed {
  while((Test-Path $phoneLock) -or (Test-Path $coordinatorHold)) {
    Write-Output "Unity held: waiting ($Stage)"; Start-Sleep -Seconds 60
  }
}
function Restore-UnityEffects { git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings }
foreach($method in @('Game.Editor.Setup.TruckAssetBuilder.BuildBatch','Game.World.Import.WorldTruckInstaller.InstallBatch')) {
  Wait-UnityAllowed
  $log=Join-Path $repo "artifacts/cab-r1/$Stage-$($method.Split('.')[-2]).log"
  $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod',$method)
  Restore-UnityEffects
  if($code -ne 0 -or !(Select-String -Path $log -SimpleMatch 'TRUCK_RESULT: OK' -Quiet)) { throw "Failed $method ($code): $log" }
}
foreach($tier in @('Low','High')) {
  foreach($light in @('overcast','clear')) {
    Wait-UnityAllowed
    & pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier $tier -Lighting $light -Cameras 'cab-driver,cab-dash,cab-left,cab-right,cab-mirrors-left,cab-mirrors-right,cab-mirror-front,cab-seat,cab-materials' -OutputDir "artifacts/cab-r1/$Stage/$tier-$light"
    Restore-UnityEffects
    if($LASTEXITCODE -ne 0) { throw "Render failed: $Stage $tier $light" }
    Wait-UnityAllowed
    $log=Join-Path $repo "artifacts/cab-r1/$Stage-mirrors-$tier-$light.log"
    $output=Join-Path $repo "artifacts/cab-r1/$Stage/$tier-$light/native-mirrors"
    $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.Editor.VisualQA.CabMirrorAudit.Run','-cabTier',$tier,'-cabLighting',$light,'-cabOutput',$output)
    Restore-UnityEffects
    if($code -ne 0 -or !(Select-String -Path $log -SimpleMatch 'CABMIRRORAUDIT_RESULT: OK' -Quiet)) { throw "Mirror audit failed $tier $light ($code)" }
    Add-Content artifacts/cab-r1/STATUS.md "Rendered $Stage $tier $light plus native mirror evidence. NEXT: continue matrix / inspect artifacts/cab-r1/$Stage"
    git add -f artifacts/cab-r1/STATUS.md
    git commit -m "wip(cab): render $Stage $tier $light"
  }
}

# 0181: rebuild tractor + trailer prefabs from the exports, install into WorldC, render lamp evidence, optional EditMode tests.
param([string]$Tag = 'after', [switch]$SkipBuild, [switch]$Tests, [string[]]$Tiers = @('High', 'Low'),
      [string]$Cams = 'trailer-34,truck-rear34,chase,lamp-trailer,lamp-truck')
$ErrorActionPreference = 'Stop'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\lamplens-0181'
$out = "$wt\artifacts\lamplens-0181\$Tag"
Set-Location $wt; . "$wt/scripts/env.ps1"
New-Item -ItemType Directory -Force $out | Out-Null
pwsh scripts/unity-slot.ps1 -Acquire -Owner lamplens-0181
try {
  if (-not $SkipBuild) {
    foreach ($step in @(
        @{id='truck';method='Game.Editor.Setup.TruckAssetBuilder.BuildBatch';result='TRUCK_RESULT: OK'},
        @{id='trailer';method='Game.Editor.Setup.TrailerAssetBuilder.BuildBatch';result='TRAILER_RESULT: OK'},
        @{id='install';method='Game.World.Import.WorldTruckInstaller.InstallBatch';result='TRUCK_RESULT: OK'})) {
      $log = "$out/build-$($step.id).log"
      $code = Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod',$step.method)
      if ($code -ne 0 -or !(Select-String -LiteralPath $log -Pattern $step.result -SimpleMatch -Quiet)) { throw "build step $($step.id) failed, exit $code" }
      "OK $($step.id)"
    }
  }
  foreach ($t in $Tiers) {
    pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $t -Lighting dusk -Cameras $Cams -OutputDir "$out/$t-dusk"
    pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $t -Lighting dusk -Cameras $Cams -TruckLamps 'brake,hazard' -OutputDir "$out/$t-dusk-brake-hazard"
    pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $t -Lighting overcast -Cameras $Cams -OutputDir "$out/$t-overcast"
    pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $t -Lighting overcast -Cameras $Cams -TruckLamps 'low,brake,hazard' -OutputDir "$out/$t-overcast-lit"
  }
  if ($Tests) {
    pwsh scripts/test.ps1 -Platform EditMode -Filter 'Game.Tests.EditMode.TruckLampEncodingTests;Game.Tests.TruckRegulationLampTests'
    Copy-Item "$wt/artifacts/tests/*.xml" $out -ErrorAction SilentlyContinue
  }
} finally {
  git -C $wt restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
  pwsh scripts/unity-slot.ps1 -Release -Owner lamplens-0181
}
"DONE $Tag $(Get-Date -Format s)" | Out-File "$out/status.txt"
git -C $wt status --short | Select-Object -First 40

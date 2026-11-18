# cab-view-s24 pipeline: slot -> TRAKT build + install in WorldC -> renders. Each step writes logs/<step>.status
param([switch]$SkipInstall, [string]$Steps = 'start,rondo')
$ErrorActionPreference = 'Continue'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\cab-view-s24'
Set-Location $wt
. "$wt/scripts/env.ps1"
$out = "$wt\artifacts\cab-view-s24"; $logs = "$out\logs"
function St($n, $c) { "exit=$c" | Set-Content "$logs\$n.status" }
pwsh scripts/unity-slot.ps1 -Acquire -Owner cab-view-s24
try {
  if (-not $SkipInstall) {
    $c = Invoke-UnityBatch -LogFile "$logs\install.log" -BuildTarget Win64 -Arguments @('-executeMethod', 'Game.World.Import.WorldTruckInstaller.InstallBatch')
    St 'install' $c
    if (-not (Select-String "$logs\install.log" -SimpleMatch 'TRUCK_RESULT: OK' -Quiet)) { return }
  }
  $cams = 'cab-view-0-fov55,cab-view-a-fov62,cab-view-b-fov70,cab-view-c-fov75,cab-view-d-fov70-p10,cab-driver'
  if ($Steps -match 'start') {
    pwsh scripts/visual-qa.ps1 -Scene WorldC_High -Tier High -Pc -BuildTarget Win64 -Width 1920 -Height 1080 -Lighting clear `
      -Cameras $cams -OutputDir "$out\start" -CabViewAudit "$out\start\audit.tsv" *> "$logs\render-start.out"
    St 'render-start' $LASTEXITCODE
  }
  if ($Steps -match 'rondo') {
    # Rondo Biezenstwa ring (gate3_cameras.json: centre E 554.676 N -716.554, circle fit r 23.362 m); theta 100 deg, CCW tangent -> heading 260
    pwsh scripts/visual-qa.ps1 -Scene WorldC_High -Tier High -Pc -BuildTarget Win64 -Width 1920 -Height 1080 -Lighting clear `
      -Cameras $cams -OutputDir "$out\rondo" -TruckPose '550.619,-693.547,260' -CabViewAudit "$out\rondo\audit.tsv" *> "$logs\render-rondo.out"
    St 'render-rondo' $LASTEXITCODE
  }
} finally {
  pwsh scripts/unity-slot.ps1 -Release -Owner cab-view-s24
  'done' | Set-Content "$logs\pipeline.status"
}

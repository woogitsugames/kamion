param([string[]]$Steps = @('import','trim','editmode','vqa_low','vqa_high'), [string]$Tag = 'after')
$ErrorActionPreference = 'Continue'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\barriers-0159'
$A = Join-Path $wt 'artifacts\barriers-0159'
$logs = Join-Path $A 'logs'
Set-Location $wt
. (Join-Path $wt 'scripts/env.ps1')
$R = 'bialystok-industrial-c'
$st = Join-Path $logs 'chain-unity.status'
function Restore { git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>&1 | Out-Null }
$cmds = [ordered]@{
  import   = { pwsh -NoProfile -File scripts/import-region.ps1 -Region $R }
  trim     = {
    $ulog = Join-Path $logs 'imptrim-unity.log'
    $p = Start-Process $UnityExe -ArgumentList @('-batchmode', '-projectPath', (Join-Path $wt 'game'), '-logFile', $ulog, '-buildTarget', 'Android',
        '-executeMethod', 'Game.World.Import.ImpostorTrimBake.RunBatch') -PassThru -NoNewWindow -Wait
    Select-String -Path $ulog -Pattern '\[IMPTRIM\]|error CS' | ForEach-Object { $_.Line }
    $global:LASTEXITCODE = $p.ExitCode
  }
  editmode = { pwsh -NoProfile -File scripts/test.ps1 -Platform EditMode }
  vqa_low  = { pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting clear -OutputDir (Join-Path $A "$Tag/Low-clear") }
  probe    = { pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting clear -Width 1280 -Height 960 -Gate3 (Join-Path $A 'tools\probe4_cameras.json') -Cameras 'r16_drive_3,p159-link-eye,p159-median-nose,p159-median-up,p159-putry-deck,p159-wall,p159-spruce,p159-join-e-plan,p159-join-e-a,p159-join-e-b,p159-join-e-c,p159-join-w-plan,p159-join-w-a,p159-join-w-b,p159-join-w-c,p159-link-end,p159-median-sw-eye,p159-median-sw-nose,p159-median-ne-face' -OutputDir (Join-Path $A "$Tag/probe") }
  vqa_high = { pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier High -Lighting clear -OutputDir (Join-Path $A "$Tag/High-clear") }
}
pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Owner barriers-0159
try {
  foreach ($s in ($Steps -split ",")) {
    if ($s -eq 'sbs') { continue }
    $log = Join-Path $logs "$Tag-$s.log"
    $t0 = Get-Date
    "=== $s start $(Get-Date -Format s)" | Out-File $log -Encoding utf8
    & $cmds[$s] *>&1 | Out-File $log -Append -Encoding utf8
    $code = $LASTEXITCODE
    Restore
    "=== $s exit $code $([int]((Get-Date) - $t0).TotalSeconds) s" | Out-File $log -Append -Encoding utf8
    "$Tag $s exit $code $(Get-Date -Format s)" | Out-File $st -Append -Encoding utf8
    if ($code -ne 0 -and $s -in "import","trim") { break }
  }
} finally {
  pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Owner barriers-0159
  Restore
  "UNITY CHAIN DONE $Tag $(Get-Date -Format s)" | Out-File $st -Append -Encoding utf8
}
# SBS pairs (the script takes its own Unity slot); before = the s16 integration renders in main
if ($Steps -contains 'sbs' -or ($Steps -join ',') -match 'sbs') {
  pwsh -NoProfile -File scripts/sbs-low-pairs.ps1 -OutputRoot (Join-Path $A "sbs-$Tag") -SlotOwner barriers-0159 `
    -Before 'C:\Users\matma\Documents\Claude\kamion\artifacts\world-int-s16\sbs' *>&1 | Out-File (Join-Path $logs "$Tag-sbs.log") -Encoding utf8
  "$Tag sbs exit $LASTEXITCODE $(Get-Date -Format s)" | Out-File $st -Append -Encoding utf8
  Restore
}

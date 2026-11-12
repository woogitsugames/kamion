param([string[]]$Steps = @('import','trim','editmode','vqa_low','vqa_high'), [string]$Tag = 'after')
$ErrorActionPreference = 'Continue'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\world-int-s16'
$A = Join-Path $wt 'artifacts\world-int-s16'
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
  vqa_high = { pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier High -Lighting clear -OutputDir (Join-Path $A "$Tag/High-clear") }
}
pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Owner world-int-s16
try {
  foreach ($s in ($Steps -split ",")) {
    $log = Join-Path $logs "$Tag-$s.log"
    $t0 = Get-Date
    "=== $s start $(Get-Date -Format s)" | Out-File $log -Encoding utf8
    & $cmds[$s] *>&1 | Out-File $log -Append -Encoding utf8
    $code = $LASTEXITCODE
    Restore
    "=== $s exit $code $([int]((Get-Date) - $t0).TotalSeconds) s" | Out-File $log -Append -Encoding utf8
    "$Tag $s exit $code $(Get-Date -Format s)" | Out-File $st -Append -Encoding utf8
    if ($code -ne 0 -and $s -in 'import','trim') { break }
  }
} finally {
  pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Owner world-int-s16
  Restore
  "UNITY CHAIN DONE $Tag $(Get-Date -Format s)" | Out-File $st -Append -Encoding utf8
}

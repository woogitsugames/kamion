<#
.SYNOPSIS
  Render the visual-QA control cameras of a scene to PNG (Unity batchmode, needs a GPU).
.EXAMPLE
  pwsh scripts/visual-qa.ps1 -Scene Boot
  pwsh scripts/visual-qa.ps1 -Scene Boot -Width 1920 -Height 1080 -Tier High
  pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting overcast -OutputDir artifacts/visual-qa/WorldC/Low-overcast
.NOTES
  Output: artifacts/visual-qa/<Scene>/<camera-id>.png. Rendering does not work with -nographics,
  so Unity runs batchmode with the GPU. Look at every PNG yourself (skill visual-qa).
#>
param(
    [string]$Scene = 'Boot',
    [int]$Width = 2340,
    [int]$Height = 1080,
    [ValidateSet('Low', 'Medium', 'High', 'Ultra')] [string]$Tier = 'Medium',
    [string]$OutputDir,
    [ValidateSet('', 'clear', 'overcast', 'lowsun', 'dusk')] [string]$Lighting = '',
    [string]$Cameras = '',
    # A7 before/after: 'off' renders without the cab fill and the cab-view lift (CabInteriorLighting).
    [ValidateSet('on', 'off')] [string]$CabFill = 'on',
    # Ablation overrides (RenderOverrides keys), e.g. 'rq_hlod=0,rq_trees=0'.
    [string]$Rq = '',
    # ADR 0043 option (c) owner A/B: phone-style white-balance adaptation strength 0..1 ('' = preset value, 0).
    [string]$WbAdapt = '',
    # ADR 0043 diagnostic: hide the glazing.
    [switch]$NoGlass,
    # Editor GPU timing: N extra renders per camera (stats.txt, VISUALQA_TIMING lines in the log).
    [int]$TimeFrames = 0,
    # Render scale override (e.g. 0.80 = ADR 0046 adaptive floor); default = the tier's.
    [string]$RenderScale = '',
    # REVIEW r6 W-P0 measurement: power-line conductors on (default), off, or solid (full opacity, black).
    [ValidateSet('on', 'off', 'solid')] [string]$Wires = 'on',
    # Adds the Stage 3 gate cameras (e.g. Data/Regions/<region>/gate3_cameras.json) to the scene's control cameras.
    [string]$Gate3 = '',
    # Parapet run-off A/B: off renders hall walls without the _RUNOFF streak layer.
    [ValidateSet('on', 'off')] [string]$Runoff = 'on'
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/env.ps1"

if (-not $OutputDir) { $OutputDir = Join-Path $ArtifactsDir "visual-qa/$Scene" }
$OutputDir = [IO.Path]::GetFullPath($OutputDir, (Get-Location).Path)
$log = Join-Path $LogsDir "visual-qa-$Scene-$(Get-Timestamp).log"
$qaArgs = @(
    '-executeMethod', 'Game.Editor.VisualQA.VisualQaRunner.RenderControlCameras',
    '-qaScene', $Scene, '-qaWidth', $Width, '-qaHeight', $Height, '-qaTier', $Tier, '-qaOutput', $OutputDir)
if ($Lighting) { $qaArgs += @('-qaLighting', $Lighting) }
if ($Cameras) { $qaArgs += @('-qaCameras', $Cameras) }
if ($WbAdapt) { $qaArgs += @('-qaWbAdapt', $WbAdapt) }
if ($NoGlass) { $qaArgs += @('-qaNoGlass', '1') }
if ($CabFill -eq 'off') { $qaArgs += @('-qaCabFill', 'off') }
if ($Rq) { $qaArgs += @('-qaRq', $Rq) }
if ($RenderScale) { $qaArgs += @('-qaRenderScale', $RenderScale) }
if ($Wires -ne 'on') { $qaArgs += @('-qaWires', $Wires) }
if ($Runoff -ne 'on') { $qaArgs += @('-qaRunoff', $Runoff) }
if ($Gate3) { $qaArgs += @('-qaGate3', [IO.Path]::GetFullPath($Gate3, (Get-Location).Path)) }
if ($TimeFrames -gt 0) { $qaArgs += @('-qaTimeFrames', $TimeFrames) }
$code = Invoke-UnityBatch -LogFile $log -Arguments $qaArgs

$result = Select-String -Path $log -Pattern 'VISUALQA_RESULT:.*' | Select-Object -Last 1
if ($code -ne 0 -or -not $result -or $result.Line -notmatch 'VISUALQA_RESULT: OK') {
    Write-Host "visual-qa FAILED (exit $code), log: $log" -ForegroundColor Red
    Show-UnityLogErrors $log
    exit ([Math]::Max(1, $code))
}
Write-Host $result.Line
Get-ChildItem $OutputDir -Filter *.png | ForEach-Object { Write-Host ("  {0}  {1:N0} KB" -f $_.FullName, ($_.Length / 1KB)) }
Write-Host "log: $log"
exit 0

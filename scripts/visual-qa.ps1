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
    [ValidateSet('on', 'off')] [string]$CabFill = 'on'
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
if ($CabFill -eq 'off') { $qaArgs += @('-qaCabFill', 'off') }
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

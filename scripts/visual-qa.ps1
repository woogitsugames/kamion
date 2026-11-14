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
    [ValidateSet('', 'clear', 'overcast', 'lowsun', 'dusk', 'night')] [string]$Lighting = '',
    [string]$Cameras = '',
    # ADR 0175 evidence: force truck lamp groups on, e.g. 'rearfog,hazard,low'.
    [string]$TruckLamps = '',
    # A7 before/after: 'off' renders without the cab fill and the cab-view lift (CabInteriorLighting).
    [ValidateSet('on', 'off')] [string]$CabFill = 'on',
    # ADR 0044 r9 A/B: 'none' renders the cab with the state the phone had before r9 (no view camera -> exterior cab state).
    [ValidateSet('explicit', 'none')] [string]$CabView = 'explicit',
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
    [ValidateSet('on', 'off')] [string]$Runoff = 'on',
    # Measurement mask: '<renderer>[:<slot>][;...]' also writes <id>_mask.png with those slots flat magenta.
    [string]$Mask = '',
    # ADR 0056: also write <id>_envcube.png (the vehicle reflection cube of that frame, 6 faces).
    [switch]$EnvDump
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
if ($TruckLamps) { $qaArgs += @('-qaTruckLamps', $TruckLamps) }
if ($WbAdapt) { $qaArgs += @('-qaWbAdapt', $WbAdapt) }
if ($NoGlass) { $qaArgs += @('-qaNoGlass', '1') }
if ($CabFill -eq 'off') { $qaArgs += @('-qaCabFill', 'off') }
if ($CabView -ne 'explicit') { $qaArgs += @('-qaCabView', $CabView) }
if ($Rq) { $qaArgs += @('-qaRq', $Rq) }
if ($RenderScale) { $qaArgs += @('-qaRenderScale', $RenderScale) }
if ($Wires -ne 'on') { $qaArgs += @('-qaWires', $Wires) }
if ($Runoff -ne 'on') { $qaArgs += @('-qaRunoff', $Runoff) }
if ($Gate3) { $qaArgs += @('-qaGate3', [IO.Path]::GetFullPath($Gate3, (Get-Location).Path)) }
if ($TimeFrames -gt 0) { $qaArgs += @('-qaTimeFrames', $TimeFrames) }
if ($Mask) { $qaArgs += @('-qaMask', $Mask) }
if ($EnvDump) { $qaArgs += @('-qaEnvDump', '1') }
$runStart = Get-Date
$code = Invoke-UnityBatch -LogFile $log -Arguments $qaArgs

$result = Select-String -Path $log -Pattern 'VISUALQA_RESULT:.*' | Select-Object -Last 1

# ADR 0051: Unity 6000.3.28f1 sporadically access-violates (0xC0000005 = -1073741819) AFTER the runner finished, inside
# EditorApplication.Exit -> DestroyGfxDevice -> ~D3D12PipelineCache -> D3D12PipelineCacheLibrary::SaveCache (engine bug,
# no managed/our resources on the stack). Accept the run only when ALL of this is proven: exit code is exactly that
# access violation, the log has VISUALQA_RESULT: OK rendered=N, the crash stack contains the known signature, and N fresh
# PNGs exist. Anything else (other crash, other stack, fewer frames) stays a failure.
if ($code -eq -1073741819 -and $result -and $result.Line -match 'VISUALQA_RESULT: OK rendered=(\d+)') {
    $n = [int]$Matches[1]
    $sig = Select-String -Path $log -SimpleMatch 'D3D12PipelineCacheLibrary::SaveCache' -Quiet
    $fresh = @(Get-ChildItem $OutputDir -Filter *.png -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -notlike '*_mask.png' -and $_.LastWriteTime -ge $runStart }).Count
    if ($sig -and $fresh -ge $n) {
        Write-Warning "Unity crashed on shutdown (0xC0000005 in D3D12PipelineCacheLibrary::SaveCache, known engine bug, ADR 0051) AFTER writing all $n frames; accepted."
        $code = 0
    }
    else { Write-Host "shutdown crash NOT accepted: signature=$sig freshPng=$fresh expected=$n" -ForegroundColor Red }
}
# ADR 0083: second shutdown flake of 6000.3.28f1 (2 of 18 runs in truck-ext-r10): the runner finished, every frame is on
# disk, the editor reaches "Cleanup mono", then "abort_threads: Failed aborting id ..." and the process ends with a
# non-zero code and NO crash stack (the log just stops after "debugger-agent: Unable to listen"). Accept only when all of
# it is proven: VISUALQA_RESULT: OK rendered=N, N fresh PNGs, "Cleanup mono" and the abort_threads line AFTER the result
# line, and no crash marker anywhere in the log. Anything else stays a failure.
if ($code -ne 0 -and $result -and $result.Line -match 'VISUALQA_RESULT: OK rendered=(\d+)') {
    $n = [int]$Matches[1]
    $after = $result.LineNumber
    $mono = Select-String -Path $log -SimpleMatch 'Cleanup mono' | Where-Object { $_.LineNumber -gt $after } | Select-Object -First 1
    $abort = Select-String -Path $log -SimpleMatch 'abort_threads: Failed aborting' | Where-Object { $_.LineNumber -gt $after } | Select-Object -First 1
    $crash = Select-String -Path $log -Pattern 'Crash!!!|Obtained \d+ stack frames|Fatal Error|error CS\d+' -Quiet
    $fresh = @(Get-ChildItem $OutputDir -Filter *.png -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -notlike '*_mask.png' -and $_.LastWriteTime -ge $runStart }).Count
    if ($mono -and $abort -and -not $crash -and $fresh -ge $n) {
        Write-Warning "Unity exited with code $code during mono cleanup (abort_threads, no crash stack) AFTER writing all $n frames; accepted (ADR 0083)."
        $code = 0
    }
}
if ($code -ne 0 -or -not $result -or $result.Line -notmatch 'VISUALQA_RESULT: OK') {
    Write-Host "visual-qa FAILED (exit $code), log: $log" -ForegroundColor Red
    Show-UnityLogErrors $log
    exit ([Math]::Max(1, $code))
}
Write-Host $result.Line
Get-ChildItem $OutputDir -Filter *.png | ForEach-Object { Write-Host ("  {0}  {1:N0} KB" -f $_.FullName, ($_.Length / 1KB)) }
Write-Host "log: $log"
exit 0

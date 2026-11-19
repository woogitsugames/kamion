<#
.SYNOPSIS
  Run Unity EditMode and/or PlayMode tests in batchmode; NUnit XML in artifacts/tests/.
.EXAMPLE
  pwsh scripts/test.ps1                 # EditMode + PlayMode
  pwsh scripts/test.ps1 -Platform EditMode
  pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64   # worktree whose Library is imported for Windows
.NOTES
  Exit 0 only if every requested run passed with at least one test. Unity runs sequentially
  (one Unity process per project).
#>
param(
    [ValidateSet('All', 'EditMode', 'PlayMode')] [string]$Platform = 'All',
    [string]$Filter,
    # Editor platform of the run. A checkout switched to Win64 (scripts/build-windows.ps1) must test with Win64,
    # otherwise Unity switches back to Android and re-imports every asset (ADR 0261).
    [ValidateSet('Android', 'Win64')] [string]$BuildTarget = 'Android'
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/env.ps1"
$ts = Get-Timestamp
$resultsDir = Join-Path $ArtifactsDir 'tests'
New-Item -ItemType Directory -Force $resultsDir | Out-Null

$platforms = if ($Platform -eq 'All') { @('EditMode', 'PlayMode') } else { @($Platform) }
$failed = 0
foreach ($p in $platforms) {
    $xml = Join-Path $resultsDir "$($p.ToLower())-$ts.xml"
    $log = Join-Path $LogsDir "test-$($p.ToLower())-$ts.log"
    $unityArgs = @('-runTests', '-testPlatform', $p, '-testResults', $xml)
    if ($Filter) { $unityArgs += @('-testFilter', $Filter) }
    # -runTests quits by itself; -quit would abort before tests run.
    $code = Invoke-UnityBatch -LogFile $log -Arguments $unityArgs -NoQuit -BuildTarget $BuildTarget
    if (-not (Test-Path $xml)) {
        Write-Host "$p : no results (exit $code), log $log" -ForegroundColor Red
        Show-UnityLogErrors $log; $failed++; continue
    }
    [xml]$doc = Get-Content $xml
    $run = $doc.'test-run'
    # Unity exits 2 also for Inconclusive (Assume.That) cases, which the NUnit "failed" count leaves out: list them, so a
    # red run is never reported as "0 failed" without a reason (test-hygiene-s24).
    $inconclusive = $doc.SelectNodes('//test-case[@result="Inconclusive"]')
    $line = "{0}: {1} total, {2} passed, {3} failed, {4} inconclusive, {5} skipped ({6}), unity exit {7} -> {8}" -f $p, $run.total, $run.passed, $run.failed, $inconclusive.Count, $run.skipped, $run.result, $code, $xml
    if ($code -ne 0 -or [int]$run.failed -gt 0 -or [int]$run.total -eq 0 -or $inconclusive.Count -gt 0) {
        Write-Host $line -ForegroundColor Red
        $doc.SelectNodes('//test-case[@result="Failed"]') | ForEach-Object { Write-Host "  FAILED $($_.fullname): $($_.failure.message.'#cdata-section')" -ForegroundColor Red }
        $inconclusive | ForEach-Object { Write-Host "  INCONCLUSIVE $($_.fullname): $($_.reason.message.'#cdata-section')" -ForegroundColor Red }
        $failed++
    } else { Write-Host $line }
}
exit $failed

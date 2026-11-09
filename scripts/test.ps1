<#
.SYNOPSIS
  Run Unity EditMode and/or PlayMode tests in batchmode; NUnit XML in artifacts/tests/.
.EXAMPLE
  pwsh scripts/test.ps1                 # EditMode + PlayMode
  pwsh scripts/test.ps1 -Platform EditMode
.NOTES
  Exit 0 only if every requested run passed with at least one test. Unity runs sequentially
  (one Unity process per project).
#>
param(
    [ValidateSet('All', 'EditMode', 'PlayMode')] [string]$Platform = 'All',
    [string]$Filter
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
    $code = Invoke-UnityBatch -LogFile $log -Arguments $unityArgs -NoQuit -BuildTarget 'Android'
    if (-not (Test-Path $xml)) {
        Write-Host "$p : no results (exit $code), log $log" -ForegroundColor Red
        Show-UnityLogErrors $log; $failed++; continue
    }
    [xml]$doc = Get-Content $xml
    $run = $doc.'test-run'
    $line = "{0}: {1} total, {2} passed, {3} failed, {4} skipped ({5}) -> {6}" -f $p, $run.total, $run.passed, $run.failed, $run.skipped, $run.result, $xml
    if ($code -ne 0 -or [int]$run.failed -gt 0 -or [int]$run.total -eq 0) {
        Write-Host $line -ForegroundColor Red
        $doc.SelectNodes('//test-case[@result="Failed"]') | ForEach-Object { Write-Host "  FAILED $($_.fullname): $($_.failure.message.'#cdata-section')" -ForegroundColor Red }
        $failed++
    } else { Write-Host $line }
}
exit $failed

param([Parameter(Mandatory)][int]$PipelineProcessId)
$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $repo
$identity=Get-CimInstance Win32_Process -Filter "ProcessId=$PipelineProcessId"
if($null -eq $identity -or $identity.Name -ne 'pwsh.exe' -or $identity.CommandLine -notmatch '-File artifacts/light-r4/regenerate-baseline\.ps1\s*$'){
    throw 'Not the expected live round4 pipeline'
}
$process=Get-Process -Id $PipelineProcessId;$null=$process.Handle
Write-Output "Waiting for actual pipeline$PipelineProcessId, created$($identity.CreationDate); no concurrent own Unity or Python."
while(-not $process.WaitForExit(1000)){}
if($null -eq $process.ExitCode -or $process.ExitCode -ne 0){throw 'Pipeline did not terminate successfully; inspect original handle before retry'}
if((git branch --show-current).Trim() -ne 'gpt-light-r4'){throw 'Branch changed while pipeline ran'}
$jobs=(Get-Content "$PSScriptRoot/baseline.json" -Raw|ConvertFrom-Json).jobs
if($jobs.Count -ne 6){throw 'Expected six baseline groups'}
foreach($job in $jobs){if(@(Get-ChildItem -LiteralPath $job.output -Filter '*.png' -ErrorAction SilentlyContinue).Count -eq 0){throw 'Missing completed baseline images'}}
Write-Output 'Pipeline terminal0 with six nonempty groups; running corrected chart through its own Unity slot.'
& pwsh -NoProfile -File "$PSScriptRoot/run-tone-chart.ps1" -OutputName tone-chart-v2
if($LASTEXITCODE){throw 'Corrected tone chart did not pass its actual-grading guards'}
Write-Output 'ROUND4_BASELINE_AND_CHART_RESULT: OK; inspect all scene captures and corrected chart before tuning.'

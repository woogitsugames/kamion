param([Parameter(Mandatory)][string]$Jobs, [string]$Gate3 = 'Data/Regions/bialystok-industrial-c/buildings_r10_cameras.json')
$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $repo
. "$repo/scripts/env.ps1"
$jobPath = [IO.Path]::GetFullPath($Jobs, $repo)
$spec = Get-Content $jobPath -Raw | ConvertFrom-Json
foreach ($job in $spec.jobs) { $job.output = [IO.Path]::GetFullPath($job.output, $repo) }
$resolved = [IO.Path]::ChangeExtension($jobPath, '.resolved.json')
$spec | ConvertTo-Json -Depth 10 | Set-Content $resolved -Encoding utf8
$log = [IO.Path]::ChangeExtension($jobPath, ".$(Get-Timestamp).log")
$unityArguments = @('-executeMethod', 'Game.Rendering.Editor.LightQaBatch.Run', '-lightQaJobs', $resolved)
if ($Gate3) { $unityArguments += @('-qaGate3', [IO.Path]::GetFullPath($Gate3, $repo)) }
& pwsh scripts/unity-slot.ps1 -Acquire -Owner gpt-light
if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu Unity' }
try {
    $code = Invoke-UnityBatch -LogFile $log -Arguments $unityArguments
    if ($code -ne 0 -or -not (Select-String $log -Pattern 'LIGHT_QA_RESULT: OK' -Quiet)) {
        Show-UnityLogErrors $log
        throw "Batch światła nieudany: exit=$code, log=$log"
    }
    Select-String $log -Pattern 'LIGHT_QA_JOB:|LIGHT_QA_RESULT:' | ForEach-Object { $_.Line }
}
finally {
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh scripts/unity-slot.ps1 -Release -Owner gpt-light
}
Add-Content artifacts/light-r1/STATUS.md "Batch światła zakończony: $Jobs; log $log. Następny krok: obejrzeć PNG i policzyć metryki, nie deklarować PASS z samego kodu wyjścia."
git add -f artifacts/light-r1/STATUS.md
git commit -m "wip(light): zapisz wykonanie batcha $([IO.Path]::GetFileNameWithoutExtension($jobPath))"

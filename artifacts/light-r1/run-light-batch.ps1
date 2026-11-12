param([Parameter(Mandatory)][string]$Jobs, [string]$Gate3 = 'Data/Regions/bialystok-industrial-c/buildings_r10_cameras.json')
$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $repo
. "$repo/scripts/env.ps1"
$slot = 'C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
$jobPath = [IO.Path]::GetFullPath($Jobs, $repo)
$spec = Get-Content $jobPath -Raw | ConvertFrom-Json
foreach ($job in $spec.jobs) { $job.output = [IO.Path]::GetFullPath($job.output, $repo) }
$resolved = [IO.Path]::ChangeExtension($jobPath, '.resolved.json')
$spec | ConvertTo-Json -Depth 10 | Set-Content $resolved -Encoding utf8
$log = [IO.Path]::ChangeExtension($jobPath, ".$(Get-Timestamp).log")
$unityArguments = @('-executeMethod', 'Game.Rendering.Editor.LightQaBatch.Run', '-lightQaJobs', $resolved)
if ($Gate3) { $unityArguments += @('-qaGate3', [IO.Path]::GetFullPath($Gate3, $repo)) }
& pwsh $slot -Acquire -Owner gpt-light
if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu Unity' }
git diff --quiet HEAD -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
if ($LASTEXITCODE -ne 0) {
    & pwsh $slot -Release -Owner gpt-light
    throw 'Przed Unity ustawienia muszą być zacommitowane: wymagane sprzątanie nie może usuwać wcześniejszych zmian'
}
try {
    $runStart = Get-Date
    $code = Invoke-UnityBatch -LogFile $log -Arguments $unityArguments
    $result = Select-String -Path $log -Pattern 'LIGHT_QA_RESULT: OK jobs=(\d+) rendered=(\d+)' | Select-Object -Last 1
    $fresh = @()
    $complete = $null -ne $result
    foreach ($job in $spec.jobs) {
        $files = @(Get-ChildItem -LiteralPath $job.output -Filter '*.png' -ErrorAction SilentlyContinue |
            Where-Object { $_.LastWriteTime -ge $runStart -and $_.Length -gt 0 -and $_.Name -notlike '*_mask.png' })
        $fresh += $files
        if ($job.cameras) {
            $ids = @($job.cameras.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ } | Select-Object -Unique)
            if ($ids.Count -ne $files.Count) { $complete = $false }
            foreach ($id in $ids) { if ($files.Name -notcontains "$id.png") { $complete = $false } }
        }
    }
    if ($result) {
        $match = [regex]::Match($result.Line, 'jobs=(\d+) rendered=(\d+)')
        $complete = $complete -and [int]$match.Groups[1].Value -eq $spec.jobs.Count -and [int]$match.Groups[2].Value -eq $fresh.Count
    }
    # Same narrowly evidenced shutdown exceptions as scripts/visual-qa.ps1 (ADR 0051 / 0083).
    $knownD3D = $code -eq -1073741819 -and (Select-String -Path $log -SimpleMatch -Pattern 'D3D12PipelineCacheLibrary::SaveCache' -Quiet)
    $knownMono = $false
    if ($result) {
        $mono = Select-String -Path $log -SimpleMatch -Pattern 'Cleanup mono' | Where-Object { $_.LineNumber -gt $result.LineNumber }
        $abort = Select-String -Path $log -SimpleMatch -Pattern 'abort_threads: Failed aborting' | Where-Object { $_.LineNumber -gt $result.LineNumber }
        $crash = Select-String -Path $log -Pattern 'Crash!!!|Obtained \d+ stack frames|Fatal Error|error CS\d+' -Quiet
        $knownMono = $mono -and $abort -and -not $crash
    }
    if ($code -ne 0 -and $complete -and ($knownD3D -or $knownMono)) {
        Write-Warning "Known Unity shutdown failure after all $($fresh.Count) fresh PNGs and LIGHT_QA_RESULT: OK; original exit=$code (ADR 0051/0083)."
        $code = 0
    }
    if ($code -ne 0 -or -not $complete) {
        Show-UnityLogErrors $log
        throw "Batch światła nieudany: exit=$code, log=$log"
    }
    Select-String -Path $log -Pattern 'LIGHT_QA_JOB:|LIGHT_QA_RESULT:' | ForEach-Object { $_.Line }
}
finally {
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh $slot -Release -Owner gpt-light
}
Add-Content artifacts/light-r1/STATUS.md "Batch światła zakończony: $Jobs; log $log. Następny krok: obejrzeć PNG i policzyć metryki, nie deklarować PASS z samego kodu wyjścia."
git add -f artifacts/light-r1/STATUS.md
git commit -m "wip(light): zapisz wykonanie batcha $([IO.Path]::GetFileNameWithoutExtension($jobPath))"

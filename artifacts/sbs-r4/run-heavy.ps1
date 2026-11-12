param(
    [Parameter(Mandatory)][ValidateSet('PrepareControls','ComposeControls','TestFile','Audit','Fidelity','FinalGis')][string]$Task,
    [string]$TestFile,
    [switch]$EndOfRound
)
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Push-Location $root
try {
    $owner=(& git branch --show-current).Trim()
    if($owner -ne 'gpt-sbs-r4'){throw 'Expected r4 branch'}
    if($Task -eq 'FinalGis' -and !$EndOfRound){throw 'Full GIS only at end of round'}
    if($Task -eq 'TestFile' -and (!$TestFile -or !(Test-Path -LiteralPath $TestFile -PathType Leaf) -or $TestFile -notmatch '^tests/gis/test_[^/\\]+\.py$')){throw 'Single GIS test file required'}
    $slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
    # Do not borrow or silently reuse another job with this owner.
    $lease='C:/Users/matma/Documents/Claude/kamion/artifacts/locks/heavy-slots/'+$owner+'.slot'
    if(Test-Path -LiteralPath $lease){throw 'Another task already owns this heavy lease'}
    $ticket='C:/Users/matma/Documents/Claude/kamion/artifacts/locks/heavy-slots/queue/'+$owner+'.wait'
    if(Test-Path -LiteralPath $ticket){throw 'Another task with this owner is already queued'}
    pwsh -NoProfile -File $slot -Acquire -Pool heavy -Owner $owner -PollSeconds 5 -StaleHours 87600
    if($LASTEXITCODE -ne 0){throw 'Heavy lease failed'}
    try {
        $started=[DateTime]::UtcNow
        $sourceHead=(& git rev-parse HEAD).Trim()
        $env:PYTHONUNBUFFERED='1'
        switch($Task) {
            PrepareControls {uv run --project tools/refs python artifacts/sbs-r4/make-controlled-probes.py}
            ComposeControls {uv run --project tools/refs python artifacts/sbs-r4/compose-controlled.py}
            TestFile {uv run --project tools/worldgen python -m pytest $TestFile -q}
            Audit {uv run --project tools/refs python artifacts/sbs-r4/audit_baseline.py}
            Fidelity {uv run --project tools/worldgen python tools/worldgen/fidelity/run.py --region bialystok-industrial-c --art artifacts/sbs-r4/fidelity}
            FinalGis {uv run --project tools/worldgen python -m pytest tests/gis -q}
        }
        $exitCode=$LASTEXITCODE
        $receiptName=if($Task -eq 'TestFile'){'test-'+[IO.Path]::GetFileNameWithoutExtension($TestFile)}else{$Task.ToLowerInvariant()}
        [ordered]@{task=$Task;test_file=$TestFile;exit_code=$exitCode;source_head=$sourceHead;started_at_utc=$started.ToString('o');completed_at_utc=[DateTime]::UtcNow.ToString('o');owner=$owner;queue='FIFO'} | ConvertTo-Json | Set-Content (Join-Path $PSScriptRoot ($receiptName+'-completed.json')) -Encoding utf8
        if($exitCode -ne 0){throw "Task $Task failed with $exitCode"}
    } finally {pwsh -NoProfile -File $slot -Release -Pool heavy -Owner $owner}
} finally {Pop-Location}

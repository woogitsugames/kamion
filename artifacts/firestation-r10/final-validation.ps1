param([ValidateSet('GIS','EditMode')][string]$Stage)
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$workRoot=[IO.Path]::GetFullPath((Join-Path $taskRoot '../..'))
Set-Location $workRoot
. "$workRoot/scripts/env.ps1"
if($Stage -eq 'GIS') {
    uv run --project tools/worldgen python tools/worldgen/fidelity/run.py --region bialystok-industrial-c --no-tile *> "$taskRoot/final-fidelity.log"
    if($LASTEXITCODE -ne 0){throw 'Fidelity generation failed'}
    uv run --project tools/worldgen python artifacts/firestation-r10/pin_products.py final
    if($LASTEXITCODE -ne 0){throw 'Final product pinning failed'}
    uv run --project tools/worldgen python -m pytest tests/gis -q *> "$taskRoot/pytest-complete.log"
    if($LASTEXITCODE -ne 0){throw 'Full GIS failed; inspect actual failures without weakening tests'}
} elseif($Stage -eq 'EditMode') {
    if(-not(Test-Path "$taskRoot/ROOT_UNITY_RELEASE.txt")){throw 'Fresh explicit ROOT release missing'}
    foreach($guard in @('PHONE_RUN','GPT_UNITY_HOLD')) {
        if(Test-Path "C:/Users/matma/Documents/Claude/kamion/artifacts/locks/$guard"){throw "Unity blocked by $guard"}
    }
    if(Test-UnityProjectLocked){throw 'Own project already running Unity'}
    $xml=Join-Path $taskRoot 'editmode-final.xml'
    if(Test-Path $xml){throw 'Existing XML must be preserved, choose a new evidence file for a justified rerun'}
    $code=Invoke-UnityBatch -LogFile "$taskRoot/editmode-final.log" -Arguments @('-runTests','-testPlatform','EditMode','-testResults',$xml) -NoQuit -BuildTarget Android
    if(-not(Test-Path $xml)){throw "No XML, Unity exit $code"}
    [xml]$doc=Get-Content $xml
    $run=$doc.'test-run'
    "$($run.total) tests / $($run.passed) passed / $($run.failed) failed / $($run.skipped) skipped / $($run.result) / exit=$code" | Set-Content "$taskRoot/editmode-result.txt"
    if($code -ne 0 -or [int]$run.failed -gt 0 -or [int]$run.total -eq 0){throw 'EditMode unsuccessful; inspect XML'}
} else {throw 'Choose GIS or EditMode explicitly; no automatic Unity queue'}

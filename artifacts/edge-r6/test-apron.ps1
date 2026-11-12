param([Parameter(Mandatory)][ValidateSet('red','green')][string]$Phase)
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if((git branch --show-current).Trim() -ne 'gpt-edge-r6'){throw 'Wrong round'}
foreach($marker in @('Baseline.ready','OwnershipDiagnostics.ready','ContactBefore.ready')){
    if(-not(Test-Path "$PSScriptRoot/$marker")){throw "Fresh baseline/diagnosis required: $marker"}
}
$tests=@('game/Assets/_Project/Tests/EditMode/WorldEdgeApronGradeTests.cs',
         'game/Assets/_Project/Tests/EditMode/WorldEdgeApronTransitionTests.cs')
$testHashes=@{};foreach($file in $tests){$testHashes[$file]=(Get-FileHash $file -Algorithm SHA256).Hash}
$source='game/Assets/_Project/World/Import/WorldEdgeBuilder.cs'
$sourceHash=(Get-FileHash $source -Algorithm SHA256).Hash
$base=(Get-Content "$PSScriptRoot/before/Low-clear/capture-inputs.json" -Raw|ConvertFrom-Json).inputs_sha256.$source
$result="$PSScriptRoot/apron-$Phase-result.json"
$xml="$PSScriptRoot/apron-$Phase.xml"
if((Test-Path $result) -or (Test-Path $xml)){throw 'Preserve existing test evidence before any deliberate rerun'}
if($Phase -eq 'red'){
    if($sourceHash -ne $base){throw 'Red requires the captured unmodified apron source'}
}else{
    $red=Get-Content "$PSScriptRoot/apron-red-result.json" -Raw|ConvertFrom-Json
    if(-not $red.expected_result_verified -or $sourceHash -eq $red.source_sha256){throw 'Green requires verified Red and a production source change'}
    foreach($file in $tests){if($testHashes[$file] -ne $red.test_sha256.$file){throw "Test changed after Red: $file"}}
}
. scripts/env.ps1
& pwsh -File "$PSScriptRoot/acquire-slot.ps1" -Pool unity -Owner gpt-edge
if($LASTEXITCODE -ne0){throw 'Unity slot failed'}
$acquired=Get-Date -Format o
$exitCode=99
try{
    $exitCode=Invoke-UnityBatch -LogFile "$PSScriptRoot/apron-$Phase.log" -NoQuit -BuildTarget Android -Arguments @(
        '-runTests','-testPlatform','EditMode','-testResults',$xml,'-testFilter','WorldEdgeApron')
}finally{
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh -File 'C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1' -Release -Pool unity -Owner gpt-edge -StaleHours 100000
    @{phase=$Phase;pool='unity';owner='gpt-edge';acquired=$acquired;finished=(Get-Date -Format o);exit_code=$exitCode}|
        ConvertTo-Json|Set-Content "$PSScriptRoot/apron-$Phase-slot.json"
}
if(-not(Test-Path $xml)){throw 'No NUnit results; compilation or launch failure is not a valid Red'}
[xml]$doc=Get-Content $xml -Raw
$run=$doc.'test-run'
$failures=@($doc.SelectNodes('//test-case[@result="Failed"]')|ForEach-Object {$_.fullname})
$valid=[int]$run.total -eq16 -and [int]$run.skipped -eq0 -and [int]$run.inconclusive -eq0
if($Phase -eq 'red'){
    $unexpected=@($failures|Where-Object {$_ -notmatch 'WorldEdgeApronTransitionTests\.(DitchTransition_ActualTrianglesMeetSmoothedProfile|BuriedCurtainProxy_DoesNotFloatAboveActualApron)\('})
    $assertions=@($doc.SelectNodes('//test-case[@result="Failed"]')|Where-Object {$_.label -and $_.label -ne 'Failure'})
    $valid=$valid -and [int]$run.failed -eq6 -and [int]$run.passed -eq10 -and $unexpected.Count -eq0 -and $assertions.Count -eq0
}else{
    $valid=$valid -and $exitCode -eq0 -and [int]$run.failed -eq0 -and [int]$run.passed -eq16
}
foreach($file in $tests){if((Get-FileHash $file -Algorithm SHA256).Hash -ne $testHashes[$file]){throw 'Test changed during execution'}}
if((Get-FileHash $source -Algorithm SHA256).Hash -ne $sourceHash){throw 'Production source changed during execution'}
@{phase=$Phase;total=[int]$run.total;passed=[int]$run.passed;failed=[int]$run.failed;skipped=[int]$run.skipped;
  unity_exit_code=$exitCode;expected_result_verified=$valid;failures=$failures;source_sha256=$sourceHash;test_sha256=$testHashes}|
    ConvertTo-Json -Depth 6|Set-Content $result
Add-Content "$PSScriptRoot/STATUS.md" "$(Get-Date -Format o) Rzeczywisty NUnit apron ${Phase}: total=$($run.total), passed=$($run.passed), failed=$($run.failed), oczekiwany wynik=$valid. Zachowano XML/log i SHA obu plików testów oraz źródła; brak podmiany testów między Red a Green."
git add -f artifacts/edge-r6/STATUS.md $result "$PSScriptRoot/apron-$Phase-slot.json"
git commit -m "WIP edge r6: preserve actual apron $Phase NUnit result and source hashes"
if($LASTEXITCODE -ne0){throw 'Test checkpoint failed'}
if(-not $valid){throw 'Unexpected actual test result; inspect NUnit before changing or accepting production'}

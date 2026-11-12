param([ValidateSet('Red','Green')][string]$Phase,[int]$WaitPid=0,[switch]$HeavyAlreadyHeld)
$ErrorActionPreference='Stop'
$env:OMP_NUM_THREADS='1';$env:OPENBLAS_NUM_THREADS='1';$env:MKL_NUM_THREADS='1';$env:NUMEXPR_NUM_THREADS='1'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
while(-not(Test-Path "$PSScriptRoot/Identification.ready")){
    if($WaitPid -le 0 -or -not(Get-Process -Id $WaitPid -ErrorAction SilentlyContinue)){throw 'Identification is not complete; inspect its process and result'}
    Start-Sleep -Seconds 5
}
if((git branch --show-current).Trim() -ne 'gpt-edge-r5'){throw 'Wrong round'}
$test='tests/gis/test_far_field_industrial_facade.py'
$source='tools/worldgen/streetscape/far_field.py'
$testSha=(Get-FileHash $test -Algorithm SHA256).Hash
$sourceSha=(Get-FileHash $source -Algorithm SHA256).Hash
if($Phase -eq 'Green'){
    $red=Get-Content "$PSScriptRoot/facade-red-result.json" -Raw|ConvertFrom-Json
    if(-not $red.expected_result_verified -or $red.test_sha256 -ne $testSha -or $red.source_sha256 -eq $sourceSha){throw 'Green requires verified Red, identical tests and changed production source'}
}
$label=$Phase.ToLowerInvariant()
New-Item -ItemType Directory -Force "$PSScriptRoot/tests"|Out-Null
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
if($HeavyAlreadyHeld){
    if(-not(Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/heavy-slots/gpt-edge-r5.slot')){throw 'No caller heavy lease'}
}else{
    & pwsh -File $slot -Acquire -Pool heavy -Owner gpt-edge-r5 -PollSeconds 1 -StaleHours 100000
    if($LASTEXITCODE -ne 0){throw 'Facade test heavy acquisition failed'}
}
$code=99
try{
    & uv run --project tools/worldgen python -m pytest $test -q --junitxml "$PSScriptRoot/tests/facade-$label.xml" *> "$PSScriptRoot/facade-$label.log"
    $code=$LASTEXITCODE
}finally{
    if(-not$HeavyAlreadyHeld){ & pwsh -File $slot -Release -Pool heavy -Owner gpt-edge-r5 -StaleHours 100000 }
}
$xml=[xml](Get-Content "$PSScriptRoot/tests/facade-$label.xml" -Raw)
$cases=@($xml.SelectNodes('//testcase'))
$failures=@($xml.SelectNodes('//testcase[failure]'))
$errors=@($xml.SelectNodes('//testcase[error]'))
$skips=@($xml.SelectNodes('//testcase[skipped]'))
if($cases.Count -ne 20 -or $errors.Count -or $skips.Count){throw 'Unexpected facade test count, error or skip'}
if($Phase -eq 'Red'){
    if($code -ne 1 -or $failures.Count -ne 2){throw 'Expected exactly two old industrial appearance failures'}
    foreach($f in $failures){
        if($f.name -notmatch '^test_measured_height_does_not_invent_a_power_plant\[(Low|High)\]$' -or
           $f.failure.InnerText -notlike '*declared industrial facade*'){throw 'Wrong failure in Red; inspect before editing production'}
    }
}elseif($code -ne 0 -or $failures.Count){throw 'Facade Green failed'}
@{phase=$Phase;tests=$cases.Count;passed=$cases.Count-$failures.Count;failed=$failures.Count;
  skipped=$skips.Count;pytest_exit_code=$code;expected_result_verified=$true;
  test_sha256=$testSha;source_sha256=$sourceSha;finished=(Get-Date -Format o)}|
    ConvertTo-Json|Set-Content "$PSScriptRoot/facade-$label-result.json"
Add-Content "$PSScriptRoot/STATUS.md" "$(Get-Date -Format o) Facade ${Phase}: $($cases.Count) testów, $($failures.Count) oczekiwanych/rzeczywistych porażek, 0errors/skips; wynik i SHA w facade-$label-result.json."
git add -f artifacts/edge-r5/STATUS.md "artifacts/edge-r5/facade-$label-result.json"
git commit -m "WIP edge r5: verify industrial facade $Phase against actual generator geometry"
if($LASTEXITCODE -ne 0){throw 'Facade test checkpoint failed'}

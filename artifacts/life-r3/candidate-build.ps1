param([Parameter(Mandatory)][ValidatePattern('^[a-z][a-z0-9-]*$')][string]$Stage)
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
$owner=(git branch --show-current).Trim()
if($owner -ne 'gpt-life-r3'){throw 'Wrong branch'}
$phase='acquire';$code=1;$held=$false
$prefix="artifacts/life-r3/candidate-$Stage"
function Checkpoint([string]$Message,[string[]]$Files=@()) {
 Add-Content artifacts/life-r3/STATUS.md ("`nKandydat {0} ({1}): {2}. Następny etap w candidate-build.ps1; po komplecie PreparedVerified, capture i oględziny." -f $Stage,(Get-Date -Format o),$Message)
 git add -u -- Data/Regions/bialystok-industrial-c/generated art-source/world/props
 git add -f -- artifacts/life-r3/STATUS.md @Files
 if($LASTEXITCODE){throw 'Staging failed'}
 git commit -m "wip(life): $Message"
 if($LASTEXITCODE){throw 'WIP failed'}
}
try {
 if((Test-Path "$prefix-world.log") -or (Test-Path "$prefix-build-result.json")){throw 'Evidence exists; use a new stage'}
 if(Test-Path "C:/Users/matma/Documents/Claude/kamion/artifacts/locks/heavy-slots/$owner.slot"){throw 'Own heavy already active'}
 if(!(Test-Path artifacts/life-r3/BASELINE-INSPECTED.json)){throw 'Inspect baseline first'}
 & pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner $owner -StaleHours 1000000 -PollSeconds 1
 if($LASTEXITCODE){throw 'Acquire failed'}; $held=$true
 $phase='early-rim-test'
 & uv run --project tools/worldgen python -m pytest tests/gis/test_car_rim_facets.py -q *> "$prefix-test_car_rim_facets.log"
 $testCode=$LASTEXITCODE
 @{file='tests/gis/test_car_rim_facets.py';file_sha=(Get-FileHash tests/gis/test_car_rim_facets.py).Hash;exit_code=$testCode;finished=(Get-Date -Format o)}|ConvertTo-Json|Set-Content "$prefix-test_car_rim_facets.log.result.json"
 Checkpoint "sprawdź normalne faz wariantu $Stage" @("$prefix-test_car_rim_facets.log","$prefix-test_car_rim_facets.log.result.json")
 if($testCode){throw 'Rim export test failed; skip expensive world generation'}
 $phase='world'
 & uv run --project tools/worldgen python -u tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> "$prefix-world.log"
 if($LASTEXITCODE){throw 'World failed'}
 if(Select-String "$prefix-world.log" -Pattern 'fallback=True' -Quiet){throw 'Fallback detected'}
 Checkpoint "wygeneruj osobówki r3 $Stage" @()
 $phase='scope'
 & uv run --project tools/worldgen python artifacts/life-r3/check-nonlife.py $Stage *> "$prefix-scope.log"
 if($LASTEXITCODE){throw 'Nonlife/primitive audit failed'}
 Checkpoint "sprawdź zakres geometrii r3 $Stage" @("artifacts/life-r3/nonlife-glb-audit-$Stage.json")
 foreach($test in @('test_cars_r9.py','test_cars_r11.py','test_car_deposition.py','test_car_plate_payload.py')) {
  $phase="test-$test"
  $log="$prefix-$($test.Replace('.py','')).log"
  & uv run --project tools/worldgen python -m pytest "tests/gis/$test" -q *> $log
  $testCode=$LASTEXITCODE
  @{file="tests/gis/$test";file_sha=(Get-FileHash "tests/gis/$test").Hash;exit_code=$testCode;finished=(Get-Date -Format o)}|ConvertTo-Json|Set-Content "$log.result.json"
  Checkpoint "sprawdź $test wariantu $Stage" @($log,"$log.result.json")
  if($testCode){throw "Targeted test failed: $test"}
 }
 $phase='proof'
 & uv run --project tools/worldgen python artifacts/life-r3/source-proof.py "candidate-$Stage" *> "$prefix-source-proof.log"
 if($LASTEXITCODE){throw 'Prepared proof failed'}
 Checkpoint "zamroź wejścia importu r3 $Stage" @("$prefix-source-proof.json")
 $phase='complete';$code=0
} catch {
 Checkpoint "zapisz przerwany etap r3 $Stage $phase" @()
 throw
} finally {
 if($held){& pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Pool heavy -Owner $owner}
 @{stage=$Stage;phase=$phase;exit_code=$code;source_commit=(git rev-parse HEAD);finished=(Get-Date -Format o)}|ConvertTo-Json|Set-Content "$prefix-build-result.json"
}

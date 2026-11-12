param([ValidatePattern('^[a-z0-9-]+$')][string]$Tag='a')
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
$owner=(git branch --show-current).Trim()
if($owner -ne 'gpt-life-r4'){throw 'Wrong branch'}
if(!(Test-Path artifacts/life-r4/BASELINE-INSPECTED.json)){throw 'Inspect baseline first'}
$prefix="artifacts/life-r4/$Tag"
if(Test-Path "$prefix-world.log"){throw 'Evidence exists; inspect before resuming'}
$sources=[ordered]@{}
foreach($name in @('tools/worldgen/streetscape/life.py','tools/worldgen/streetscape/life_cars.py','tools/worldgen/streetscape/life_props.py','tools/worldgen/streetscape/depot_yard.py','tools/worldgen/streetscape/materials.py','game/Assets/_Project/Environment/Shaders/WorldPBR.shader','game/Assets/_Project/World/Import/WorldPbrMaterials.cs')){
 $sources[$name]=(Get-FileHash $name).Hash
}
@{started=(Get-Date -Format o);source_commit=(git rev-parse HEAD).Trim();source_sha=$sources}|ConvertTo-Json -Depth 4|Set-Content "$prefix-gen-inputs.json"
function Assert-Sources {
 foreach($entry in $sources.GetEnumerator()){if((Get-FileHash $entry.Key).Hash -ne $entry.Value){throw "Candidate source changed: $($entry.Key)"}}
}
function Save-Step([string]$message,[string[]]$files=@()){
 Add-Content artifacts/life-r4/STATUS.md ("`nKandydat {0} ({1}): {2}. Następny etap w candidate-gen.ps1; potem import/capture i oględziny. Limity klatki bez zmiany." -f $Tag,(Get-Date -Format o),$message)
 git add -u -- Data/Regions/bialystok-industrial-c/generated art-source/world
 git add -f artifacts/life-r4/STATUS.md artifacts/life-r4/SOURCE-MODE.json @files
 git commit -m "wip(life): $message"
 if($LASTEXITCODE){throw 'WIP failed'}
}
if(Test-Path "C:/Users/matma/Documents/Claude/kamion/artifacts/locks/heavy-slots/$owner.slot"){throw 'Own heavy already held'}
& pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner $owner -StaleHours 1000000 -PollSeconds 1
if($LASTEXITCODE){throw 'Acquire failed'}
$phase='preflight';$code=1
try {
 Assert-Sources
 & uv run --project tools/worldgen python artifacts/life-r4/audit-wheel-scope.py "$Tag-prebuild" *> "$prefix-prebuild-scope.log"
 if($LASTEXITCODE){throw 'Stored baseline GLB/scope preflight failed'}
 $phase='focused-tests'
 foreach($file in @('test_yard_wheel_recess','test_yard_vehicle_lod')){
  & uv run --project tools/worldgen python -m pytest "tests/gis/$file.py" -q *> "$prefix-$file.log"
  if($LASTEXITCODE){throw "Focused test failed: $file"}
 }
 Save-Step "sprawdź lustrzane wnętrza felg i kontrakt pojazdów $Tag" @("$prefix-gen-inputs.json","$prefix-test_yard_wheel_recess.log","$prefix-test_yard_vehicle_lod.log","$prefix-prebuild-wheel-scope.json")
 $phase='world'
 & uv run --project tools/worldgen python -u tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> "$prefix-world.log"
 if($LASTEXITCODE){throw 'Candidate World failed'}
 if(Select-String "$prefix-world.log" -Pattern 'fallback=True' -Quiet){throw 'Unexpected fallback'}
 Assert-Sources
 Save-Step "wygeneruj przestrzenne koła placowe $Tag"
 $phase='scope'
 & uv run --project tools/worldgen python artifacts/life-r4/audit-wheel-scope.py $Tag *> "$prefix-scope.log"
 if($LASTEXITCODE){throw 'Candidate escaped near wheel scope'}
 $phase='fidelity-test'
 & uv run --project tools/worldgen python -m pytest tests/gis/test_road_fidelity.py -q *> "$prefix-fidelity-test.log"
 if($LASTEXITCODE){throw 'Inspect fidelity; do not edit report hashes or skip test'}
 $mode=Get-Content artifacts/life-r4/SOURCE-MODE.json -Raw|ConvertFrom-Json
 $mode.mode="candidate-$Tag-generated"
 $mode.requires_generation=$false;$mode.requires_reimport=$true;$mode.requires_shader_compile=$false
 $mode.note='Geometry of near static wheels only; local prototype cap remains pending measured route budget and visual review.'
 $mode|ConvertTo-Json|Set-Content artifacts/life-r4/SOURCE-MODE.json
 $phase='proof'
 & uv run --project tools/worldgen python artifacts/life-r4/source-proof.py "$Tag-generated" *> "$prefix-source-proof.log"
 if($LASTEXITCODE){throw 'Candidate source proof failed'}
 Assert-Sources
 Save-Step "potwierdź zakres GLB, raw i fidelity kół $Tag" @("$prefix-wheel-scope.json","$prefix-generated-source-proof.json","$prefix-fidelity-test.log")
 $phase='complete';$code=0
} catch {
 Save-Step "zapisz przerwany kandydat $Tag na etapie $phase"
 throw
} finally {
 & pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Pool heavy -Owner $owner
 @{phase=$phase;exit_code=$code;finished=(Get-Date -Format o);source_commit=(git rev-parse HEAD).Trim()}|ConvertTo-Json|Set-Content "$prefix-gen-result.json"
}

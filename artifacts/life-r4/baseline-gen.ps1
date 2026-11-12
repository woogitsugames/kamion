$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
$owner=(git branch --show-current).Trim()
if($owner -ne 'gpt-life-r4'){throw 'Wrong branch'}
if(!(Test-Path artifacts/life-r4/prepared-fixtures.json)){throw 'Prepare sources first'}
$phase='acquire';$code=1;$held=$false
function Save-Step([string]$message){
 Add-Content artifacts/life-r4/STATUS.md ("`nBaseline ({0}): {1}. Następny etap w baseline-gen.ps1; potem import i oględziny, bez zmiany produkcji przed baseline." -f (Get-Date -Format o),$message)
 git add -u -- Data/Regions/bialystok-industrial-c/generated art-source/world
 git add -f artifacts/life-r4/STATUS.md artifacts/life-r4/SOURCE-MODE.json
 git commit -m "wip(life): $message"
 if($LASTEXITCODE){throw 'WIP failed'}
}
try {
 if(Test-Path "C:/Users/matma/Documents/Claude/kamion/artifacts/locks/heavy-slots/$owner.slot"){throw 'Own heavy already held'}
 & pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner $owner -StaleHours 1000000 -PollSeconds 1
 if($LASTEXITCODE){throw 'Acquire failed'};$held=$true
 $phase='materials'
 if(Test-Path artifacts/life-r4/baseline-materials.log){throw 'Evidence already exists'}
 & uv run --project tools/worldgen python -u art-source/world/materials/_src/build_all.py *> artifacts/life-r4/baseline-materials.log
 if($LASTEXITCODE){throw 'Materials failed'}
 Save-Step 'odtwórz materiały baseline r4'
 $phase='world'
 & uv run --project tools/worldgen python -u tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> artifacts/life-r4/baseline-world.log
 if($LASTEXITCODE){throw 'World failed'}
 if(Select-String artifacts/life-r4/baseline-world.log -Pattern 'fallback=True' -Quiet){throw 'Unexpected fallback'}
 Save-Step 'wygeneruj World baseline r4'
 $phase='fidelity'
 & uv run --project tools/worldgen python -u tools/worldgen/fidelity/run.py --region bialystok-industrial-c --art artifacts/life-r4/baseline-fidelity *> artifacts/life-r4/baseline-fidelity.log
 if($LASTEXITCODE){throw 'Fidelity failed'}
 & uv run --project tools/worldgen python -m pytest tests/gis/test_road_fidelity.py -q *> artifacts/life-r4/baseline-fidelity-test.log
 if($LASTEXITCODE){throw 'Fidelity test failed'}
 $mode=Get-Content artifacts/life-r4/SOURCE-MODE.json -Raw|ConvertFrom-Json
 $mode.requires_generation=$false
 $mode|ConvertTo-Json|Set-Content artifacts/life-r4/SOURCE-MODE.json
 $phase='proof'
 & uv run --project tools/worldgen python artifacts/life-r4/source-proof.py baseline-generated *> artifacts/life-r4/baseline-source-proof.log
 if($LASTEXITCODE){throw 'Source proof failed'}
 Copy-Item art-source/world/props/street_props.glb artifacts/life-r4/baseline-street_props.glb
 Copy-Item art-source/world/props/props_meta.json artifacts/life-r4/baseline-props_meta.json
 Copy-Item Data/Regions/bialystok-industrial-c/generated/world_manifest.json artifacts/life-r4/baseline-world_manifest.json
 Save-Step 'potwierdź World i fidelity baseline r4'
 $phase='complete';$code=0
} catch {
 Save-Step "zapisz przerwany baseline r4 na etapie $phase"
 throw
} finally {
 if($held){& pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Pool heavy -Owner $owner}
 @{phase=$phase;exit_code=$code;finished=(Get-Date -Format o);source_commit=(git rev-parse HEAD).Trim()}|ConvertTo-Json|Set-Content artifacts/life-r4/baseline-gen-result.json
}

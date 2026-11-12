$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
if((git branch --show-current).Trim() -ne 'gpt-life-r5'){throw 'Wrong branch'}
if(!(Get-Content artifacts/life-r5/prepared-maps.json -Raw|ConvertFrom-Json).pass){throw 'Verify prepared material inputs first'}
if(Test-Path artifacts/life-r5/baseline-world.log){throw 'Baseline evidence already exists'}
if(Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/heavy-slots/gpt-life-r5.slot'){throw 'Own heavy held'}
$phase='acquire';$code=1
function Save-Step([string]$message,[string[]]$files=@()){
 Add-Content artifacts/life-r5/STATUS.md ("`nBaseline ({0}): {1}. Następny etap World/fidelity/kamery; potem świeży import i oględziny przed zmianą palet." -f (Get-Date -Format o),$message)
 git add -u -- Data/Regions/bialystok-industrial-c/generated art-source/world
 git add -f artifacts/life-r5/STATUS.md artifacts/life-r5/SOURCE-MODE.json @files
 git commit -m "wip(life): $message"
 if($LASTEXITCODE){throw 'WIP failed'}
}
& pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner gpt-life-r5 -StaleHours 1000000 -PollSeconds 1
if($LASTEXITCODE){throw 'Acquire failed'}
try {
 $phase='world'
 & uv run --project tools/worldgen python -u tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> artifacts/life-r5/baseline-world.log
 if($LASTEXITCODE){throw 'World failed'}
 if(Select-String artifacts/life-r5/baseline-world.log -Pattern 'fallback=True' -Quiet){throw 'Unexpected fallback'}
 Save-Step 'wygeneruj świeży World palet r5'
 $phase='fidelity'
 & uv run --project tools/worldgen python -u tools/worldgen/fidelity/run.py --region bialystok-industrial-c --art artifacts/life-r5/baseline-fidelity *> artifacts/life-r5/baseline-fidelity.log
 if($LASTEXITCODE){throw 'Fidelity failed'}
 & uv run --project tools/worldgen python -m pytest tests/gis/test_road_fidelity.py -q *> artifacts/life-r5/baseline-fidelity-test.log
 if($LASTEXITCODE){throw 'Fidelity test failed'}
 $mode=Get-Content artifacts/life-r5/SOURCE-MODE.json -Raw|ConvertFrom-Json
 $mode.requires_generation=$false
 $mode|ConvertTo-Json|Set-Content artifacts/life-r5/SOURCE-MODE.json
 $phase='proof'
 & uv run --project tools/worldgen python artifacts/life-r5/source-proof.py baseline-generated *> artifacts/life-r5/baseline-source-proof.log
 if($LASTEXITCODE){throw 'Source proof failed'}
 Copy-Item art-source/world/props/street_props.glb artifacts/life-r5/baseline-street_props.glb
 Copy-Item art-source/world/props/props_meta.json artifacts/life-r5/baseline-props_meta.json
 Copy-Item Data/Regions/bialystok-industrial-c/generated/world_manifest.json artifacts/life-r5/baseline-world_manifest.json
 Copy-Item tools/worldgen/streetscape/life_props.py artifacts/life-r5/baseline-life_props.py
 $phase='cameras'
 if(!(Test-Path artifacts/life-r5/prepare-pallet-cameras.py)){throw 'Finish camera helper before resuming; do not repeat World'}
 & uv run --project tools/worldgen python artifacts/life-r5/prepare-pallet-cameras.py *> artifacts/life-r5/prepare-pallet-cameras.log
 if($LASTEXITCODE){throw 'Pallet camera preparation failed'}
 Save-Step 'potwierdź baseline i rzeczywiste cele palet r5' @('artifacts/life-r5/baseline-generated-source-proof.json','artifacts/life-r5/cameras.json','artifacts/life-r5/pallet-targets.json')
 $phase='complete';$code=0
} catch {
 Save-Step "zapisz przerwany baseline r5 $phase"
 throw
} finally {
 & pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Pool heavy -Owner gpt-life-r5
 @{phase=$phase;exit_code=$code;finished=(Get-Date -Format o);source_commit=(git rev-parse HEAD).Trim()}|ConvertTo-Json|Set-Content artifacts/life-r5/baseline-gen-result.json
}

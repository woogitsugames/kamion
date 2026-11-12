$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
$owner=(git branch --show-current).Trim()
if($owner -ne 'gpt-life-r3'){throw 'Wrong branch'}
$phase='acquire'; $code=1; $held=$false
function Checkpoint([string]$Message){
 Add-Content artifacts/life-r3/STATUS.md ("`nBaseline ({0}): {1}. Następny etap w baseline-gen.ps1; po generacji nowe kamery i PreparedImport." -f (Get-Date -Format o),$Message)
 git add -u -- Data/Regions/bialystok-industrial-c/generated art-source/world
 git add -f -- artifacts/life-r3/STATUS.md
 git commit -m "wip(life): $Message"
 if($LASTEXITCODE){throw 'WIP failed'}
}
try {
 if(Test-Path "C:/Users/matma/Documents/Claude/kamion/artifacts/locks/heavy-slots/$owner.slot"){throw 'Own heavy already held'}
 & pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner $owner -StaleHours 1000000 -PollSeconds 1
 if($LASTEXITCODE){throw 'Acquire failed'}; $held=$true
 $phase='materials'
 if(Test-Path artifacts/life-r3/baseline-materials.log){throw 'Evidence exists'}
 & uv run --project tools/worldgen python -u art-source/world/materials/_src/build_all.py *> artifacts/life-r3/baseline-materials.log
 if($LASTEXITCODE){throw 'Materials failed'}
 Checkpoint 'odtwórz materiały świeżego baseline r3'
 $phase='world'
 if(Test-Path artifacts/life-r3/baseline-world.log){throw 'Evidence exists'}
 & uv run --project tools/worldgen python -u tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> artifacts/life-r3/baseline-world.log
 if($LASTEXITCODE){throw 'World failed'}
 if(Select-String artifacts/life-r3/baseline-world.log -Pattern 'fallback=True' -Quiet){throw 'World fallback'}
 & uv run --project tools/worldgen python artifacts/life-r3/source-proof.py baseline-generated *> artifacts/life-r3/baseline-source-proof.log
 if($LASTEXITCODE){throw 'Source proof failed'}
 Copy-Item art-source/world/props/street_props.glb artifacts/life-r3/baseline-street_props.glb
 Copy-Item art-source/world/props/props_meta.json artifacts/life-r3/baseline-props_meta.json
 Copy-Item Data/Regions/bialystok-industrial-c/generated/world_manifest.json artifacts/life-r3/baseline-world_manifest.json
 Checkpoint 'wygeneruj i potwierdź świeży baseline r3'
 $phase='complete'; $code=0
} catch {
 Checkpoint ("zapisz przerwany baseline r3 na etapie $phase")
 throw
} finally {
 if($held){& pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Pool heavy -Owner $owner}
 @{phase=$phase;exit_code=$code;finished=(Get-Date -Format o);source_commit=(git rev-parse HEAD)}|ConvertTo-Json|Set-Content artifacts/life-r3/baseline-gen-result.json
}

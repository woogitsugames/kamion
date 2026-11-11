$ErrorActionPreference='Stop'
$sourceRoot='C:/Users/matma/Documents/Claude/kamion'
$taskRoot='C:/Users/matma/Documents/Claude/kamion/.claude/worktrees/gpt-car-paint'
$stableCache='C:/Users/matma/Documents/Claude/kamion/.claude/worktrees/gpt-light-r12'
Set-Location $taskRoot
function Copy-Tree([string]$from,[string]$rel,[string]$pattern='*') {
 $src=Join-Path $from $rel;$dst=Join-Path $taskRoot $rel
 if(-not(Test-Path $src)){throw "Missing bootstrap source $src"}
 Write-Output "COPY $from -> $rel ($pattern)"
 & robocopy $src $dst $pattern /E /XJ /R:1 /W:1 /NFL /NDL /NJH /NJS
 if($LASTEXITCODE-ge8){throw "Copy failed $rel exit$LASTEXITCODE"}
}
foreach($rel in @('Data/raw/derived','Data/raw/cc0','art-source/world/cc0/_raw','art-source/world/megascans','Data/photos')){Copy-Tree $sourceRoot $rel}
# Main integration may hold these files open; stable retainedC is cache-only provenance, not source policy.
foreach($rel in @('game/Assets/_Generated','game/Library')){Copy-Tree $stableCache $rel}
# Only ignored PNG products: no copied material generators/specs/tracked source drift.
Copy-Tree $sourceRoot 'art-source/world/materials' '*.png'
Copy-Item (Join-Path $sourceRoot 'art-source/truck/interior/export/SM_CabInterior_LOD0.fbx') (Join-Path $taskRoot 'art-source/truck/interior/export/SM_CabInterior_LOD0.fbx')
foreach($name in @('gugik','osm','refs','mapillary','fab')) {
 $src=Join-Path $sourceRoot "Data/raw/$name";$dst=Join-Path $taskRoot "Data/raw/$name"
 if((Test-Path $src)-and-not(Test-Path $dst)){New-Item -ItemType Junction -Path $dst -Target $src | Out-Null}
}
# Read-only camera metadata copy; placement must not be altered to fit a desired result.
Copy-Item (Join-Path $sourceRoot 'artifacts/cars-r10/car_cams.json') (Join-Path $taskRoot 'artifacts/car-paint-r1/car_cams.json')
Write-Output 'BOOTSTRAP COMPLETE; raw source junctions read-only by task policy; fresh own build/import required.'

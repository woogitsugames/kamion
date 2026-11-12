$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
& uv run --project tools/worldgen python artifacts/life-r2/validate_exact.py after-a-exact after
if($LASTEXITCODE -ne 0){throw 'Candidate exact capture failed validation'}
$library='art-source/world/props/street_props.glb'
$meta='art-source/world/props/props_meta.json'
$original=(Get-FileHash $library).Hash
$originalMeta=(Get-FileHash $meta).Hash
if((Get-FileHash artifacts/life-r2/baseline-street_props.glb).Hash -ne 'C56CBE59B99B61D8CF15C605C6B0B78697C45E76AF8BDAEA404DE7F5602D3CFD'){throw 'Baseline library hash mismatch'}
Copy-Item -LiteralPath $library -Destination artifacts/life-r2/candidate-a-street_props.glb
Copy-Item -LiteralPath $meta -Destination artifacts/life-r2/candidate-a-props_meta.json
@{mode='baseline-library-override';builder_not_executed=$true;source_candidate_sha=(git rev-parse HEAD);library=(Get-FileHash artifacts/life-r2/baseline-street_props.glb).Hash;next='PreparedImport then before-exact; restore candidate source in finally; native remains baseline until reimport'} | ConvertTo-Json | Set-Content artifacts/life-r2/SOURCE-MODE.json
try {
 Copy-Item -LiteralPath artifacts/life-r2/baseline-street_props.glb -Destination $library
 Copy-Item -LiteralPath artifacts/life-r2/baseline-props_meta.json -Destination $meta
 & pwsh -NoProfile -File artifacts/life-r2/unity-phase.ps1 -Phase PreparedImport
 if($LASTEXITCODE -ne 0){throw 'Baseline exact import failed'}
 & pwsh -NoProfile -File artifacts/life-r2/capture-exact.ps1 -Stage before-exact
 if($LASTEXITCODE -ne 0){throw 'Baseline exact capture failed'}
 & uv run --project tools/worldgen python artifacts/life-r2/validate_exact.py before-exact before
 if($LASTEXITCODE -ne 0){throw 'Baseline exact capture validation failed'}
} finally {
 Copy-Item -LiteralPath artifacts/life-r2/candidate-a-street_props.glb -Destination $library
 Copy-Item -LiteralPath artifacts/life-r2/candidate-a-props_meta.json -Destination $meta
 if((Get-FileHash $library).Hash -ne $original -or (Get-FileHash $meta).Hash -ne $originalMeta){throw 'Candidate source restoration failed'}
 @{mode='candidate-a-source-restored';native_library='baseline-or-incomplete-baseline-import';requires_candidate_reimport=$true;restored=(Get-Date -Format o)} | ConvertTo-Json | Set-Content artifacts/life-r2/SOURCE-MODE.json
}


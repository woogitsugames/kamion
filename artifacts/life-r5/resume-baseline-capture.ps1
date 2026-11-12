$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
if((git branch --show-current).Trim() -ne 'gpt-life-r5'){throw 'Wrong branch'}
$old=Get-Content artifacts/life-r5/post-baseline-result.json -Raw|ConvertFrom-Json
if($old.phase -ne 'capture' -or $old.exit_code -ne 1){throw 'Unexpected stopped phase'}
if(Test-Path artifacts/life-r5/before){throw 'Capture directory already exists; inspect'}
if(!(Select-String artifacts/life-r5/prepared-import-20261112-154301.log -Pattern 'IMPORT_RESULT: OK' -Quiet)){throw 'Successful original import not proven'}
$proof=Get-Content artifacts/life-r5/baseline-generated-source-proof.json -Raw|ConvertFrom-Json
foreach($map in @($proof.source_sha,$proof.prepared_medium_textures,$proof.fixtures)){
 foreach($entry in $map.PSObject.Properties){if((Get-FileHash $entry.Name).Hash -ne $entry.Value){throw "Prepared input changed: $($entry.Name)"}}
}
if((Get-FileHash Data/Regions/bialystok-industrial-c/generated/world_manifest.json).Hash -ne $proof.manifest_sha){throw 'Manifest changed'}
foreach($item in $proof.products){if((Get-FileHash $item.file).Hash -ne $item.actual){throw "Raw changed: $($item.file)"}}
function Save-Step([string]$message,[string[]]$files=@()){
 Add-Content artifacts/life-r5/STATUS.md ("`nWznowienie baseline ({0}): {1}. Następny krok capture/LOD/oględziny; oryginalny błąd snapshotu zachowany." -f (Get-Date -Format o),$message)
 git add -f artifacts/life-r5/STATUS.md artifacts/life-r5/SOURCE-MODE.json @files
 git commit -m "wip(life): $message"
 if($LASTEXITCODE){throw 'WIP failed'}
}
$phase='capture';$code=1
try {
 & pwsh -NoProfile -File artifacts/life-r5/capture-exact.ps1 -Stage before
 if($LASTEXITCODE){throw 'Resumed capture failed'}
 & uv run --project tools/worldgen python artifacts/life-r5/validate_exact.py before *> artifacts/life-r5/before-validation.log
 if($LASTEXITCODE){throw 'Baseline metadata failed'}
 $mode=Get-Content artifacts/life-r5/SOURCE-MODE.json -Raw|ConvertFrom-Json
 $mode.requires_shader_compile=$false
 $mode|ConvertTo-Json|Set-Content artifacts/life-r5/SOURCE-MODE.json
 Save-Step 'potwierdź pełny baseline palet po poprawce snapshotu' @('artifacts/life-r5/before-inputs.json','artifacts/life-r5/before-validation.json','artifacts/life-r5/native-material-backups/baseline-native/snapshot.json')
 $phase='native-lod'
 & pwsh -NoProfile -File artifacts/life-r5/diagnose-lod.ps1
 if($LASTEXITCODE){throw 'Native pallet LOD diagnostic failed'}
 Save-Step 'potwierdź natywny LOD baseline palet' @('artifacts/life-r5/baseline-lod-result.json','artifacts/life-r5/yard-native-targets.json')
 $phase='await-author-inspection';$code=0
} catch {
 Save-Step "zapisz przerwane wznowienie baseline $phase"
 throw
} finally {
 @{phase=$phase;exit_code=$code;finished=(Get-Date -Format o);original_result_sha=(Get-FileHash artifacts/life-r5/post-baseline-result.json).Hash;original_import_log_sha=(Get-FileHash artifacts/life-r5/prepared-import-20261112-154301.log).Hash}|ConvertTo-Json|Set-Content artifacts/life-r5/post-baseline-resume-result.json
}

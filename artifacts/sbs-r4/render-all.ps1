$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Push-Location $taskRoot
try {
    $import=Get-Content artifacts/sbs-r4/import-completed.json -Raw | ConvertFrom-Json
    if($import.exit_code -ne 0 -or $import.world_manifest_sha256 -ne (Get-FileHash Data/Regions/bialystok-industrial-c/generated/world_manifest.json).Hash.ToLowerInvariant() -or $import.materials_spec_sha256 -ne (Get-FileHash art-source/world/materials/materials_spec.json).Hash.ToLowerInvariant()){throw 'Imported baseline no longer matches inputs'}
    $renderHead=(& git rev-parse HEAD).Trim()
    & scripts/sbs-gate3.ps1 -Tiers @('Low','High') -Lighting @('overcast','clear') -SlotOwner gpt-sbs -OutputRoot artifacts/sbs-r4/evidence -RenderOnly
    if($LASTEXITCODE -ne 0){throw 'Full SBS render failed'}
    if($renderHead -ne (& git rev-parse HEAD).Trim()){throw 'HEAD changed during full capture'}
    [ordered]@{exit_code=0;git_sha=$renderHead;completed_at_utc=[DateTime]::UtcNow.ToString('o');world_manifest_sha256=$import.world_manifest_sha256;materials_spec_sha256=$import.materials_spec_sha256;expected_raw_count=168;note='Receipt of wrapper completion; final audit still verifies all files and epochs.'} | ConvertTo-Json -Depth 5 | Set-Content artifacts/sbs-r4/full-render-completed.json -Encoding utf8
} finally {Pop-Location}


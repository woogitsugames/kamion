$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Push-Location $root
try {
    $started=[DateTime]::UtcNow
    $head=(& git rev-parse HEAD).Trim()
    $sources=[ordered]@{wrapper=$PSCommandPath;script='scripts/sbs-gate3.ps1';compositor='tools/refs/sbs_gate3.py'}
    $hashes=[ordered]@{};foreach($key in $sources.Keys){$hashes[$key]=(Get-FileHash -LiteralPath $sources[$key]).Hash.ToLowerInvariant()}
    & scripts/sbs-gate3.ps1 -Tiers @('Low','High') -Lighting @('overcast','clear') -SlotOwner gpt-sbs -OutputRoot artifacts/sbs-r4/evidence -ComposeOnly -IncludeDiagnostics
    if($LASTEXITCODE -ne 0){throw 'Full composition failed'}
    foreach($key in $sources.Keys){if($hashes[$key] -ne (Get-FileHash -LiteralPath $sources[$key]).Hash.ToLowerInvariant()){throw 'Composition code changed during run'}}
    [ordered]@{exit_code=0;source_head=$head;started_at_utc=$started.ToString('o');completed_at_utc=[DateTime]::UtcNow.ToString('o');code_sha256=$hashes;inputs_zip_sha256=(Get-FileHash artifacts/sbs-r4/evidence/inputs.zip).Hash.ToLowerInvariant();note='Strict captured inputs; separate heavy lease per state; baseline dataset only'} | ConvertTo-Json -Depth 6 | Set-Content artifacts/sbs-r4/composition-completed.json -Encoding utf8
} finally {Pop-Location}


$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Push-Location $root
try {
    & scripts/sbs-gate3.ps1 -Tiers @('Low','High') -Lighting @('overcast','clear') -SlotOwner gpt-sbs -OutputRoot artifacts/sbs-r3/evidence -ComposeOnly -IncludeDiagnostics -Photometry Data/Regions/bialystok-industrial-c/sbs_photometry.json
    if($LASTEXITCODE -ne 0){throw 'Full composition failed'}
} finally {Pop-Location}

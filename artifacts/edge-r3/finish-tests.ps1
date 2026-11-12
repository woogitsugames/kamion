$ErrorActionPreference = 'Stop'
$env:OMP_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
$env:NUMEXPR_NUM_THREADS = '1'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$slot = 'C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
$owner = (git branch --show-current).Trim()
if ($owner -ne 'gpt-edge-r3') { throw 'Unexpected round' }
while (-not (Test-Path "$PSScriptRoot/corrected-forest-receipt.json")) { Start-Sleep -Seconds 5 }
$audit = Get-Content "$PSScriptRoot/corrected-forest-receipt.json" -Raw | ConvertFrom-Json
if ($audit.exit_code -ne 0) { throw 'Corrected audit must pass first' }
Copy-Item Data/Regions/bialystok-industrial-c/generated/world_manifest.json "$PSScriptRoot/regenerated-world-manifest.json"
$manifest = Get-Content "$PSScriptRoot/regenerated-world-manifest.json" -Raw | ConvertFrom-Json
$chunks = foreach ($chunk in $manifest.chunks) {
    @{id=$chunk.id;file=$chunk.file;sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $chunk.file).Hash.ToLowerInvariant();manifest_sha256=$chunk.sha256}
}
$chunks | ConvertTo-Json -Depth 5 | Set-Content "$PSScriptRoot/cli-chunks-before-gis.json"
& pwsh -File $slot -Acquire -Pool heavy -Owner $owner -PollSeconds 1 -StaleHours 100000
if ($LASTEXITCODE -ne 0) { throw 'Heavy acquisition failed' }
$code = 1
try {
    # Test the required fresh whole-world regeneration, then restore unrelated
    # tracked metadata in post-gis.ps1 after output hashes have been checked.
    Add-Content "$PSScriptRoot/STATUS.md" 'Krok 27: poprawny audyt kurtyn zakończony pod heavy; zachowano świeży manifest i SHA wszystkich 64 plików CLI. Zaczynamy jedyny pełny GIS na zakończenie r3 pod heavy, wobec faktycznej pełnej regeneracji. Cudze metadane zostaną odtworzone dopiero po teście i kontroli SHA w post-gis.ps1; wynik pozostaje otwarty.'
    git add artifacts/edge-r3/STATUS.md
    git commit -m 'WIP edge r3: freeze CLI chunk hashes and start round-end GIS'
    & uv run --project tools/worldgen python -m pytest tests/gis -q *> "$PSScriptRoot/gis-final.log"
    $code = $LASTEXITCODE
} finally {
    & pwsh -File $slot -Release -Pool heavy -Owner $owner -StaleHours 100000
    @{task='RoundEndGis';pool='heavy';owner=$owner;exit_code=$code;finished=(Get-Date -Format o)} |
        ConvertTo-Json | Set-Content "$PSScriptRoot/gis-final-receipt.json"
}
exit $code
